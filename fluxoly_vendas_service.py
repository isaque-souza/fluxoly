"""
fluxoly_vendas_service.py

Regra de negócio pura do domínio Vendas MVP (docs/product/features/VENDAS.md)
— não conhece Flask, `request` nem `jsonify` (ENGINEERING_GUIDE.md §3.1).
Primeiro módulo a nascer com o prefixo `fluxoly_` (ADR-008).

Modelo de domínio vigente para as próximas fases: `ADR-009` (Unidade
Serializada como agregado raiz — Estado Operacional do Ativo × Situação
Comercial em eixos separados, cancelamento/garantia como eventos de
processo, não estado da unidade). Esta sprint (Vendas 1.1 — Histórico +
Detalhe) é só consulta: nenhuma mudança de schema, nenhum cancelamento,
desconto, comissão, garantia ou reserva implementados aqui.

`valor_tabela` (preço de catálogo no momento da venda, de
`unidades_serializadas_service.py::preco_catalogo`) e `valor_unitario`
(preço efetivo, editável pelo vendedor) são guardados separados em
`vendas_itens` -- nenhuma autorização de desconto nesta fatia (qualquer
vendedor pode alterar o preço livremente), mas o schema já preserva os dois
valores para relatórios futuros de desconto/margem sem migração. `desconto`
exposto aqui é só a diferença calculada (`valor_tabela - valor_unitario`),
não uma feature de desconto com aprovação -- essa é a V1.4 do roadmap.

Sequência transacional de `iniciar_venda` (única transação, cliente -> venda
-> item -> unidade -> auditoria -> commit): validações de leitura (cliente,
unidade) rodam antes, em conexões próprias e curtas; a escrita real
(inserir_venda, inserir_item, marcar_como_vendida) roda inteira dentro de uma
única conexão/transação -- qualquer falha no meio reverte tudo, a unidade
nunca fica "vendida" sem uma `venda`/`vendas_itens` real por trás, nem uma
`venda` órfã sem a unidade marcada.

Depende de: `fluxoly_clientes_service.py` (validar cliente),
`fluxoly_unidades_serializadas_service.py` (validar/marcar unidade --
`marcar_como_vendida`, exclusiva deste domínio por ADR-007), `fluxoly_audit.py`.
"""

import sqlite3
from collections import defaultdict
from datetime import date

import fluxoly_caixa_service as caixa_service
import fluxoly_clientes_service as clientes_service
import fluxoly_tipos_garantia_service as tipos_garantia_service
import fluxoly_unidades_serializadas_service as unidades_service
import fluxoly_vendas_repository as repo
from fluxoly_audit import registrar_log_auditoria
from fluxoly_core import calcular_data_fim_garantia

FORMAS_PAGAMENTO_VALIDAS = {"pix", "cartao", "dinheiro", "transferencia"}
PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20

# V1.2 -- Cancelamento (BR-032, VENDAS.md "V1.2 -- Cancelamento"): lista fechada, valor fora
# rejeitado com erro explícito, nunca normalizado -- mesmo padrão de categoria/condicao em
# fluxoly_produtos_service.py (BR-027).
MOTIVOS_CANCELAMENTO_VALIDOS = {
    "cliente_desistiu",
    "erro_lancamento",
    "imei_incorreto",
    "venda_duplicada",
    "pagamento_nao_concluido",
    "produto_indisponivel",
    "outro",
}


class VendaConflitoError(Exception):
    """A unidade deixou de estar disponível entre a pré-checagem e a
    transação de escrita -- outra venda venceu a corrida."""


def _venda_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "cliente_id": row[1],
        "vendedor_id": row[2],
        "forma_pagamento": row[3],
        "valor_total": row[4],
        "status": row[5],
        "observacoes": row[6] or "",
        "criado_em": row[7],
        "cliente_nome": row[8] or "",
        "cliente_telefone": row[9] or "",
        "vendedor_nome": row[10] or "",
        "motivo_cancelamento": row[11],
        "observacao_cancelamento": row[12] or "",
        "cancelado_por": row[13],
        "cancelado_em": row[14],
    }


def _item_para_dict(row):
    valor_tabela = row[7]
    valor_unitario = row[8]
    return {
        "id": row[0],
        "venda_id": row[1],
        "unidade_serializada_id": row[2],
        "produto_id": row[3],
        "produto_nome": row[4],
        "produto_sku": row[5] or "",
        "quantidade": row[6],
        "valor_tabela": valor_tabela,
        "valor_unitario": valor_unitario,
        # Diferença calculada -- o próprio desconto (BR-053: sempre permitido,
        # sempre registrado, nunca exige aprovação). None quando não há
        # preço de tabela para comparar.
        "desconto": round(valor_tabela - valor_unitario, 2) if valor_tabela is not None else None,
        "subtotal": row[9],
        "criado_em": row[10],
        "imei": row[11] or "",
        "motivo_desconto": row[12] or "",
        "desconto_aprovado_em": row[13],
        # V1.4 -- Comissão (BR-047): a ocultação por perfil (vendedor não vê
        # nada de comissão) acontece no controller, nunca aqui -- o service
        # continua perfil-agnóstico, sempre retorna o dado completo.
        "comissao_valor": row[14],
        # V1.5 -- Garantia de Venda (BR-056/BR-057): snapshot completo, sem
        # ocultação por perfil (diferente da comissão) -- qualquer usuário
        # autenticado que vê a venda vê a garantia.
        "tipo_garantia_id": row[15],
        "garantia_nome": row[16],
        "garantia_duracao_meses": row[17],
        "garantia_data_inicio": row[18],
        "garantia_data_fim": row[19],
    }


def iniciar_venda(
    conectar,
    usuario_id,
    cliente_id,
    unidade_serializada_id,
    forma_pagamento,
    valor_unitario,
    tipo_garantia_id,
    observacoes="",
    motivo_desconto=None,
):
    """Retorna (venda_id, erro). `erro` é None em caso de sucesso.

    `usuario_id` é sempre o vendedor (sessão logada) -- nunca escolhido no
    payload, mesmo padrão de auditoria já usado no resto do sistema.

    Desconto (BR-053, revisão de 2026-07-29): nunca bloqueia a venda,
    independente do valor -- sempre permitido e sempre registrado. `motivo`
    é opcional (BR-039). A V1.3 chegou a exigir aprovação acima de um limite
    por vendedor (BR-037/BR-038); revogado no dia seguinte por não refletir
    o fluxo real de negociação da loja -- ver `VENDAS.md` "Revisão do modelo
    de desconto".

    Garantia de Venda (BR-056/BR-057): `tipo_garantia_id` é obrigatório --
    sem default vindo do produto do catálogo, decisão deliberada da
    discovery. Resolvido e congelado (nome/duração/datas) no momento da
    criação; editar o cadastro de Tipos de Garantia depois nunca afeta esta
    venda.
    """
    forma_pagamento = (forma_pagamento or "").strip().lower()
    if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
        return None, "Forma de pagamento inválida."
    if not isinstance(valor_unitario, int | float) or valor_unitario <= 0:
        return None, "Valor deve ser maior que zero."

    tipo_garantia = tipos_garantia_service.obter_tipo_garantia(conectar, tipo_garantia_id)
    if not tipo_garantia or not tipo_garantia["ativo"]:
        return None, "Tipo de Garantia inválido ou inativo."

    cliente = clientes_service.obter_cliente(conectar, cliente_id)
    if not cliente:
        return None, "Cliente não encontrado."

    unidade = unidades_service.obter_unidade(conectar, unidade_serializada_id)
    if not unidade:
        return None, "Unidade não encontrada."
    if unidade["status"] != "disponivel":
        return None, "Unidade não está disponível para venda."

    produto_nome = unidade["origem_label"] or "Aparelho"
    produto_sku = unidade["origem_sku"] or None
    produto_id = unidade["produto_id"]
    valor_tabela = unidade["preco_catalogo"]

    garantia_data_inicio = date.today()
    garantia_data_fim = calcular_data_fim_garantia(garantia_data_inicio, tipo_garantia["duracao_meses"])

    conn = conectar()
    try:
        cursor = conn.cursor()
        venda_id = repo.inserir_venda(cursor, cliente_id, usuario_id, forma_pagamento, valor_unitario, observacoes)
        item_id = repo.inserir_item(
            cursor,
            venda_id,
            unidade_serializada_id,
            produto_id,
            produto_nome,
            produto_sku,
            valor_tabela,
            valor_unitario,
            motivo_desconto or "",
            tipo_garantia_id=tipo_garantia["id"],
            garantia_nome=tipo_garantia["nome"],
            garantia_duracao_meses=tipo_garantia["duracao_meses"],
            garantia_data_inicio=garantia_data_inicio.isoformat(),
            garantia_data_fim=garantia_data_fim.isoformat(),
        )

        sucesso, erro = unidades_service.marcar_como_vendida(cursor, unidade_serializada_id, venda_id, usuario_id)
        if not sucesso:
            raise VendaConflitoError(erro)

        # V1.5 -- Garantia de Venda (BR-057): evento de concessão original,
        # mesmo padrão do lado de Garantia de Reparo (fluxoly_blueprints_api.py).
        registrar_log_auditoria(
            cursor,
            "venda_item",
            item_id,
            usuario_id,
            "garantia_concedida",
            depois={
                "tipo_garantia_id": tipo_garantia["id"],
                "garantia_nome": tipo_garantia["nome"],
                "garantia_duracao_meses": tipo_garantia["duracao_meses"],
                "garantia_data_inicio": garantia_data_inicio.isoformat(),
                "garantia_data_fim": garantia_data_fim.isoformat(),
            },
        )

        registrar_log_auditoria(
            cursor,
            "venda",
            venda_id,
            usuario_id,
            "create",
            depois={
                # venda_id/vendedor_id já são entidade_id/usuario_id da própria linha de
                # audit_log, mas repetidos aqui dentro do JSON para quem filtra/grepa o
                # conteúdo de valor_novo diretamente, sem cruzar com as colunas de fora.
                "venda_id": venda_id,
                "cliente_id": cliente_id,
                "vendedor_id": usuario_id,
                "unidade_serializada_id": unidade_serializada_id,
                "valor_tabela": valor_tabela,
                "valor_total": valor_unitario,
            },
        )

        # Financeiro Mínimo (BR-069, PLAN-financeiro-minimo.md): entrada de
        # caixa na mesma transação -- nunca uma venda "concluida" sem a
        # entrada correspondente, nem o contrário.
        caixa_service.registrar_entrada_de_venda(cursor, venda_id, valor_unitario, usuario_id)

        conn.commit()
    except VendaConflitoError as exc:
        conn.rollback()
        return None, str(exc)
    except sqlite3.IntegrityError:
        # UNIQUE em vendas_itens.unidade_serializada_id -- outra venda já
        # commitou para esta unidade entre a pré-checagem e esta transação
        # (mesma corrida que marcar_como_vendida também protege).
        conn.rollback()
        return None, "Unidade não está mais disponível."
    except Exception as exc:
        conn.rollback()
        return None, str(exc)
    finally:
        conn.close()

    return venda_id, None


def obter_venda_com_itens(conectar, venda_id):
    """Retorna (venda, itens). `venda` é `None` se não encontrada (`itens`
    vem vazio nesse caso). Pensado desde já para múltiplos itens por venda,
    mesmo que esta fatia sempre crie exatamente um."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        venda_row = repo.buscar_por_id(cursor, venda_id)
        if not venda_row:
            return None, []
        itens_rows = repo.buscar_itens_por_venda(cursor, venda_id)
    finally:
        conn.close()
    return _venda_para_dict(venda_row), [_item_para_dict(r) for r in itens_rows]


def listar_vendas(
    conectar,
    cliente_id=None,
    vendedor_id=None,
    forma_pagamento=None,
    status=None,
    data_inicio=None,
    data_fim=None,
    termo="",
    sort="recente",
    page=None,
    per_page=None,
):
    """Histórico de vendas (Sprint Vendas 1.1) -- paginado, com um resumo dos
    itens de cada venda (`itens_resumo`) para a listagem não precisar de uma
    chamada por linha. `termo` busca por nome do cliente, IMEI ou nome do
    produto vendido (ver `fluxoly_vendas_repository.py::_montar_filtros`)."""
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page
    termo = (termo or "").strip()

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar_vendas(
            cursor, cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo
        )
        venda_rows = repo.buscar_paginado(
            cursor,
            cliente_id,
            vendedor_id,
            forma_pagamento,
            status,
            data_inicio,
            data_fim,
            termo,
            sort,
            per_page,
            offset,
        )
        vendas = [_venda_para_dict(r) for r in venda_rows]
        itens_rows = repo.buscar_itens_por_vendas(cursor, [v["id"] for v in vendas])
    finally:
        conn.close()

    itens_por_venda = defaultdict(list)
    for row in itens_rows:
        itens_por_venda[row[1]].append(_item_para_dict(row))

    for venda in vendas:
        venda["itens_resumo"] = itens_por_venda.get(venda["id"], [])

    return {
        "items": vendas,
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def cancelar_venda(conectar, venda_id, usuario_id, usuario_perfil, motivo, observacao=None):
    """V1.2 -- Cancelamento (BR-031 a BR-036, VENDAS.md "V1.2 -- Cancelamento"). Retorna
    (sucesso, erro). `erro` é None em caso de sucesso.

    `admin` cancela qualquer venda; `vendedor` só as que ele mesmo realizou; qualquer outro
    perfil é negado -- checagem fina de dono vive aqui (service), não no controller, mesma
    filosofia já aplicada ao índice único: o banco/controller são a última linha de defesa,
    a regra de negócio vive na camada de serviço. Motivo é lista fechada; 'outro' exige
    observação. Terminal: só transiciona de 'concluida' para 'cancelada' (Princípio da
    Imutabilidade da Venda) -- não existe reativação.
    """
    motivo = (motivo or "").strip().lower()
    observacao = (observacao or "").strip()
    if motivo not in MOTIVOS_CANCELAMENTO_VALIDOS:
        return False, "Motivo de cancelamento inválido."
    if motivo == "outro" and not observacao:
        return False, "Descrição obrigatória quando o motivo é 'Outro'."

    venda, _itens = obter_venda_com_itens(conectar, venda_id)
    if not venda:
        return False, "Venda não encontrada."
    if venda["status"] != "concluida":
        return False, "Venda não pode ser cancelada (já cancelada ou em outro estado)."
    if usuario_perfil == "admin":
        pass
    elif usuario_perfil == "vendedor":
        if venda["vendedor_id"] != usuario_id:
            return False, "Permissão negada — só é possível cancelar as próprias vendas."
    else:
        return False, "Permissão negada."

    conn = conectar()
    try:
        cursor = conn.cursor()
        linhas = repo.cancelar_venda(cursor, venda_id, motivo, observacao, usuario_id)
        if linhas == 0:
            conn.rollback()
            return False, "Venda não pode ser cancelada (estado mudou)."

        repo.desativar_itens_da_venda(cursor, venda_id)

        for unidade_id in repo.buscar_unidades_da_venda(cursor, venda_id):
            sucesso, erro = unidades_service.liberar_unidade_para_venda(cursor, unidade_id, usuario_id)
            if not sucesso:
                raise VendaConflitoError(erro)

        # V1.4 -- Comissão (BR-051): zera a comissão de qualquer item que já
        # tinha valor atribuído, na mesma transação do cancelamento --
        # sempre com evento de auditoria, nunca uma mutação silenciosa.
        for item_id, comissao_anterior in repo.buscar_itens_com_comissao_por_venda(cursor, venda_id):
            repo.zerar_comissao_item(cursor, item_id)
            registrar_log_auditoria(
                cursor,
                "venda_item",
                item_id,
                usuario_id,
                "comissao_alterada",
                antes={"comissao_valor": comissao_anterior},
                depois={"comissao_valor": 0},
            )

        # V1.5 -- Garantia de Venda (BR-058): mesmo padrão da comissão acima --
        # zera o snapshot inteiro de qualquer item com Garantia de Venda
        # concedida, na mesma transação do cancelamento, sempre com evento de
        # auditoria.
        for (
            item_id,
            tipo_garantia_id,
            garantia_nome,
            garantia_duracao_meses,
            garantia_data_inicio,
            garantia_data_fim,
        ) in repo.buscar_itens_com_garantia_por_venda(cursor, venda_id):
            repo.zerar_garantia_item(cursor, item_id)
            registrar_log_auditoria(
                cursor,
                "venda_item",
                item_id,
                usuario_id,
                "garantia_alterada",
                antes={
                    "tipo_garantia_id": tipo_garantia_id,
                    "garantia_nome": garantia_nome,
                    "garantia_duracao_meses": garantia_duracao_meses,
                    "garantia_data_inicio": garantia_data_inicio,
                    "garantia_data_fim": garantia_data_fim,
                },
                depois=None,
            )

        registrar_log_auditoria(
            cursor,
            "venda",
            venda_id,
            usuario_id,
            "status_change",
            antes="concluida",
            depois={"status": "cancelada", "motivo": motivo, "observacao": observacao or None},
        )

        # Financeiro Mínimo (BR-069, PLAN-financeiro-minimo.md): estorna a
        # entrada de caixa correspondente na mesma transação do cancelamento.
        caixa_service.estornar_entrada_de_venda(cursor, venda_id, usuario_id)

        conn.commit()
    except VendaConflitoError as exc:
        conn.rollback()
        return False, str(exc)
    except Exception as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()

    return True, None


def ajustar_desconto_item(conectar, venda_id, item_id, usuario_id, usuario_perfil, valor_unitario_novo, motivo):
    """Ajuste Comercial Autorizado (BR-043) -- a única exceção formalmente
    definida ao Princípio da Imutabilidade da Venda (BR-034, que continua
    válido para todo o resto: cliente, IMEI/unidade, forma de pagamento,
    vendedor, data, status, outros itens). Só `admin`; motivo é OBRIGATÓRIO
    aqui (diferente do motivo opcional na criação, BR-039) -- um ajuste
    pós-venda é excepcional o suficiente para exigir justificativa. Retorna
    (sucesso, erro)."""
    if usuario_perfil != "admin":
        return False, "Permissão negada."
    motivo = (motivo or "").strip()
    if not motivo:
        return False, "Motivo é obrigatório para o ajuste comercial."
    if not isinstance(valor_unitario_novo, int | float) or valor_unitario_novo <= 0:
        return False, "Valor deve ser maior que zero."

    conn = conectar()
    try:
        cursor = conn.cursor()
        item_row = repo.buscar_item_por_id(cursor, venda_id, item_id)
        if not item_row:
            conn.rollback()
            return False, "Item não encontrado."
        valor_anterior = item_row[2]

        # Compare-and-swap: revalida `status='concluida'` NO MOMENTO da escrita,
        # não confia no estado lido acima -- protege contra a venda ser
        # cancelada entre a leitura e este ajuste (estado obsoleto).
        linhas = repo.ajustar_valor_item(cursor, venda_id, item_id, valor_unitario_novo)
        if linhas == 0:
            conn.rollback()
            return False, "Venda não pode ser ajustada (cancelada ou em outro estado)."

        # Recalculado sempre a partir da soma de todos os itens ativos --
        # nunca só o delta deste item (BR-043).
        repo.recalcular_valor_total_venda(cursor, venda_id)

        registrar_log_auditoria(
            cursor,
            "venda_item",
            item_id,
            usuario_id,
            "ajuste_desconto",
            antes={"valor_unitario": valor_anterior},
            depois={"valor_unitario": valor_unitario_novo, "motivo": motivo},
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()

    return True, None


def _evento_historico_item_para_dict(row):
    return {
        "id": row[0],
        "acao": row[1],
        "valor_anterior": row[2],
        "valor_novo": row[3],
        "criado_em": row[4],
        "usuario_nome": row[5] or "",
    }


def obter_historico_desconto_item(conectar, item_id):
    """Histórico de Ajustes Comerciais do item (BR-043) -- só leitura."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        rows = repo.buscar_historico_desconto_item(cursor, item_id)
    finally:
        conn.close()
    return [_evento_historico_item_para_dict(r) for r in rows]


def atribuir_comissao_item(conectar, venda_id, item_id, usuario_id, usuario_perfil, valor):
    """V1.4 -- Comissão (BR-044 a BR-049). Só `admin`/`financeiro` (a checagem
    de perfil vive no controller, via `usuario_pode_financeiro` -- aqui só
    valida o dado). `valor` sempre em R$, sem campo de "tipo" (BR-048) --
    qualquer política de comissão da loja usa a mesma estrutura. Mesmo
    compare-and-swap do Ajuste Comercial: rejeita se a venda não está
    `concluida` no momento da escrita (BR-034). Retorna (sucesso, erro)."""
    if not isinstance(valor, int | float) or valor < 0:
        return False, "Valor deve ser maior ou igual a zero."

    conn = conectar()
    try:
        cursor = conn.cursor()
        item_row = repo.buscar_comissao_item(cursor, venda_id, item_id)
        if not item_row:
            conn.rollback()
            return False, "Item não encontrado."
        comissao_anterior = item_row[1]

        linhas = repo.atribuir_comissao_item(cursor, venda_id, item_id, valor)
        if linhas == 0:
            conn.rollback()
            return False, "Venda não pode receber comissão (cancelada ou em outro estado)."

        registrar_log_auditoria(
            cursor,
            "venda_item",
            item_id,
            usuario_id,
            "comissao_alterada",
            antes={"comissao_valor": comissao_anterior},
            depois={"comissao_valor": valor},
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()

    return True, None


def obter_historico_comissao_item(conectar, item_id):
    """Histórico de alterações de comissão do item (BR-049) -- só leitura,
    restrito a `admin`/`financeiro` (checagem no controller)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        rows = repo.buscar_historico_comissao_item(cursor, item_id)
    finally:
        conn.close()
    return [_evento_historico_item_para_dict(r) for r in rows]


def corrigir_garantia_item(conectar, venda_id, item_id, usuario_id, usuario_perfil, tipo_garantia_id):
    """V1.5 -- Garantia de Venda (BR-059). Só `admin` (mais restrito que a
    atribuição original, `admin`/`vendedor` -- mesma assimetria do Ajuste
    Comercial, BR-043). Sem motivo obrigatório (diferente do Ajuste
    Comercial, igual à correção de comissão). Recalcula `garantia_data_fim` a
    partir da data de início já concedida -- corrigir o Tipo de Garantia não
    é reemitir a garantia a partir de hoje. Mesmo compare-and-swap do Ajuste
    Comercial/Comissão: rejeita se a venda não está mais `concluida`. Retorna
    (sucesso, erro)."""
    if usuario_perfil != "admin":
        return False, "Permissão negada."

    tipo_garantia = tipos_garantia_service.obter_tipo_garantia(conectar, tipo_garantia_id)
    if not tipo_garantia or not tipo_garantia["ativo"]:
        return False, "Tipo de Garantia inválido ou inativo."

    conn = conectar()
    try:
        cursor = conn.cursor()
        item_row = repo.buscar_garantia_item(cursor, venda_id, item_id)
        if not item_row:
            conn.rollback()
            return False, "Item não encontrado."
        (
            _id,
            tipo_garantia_id_anterior,
            garantia_nome_anterior,
            garantia_duracao_meses_anterior,
            garantia_data_inicio_anterior,
            garantia_data_fim_anterior,
        ) = item_row

        data_inicio = (
            date.fromisoformat(garantia_data_inicio_anterior) if garantia_data_inicio_anterior else date.today()
        )
        garantia_data_fim = calcular_data_fim_garantia(data_inicio, tipo_garantia["duracao_meses"])

        linhas = repo.corrigir_garantia_item(
            cursor,
            venda_id,
            item_id,
            tipo_garantia["id"],
            tipo_garantia["nome"],
            tipo_garantia["duracao_meses"],
            data_inicio.isoformat(),
            garantia_data_fim.isoformat(),
        )
        if linhas == 0:
            conn.rollback()
            return False, "Venda não pode ser corrigida (cancelada ou em outro estado)."

        registrar_log_auditoria(
            cursor,
            "venda_item",
            item_id,
            usuario_id,
            "garantia_alterada",
            antes={
                "tipo_garantia_id": tipo_garantia_id_anterior,
                "garantia_nome": garantia_nome_anterior,
                "garantia_duracao_meses": garantia_duracao_meses_anterior,
                "garantia_data_inicio": garantia_data_inicio_anterior,
                "garantia_data_fim": garantia_data_fim_anterior,
            },
            depois={
                "tipo_garantia_id": tipo_garantia["id"],
                "garantia_nome": tipo_garantia["nome"],
                "garantia_duracao_meses": tipo_garantia["duracao_meses"],
                "garantia_data_inicio": data_inicio.isoformat(),
                "garantia_data_fim": garantia_data_fim.isoformat(),
            },
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()

    return True, None


def obter_historico_garantia_item(conectar, item_id):
    """Histórico de correções da Garantia de Venda do item (BR-059) -- só
    leitura, aberto a qualquer usuário autenticado (mesmo padrão do
    histórico de desconto, diferente do de comissão)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        rows = repo.buscar_historico_garantia_item(cursor, item_id)
    finally:
        conn.close()
    return [_evento_historico_item_para_dict(r) for r in rows]


# Mesmo limiar de "vencendo" da garantia de reparo (`api_garantias.py::_classificar_garantia`),
# para o painel unificado não classificar venda e OS com réguas diferentes.
DIAS_GARANTIA_VENCENDO = 7


def classificar_garantia(dias_restantes):
    if dias_restantes is None:
        return "desconhecida"
    if dias_restantes < 0:
        return "vencida"
    if dias_restantes <= DIAS_GARANTIA_VENCENDO:
        return "vencendo"
    return "ativa"


def listar_garantias_venda(conectar, termo="", hoje=None):
    """Painel de garantias unificado -- garantias de venda (BR-056/BR-057) com
    dias restantes e status, mais a contagem por status. Leitura pura do
    snapshot gravado em `vendas_itens` (nunca recalcula pelo tipo de garantia
    atual, BR-057)."""
    hoje = hoje or date.today()
    conn = conectar()
    try:
        rows = repo.buscar_garantias_venda(conn.cursor(), termo)
    finally:
        conn.close()

    items = []
    for row in rows:
        (item_id, venda_id, venda_criado_em, cliente_id, cliente_nome, produto_nome, imei,
         garantia_nome, garantia_data_inicio, garantia_data_fim) = row
        try:
            fim = date.fromisoformat(str(garantia_data_fim)[:10])
            dias = (fim - hoje).days
        except ValueError:
            dias = None
        items.append({
            "item_id": item_id,
            "venda_id": venda_id,
            "venda_criado_em": venda_criado_em,
            "cliente_id": cliente_id,
            "cliente_nome": cliente_nome or "",
            "produto_nome": produto_nome or "",
            "imei": imei or "",
            "garantia_nome": garantia_nome or "",
            "garantia_data_inicio": garantia_data_inicio,
            "garantia_data_fim": garantia_data_fim,
            "dias_restantes": dias,
            "status_garantia": classificar_garantia(dias),
        })

    contagem = {s: sum(1 for i in items if i["status_garantia"] == s) for s in ("ativa", "vencendo", "vencida")}
    return {"items": items, "total": len(items), **contagem}


def resumir_vendas_periodo(conectar, inicio=None, fim=None):
    """Dashboard somando vendas e OS (PLAN-dashboard-vendas-os.md): faturamento,
    quantidade, ticket médio e ranking por vendedor das vendas concluídas no
    período. Sem lucro -- o custo do aparelho é do domínio Compra de Aparelhos
    (BR-092) e é composto no endpoint, não aqui (evita import circular)."""
    conn = conectar()
    try:
        rows = repo.resumir_vendas_por_vendedor(conn.cursor(), inicio, fim)
    finally:
        conn.close()
    quantidade = sum(r[1] for r in rows)
    faturamento = round(sum(r[2] or 0.0 for r in rows), 2)
    return {
        "quantidade": quantidade,
        "faturamento": faturamento,
        "ticket_medio": round(faturamento / quantidade, 2) if quantidade else 0,
        "por_vendedor": [
            {"vendedor": r[0] or "—", "quantidade": r[1], "faturamento": round(r[2] or 0.0, 2)} for r in rows
        ],
    }


ROTULOS_FORMA_PAGAMENTO = {"pix": "Pix", "cartao": "Cartão", "dinheiro": "Dinheiro", "transferencia": "Transferência"}


def montar_recibo_venda(venda, itens, loja, cliente_cadastro):
    """BR-103 -- conteúdo do recibo de venda para o cliente. Retorna (recibo, erro).

    Só o que está montado aqui sai para o cliente: produto, IMEI, valor praticado e garantia
    de cada item, total e forma de pagamento. Nunca custo, lucro, comissão, preço de tabela
    nem motivo de desconto. `cliente_cadastro` já vem com o CPF/CNPJ apagado para quem não
    pode lê-lo (KI-045, decidido no controller)."""
    if not venda:
        return None, "Venda não encontrada."
    if venda["status"] != "concluida":
        return None, "Venda cancelada não gera recibo."
    if not (loja.get("nome_fantasia") or "").strip():
        return None, "Cadastre os Dados da Loja antes de gerar documentos."

    cliente = {"nome": venda["cliente_nome"], "telefone": venda["cliente_telefone"], "email": "", "cpf_cnpj": ""}
    if cliente_cadastro:
        for chave in ("nome", "telefone", "email", "cpf_cnpj"):
            cliente[chave] = cliente_cadastro.get(chave) or cliente[chave]

    return {
        "loja": {
            chave: loja.get(chave) or ""
            for chave in ("nome_fantasia", "razao_social", "cnpj", "telefone", "email", "endereco")
        },
        "termos": loja.get("termos_garantia") or "",
        "cliente": cliente,
        "venda": {
            "id": venda["id"],
            "data": venda["criado_em"],
            "vendedor": venda["vendedor_nome"],
            "forma_pagamento": ROTULOS_FORMA_PAGAMENTO.get(venda["forma_pagamento"], venda["forma_pagamento"] or ""),
            "valor_total": round(venda["valor_total"] or 0, 2),
            "observacoes": venda["observacoes"],
            "itens": [
                {
                    "produto": item["produto_nome"],
                    "imei": item["imei"],
                    "valor": round(item["valor_unitario"] or 0, 2),
                    "garantia": (
                        {
                            "nome": item["garantia_nome"],
                            "duracao_meses": item["garantia_duracao_meses"],
                            "data_fim": item["garantia_data_fim"] or "",
                        }
                        if item["garantia_nome"]
                        else None
                    ),
                }
                for item in itens
            ],
        },
    }, None
