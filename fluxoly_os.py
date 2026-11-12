from datetime import datetime

from fluxoly_core import (
    STATUS_CANCELADO,
    STATUS_FINALIZADO,
    TIPO_OS_INTERNA,
    calcular_data_fim_garantia,
    texto_limpo,
    to_float,
)


def _consumir_lotes_fifo(cursor, estoque_id, quantidade):
    restante = int(quantidade or 0)
    if restante <= 0:
        return

    cursor.execute(
        """
        SELECT id, COALESCE(quantidade_disponivel, 0)
        FROM estoque_lotes
        WHERE estoque_id=? AND COALESCE(quantidade_disponivel, 0) > 0
        ORDER BY COALESCE(data_compra, '') ASC, id ASC
        """,
        (estoque_id,),
    )
    lotes = cursor.fetchall()

    for lote_id, disponivel in lotes:
        if restante <= 0:
            break
        consumir = min(restante, int(disponivel or 0))
        if consumir <= 0:
            continue
        cursor.execute(
            "UPDATE estoque_lotes SET quantidade_disponivel = MAX(0, quantidade_disponivel - ?) WHERE id=?",
            (consumir, lote_id),
        )
        restante -= consumir


def _criar_lote_retorno(cursor, estoque_id, quantidade, valor, fornecedor, observacoes):
    qtd = int(quantidade or 0)
    if qtd <= 0:
        return
    data_ref = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        """
        INSERT INTO estoque_lotes (
            estoque_id, fornecedor, valor_compra, quantidade, quantidade_disponivel, data_compra, observacoes, criado_em
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            estoque_id,
            fornecedor or "Nao informado",
            float(valor or 0),
            qtd,
            qtd,
            data_ref,
            observacoes or "devolucao",
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        ),
    )


def extrair_reparo_ids(formulario):
    valores = formulario.getlist("reparo_ids")
    if not valores:
        valor_unico = (formulario.get("reparo_id") or "").strip()
        if valor_unico:
            valores = [valor_unico]

    ids = []
    vistos = set()
    for valor in valores:
        texto = str(valor or "").strip()
        if not texto:
            continue
        try:
            reparo_id = int(texto)
        except ValueError as exc:
            raise ValueError("Reparo invalido selecionado.") from exc
        if reparo_id in vistos:
            continue
        vistos.add(reparo_id)
        ids.append(reparo_id)
    return ids


def validar_reparo_ids(cursor, reparo_ids):
    if not reparo_ids:
        return False

    placeholders = ",".join("?" for _ in reparo_ids)
    cursor.execute(
        f"SELECT id FROM reparos WHERE id IN ({placeholders})",
        reparo_ids,
    )
    encontrados = {row[0] for row in cursor.fetchall()}
    return len(encontrados) == len(reparo_ids)


def salvar_reparos_os(cursor, os_id, reparo_ids):
    """Sincroniza `os_reparos` com `reparo_ids` de forma não-destrutiva: só
    remove linhas cujo `reparo_id` saiu da lista e só insere as que entraram
    -- nunca um DELETE+INSERT cego de todas. Necessário desde a V1.5 (Garantia
    de Reparo, BR-062): as colunas de snapshot de garantia vivem nesta mesma
    linha (sem `id` substituto, chave é o par `os_id`+`reparo_id`); um
    DELETE+INSERT cego apagaria silenciosamente a garantia já concedida de
    qualquer linha mantida, mesmo numa edição que não mexe em status/reparos."""
    reparo_ids = list(reparo_ids or [])
    cursor.execute("SELECT reparo_id FROM os_reparos WHERE os_id=?", (os_id,))
    atuais = {row[0] for row in cursor.fetchall()}
    novos = set(reparo_ids)

    for reparo_id in atuais - novos:
        cursor.execute("DELETE FROM os_reparos WHERE os_id=? AND reparo_id=?", (os_id, reparo_id))
    for reparo_id in novos - atuais:
        cursor.execute("INSERT INTO os_reparos (os_id, reparo_id) VALUES (?, ?)", (os_id, reparo_id))

    cursor.execute(
        "UPDATE os SET reparo_id=? WHERE id=?",
        (reparo_ids[0] if reparo_ids else None, os_id),
    )


def obter_ou_criar_reparo(cursor, nome):
    nome_limpo = texto_limpo(nome)
    if not nome_limpo:
        return None

    cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?)", (nome_limpo,))
    row = cursor.fetchone()
    if row:
        return row[0]

    cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (nome_limpo,))
    return cursor.lastrowid


def obter_reparos_por_os(cursor):
    cursor.execute(
        """
        SELECT
            os_reparos.os_id,
            reparos.id,
            COALESCE(reparos.nome, '')
        FROM os_reparos
        JOIN reparos ON reparos.id = os_reparos.reparo_id
        ORDER BY reparos.nome
        """
    )
    mapa = {}
    for os_id, reparo_id, nome in cursor.fetchall():
        if os_id not in mapa:
            mapa[os_id] = {"ids": [], "nomes": []}
        mapa[os_id]["ids"].append(reparo_id)
        if nome:
            mapa[os_id]["nomes"].append(nome)
    return mapa


# V1.5 -- Garantia de Reparo (BR-061 a BR-065, docs/engineering/plans/PLAN-V1.5-Garantia.md).
# `os_reparos` tem PRIMARY KEY composta (os_id, reparo_id), sem coluna `id` própria -- toda
# consulta/gravação por linha usa esse par, nunca um id substituto. Auditoria (`audit_log`)
# usa `entidade_id=os_id` (não o par) porque `entidade_id` é uma coluna INTEGER única; o
# `reparo_id` de cada linha vai dentro do JSON de `antes`/`depois` e é filtrado via
# `json_extract` -- decisão de implementação (não de regra de negócio), documentada aqui por
# não ser óbvia given a ausência de id substituto na tabela.


def buscar_reparo_ids_da_os(cursor, os_id):
    cursor.execute("SELECT reparo_id FROM os_reparos WHERE os_id=?", (os_id,))
    return [row[0] for row in cursor.fetchall()]


def resolver_garantias_reparo(garantias_payload, reparo_ids, resolver_tipo_garantia):
    """BR-061 -- exige um Tipo de Garantia válido e ativo para cada linha de
    reparo da OS antes de concluí-la. `garantias_payload` é o dict
    `{reparo_id: tipo_garantia_id}` recebido do cliente (chaves podem chegar
    como string, via JSON); `resolver_tipo_garantia` é uma função
    `tipo_garantia_id -> dict|None` injetada pelo chamador -- este módulo
    permanece sem I/O de `tipos_garantia` (essa consulta vive em
    `fluxoly_tipos_garantia_service.py`, mesma regra de camadas do resto do
    domínio). Retorna (lista de tuplas `(reparo_id, tipo_garantia)`, erro)."""
    resolvidos = []
    for reparo_id in reparo_ids:
        tipo_garantia_id = garantias_payload.get(reparo_id, garantias_payload.get(str(reparo_id)))
        if tipo_garantia_id is None:
            return None, f"Tipo de Garantia obrigatório para o reparo {reparo_id}."
        tipo_garantia = resolver_tipo_garantia(tipo_garantia_id)
        if not tipo_garantia or not tipo_garantia["ativo"]:
            return None, f"Tipo de Garantia inválido ou inativo para o reparo {reparo_id}."
        resolvidos.append((reparo_id, tipo_garantia))
    return resolvidos, None


def gravar_garantias_reparo(cursor, os_id, resolvidos, data_inicio):
    """Snapshot completo por linha (BR-062) -- `garantia_data_fim` calculado
    a partir de `data_inicio` (= data de finalização da OS), nunca um JOIN ao
    vivo com `tipos_garantia`."""
    for reparo_id, tipo_garantia in resolvidos:
        data_fim = calcular_data_fim_garantia(data_inicio, tipo_garantia["duracao_meses"])
        cursor.execute(
            """
            UPDATE os_reparos
            SET tipo_garantia_id=?, garantia_nome=?, garantia_duracao_meses=?,
                garantia_data_inicio=?, garantia_data_fim=?
            WHERE os_id=? AND reparo_id=?
            """,
            (
                tipo_garantia["id"], tipo_garantia["nome"], tipo_garantia["duracao_meses"],
                data_inicio.isoformat(), data_fim.isoformat(), os_id, reparo_id,
            ),
        )


def buscar_linhas_com_garantia_da_os(cursor, os_id):
    """BR-064 -- linhas de reparo da OS com Garantia de Reparo já concedida
    (`tipo_garantia_id` não nulo) -- usado no cancelamento pós-conclusão para
    zerar cada uma e registrar o evento de auditoria correspondente."""
    cursor.execute(
        """
        SELECT reparo_id, tipo_garantia_id, garantia_nome, garantia_duracao_meses,
               garantia_data_inicio, garantia_data_fim
        FROM os_reparos WHERE os_id=? AND tipo_garantia_id IS NOT NULL
        """,
        (os_id,),
    )
    return cursor.fetchall()


def zerar_garantia_reparo(cursor, os_id, reparo_id):
    """BR-064 -- invalida a Garantia de Reparo de uma linha quando a OS é
    cancelada pós-conclusão. Zera o snapshot inteiro (mesmo padrão de
    `fluxoly_vendas_repository.py::zerar_garantia_item`)."""
    cursor.execute(
        """
        UPDATE os_reparos
        SET tipo_garantia_id=NULL, garantia_nome=NULL, garantia_duracao_meses=NULL,
            garantia_data_inicio=NULL, garantia_data_fim=NULL
        WHERE os_id=? AND reparo_id=?
        """,
        (os_id, reparo_id),
    )


def buscar_garantia_reparo(cursor, os_id, reparo_id):
    """Lê o snapshot atual da linha antes de uma correção (BR-065) --
    necessário para o evento de auditoria registrar o valor_anterior real."""
    cursor.execute(
        """
        SELECT tipo_garantia_id, garantia_nome, garantia_duracao_meses,
               garantia_data_inicio, garantia_data_fim
        FROM os_reparos WHERE os_id=? AND reparo_id=?
        """,
        (os_id, reparo_id),
    )
    return cursor.fetchone()


def corrigir_garantia_reparo(cursor, os_id, reparo_id, tipo_garantia, data_inicio):
    """BR-065 -- mesmo compare-and-swap do Ajuste Comercial/Comissão de
    Vendas: só corrige se a OS ainda está `Finalizado` no momento da escrita
    (uma OS cancelada já teve a garantia zerada, BR-064). Retorna o número de
    linhas afetadas."""
    data_fim = calcular_data_fim_garantia(data_inicio, tipo_garantia["duracao_meses"])
    cursor.execute(
        """
        UPDATE os_reparos
        SET tipo_garantia_id=?, garantia_nome=?, garantia_duracao_meses=?,
            garantia_data_inicio=?, garantia_data_fim=?
        WHERE os_id=? AND reparo_id=?
          AND EXISTS (SELECT 1 FROM os WHERE id=os_reparos.os_id AND status=?)
        """,
        (
            tipo_garantia["id"], tipo_garantia["nome"], tipo_garantia["duracao_meses"],
            data_inicio.isoformat(), data_fim.isoformat(), os_id, reparo_id, STATUS_FINALIZADO,
        ),
    )
    return cursor.rowcount


def buscar_historico_garantia_reparo(cursor, os_id, reparo_id):
    """Histórico de correções/zeragens da Garantia de Reparo da linha
    (BR-065), mais recente primeiro -- filtra por `reparo_id` dentro do JSON
    de `antes`/`depois` (ver nota de módulo sobre a chave de auditoria)."""
    cursor.execute(
        """
        SELECT a.id, a.acao, a.valor_anterior, a.valor_novo, a.criado_em, COALESCE(u.nome, '')
        FROM audit_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.entidade = 'os_reparo' AND a.entidade_id = ?
          AND (
              json_extract(a.valor_anterior, '$.reparo_id') = ?
              OR json_extract(a.valor_novo, '$.reparo_id') = ?
          )
        ORDER BY a.id DESC
        """,
        (os_id, reparo_id, reparo_id),
    )
    return cursor.fetchall()


# Whitelist do fragmento SQL interpolado abaixo (achado da 2a triagem Aikido,
# docs/security/SECURITY_AUDIT_2026-07.md) -- hoje todo chamador passa o
# mesmo literal fixo "os.id DESC", nunca algo vindo do cliente direto no SQL.
# Mesmo assim, `order_by` era interpolado sem validacao dentro da funcao --
# corrigido para nao depender de todo chamador presente e futuro fazer isso
# certo sozinho.
_ORDENACOES_OS = {
    "os.id DESC": "os.id DESC",
    "os.id ASC": "os.id ASC",
}


def carregar_os_com_relacoes(cursor, order_by="os.id DESC"):
    order_by_sql = _ORDENACOES_OS.get(order_by, _ORDENACOES_OS["os.id DESC"])
    cursor.execute(
        f"""
        SELECT
            os.id,
            os.tipo,
            os.cliente,
            os.aparelho,
            os.tecnico,
            os.reparo_id,
            os.status,
            COALESCE(os.valor_cobrado, 0),
            COALESCE(os.valor_descontado, 0),
            COALESCE(os.custo_pecas, 0),
            COALESCE(os.data, ''),
            COALESCE(os.observacoes, ''),
            COALESCE(os.modelo, ''),
            COALESCE(os.vendedor, ''),
            COALESCE(os.cor, ''),
            COALESCE(os.imei, ''),
            COALESCE(os.origem_integracao, ''),
            COALESCE(os.id_externo_integracao, ''),
            COALESCE(os.data_previsao, '')
        FROM os
        ORDER BY {order_by_sql}
        """
    )
    dados = cursor.fetchall()
    reparos_por_os = obter_reparos_por_os(cursor)

    cursor.execute(
        """
        SELECT os_id, COALESCE(SUM(valor), 0)
        FROM os_pecas
        GROUP BY os_id
        """
    )
    custos = {row[0]: row[1] or 0 for row in cursor.fetchall()}
    return dados, reparos_por_os, custos


def registrar_movimentacao(cursor, estoque_id, tipo, quantidade):
    cursor.execute(
        """
        INSERT INTO movimentacoes (estoque_id, tipo, quantidade, data)
        VALUES (?, ?, ?, ?)
        """,
        (estoque_id, tipo, quantidade, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def modelo_compativel(modelo_peca, modelo_os):
    modelo_os_norm = (modelo_os or "").strip().lower()
    if not modelo_os_norm:
        return False

    modelo_peca_norm = (modelo_peca or "").strip().lower()
    if not modelo_peca_norm:
        return True

    tokens = [t.strip() for t in modelo_peca_norm.replace(";", ",").replace("|", ",").replace("/", ",").split(",")]
    tokens = [t for t in tokens if t]
    if not tokens:
        return True

    return any(token in modelo_os_norm or modelo_os_norm in token for token in tokens)


def ler_valores_financeiros_form(formulario):
    valor_cobrado = to_float((formulario.get("valor_cobrado") or "").strip(), 0)
    valor_descontado = to_float((formulario.get("valor_descontado") or "").strip(), 0)
    if valor_cobrado < 0 or valor_descontado < 0:
        raise ValueError("Valores financeiros nao podem ser negativos.")
    return valor_cobrado, valor_descontado


def vendedor_valido(vendedor, vendedores_validos):
    if not vendedor:
        return True
    return vendedor in vendedores_validos


def consumir_peca_da_os(cursor, os_id, estoque_id):
    cursor.execute(
        """
        SELECT quantidade, valor, descricao, fornecedor, modelo
        FROM estoque
        WHERE id=?
        """,
        (estoque_id,),
    )
    result = cursor.fetchone()

    if not result:
        return False, "Peca nao encontrada no estoque."

    estoque_atual, valor_peca, descricao_peca, fornecedor_peca, modelo_peca = result

    if (estoque_atual or 0) <= 0:
        return False, f"Sem estoque para: {descricao_peca or 'peca'}."

    cursor.execute(
        """
        INSERT INTO os_pecas (os_id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (os_id, estoque_id, 1, valor_peca, descricao_peca, fornecedor_peca, modelo_peca),
    )

    cursor.execute(
        "UPDATE estoque SET quantidade = MAX(0, quantidade - 1) WHERE id = ?",
        (estoque_id,),
    )
    _consumir_lotes_fifo(cursor, estoque_id, 1)
    registrar_movimentacao(cursor, estoque_id, "saida", 1)
    return True, ""


def adicionar_peca_os_sem_consumir(cursor, os_id, estoque_id):
    cursor.execute(
        """
        SELECT quantidade, valor, descricao, fornecedor, modelo
        FROM estoque
        WHERE id=?
        """,
        (estoque_id,),
    )
    result = cursor.fetchone()

    if not result:
        return False, "Peca nao encontrada no estoque."

    estoque_atual, valor_peca, descricao_peca, fornecedor_peca, modelo_peca = result

    if (estoque_atual or 0) <= 0:
        return False, f"Sem estoque para: {descricao_peca or 'peca'}."

    cursor.execute(
        """
        INSERT INTO os_pecas (os_id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (os_id, estoque_id, 1, valor_peca, descricao_peca, fornecedor_peca, modelo_peca),
    )
    return True, ""


def devolver_pecas_da_os(cursor, os_id, tipo_movimentacao):
    cursor.execute(
        """
        SELECT id, estoque_id, quantidade, valor, peca_descricao, peca_fornecedor, peca_modelo
        FROM os_pecas
        WHERE os_id=?
        """,
        (os_id,),
    )
    pecas = cursor.fetchall()

    for _os_peca_id, estoque_id, qtd, valor, descricao, fornecedor, modelo in pecas:
        cursor.execute("SELECT id FROM estoque WHERE id=?", (estoque_id,))
        existe = cursor.fetchone()

        if existe:
            cursor.execute(
                """
                UPDATE estoque
                SET quantidade = quantidade + ?
                WHERE id = ?
                """,
                (qtd, estoque_id),
            )
            _criar_lote_retorno(
                cursor,
                estoque_id,
                qtd,
                valor,
                fornecedor,
                f"retorno {tipo_movimentacao}",
            )
        else:
            cursor.execute(
                """
                INSERT OR REPLACE INTO estoque (
                    id, descricao, valor, fornecedor, quantidade, data_compra, modelo, sku, tipo, qualidade
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    estoque_id,
                    descricao or "Peca devolvida",
                    valor or 0,
                    fornecedor or "Nao informado",
                    qtd or 0,
                    datetime.now().strftime("%Y-%m-%d"),
                    modelo or "",
                    f"RET-{estoque_id:05d}",
                    "Outros",
                    "Padrao",
                ),
            )
            _criar_lote_retorno(
                cursor,
                estoque_id,
                qtd,
                valor,
                fornecedor,
                f"retorno {tipo_movimentacao}",
            )

        registrar_movimentacao(cursor, estoque_id, tipo_movimentacao, qtd or 0)


# Documentos da OS para o cliente (BR-095 a BR-098,
# docs/engineering/plans/PLAN-documentos-os-cliente.md). A leitura do banco e a
# montagem ficam separadas: `montar_documento_cliente` é pura e é ela que fecha
# a allowlist do que pode sair para o cliente (BR-097).
DOCUMENTO_ENTRADA = "entrada"
DOCUMENTO_ENTREGA = "entrega"
TIPOS_DOCUMENTO_CLIENTE = (DOCUMENTO_ENTRADA, DOCUMENTO_ENTREGA)


def buscar_os_para_documento(cursor, os_id):
    """Linha da OS com só as colunas que um documento pode usar, mais os
    serviços com o snapshot de garantia (BR-062). None se a OS não existe."""
    cursor.execute(
        """
        SELECT id, COALESCE(tipo, ''), COALESCE(cliente, ''), cliente_id,
               COALESCE(aparelho, ''), COALESCE(modelo, ''), COALESCE(cor, ''),
               COALESCE(imei, ''), COALESCE(tecnico, ''), COALESCE(status, ''),
               COALESCE(data, ''), COALESCE(data_finalizado, ''),
               COALESCE(observacoes, ''), COALESCE(valor_cobrado, 0),
               COALESCE(valor_descontado, 0)
        FROM os WHERE id=?
        """,
        (os_id,),
    )
    row = cursor.fetchone()
    if not row:
        return None
    cursor.execute(
        """
        SELECT COALESCE(reparos.nome, ''), os_reparos.garantia_nome,
               os_reparos.garantia_duracao_meses, os_reparos.garantia_data_fim
        FROM os_reparos
        JOIN reparos ON reparos.id = os_reparos.reparo_id
        WHERE os_reparos.os_id=?
        ORDER BY reparos.nome
        """,
        (os_id,),
    )
    servicos = cursor.fetchall()
    chaves = (
        "id", "tipo", "cliente", "cliente_id", "aparelho", "modelo", "cor", "imei", "tecnico",
        "status", "data", "data_finalizado", "observacoes", "valor_cobrado", "valor_descontado",
    )  # fmt: skip
    dados = dict(zip(chaves, row, strict=True))
    dados["servicos"] = [
        {"nome": nome, "garantia_nome": g_nome, "garantia_duracao_meses": g_meses, "garantia_data_fim": g_fim}
        for nome, g_nome, g_meses, g_fim in servicos
    ]
    return dados


def montar_documento_cliente(tipo_documento, os_dados, loja, cliente_cadastro, status, valor_total):
    """Retorna (documento, erro). Só o que está montado aqui sai para o cliente:
    nunca custo, lucro, peças, fornecedor, vendedor ou integração (BR-097).

    `status` já normalizado; `valor_total` calculado pelo chamador com
    `calcular_faturamento_os` (mesmo valor da listagem). `cliente_cadastro` é o
    cadastro vinculado (dict com nome/telefone e, se quem gera pode ver,
    cpf_cnpj) ou None."""
    if tipo_documento not in TIPOS_DOCUMENTO_CLIENTE:
        return None, "Tipo de documento inválido."
    if os_dados["tipo"] == TIPO_OS_INTERNA:
        return None, "OS interna não tem documento para cliente."
    if status == STATUS_CANCELADO:
        return None, "OS cancelada não gera documento para cliente."
    if tipo_documento == DOCUMENTO_ENTREGA and status != STATUS_FINALIZADO:
        return None, "O comprovante de entrega só existe para OS finalizada."
    if not (loja.get("nome_fantasia") or "").strip():
        return None, "Cadastre os Dados da Loja antes de gerar documentos."

    cliente = {"nome": os_dados["cliente"], "telefone": "", "email": "", "cpf_cnpj": ""}
    if cliente_cadastro:
        cliente["nome"] = cliente_cadastro.get("nome") or cliente["nome"]
        cliente["telefone"] = cliente_cadastro.get("telefone") or ""
        cliente["email"] = cliente_cadastro.get("email") or ""
        cliente["cpf_cnpj"] = cliente_cadastro.get("cpf_cnpj") or ""

    entrega = tipo_documento == DOCUMENTO_ENTREGA
    servicos = []
    for servico in os_dados["servicos"]:
        item = {"nome": servico["nome"]}
        if entrega:
            item["garantia"] = (
                {
                    "nome": servico["garantia_nome"] or "",
                    "duracao_meses": servico["garantia_duracao_meses"],
                    "data_fim": servico["garantia_data_fim"] or "",
                }
                if servico["garantia_nome"]
                else None
            )
        servicos.append(item)

    documento = {
        "tipo": tipo_documento,
        "loja": {
            chave: loja.get(chave) or ""
            for chave in ("nome_fantasia", "razao_social", "cnpj", "telefone", "email", "endereco")
        },
        "termos": loja.get("termos_garantia" if entrega else "termos_entrada") or "",
        "cliente": cliente,
        "ordem": {
            "id": os_dados["id"],
            "data": os_dados["data"],
            "data_finalizado": os_dados["data_finalizado"] if entrega else "",
            "status": status,
            "aparelho": os_dados["aparelho"],
            "modelo": os_dados["modelo"],
            "cor": os_dados["cor"],
            "imei": os_dados["imei"],
            "tecnico": os_dados["tecnico"],
            "observacoes": os_dados["observacoes"],
            "valor_total": round(valor_total or 0, 2),
            "servicos": servicos,
        },
    }
    return documento, None
