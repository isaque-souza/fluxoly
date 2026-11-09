"""
fluxoly_compras_aparelhos_repository.py

Único ponto de acesso SQL do domínio Compra de Aparelhos (BR-083 a BR-093,
docs/engineering/plans/PLAN-compra-aparelhos.md). Segue a convenção de
docs/engineering/ENGINEERING_GUIDE.md §3.1 -- nenhuma regra de negócio aqui,
só queries parametrizadas.

Tabela: `compras_aparelhos`. FKs lógicas (sem `FOREIGN KEY`, mesma convenção
do schema): `unidade_serializada_id`, `produto_id`, `cliente_id`, `venda_id`,
`usuario_id`, `cancelado_por`. Os JOINs em `unidades_serializadas`/`produtos`/
`clientes`/`usuarios` são só para exibição (IMEI, modelo, nomes) -- mesma
justificativa de `fluxoly_unidades_serializadas_repository.buscar_historico`.

Depende de: nenhum outro módulo de domínio.
"""

# Ordem fixa -- `_compra_para_dict` (service) faz leitura posicional; colunas
# novas sempre no final.
_COLUNAS = (
    "c.id, c.unidade_serializada_id, c.produto_id, c.origem, c.cliente_id, c.venda_id, "
    "c.vendedor_nome, c.vendedor_telefone, c.valor_pago, c.forma_pagamento, c.estado, c.defeito, "
    "c.status, c.motivo_cancelamento, c.cancelado_por, c.cancelado_em, c.usuario_id, c.criado_em, "
    "u.imei, u.status AS unidade_status, "
    "COALESCE(p.modelo, p.descricao, '') AS produto_label, p.cor, p.capacidade, "
    "cl.nome AS cliente_nome, us.nome AS usuario_nome"
)
_JOIN = (
    "FROM compras_aparelhos c "
    "LEFT JOIN unidades_serializadas u ON c.unidade_serializada_id = u.id "
    "LEFT JOIN produtos p ON c.produto_id = p.id "
    "LEFT JOIN clientes cl ON c.cliente_id = cl.id "
    "LEFT JOIN usuarios us ON c.usuario_id = us.id"
)


def inserir(
    cursor,
    unidade_serializada_id,
    produto_id,
    origem,
    cliente_id,
    venda_id,
    vendedor_nome,
    vendedor_telefone,
    valor_pago,
    forma_pagamento,
    estado,
    defeito,
    usuario_id,
):
    cursor.execute(
        """
        INSERT INTO compras_aparelhos (
            unidade_serializada_id, produto_id, origem, cliente_id, venda_id,
            vendedor_nome, vendedor_telefone, valor_pago, forma_pagamento,
            estado, defeito, usuario_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            unidade_serializada_id,
            produto_id,
            origem,
            cliente_id,
            venda_id,
            vendedor_nome,
            vendedor_telefone,
            valor_pago,
            forma_pagamento,
            estado,
            defeito,
            usuario_id,
        ),
    )
    return cursor.lastrowid


def buscar_por_id(cursor, compra_id):
    cursor.execute(f"SELECT {_COLUNAS} {_JOIN} WHERE c.id = ?", (compra_id,))
    return cursor.fetchone()


def _montar_filtros(origem, status, data_inicio, data_fim, termo):
    condicoes = []
    params = []
    if origem:
        condicoes.append("c.origem = ?")
        params.append(origem)
    if status:
        condicoes.append("c.status = ?")
        params.append(status)
    if data_inicio:
        condicoes.append("c.criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("c.criado_em <= ?")
        params.append(data_fim)
    if termo:
        padrao = f"%{termo.lower()}%"
        condicoes.append(
            "(lower(COALESCE(u.imei, '')) LIKE ? OR lower(COALESCE(p.modelo, '')) LIKE ? "
            "OR lower(COALESCE(p.descricao, '')) LIKE ? OR lower(COALESCE(cl.nome, '')) LIKE ? "
            "OR lower(COALESCE(c.vendedor_nome, '')) LIKE ?)"
        )
        params.extend([padrao] * 5)
    where = f"WHERE {' AND '.join(condicoes)}" if condicoes else ""
    return where, params


def buscar_paginado(cursor, origem, status, data_inicio, data_fim, termo, limit, offset):
    where, params = _montar_filtros(origem, status, data_inicio, data_fim, termo)
    cursor.execute(
        f"SELECT {_COLUNAS} {_JOIN} {where} ORDER BY c.criado_em DESC, c.id DESC LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return cursor.fetchall()


def contar(cursor, origem, status, data_inicio, data_fim, termo):
    where, params = _montar_filtros(origem, status, data_inicio, data_fim, termo)
    cursor.execute(f"SELECT COUNT(*) {_JOIN} {where}", params)
    return cursor.fetchone()[0] or 0


def existe_compra_ativa_da_unidade(cursor, unidade_id):
    cursor.execute(
        "SELECT 1 FROM compras_aparelhos WHERE unidade_serializada_id = ? AND status = 'ativa' LIMIT 1",
        (unidade_id,),
    )
    return cursor.fetchone() is not None


# ---------------------------------------------------------------------------
# Custo, lucro e relatório (BR-092/BR-093). Leem `os`, `vendas`, `vendas_itens` e
# `unidades_serializadas` só para agregação -- nenhuma escrita fora de compras_aparelhos.
# ---------------------------------------------------------------------------

_SOMA_PECAS_OS_INTERNAS = (
    "COALESCE((SELECT SUM(COALESCE(o.custo_pecas, 0)) FROM os o "
    "WHERE o.tipo = 'Interna' AND o.unidade_serializada_id = c.unidade_serializada_id "
    "AND COALESCE(o.status, '') != 'Cancelado'), 0)"
)


def buscar_custo_da_unidade(cursor, unidade_id):
    """(valor_pago, custo_pecas) da compra ativa da unidade, ou None se ela não veio de compra.
    OS interna cancelada não entra -- as peças dela voltaram para o estoque."""
    cursor.execute(
        f"SELECT c.valor_pago, {_SOMA_PECAS_OS_INTERNAS} FROM compras_aparelhos c "
        "WHERE c.unidade_serializada_id = ? AND c.status = 'ativa'",
        (unidade_id,),
    )
    return cursor.fetchone()


def resumir_compras_do_periodo(cursor, inicio, fim):
    cursor.execute(
        "SELECT COUNT(*), COALESCE(SUM(valor_pago), 0) FROM compras_aparelhos "
        "WHERE status = 'ativa' AND criado_em >= ? AND criado_em < ?",
        (inicio, fim),
    )
    return cursor.fetchone()


def somar_pecas_os_internas_do_periodo(cursor, inicio, fim):
    cursor.execute(
        "SELECT COALESCE(SUM(COALESCE(custo_pecas, 0)), 0) FROM os "
        "WHERE tipo = 'Interna' AND COALESCE(status, '') != 'Cancelado' AND data >= ? AND data < ?",
        (inicio[:10], fim[:10]),
    )
    return cursor.fetchone()[0] or 0.0


def buscar_vendas_de_aparelhos_comprados(cursor, inicio, fim):
    """Itens vigentes de vendas concluídas no período cuja unidade veio de uma compra ativa."""
    cursor.execute(
        f"""
        SELECT v.id, v.criado_em, vi.unidade_serializada_id, vi.produto_nome, COALESCE(u.imei, ''),
               vi.valor_unitario, c.valor_pago, {_SOMA_PECAS_OS_INTERNAS}
        FROM vendas_itens vi
        JOIN vendas v ON v.id = vi.venda_id
        JOIN compras_aparelhos c ON c.unidade_serializada_id = vi.unidade_serializada_id AND c.status = 'ativa'
        LEFT JOIN unidades_serializadas u ON u.id = vi.unidade_serializada_id
        WHERE vi.ativo = 1 AND v.status = 'concluida' AND v.criado_em >= ? AND v.criado_em < ?
        ORDER BY v.criado_em, v.id
        """,
        (inicio, fim),
    )
    return cursor.fetchall()


def buscar_aparelhos_comprados_em_estoque(cursor):
    """Retrato atual (não do período): aparelhos de compra ativa ainda não vendidos."""
    cursor.execute(
        f"""
        SELECT u.status, c.valor_pago, {_SOMA_PECAS_OS_INTERNAS}
        FROM compras_aparelhos c
        JOIN unidades_serializadas u ON u.id = c.unidade_serializada_id
        WHERE c.status = 'ativa' AND u.status IN ('disponivel', 'em_reparo')
        """
    )
    return cursor.fetchall()


def cancelar(cursor, compra_id, motivo, usuario_id):
    """CAS: só cancela compra ainda `ativa`. Retorna linhas afetadas (0 = estado mudou)."""
    cursor.execute(
        "UPDATE compras_aparelhos SET status = 'cancelada', motivo_cancelamento = ?, "
        "cancelado_por = ?, cancelado_em = datetime('now') WHERE id = ? AND status = 'ativa'",
        (motivo, usuario_id, compra_id),
    )
    return cursor.rowcount
