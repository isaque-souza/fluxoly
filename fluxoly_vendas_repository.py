"""
fluxoly_vendas_repository.py

Único ponto de acesso SQL do domínio Vendas (docs/product/features/VENDAS.md).
Primeiro módulo a nascer com o prefixo `fluxoly_` (ADR-008,
docs/engineering/adr/ADR-008.md) — segue a mesma convenção de camadas de
`docs/engineering/ENGINEERING_GUIDE.md` §3.1 (controller → service →
repository), só muda o prefixo de nome.

Tabelas: `vendas`, `vendas_itens`. `vendas_itens.unidade_serializada_id` tem
índice UNIQUE (app.py::criar_tabelas()) — a mesma unidade nunca pode aparecer
em duas vendas, garantido pelo banco, não só pela camada de serviço (ver
ADR-009 para o plano de evolução dessa proteção quando cancelamento existir).

Sprint Vendas 1.1 (Histórico + Detalhe): só consulta, nenhuma mudança de
schema. `nome` de cliente/vendedor e `imei` do item são obtidos via LEFT JOIN
em `clientes`/`usuarios`/`unidades_serializadas` só para exibição -- mesma
justificativa já usada em `fluxoly_unidades_serializadas_repository.py`
(join de origem) e `shopping_list_logs` (join de usuário para nome).
"""

# Colunas + JOIN de vendas com nome de cliente/vendedor, só para exibição --
# não introduz filtro novo por si (filtros são aplicados via WHERE separado).
_COLUNAS_VENDA_COM_NOMES = (
    "v.id, v.cliente_id, v.vendedor_id, v.forma_pagamento, v.valor_total, v.status, "
    "v.observacoes, v.criado_em, "
    "c.nome AS cliente_nome, c.telefone AS cliente_telefone, u.nome AS vendedor_nome, "
    "v.motivo_cancelamento, v.observacao_cancelamento, v.cancelado_por, v.cancelado_em"
)
_JOIN_VENDA_COM_NOMES = (
    "FROM vendas v "
    "LEFT JOIN clientes c ON v.cliente_id = c.id "
    "LEFT JOIN usuarios u ON v.vendedor_id = u.id"
)


def inserir_venda(cursor, cliente_id, vendedor_id, forma_pagamento, valor_total, observacoes=""):
    cursor.execute(
        """
        INSERT INTO vendas (cliente_id, vendedor_id, forma_pagamento, valor_total, observacoes)
        VALUES (?, ?, ?, ?, ?)
        """,
        (cliente_id, vendedor_id, forma_pagamento, valor_total, observacoes or ""),
    )
    return cursor.lastrowid


def inserir_item(
    cursor, venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku, valor_tabela,
    valor_unitario, motivo_desconto="",
    tipo_garantia_id=None, garantia_nome=None, garantia_duracao_meses=None,
    garantia_data_inicio=None, garantia_data_fim=None,
):
    """`quantidade` é sempre 1 nesta fatia — uma unidade serializada não é
    fungível (uma linha de item = uma unidade física). `subtotal` calculado
    aqui, não recebido do chamador, para nunca divergir de `valor_unitario *
    quantidade`. `valor_tabela` é o preço de catálogo no momento da venda
    (nullable — item pode não ter preço cadastrado); `valor_unitario` é o
    preço efetivo, pode divergir de `valor_tabela` (negociação) -- nenhum dos
    dois sobrescreve o outro.

    `motivo_desconto` é opcional, texto livre (BR-039). `desconto_aprovado_em`
    nunca é gravado a partir daqui (BR-053/BR-054, revisão de 2026-07-29) --
    permanece sempre `NULL` para vendas novas; a coluna só existe por
    compatibilidade histórica com vendas da V1.3.

    V1.5 -- Garantia de Venda (BR-056/BR-057): os cinco campos de garantia são
    o snapshot completo resolvido pelo service no momento da criação -- esta
    função só grava, nunca resolve `tipo_garantia_id` nem calcula
    `garantia_data_fim` (isso é responsabilidade do service, que já validou a
    obrigatoriedade antes de chegar aqui)."""
    quantidade = 1
    subtotal = valor_unitario * quantidade
    cursor.execute(
        """
        INSERT INTO vendas_itens (
            venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku,
            quantidade, valor_tabela, valor_unitario, subtotal, motivo_desconto,
            tipo_garantia_id, garantia_nome, garantia_duracao_meses,
            garantia_data_inicio, garantia_data_fim
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            venda_id, unidade_serializada_id, produto_id, produto_nome, produto_sku,
            quantidade, valor_tabela, valor_unitario, subtotal, motivo_desconto or "",
            tipo_garantia_id, garantia_nome, garantia_duracao_meses,
            garantia_data_inicio, garantia_data_fim,
        ),
    )
    return cursor.lastrowid


def buscar_item_por_id(cursor, venda_id, item_id):
    """Usado pelo Ajuste Comercial (BR-043) para ler o `valor_unitario`
    anterior antes de sobrescrever -- necessário para o evento de auditoria
    registrar o valor_anterior real."""
    cursor.execute(
        "SELECT id, venda_id, valor_unitario FROM vendas_itens WHERE id = ? AND venda_id = ?",
        (item_id, venda_id),
    )
    return cursor.fetchone()


def ajustar_valor_item(cursor, venda_id, item_id, valor_unitario_novo):
    """Ajuste Comercial Autorizado (BR-043). `WHERE` revalida o estado da
    venda NO MOMENTO da escrita (nunca confia no estado lido quando a tela
    foi aberta) -- mesmo padrão de compare-and-swap de `cancelar_venda`/
    `marcar_vendida`. Retorna o número de linhas afetadas: 0 significa que a
    venda deixou de estar `concluida` entre a leitura e esta escrita (ex.:
    foi cancelada nesse meio-tempo) -- o chamador trata isso como falha."""
    cursor.execute(
        """
        UPDATE vendas_itens
        SET valor_unitario = ?, subtotal = ? * quantidade
        WHERE id = ? AND venda_id = ? AND ativo = 1
          AND EXISTS (
              SELECT 1 FROM vendas WHERE id = vendas_itens.venda_id AND status = 'concluida'
          )
        """,
        (valor_unitario_novo, valor_unitario_novo, item_id, venda_id),
    )
    return cursor.rowcount


def recalcular_valor_total_venda(cursor, venda_id):
    """`vendas.valor_total` é sempre recalculado como a soma dos `subtotal`
    de todos os itens ATIVOS da venda -- nunca escrito diretamente a partir
    do delta de um único item ajustado. Evita divergência quando uma venda
    futura tiver múltiplos itens e só um sofrer ajuste (BR-043)."""
    cursor.execute(
        "SELECT COALESCE(SUM(subtotal), 0) FROM vendas_itens WHERE venda_id = ? AND ativo = 1",
        (venda_id,),
    )
    total = cursor.fetchone()[0]
    cursor.execute("UPDATE vendas SET valor_total = ? WHERE id = ?", (total, venda_id))


def buscar_historico_desconto_item(cursor, item_id):
    """Histórico de ajustes comerciais do item (BR-043), mais recente
    primeiro -- mesmo padrão de
    `fluxoly_unidades_serializadas_repository.py::buscar_historico`."""
    cursor.execute(
        """
        SELECT a.id, a.acao, a.valor_anterior, a.valor_novo, a.criado_em, COALESCE(u.nome, '')
        FROM audit_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.entidade = 'venda_item' AND a.entidade_id = ? AND a.acao = 'ajuste_desconto'
        ORDER BY a.id DESC
        """,
        (item_id,),
    )
    return cursor.fetchall()


def buscar_comissao_item(cursor, venda_id, item_id):
    """V1.4 -- Comissão (BR-048/BR-049). Lê `comissao_valor` atual antes de
    sobrescrever -- necessário para o evento de auditoria registrar o
    valor_anterior real (`None` = ainda não atribuída)."""
    cursor.execute(
        "SELECT id, comissao_valor FROM vendas_itens WHERE id = ? AND venda_id = ?",
        (item_id, venda_id),
    )
    return cursor.fetchone()


def atribuir_comissao_item(cursor, venda_id, item_id, valor):
    """V1.4 -- Comissão (BR-048/BR-049). Mesmo compare-and-swap do Ajuste
    Comercial: `WHERE` revalida `status='concluida'` no momento da escrita --
    comissão não é atribuível/editável numa venda cancelada (BR-034).
    Retorna o número de linhas afetadas -- 0 significa que a venda deixou de
    estar `concluida` entre a leitura e esta escrita."""
    cursor.execute(
        """
        UPDATE vendas_itens
        SET comissao_valor = ?
        WHERE id = ? AND venda_id = ? AND ativo = 1
          AND EXISTS (
              SELECT 1 FROM vendas WHERE id = vendas_itens.venda_id AND status = 'concluida'
          )
        """,
        (valor, item_id, venda_id),
    )
    return cursor.rowcount


def buscar_itens_com_comissao_por_venda(cursor, venda_id):
    """Itens da venda com comissão já atribuída (`comissao_valor` não nulo) --
    usado no cancelamento (BR-051) para zerar cada um e registrar o evento de
    auditoria correspondente."""
    cursor.execute(
        "SELECT id, comissao_valor FROM vendas_itens WHERE venda_id = ? AND comissao_valor IS NOT NULL",
        (venda_id,),
    )
    return cursor.fetchall()


def zerar_comissao_item(cursor, item_id):
    """BR-051 -- zera a comissão de um item quando a venda é cancelada."""
    cursor.execute("UPDATE vendas_itens SET comissao_valor = 0 WHERE id = ?", (item_id,))


def buscar_historico_comissao_item(cursor, item_id):
    """Histórico de alterações de comissão do item (BR-049), mais recente
    primeiro -- mesmo padrão de `buscar_historico_desconto_item`."""
    cursor.execute(
        """
        SELECT a.id, a.acao, a.valor_anterior, a.valor_novo, a.criado_em, COALESCE(u.nome, '')
        FROM audit_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.entidade = 'venda_item' AND a.entidade_id = ? AND a.acao = 'comissao_alterada'
        ORDER BY a.id DESC
        """,
        (item_id,),
    )
    return cursor.fetchall()


def buscar_garantia_item(cursor, venda_id, item_id):
    """V1.5 -- Garantia de Venda (BR-057/BR-059). Lê o snapshot completo atual
    antes de uma correção -- necessário para o evento de auditoria registrar
    o valor_anterior real. Diferente da comissão, a concessão original
    acontece na criação da venda (não é lida aqui, é o próprio `inserir_item`
    que já grava o primeiro valor) -- esta função só serve para corrigir."""
    cursor.execute(
        """
        SELECT id, tipo_garantia_id, garantia_nome, garantia_duracao_meses,
               garantia_data_inicio, garantia_data_fim
        FROM vendas_itens WHERE id = ? AND venda_id = ?
        """,
        (item_id, venda_id),
    )
    return cursor.fetchone()


def corrigir_garantia_item(
    cursor, venda_id, item_id, tipo_garantia_id, garantia_nome, garantia_duracao_meses,
    garantia_data_inicio, garantia_data_fim,
):
    """V1.5 -- Garantia de Venda (BR-059). Mesmo compare-and-swap do Ajuste
    Comercial/Comissão: `WHERE` revalida `status='concluida'` no momento da
    escrita -- não corrige garantia de uma venda cancelada (ela já foi
    zerada, BR-058). Retorna o número de linhas afetadas."""
    cursor.execute(
        """
        UPDATE vendas_itens
        SET tipo_garantia_id = ?, garantia_nome = ?, garantia_duracao_meses = ?,
            garantia_data_inicio = ?, garantia_data_fim = ?
        WHERE id = ? AND venda_id = ? AND ativo = 1
          AND EXISTS (
              SELECT 1 FROM vendas WHERE id = vendas_itens.venda_id AND status = 'concluida'
          )
        """,
        (
            tipo_garantia_id, garantia_nome, garantia_duracao_meses,
            garantia_data_inicio, garantia_data_fim, item_id, venda_id,
        ),
    )
    return cursor.rowcount


def buscar_itens_com_garantia_por_venda(cursor, venda_id):
    """Itens da venda com Garantia de Venda concedida (`tipo_garantia_id` não
    nulo) -- usado no cancelamento (BR-058) para zerar cada um e registrar o
    evento de auditoria correspondente."""
    cursor.execute(
        """
        SELECT id, tipo_garantia_id, garantia_nome, garantia_duracao_meses,
               garantia_data_inicio, garantia_data_fim
        FROM vendas_itens WHERE venda_id = ? AND tipo_garantia_id IS NOT NULL
        """,
        (venda_id,),
    )
    return cursor.fetchall()


def zerar_garantia_item(cursor, item_id):
    """BR-058 -- invalida a Garantia de Venda de um item quando a venda é
    cancelada. Zera todos os campos do snapshot (não só um valor escalar,
    diferente de `zerar_comissao_item`) -- uma venda cancelada não tem
    garantia parcial, o snapshot inteiro deixa de fazer sentido."""
    cursor.execute(
        """
        UPDATE vendas_itens
        SET tipo_garantia_id = NULL, garantia_nome = NULL, garantia_duracao_meses = NULL,
            garantia_data_inicio = NULL, garantia_data_fim = NULL
        WHERE id = ?
        """,
        (item_id,),
    )


def buscar_historico_garantia_item(cursor, item_id):
    """Histórico da Garantia de Venda do item (BR-057/BR-059), mais recente
    primeiro -- inclui tanto a concessão original (`garantia_concedida`,
    gravada na criação da venda) quanto correções (`garantia_alterada`)."""
    cursor.execute(
        """
        SELECT a.id, a.acao, a.valor_anterior, a.valor_novo, a.criado_em, COALESCE(u.nome, '')
        FROM audit_log a
        LEFT JOIN usuarios u ON a.usuario_id = u.id
        WHERE a.entidade = 'venda_item' AND a.entidade_id = ?
          AND a.acao IN ('garantia_concedida', 'garantia_alterada')
        ORDER BY a.id DESC
        """,
        (item_id,),
    )
    return cursor.fetchall()


def buscar_por_id(cursor, venda_id):
    cursor.execute(
        f"SELECT {_COLUNAS_VENDA_COM_NOMES} {_JOIN_VENDA_COM_NOMES} WHERE v.id = ?",
        (venda_id,),
    )
    return cursor.fetchone()


def buscar_itens_por_venda(cursor, venda_id):
    """`imei` vem do join com `unidades_serializadas` -- estável (imutável
    após o cadastro, decisão já registrada em C1.3.4), seguro de exibir ao
    vivo mesmo para vendas antigas, diferente de `produto_nome`/`produto_sku`
    (snapshot, podem divergir do cadastro atual)."""
    cursor.execute(
        """
        SELECT vi.id, vi.venda_id, vi.unidade_serializada_id, vi.produto_id, vi.produto_nome,
               vi.produto_sku, vi.quantidade, vi.valor_tabela, vi.valor_unitario, vi.subtotal,
               vi.criado_em, u.imei, vi.motivo_desconto, vi.desconto_aprovado_em, vi.comissao_valor,
               vi.tipo_garantia_id, vi.garantia_nome, vi.garantia_duracao_meses,
               vi.garantia_data_inicio, vi.garantia_data_fim
        FROM vendas_itens vi
        LEFT JOIN unidades_serializadas u ON vi.unidade_serializada_id = u.id
        WHERE vi.venda_id = ?
        ORDER BY vi.id
        """,
        (venda_id,),
    )
    return cursor.fetchall()


def _montar_filtros(cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo):
    condicoes = []
    params = []

    if cliente_id:
        condicoes.append("v.cliente_id = ?")
        params.append(cliente_id)
    if vendedor_id:
        condicoes.append("v.vendedor_id = ?")
        params.append(vendedor_id)
    if forma_pagamento:
        condicoes.append("v.forma_pagamento = ?")
        params.append(forma_pagamento)
    if status:
        condicoes.append("v.status = ?")
        params.append(status)
    if data_inicio:
        condicoes.append("v.criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("v.criado_em <= ?")
        params.append(data_fim)
    if termo:
        condicoes.append(
            "(c.nome LIKE ? OR EXISTS ("
            "SELECT 1 FROM vendas_itens vi LEFT JOIN unidades_serializadas u2 "
            "ON vi.unidade_serializada_id = u2.id "
            "WHERE vi.venda_id = v.id AND (u2.imei LIKE ? OR vi.produto_nome LIKE ?)"
            "))"
        )
        coringa = f"%{termo}%"
        params.extend([coringa, coringa, coringa])

    where_sql = " AND ".join(condicoes) if condicoes else "1=1"
    return where_sql, params


_ORDENACOES = {
    "recente": "v.criado_em DESC, v.id DESC",
    "antigo": "v.criado_em ASC, v.id ASC",
}


def contar_vendas(cursor, cliente_id=None, vendedor_id=None, forma_pagamento=None, status=None,
                   data_inicio=None, data_fim=None, termo=None):
    where_sql, params = _montar_filtros(
        cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo
    )
    cursor.execute(f"SELECT COUNT(*) {_JOIN_VENDA_COM_NOMES} WHERE {where_sql}", params)
    return cursor.fetchone()[0] or 0


def buscar_paginado(cursor, cliente_id=None, vendedor_id=None, forma_pagamento=None, status=None,
                     data_inicio=None, data_fim=None, termo=None, sort="recente", limit=20, offset=0):
    where_sql, params = _montar_filtros(
        cliente_id, vendedor_id, forma_pagamento, status, data_inicio, data_fim, termo
    )
    order_sql = _ORDENACOES.get(sort, _ORDENACOES["recente"])
    cursor.execute(
        f"SELECT {_COLUNAS_VENDA_COM_NOMES} {_JOIN_VENDA_COM_NOMES} WHERE {where_sql} "
        f"ORDER BY {order_sql} LIMIT ? OFFSET ?",
        [*params, limit, offset],
    )
    return cursor.fetchall()


def buscar_itens_por_vendas(cursor, venda_ids):
    """Busca os itens de várias vendas de uma vez (evita N+1 na listagem do
    histórico) -- mesmo `imei` ao vivo via join, ver `buscar_itens_por_venda`."""
    if not venda_ids:
        return []
    marcadores = ",".join("?" * len(venda_ids))
    cursor.execute(
        f"""
        SELECT vi.id, vi.venda_id, vi.unidade_serializada_id, vi.produto_id, vi.produto_nome,
               vi.produto_sku, vi.quantidade, vi.valor_tabela, vi.valor_unitario, vi.subtotal,
               vi.criado_em, u.imei, vi.motivo_desconto, vi.desconto_aprovado_em, vi.comissao_valor,
               vi.tipo_garantia_id, vi.garantia_nome, vi.garantia_duracao_meses,
               vi.garantia_data_inicio, vi.garantia_data_fim
        FROM vendas_itens vi
        LEFT JOIN unidades_serializadas u ON vi.unidade_serializada_id = u.id
        WHERE vi.venda_id IN ({marcadores})
        ORDER BY vi.venda_id, vi.id
        """,
        venda_ids,
    )
    return cursor.fetchall()


def cancelar_venda(cursor, venda_id, motivo, observacao, usuario_id):
    """V1.2 -- Cancelamento (BR-031 a BR-036). `WHERE status = 'concluida'` é compare-and-swap
    contra cancelamento concorrente da mesma venda (mesmo padrão de
    `fluxoly_unidades_serializadas_repository.py::marcar_vendida`) -- também é o que impede
    "descancelar", já que só há caminho de `concluida` para `cancelada`, nunca o inverso
    (Princípio da Imutabilidade da Venda). Retorna o número de linhas afetadas -- 0 significa
    que a venda não estava mais `concluida` (já cancelada ou estado mudou)."""
    cursor.execute(
        """
        UPDATE vendas
        SET status = 'cancelada', motivo_cancelamento = ?, observacao_cancelamento = ?,
            cancelado_por = ?, cancelado_em = datetime('now')
        WHERE id = ? AND status = 'concluida'
        """,
        (motivo, observacao or None, usuario_id, venda_id),
    )
    return cursor.rowcount


def desativar_itens_da_venda(cursor, venda_id):
    """Marca os itens da venda cancelada como não-vigentes (`ativo = 0`) -- permite que a(s)
    mesma(s) unidade(s) apareça(m) numa venda nova sem violar o índice único parcial
    (`idx_vendas_itens_unidade_ativa`, `app.py::criar_tabelas()`), preservando a linha
    original para histórico/auditoria."""
    cursor.execute("UPDATE vendas_itens SET ativo = 0 WHERE venda_id = ?", (venda_id,))


def buscar_unidades_da_venda(cursor, venda_id):
    """Unidades a liberar (voltar para `disponivel`) ao cancelar a venda -- nesta fatia sempre
    1 item, mas já pronto para múltiplos itens por venda (mesmo padrão de
    `buscar_itens_por_venda`)."""
    cursor.execute("SELECT unidade_serializada_id FROM vendas_itens WHERE venda_id = ?", (venda_id,))
    return [row[0] for row in cursor.fetchall()]


def buscar_garantias_venda(cursor, termo=""):
    """Painel de garantias unificado (PLAN-painel-garantias-unificado.md): uma
    linha por item de venda concluída com garantia concedida. Itens com
    `garantia_duracao_meses = 0` ("sem garantia", BR-055) e de venda cancelada
    ficam de fora -- nunca lista uma garantia que não vale."""
    condicoes = [
        "v.status = 'concluida'",
        "COALESCE(vi.garantia_data_fim, '') != ''",
        "COALESCE(vi.garantia_duracao_meses, 0) > 0",
    ]
    params = []
    termo = (termo or "").strip()
    if termo:
        condicoes.append(
            "(LOWER(COALESCE(c.nome,'')) LIKE ? OR COALESCE(u.imei,'') LIKE ? "
            "OR LOWER(COALESCE(vi.produto_nome,'')) LIKE ?)"
        )
        like = f"%{termo.lower()}%"
        params += [like, f"%{termo}%", like]
    cursor.execute(
        f"""
        SELECT vi.id, vi.venda_id, v.criado_em, v.cliente_id, c.nome, vi.produto_nome, u.imei,
               vi.garantia_nome, vi.garantia_data_inicio, vi.garantia_data_fim
        FROM vendas_itens vi
        JOIN vendas v ON vi.venda_id = v.id
        LEFT JOIN clientes c ON v.cliente_id = c.id
        LEFT JOIN unidades_serializadas u ON vi.unidade_serializada_id = u.id
        WHERE {" AND ".join(condicoes)}
        ORDER BY vi.garantia_data_fim ASC, vi.id ASC
        """,
        params,
    )
    return cursor.fetchall()


def resumir_vendas_por_vendedor(cursor, inicio=None, fim=None):
    """Dashboard (PLAN-dashboard-vendas-os.md): quantidade e soma de
    `valor_total` das vendas concluídas no período, agrupadas por vendedor.
    `inicio` inclusivo, `fim` exclusivo (timestamps `YYYY-MM-DD HH:MM:SS`)."""
    condicoes, params = ["v.status = 'concluida'"], []
    if inicio:
        condicoes.append("v.criado_em >= ?")
        params.append(inicio)
    if fim:
        condicoes.append("v.criado_em < ?")
        params.append(fim)
    cursor.execute(
        f"""
        SELECT COALESCE(u.nome, ''), COUNT(*), COALESCE(SUM(v.valor_total), 0)
        FROM vendas v
        LEFT JOIN usuarios u ON v.vendedor_id = u.id
        WHERE {" AND ".join(condicoes)}
        GROUP BY v.vendedor_id
        ORDER BY 3 DESC
        """,
        params,
    )
    return cursor.fetchall()


def buscar_vendas_concluidas_nas_datas(cursor, datas):
    """Lembretes de pós-venda (PLAN-lembretes-pos-venda.md): vendas concluídas cujo dia de
    `criado_em` está em `datas` (`YYYY-MM-DD`, UTC como o resto do sistema -- KI-061), com o
    cliente e os produtos vigentes. Uma linha por venda."""
    if not datas:
        return []
    marcadores = ",".join("?" for _ in datas)
    cursor.execute(
        f"""
        SELECT v.id, substr(v.criado_em, 1, 10), v.cliente_id, COALESCE(c.nome, ''),
               COALESCE(c.telefone, ''), GROUP_CONCAT(vi.produto_nome, ', ')
        FROM vendas v
        JOIN vendas_itens vi ON vi.venda_id = v.id AND vi.ativo = 1
        LEFT JOIN clientes c ON c.id = v.cliente_id
        WHERE v.status = 'concluida' AND substr(v.criado_em, 1, 10) IN ({marcadores})
        GROUP BY v.id
        ORDER BY v.criado_em, v.id
        """,
        list(datas),
    )
    return cursor.fetchall()
