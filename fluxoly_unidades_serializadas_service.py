"""
fluxoly_unidades_serializadas_service.py

Regra de negócio pura do domínio `unidades_serializadas` (rastreamento
individual por IMEI/serial) — não conhece Flask, `request` nem `jsonify`
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Responsabilidade: registrar unidades individuais originadas de `estoque`
(peças que exigem rastreamento por IMEI, `estoque.requer_imei = 1`) OU de
`produtos` (catálogo comercial que exige rastreamento por unidade,
`produtos.requer_rastreio_unidade = 1`), e suas transições manuais de
status. Uma unidade tem origem em exatamente um dos dois — nunca ambos,
nunca nenhum (Regra de Ouro / invariante de origem, ver ADR-007). `reservado`/
`vendido` existem no schema para o futuro módulo de Vendas, mas nenhuma
função aqui produz ou aceita esses estados — só `disponivel`, `em_reparo` e
`devolvido` são alcançáveis nesta sprint.

Tabelas usadas: `unidades_serializadas` (via
`fluxoly_unidades_serializadas_repository.py`), leitura de
`estoque.requer_imei` e `produtos.requer_rastreio_unidade`.

Depende de: `fluxoly_unidades_serializadas_repository.py` (SQL),
`fluxoly_audit.py` (auditoria — create/status_change).
"""

import sqlite3

import fluxoly_unidades_serializadas_repository as repo
from fluxoly_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20

# Estados alcançáveis nesta sprint — 'reservado'/'vendido' ficam de fora até
# o módulo de Vendas existir (nem como origem, nem como destino).
TRANSICOES_VALIDAS = {
    "disponivel": {"em_reparo"},
    "em_reparo": {"disponivel", "devolvido"},
    "devolvido": {"disponivel"},
}


def _unidade_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "estoque_id": row[1],
        "produto_id": row[2],
        "lote_id": row[3],
        "imei": row[4] or "",
        "status": row[5],
        "reservado_por": row[6],
        "reservado_ate": row[7],
        "venda_id": row[8],
        "saude_bateria": row[9],
        "localizacao": row[10],
        "criado_em": row[11],
        "atualizado_em": row[12],
    }


def _origem_label(estoque_modelo, estoque_descricao, produto_modelo, produto_descricao):
    """Label de exibição da origem — modelo com fallback para descrição, por domínio."""
    return (estoque_modelo or estoque_descricao) or (produto_modelo or produto_descricao) or ""


def _unidade_com_origem_para_dict(row):
    """Mesma forma de `_unidade_para_dict`, com campos de origem (join) para listagem/exibição."""
    if not row:
        return None
    base = _unidade_para_dict(row)
    (_estoque_modelo, _estoque_descricao, _produto_modelo, _produto_descricao,
     _produto_categoria, _produto_marca) = row[13:19]
    _estoque_sku, _produto_sku = row[19:21]
    _estoque_valor, _produto_preco_venda, _produto_cor, _produto_capacidade = row[21:25]
    base["origem_tipo"] = "estoque" if base["estoque_id"] else ("produto" if base["produto_id"] else None)
    base["origem_label"] = _origem_label(_estoque_modelo, _estoque_descricao, _produto_modelo, _produto_descricao)
    base["produto_categoria"] = _produto_categoria
    base["produto_marca"] = _produto_marca
    base["produto_cor"] = _produto_cor
    base["produto_capacidade"] = _produto_capacidade
    # Snapshot para fluxoly_vendas_service.py (vendas_itens.produto_sku) -- SKU real,
    # nunca coagido/normalizado, mesmo campo já exposto por Estoque/Produtos.
    base["origem_sku"] = _estoque_sku or _produto_sku or ""
    # Preço de catálogo (fluxoly_vendas_service.py, vendas_itens.valor_tabela) -- checagem
    # explícita por None, não `or`: um preço 0 (embora incomum) é um valor real, não
    # "ausente", e `or` trataria 0 como falsy e cairia incorretamente no fallback.
    if _estoque_valor is not None:
        base["preco_catalogo"] = _estoque_valor
    elif _produto_preco_venda is not None:
        base["preco_catalogo"] = _produto_preco_venda
    else:
        base["preco_catalogo"] = None
    return base


# Faixas de saúde da bateria (C1.3.3) — mapeadas para min/max ou "não informado"
# na camada de serviço, repository só recebe limites numéricos já resolvidos.
FAIXAS_SAUDE_BATERIA = {
    "100-95": (95, 100),
    "94-90": (90, 94),
    "89-85": (85, 89),
    "<85": (None, 84),
    "nao_informado": (None, None),
}


def listar_unidades(
    conectar, termo="", estoque_id=None, produto_id=None, origem=None, status="",
    saude_bateria_faixa="", localizacao="", sort="recente", page=None, per_page=None,
):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    saude_min, saude_max = FAIXAS_SAUDE_BATERIA.get(saude_bateria_faixa, (None, None))
    saude_nao_informado = saude_bateria_faixa == "nao_informado"

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(
            cursor, termo, estoque_id, produto_id, origem, status,
            saude_min, saude_max, saude_nao_informado, localizacao,
        )
        rows = repo.buscar_paginado(
            cursor, termo, estoque_id, produto_id, origem, status,
            saude_min, saude_max, saude_nao_informado, localizacao,
            sort, per_page, offset,
        )
    finally:
        conn.close()

    return {
        "items": [_unidade_com_origem_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_unidade(conectar, unidade_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id_com_origem(cursor, unidade_id)
    finally:
        conn.close()
    return _unidade_com_origem_para_dict(row)


def _evento_historico_para_dict(row):
    return {
        "id": row[0],
        "acao": row[1],
        "valor_anterior": row[2],
        "valor_novo": row[3],
        "criado_em": row[4],
        "usuario_nome": row[5] or "",
    }


def obter_historico(conectar, unidade_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        rows = repo.buscar_historico(cursor, unidade_id)
    finally:
        conn.close()
    return [_evento_historico_para_dict(r) for r in rows]


def criar_unidade(conectar, usuario_id, estoque_id, produto_id, imei, lote_id=None):
    """Retorna (unidade_id, erro). `erro` é None em caso de sucesso.

    Exatamente um de `estoque_id`/`produto_id` deve estar preenchido —
    rejeitado com erro explícito se nenhum ou ambos estiverem (nunca
    coagido silenciosamente, mesma filosofia de KI-015/KI-016).
    """
    imei = (imei or "").strip()
    if not estoque_id and not produto_id:
        return None, "Informe estoque_id ou produto_id."
    if estoque_id and produto_id:
        return None, "Informe apenas um de estoque_id ou produto_id, não os dois."
    if not imei:
        return None, "IMEI é obrigatório."

    conn = conectar()
    try:
        cursor = conn.cursor()
        if estoque_id:
            requer_rastreio = repo.obter_estoque_requer_imei(cursor, estoque_id)
            if requer_rastreio is None:
                return None, "Item de estoque não encontrado."
            if not requer_rastreio:
                return None, "Este item de estoque não está marcado para rastreamento por IMEI."
        else:
            requer_rastreio = repo.obter_produto_requer_rastreio_unidade(cursor, produto_id)
            if requer_rastreio is None:
                return None, "Produto não encontrado."
            if not requer_rastreio:
                return None, "Este produto não está marcado para rastreamento por unidade."

        try:
            unidade_id = repo.inserir(
                cursor, estoque_id=estoque_id, produto_id=produto_id, imei=imei, lote_id=lote_id
            )
        except Exception:
            conn.rollback()
            return None, "IMEI já cadastrado."

        registrar_log_auditoria(
            cursor,
            "unidade_serializada",
            unidade_id,
            usuario_id,
            "create",
            depois={"estoque_id": estoque_id, "produto_id": produto_id, "imei": imei},
        )
        conn.commit()
    finally:
        conn.close()

    return unidade_id, None


def transicionar_status(conectar, usuario_id, unidade_id, novo_status):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, unidade_id)
        if not antes:
            return False, "Unidade não encontrada."

        status_atual = antes[5]
        destinos_validos = TRANSICOES_VALIDAS.get(status_atual, set())
        if novo_status not in destinos_validos:
            return False, f"Transição inválida de '{status_atual}' para '{novo_status}'."

        repo.atualizar_status(cursor, unidade_id, novo_status)
        registrar_log_auditoria(
            cursor,
            "unidade_serializada",
            unidade_id,
            usuario_id,
            "status_change",
            antes=status_atual,
            depois=novo_status,
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def marcar_como_vendida(cursor, unidade_id, venda_id, usuario_id):
    """Transição disponivel -> vendido, exclusiva do domínio Vendas (Princípio da
    Responsabilidade de Transição, ADR-007). Recebe `cursor` (não `conectar`) --
    exceção deliberada ao padrão do resto deste arquivo, porque precisa viver na
    MESMA transação de `fluxoly_vendas_service.py::iniciar_venda` (cliente ->
    venda -> item -> unidade -> commit único), mesmo motivo de `fluxoly_os.py`
    já citado em `ENGINEERING_GUIDE.md` §3.1 para funções compartilhadas entre
    domínios.

    Deliberadamente SEPARADA de `transicionar_status`/`TRANSICOES_VALIDAS`: se
    'vendido' fosse adicionado a `TRANSICOES_VALIDAS`, o endpoint genérico
    `PATCH /api/unidades-serializadas/<id>/status` passaria a aceitar
    `{"status": "vendido"}` de qualquer admin/tecnico, marcando uma unidade como
    vendida sem nenhuma `venda`/`vendas_itens` por trás -- corromperia a
    integridade que o índice UNIQUE de `vendas_itens.unidade_serializada_id`
    protege. Retorna (sucesso, erro)."""
    linhas = repo.marcar_vendida(cursor, unidade_id, venda_id)
    if linhas == 0:
        return False, "Unidade não está mais disponível."

    registrar_log_auditoria(
        cursor,
        "unidade_serializada",
        unidade_id,
        usuario_id,
        "status_change",
        antes="disponivel",
        depois="vendido",
    )
    return True, None


def liberar_unidade_para_venda(cursor, unidade_id, usuario_id):
    """Transição vendido -> disponivel, efeito colateral exclusivo de cancelar uma venda
    (fluxoly_vendas_service.py::cancelar_venda, BR-033). Recebe `cursor` (não `conectar`) --
    mesma razão de `marcar_como_vendida`: precisa viver na MESMA transação de
    `cancelar_venda` (cancelar venda -> desativar item -> liberar unidade -> auditoria ->
    commit único). Deliberadamente fora de `TRANSICOES_VALIDAS`, mesmo motivo de
    `marcar_como_vendida`: não abrir uma porta lateral no endpoint genérico
    `PATCH /api/unidades-serializadas/<id>/status`. Retorna (sucesso, erro)."""
    linhas = repo.liberar_venda(cursor, unidade_id)
    if linhas == 0:
        return False, "Unidade não está mais vendida."

    registrar_log_auditoria(
        cursor,
        "unidade_serializada",
        unidade_id,
        usuario_id,
        "status_change",
        antes="vendido",
        depois="disponivel",
    )
    return True, None


def criar_unidade_de_compra(cursor, usuario_id, produto_id, imei, com_defeito):
    """Compra de aparelho (BR-084, fluxoly_compras_aparelhos_service.py): cria a unidade
    (origem Produto, ADR-007) já no status certo -- `em_reparo` se veio com defeito,
    `disponivel` se não. Recebe `cursor` (não `conectar`) pelo mesmo motivo de
    `marcar_como_vendida`: precisa viver na MESMA transação da compra e da saída de caixa
    (nunca uma unidade sem compra, nem o contrário). Não faz rollback -- em caso de erro,
    devolve a mensagem e quem abriu a transação decide. Retorna (unidade_id, erro)."""
    imei = (imei or "").strip()
    if not imei:
        return None, "IMEI é obrigatório."

    requer_rastreio = repo.obter_produto_requer_rastreio_unidade(cursor, produto_id)
    if requer_rastreio is None:
        return None, "Produto não encontrado."
    if not requer_rastreio:
        return None, "Este produto não está marcado para rastreamento por unidade."

    try:
        unidade_id = repo.inserir(cursor, produto_id=produto_id, imei=imei)
    except sqlite3.IntegrityError:
        return None, "IMEI já cadastrado."

    registrar_log_auditoria(
        cursor,
        "unidade_serializada",
        unidade_id,
        usuario_id,
        "create",
        depois={"estoque_id": None, "produto_id": produto_id, "imei": imei, "origem": "compra_aparelho"},
    )
    if com_defeito:
        repo.atualizar_status(cursor, unidade_id, "em_reparo")
        registrar_log_auditoria(
            cursor,
            "unidade_serializada",
            unidade_id,
            usuario_id,
            "status_change",
            antes="disponivel",
            depois="em_reparo",
        )
    return unidade_id, None


def devolver_unidade_de_compra(cursor, unidade_id, usuario_id):
    """Cancelamento de compra de aparelho (BR-087): `disponivel`/`em_reparo` -> `devolvido`.
    Fora de `TRANSICOES_VALIDAS` de propósito (mesmo motivo de `marcar_como_vendida`): o
    endpoint genérico de status não ganha uma porta lateral. Recebe `cursor` -- mesma
    transação do cancelamento e do estorno de caixa. Retorna (sucesso, erro)."""
    antes = repo.buscar_por_id(cursor, unidade_id)
    if not antes:
        return False, "Unidade não encontrada."
    if repo.devolver_de_compra(cursor, unidade_id) == 0:
        return False, "Aparelho já vendido ou fora do estoque — a compra não pode ser cancelada."

    registrar_log_auditoria(
        cursor,
        "unidade_serializada",
        unidade_id,
        usuario_id,
        "status_change",
        antes=antes[5],
        depois="devolvido",
    )
    return True, None


def iniciar_reparo_interno(cursor, unidade_id, usuario_id):
    """OS interna (BR-090): aparelho `disponivel` vai para `em_reparo`; `em_reparo` continua
    como está. Qualquer outro status (vendido, devolvido) é recusado. Recebe `cursor` -- vive
    na transação da OS. Retorna (imei, erro)."""
    antes = repo.buscar_por_id(cursor, unidade_id)
    if not antes:
        return None, "Aparelho não encontrado."
    status_atual = antes[5]
    if status_atual == "disponivel":
        repo.atualizar_status(cursor, unidade_id, "em_reparo")
        registrar_log_auditoria(
            cursor,
            "unidade_serializada",
            unidade_id,
            usuario_id,
            "status_change",
            antes="disponivel",
            depois="em_reparo",
        )
    elif status_atual != "em_reparo":
        return None, "Este aparelho não está no estoque (vendido ou devolvido)."
    return antes[4] or "", None


def concluir_reparo_interno(cursor, unidade_id, usuario_id):
    """BR-091: OS interna finalizada -> aparelho `em_reparo` vira `disponivel`. Se o aparelho
    não está mais `em_reparo` (alguém já mudou à mão), não faz nada. Recebe `cursor`."""
    antes = repo.buscar_por_id(cursor, unidade_id)
    if not antes or antes[5] != "em_reparo":
        return
    repo.atualizar_status(cursor, unidade_id, "disponivel")
    registrar_log_auditoria(
        cursor,
        "unidade_serializada",
        unidade_id,
        usuario_id,
        "status_change",
        antes="em_reparo",
        depois="disponivel",
    )


# C1.3.4 — únicos campos editáveis fora da máquina de estados de status:
# localizacao e saude_bateria. IMEI é tratado como imutável após o cadastro
# (decisão do usuário/CTO, 2026-07-22 — identificador primário usado em
# busca/auditoria/futura garantia). Origem (estoque_id/produto_id) nunca é
# editável — é a invariante do domínio (Regra de Ouro, ADR-007).
CAMPOS_BLOQUEADOS = {"estoque_id", "produto_id", "imei", "status", "venda_id", "reservado_por", "reservado_ate"}


def atualizar_campos(conectar, usuario_id, unidade_id, localizacao=None, saude_bateria=None):
    """Retorna (sucesso, erro). `erro` é None em caso de sucesso.

    `saude_bateria` é validado como percentual (0-100) quando não vazio —
    rejeitado com erro explícito se inválido, nunca coagido silenciosamente
    (mesma filosofia de KI-015/KI-016)."""
    localizacao = (localizacao or "").strip()
    saude_bateria = (saude_bateria or "").strip()
    if saude_bateria and not (saude_bateria.isdigit() and 0 <= int(saude_bateria) <= 100):
        return False, "Saúde da bateria deve ser um número entre 0 e 100."

    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, unidade_id)
        if not antes:
            return False, "Unidade não encontrada."

        antes_dict = {"localizacao": antes[10], "saude_bateria": antes[9]}
        depois_dict = {"localizacao": localizacao or None, "saude_bateria": saude_bateria or None}
        repo.atualizar_campos(cursor, unidade_id, depois_dict["localizacao"], depois_dict["saude_bateria"])
        registrar_log_auditoria(
            cursor, "unidade_serializada", unidade_id, usuario_id, "update",
            antes=antes_dict, depois=depois_dict,
        )
        conn.commit()
    finally:
        conn.close()

    return True, None
