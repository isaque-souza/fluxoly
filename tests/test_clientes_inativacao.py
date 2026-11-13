"""
Inativação de clientes no lugar da exclusão física (hotfix P1-3, KI-066, BR-024 a BR-024d,
docs/engineering/plans/PLAN-inativacao-clientes.md).

Causa-raiz reproduzida: `excluir_cliente` só checava `os.cliente_id`. Um cliente com venda ou
compra por troca era apagado, e a venda, o recibo e a troca perdiam o titular (LEFT JOIN, sem FK).

Cenários do pedido (A a H): histórico preservado com venda e recibo (A), com OS (B), API bloqueando
nova operação com cliente inativo (C), reativação (D), DELETE direto com venda (E), permissões (F),
integridade (G) e compatibilidade (H).
"""

import uuid

import pytest

import app as _app
from migrations.versions import m0007_clientes_ativo


def _executar(sql, params=()):
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _um(sql, params=()):
    conn = _app.conectar()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def _imei():
    return f"35{uuid.uuid4().int % 10**13:013d}"


@pytest.fixture
def cliente_id():
    cid = _executar(
        "INSERT INTO clientes (nome, telefone) VALUES (?, '11988887777')",
        (f"Cliente Inativacao {uuid.uuid4().hex[:6]}",),
    )
    yield cid
    # Limpeza só do que este módulo criou (banco de teste isolado; nunca database.db).
    conn = _app.conectar()
    try:
        venda_ids = [r[0] for r in conn.execute("SELECT id FROM vendas WHERE cliente_id=?", (cid,))]
        for vid in venda_ids:
            conn.execute("DELETE FROM vendas_itens WHERE venda_id=?", (vid,))
        conn.execute("DELETE FROM vendas WHERE cliente_id=?", (cid,))
        conn.execute("UPDATE os SET cliente_id=NULL WHERE cliente_id=?", (cid,))
        conn.execute("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=?", (cid,))
        conn.execute("DELETE FROM clientes WHERE id=?", (cid,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def produto_rastreavel_id():
    return _executar(
        "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('iPhone', 'Apple', ?, 'Seminovo', 3500.0, 0, 1)",
        (f"iPhone 13 Inativacao {uuid.uuid4().hex[:6]}",),
    )


@pytest.fixture
def nova_unidade(produto_rastreavel_id):
    def _criar():
        return _executar(
            "INSERT INTO unidades_serializadas (produto_id, imei, status) VALUES (?, ?, 'disponivel')",
            (produto_rastreavel_id, _imei()),
        )

    return _criar


@pytest.fixture
def loja():
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute(
            "INSERT INTO dados_loja (id, nome_fantasia, termos_garantia) VALUES (1, 'Loja Inativacao', 'Termos.')"
        )
        conn.commit()
        yield
        conn.execute("DELETE FROM dados_loja")
        conn.commit()
    finally:
        conn.close()


def _vender(client, cliente, unidade, tipo_garantia_id):
    return client.post(
        "/api/vendas",
        json={
            "cliente_id": cliente,
            "unidade_serializada_id": unidade,
            "forma_pagamento": "pix",
            "valor_unitario": 3200.0,
            "tipo_garantia_id": tipo_garantia_id,
        },
    )


def _troca(client, cliente, produto_id):
    return client.post(
        "/api/compras-aparelhos",
        json={
            "produto_id": produto_id,
            "imei": _imei(),
            "origem": "troca",
            "cliente_id": cliente,
            "valor_pago": 900.0,
            "forma_pagamento": "pix",
            "estado": "Bom estado",
        },
    )


def _snapshot(cliente):
    """Tudo que aponta para o cliente -- precisa ser idêntico antes e depois de inativar/reativar."""
    conn = _app.conectar()
    try:
        return {
            "cliente": conn.execute(
                "SELECT id, nome, telefone, email, cpf_cnpj, observacoes, criado_em FROM clientes WHERE id=?",
                (cliente,),
            ).fetchone(),
            "vendas": conn.execute(
                "SELECT id, cliente_id, valor_total, status, criado_em FROM vendas WHERE cliente_id=? ORDER BY id",
                (cliente,),
            ).fetchall(),
            "itens": conn.execute(
                "SELECT vi.id, vi.venda_id, vi.unidade_serializada_id, vi.valor_unitario, vi.tipo_garantia_id "
                "FROM vendas_itens vi JOIN vendas v ON v.id = vi.venda_id WHERE v.cliente_id=? ORDER BY vi.id",
                (cliente,),
            ).fetchall(),
            "os": conn.execute(
                "SELECT id, cliente_id, status FROM os WHERE cliente_id=? ORDER BY id", (cliente,)
            ).fetchall(),
            "compras": conn.execute(
                "SELECT id, cliente_id, status, valor_pago FROM compras_aparelhos WHERE cliente_id=? ORDER BY id",
                (cliente,),
            ).fetchall(),
        }
    finally:
        conn.close()


def _ativo_no_banco(cliente):
    return _um("SELECT ativo FROM clientes WHERE id=?", (cliente,))[0]


# ── Migration ────────────────────────────────────────────────────────────────


class TestMigration:
    def test_coluna_ativo_existe_com_default_1(self):
        conn = _app.conectar()
        try:
            colunas = {r[1]: r for r in conn.execute("PRAGMA table_info(clientes)")}
        finally:
            conn.close()
        assert "ativo" in colunas
        _cid, _nome, tipo, notnull, default, _pk = colunas["ativo"]
        assert tipo == "INTEGER" and notnull == 1 and default == "1"

    def test_insert_antigo_sem_coluna_ativo_nasce_ativo(self, cliente_id):
        """H: código antigo (que não conhece `ativo`) continua criando cliente ativo."""
        assert _ativo_no_banco(cliente_id) == 1

    def test_migration_preserva_clientes_e_ids_e_e_idempotente(self):
        import sqlite3

        conn = sqlite3.connect(":memory:")
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE clientes (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, telefone TEXT)")
        cursor.executemany("INSERT INTO clientes (id, nome) VALUES (?, ?)", [(3, "A"), (7, "B"), (42, "C")])
        cursor.execute("CREATE TABLE vendas (id INTEGER PRIMARY KEY, cliente_id INTEGER)")
        cursor.executemany("INSERT INTO vendas (id, cliente_id) VALUES (?, ?)", [(1, 3), (2, 42)])
        conn.commit()

        m0007_clientes_ativo.apply(cursor, conn)
        m0007_clientes_ativo.apply(cursor, conn)  # idempotente

        assert cursor.execute("SELECT id, nome, ativo FROM clientes ORDER BY id").fetchall() == [
            (3, "A", 1),
            (7, "B", 1),
            (42, "C", 1),
        ]
        assert cursor.execute("SELECT id, cliente_id FROM vendas ORDER BY id").fetchall() == [(1, 3), (2, 42)]
        conn.close()


# ── E: DELETE direto não apaga cliente com histórico ─────────────────────────


class TestExclusaoBloqueada:
    def test_delete_de_cliente_com_venda_responde_409_e_preserva_tudo(
        self, client, login_como, usuario_admin, cliente_id, nova_unidade, tipo_garantia_padrao_id
    ):
        """Reproduz o P1-3: antes do fix, este DELETE respondia 200 e a venda ficava sem titular."""
        login_como(client, usuario_admin)
        venda = _vender(client, cliente_id, nova_unidade(), tipo_garantia_padrao_id)
        assert venda.status_code == 201, venda.get_json()
        antes = _snapshot(cliente_id)

        resp = client.delete(f"/api/clientes/{cliente_id}")

        assert resp.status_code == 409
        body = resp.get_json()
        assert body["ok"] is False and "Inative" in body["erro"]
        assert body["vinculos"] == {"os": 0, "vendas": 1, "compras_aparelhos": 0}
        assert _snapshot(cliente_id) == antes
        assert (
            _um(
                "SELECT COUNT(*) FROM audit_log WHERE entidade='cliente' AND entidade_id=? AND acao='delete'",
                (cliente_id,),
            )[0]
            == 0
        )

    def test_delete_de_cliente_com_compra_por_troca_responde_409(
        self, client, login_como, usuario_admin, cliente_id, produto_rastreavel_id
    ):
        login_como(client, usuario_admin)
        assert _troca(client, cliente_id, produto_rastreavel_id).status_code == 201
        resp = client.delete(f"/api/clientes/{cliente_id}")
        assert resp.status_code == 409
        assert resp.get_json()["vinculos"]["compras_aparelhos"] == 1
        assert _um("SELECT id FROM clientes WHERE id=?", (cliente_id,)) is not None

    def test_delete_de_cliente_com_os_continua_bloqueado(self, client, login_como, usuario_admin, cliente_id, criar_os):
        """B: regra já existente (BR-024 original) mantida."""
        os_id = criar_os()
        _executar("UPDATE os SET cliente_id=? WHERE id=?", (cliente_id, os_id))
        login_como(client, usuario_admin)
        resp = client.delete(f"/api/clientes/{cliente_id}")
        assert resp.status_code == 409
        assert resp.get_json()["vinculos"]["os"] == 1
        assert _um("SELECT cliente_id FROM os WHERE id=?", (os_id,))[0] == cliente_id

    def test_cliente_sem_historico_continua_podendo_ser_excluido(self, client, login_como, usuario_admin):
        """H: compatibilidade -- sem vínculo não há o que ficar órfão."""
        login_como(client, usuario_admin)
        cid = client.post("/api/clientes", json={"nome": "Sem Historico", "telefone": "11900000000"}).get_json()["id"]
        resp = client.delete(f"/api/clientes/{cid}")
        assert resp.status_code == 200
        assert _um("SELECT id FROM clientes WHERE id=?", (cid,)) is None
        _executar("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=?", (cid,))


# ── A, B, D, G: inativar e reativar preservando o histórico ──────────────────


class TestInativarReativar:
    def test_a_inativar_cliente_com_venda_preserva_historico_e_recibo(
        self, client, login_como, usuario_admin, cliente_id, nova_unidade, tipo_garantia_padrao_id, loja
    ):
        login_como(client, usuario_admin)
        venda_id = _vender(client, cliente_id, nova_unidade(), tipo_garantia_padrao_id).get_json()["id"]
        recibo_antes = client.get(f"/api/vendas/{venda_id}/recibo").get_json()
        antes = _snapshot(cliente_id)

        resp = client.post(f"/api/clientes/{cliente_id}/inativar")

        assert resp.status_code == 200
        assert resp.get_json() == {"ok": True, "alterado": True, "ativo": False}
        assert _ativo_no_banco(cliente_id) == 0
        assert _snapshot(cliente_id) == antes  # G: ids, vínculos e valores intactos
        # Consulta histórica: o cliente segue acessível e a venda segue com titular.
        detalhe = client.get(f"/api/clientes/{cliente_id}").get_json()["cliente"]
        assert detalhe["ativo"] is False and detalhe["nome"] == antes["cliente"][1]
        venda = client.get(f"/api/vendas/{venda_id}").get_json()
        assert venda["venda"]["cliente_nome"] == antes["cliente"][1]
        assert client.get(f"/api/vendas?cliente_id={cliente_id}").get_json()["total"] == 1
        recibo_depois = client.get(f"/api/vendas/{venda_id}/recibo").get_json()
        assert recibo_depois == recibo_antes
        assert recibo_depois["recibo"]["cliente"]["nome"] == antes["cliente"][1]

    def test_b_inativar_cliente_com_os_preserva_os_e_documento(
        self, client, login_como, usuario_admin, cliente_id, criar_os, loja
    ):
        os_id = criar_os()
        _executar("UPDATE os SET cliente_id=? WHERE id=?", (cliente_id, os_id))
        login_como(client, usuario_admin)
        doc_antes = client.get(f"/api/ordens/{os_id}/documento?tipo=entrada").get_json()

        assert client.post(f"/api/clientes/{cliente_id}/inativar").status_code == 200

        assert _um("SELECT cliente_id FROM os WHERE id=?", (os_id,))[0] == cliente_id
        assert client.get(f"/api/ordens/{os_id}").status_code == 200
        assert client.get(f"/api/ordens/{os_id}/documento?tipo=entrada").get_json() == doc_antes

    def test_d_reativar_devolve_disponibilidade_sem_alterar_historico(
        self, client, login_como, usuario_admin, cliente_id, nova_unidade, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        assert _vender(client, cliente_id, nova_unidade(), tipo_garantia_padrao_id).status_code == 201
        client.post(f"/api/clientes/{cliente_id}/inativar")
        antes = _snapshot(cliente_id)

        resp = client.post(f"/api/clientes/{cliente_id}/reativar")

        assert resp.get_json() == {"ok": True, "alterado": True, "ativo": True}
        assert _snapshot(cliente_id) == antes
        assert _vender(client, cliente_id, nova_unidade(), tipo_garantia_padrao_id).status_code == 201
        ids = [c["id"] for c in client.get("/api/clientes?per_page=500").get_json()["items"]]
        assert cliente_id in ids

    def test_idempotencia_nao_grava_auditoria_repetida(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        assert client.post(f"/api/clientes/{cliente_id}/inativar").get_json()["alterado"] is True
        segunda = client.post(f"/api/clientes/{cliente_id}/inativar")
        assert segunda.status_code == 200
        assert segunda.get_json() == {"ok": True, "alterado": False, "ativo": False}
        assert client.post(f"/api/clientes/{cliente_id}/reativar").get_json()["alterado"] is True
        assert client.post(f"/api/clientes/{cliente_id}/reativar").get_json()["alterado"] is False

        linhas = (
            _app.conectar()
            .execute(
                "SELECT acao, valor_anterior, valor_novo, usuario_id FROM audit_log "
                "WHERE entidade='cliente' AND entidade_id=? AND acao='status_change' ORDER BY id",
                (cliente_id,),
            )
            .fetchall()
        )
        assert [(r[1], r[2]) for r in linhas] == [
            ('{"ativo": true}', '{"ativo": false}'),
            ('{"ativo": false}', '{"ativo": true}'),
        ]
        assert all(r[3] == usuario_admin["id"] for r in linhas)

    def test_auditoria_aparece_no_filtro_status_change(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        client.post(f"/api/clientes/{cliente_id}/inativar")
        resp = client.get(f"/api/auditoria?entidade=cliente&entidade_id={cliente_id}&acao=status_change")
        assert resp.status_code == 200
        item = resp.get_json()["items"][0]
        assert item["alteracoes"] == [{"campo": "ativo", "antes": True, "depois": False}]

    def test_cliente_inexistente_responde_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        assert client.post("/api/clientes/99999999/inativar").status_code == 404
        assert client.post("/api/clientes/99999999/reativar").status_code == 404

    def test_editar_cliente_inativo_mantem_inativo(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        client.post(f"/api/clientes/{cliente_id}/inativar")
        resp = client.put(f"/api/clientes/{cliente_id}", json={"nome": "Nome Corrigido", "telefone": "11911112222"})
        assert resp.status_code == 200
        assert _ativo_no_banco(cliente_id) == 0

    def test_update_comum_nao_registra_ativo_como_campo_alterado(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        client.put(f"/api/clientes/{cliente_id}", json={"nome": "Outro Nome", "telefone": "11911112222"})
        valor_anterior = _um(
            "SELECT valor_anterior FROM audit_log WHERE entidade='cliente' AND entidade_id=? AND acao='update'",
            (cliente_id,),
        )[0]
        assert '"ativo"' not in valor_anterior


# ── C: API recusa nova operação com cliente inativo ──────────────────────────


class TestNovaOperacaoComInativo:
    def test_venda_com_cliente_inativo_e_recusada_sem_efeito(
        self, client, login_como, usuario_admin, cliente_id, nova_unidade, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        client.post(f"/api/clientes/{cliente_id}/inativar")
        unidade = nova_unidade()

        resp = _vender(client, cliente_id, unidade, tipo_garantia_padrao_id)

        assert resp.status_code == 400
        assert "inativo" in resp.get_json()["erro"].lower()
        assert _um("SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cliente_id,))[0] == 0
        assert _um("SELECT status FROM unidades_serializadas WHERE id=?", (unidade,))[0] == "disponivel"

    def test_compra_por_troca_com_cliente_inativo_e_recusada_sem_efeito(
        self, client, login_como, usuario_admin, cliente_id, produto_rastreavel_id
    ):
        login_como(client, usuario_admin)
        client.post(f"/api/clientes/{cliente_id}/inativar")
        caixa_antes = _um("SELECT COUNT(*) FROM movimentacoes_caixa")[0]

        resp = _troca(client, cliente_id, produto_rastreavel_id)

        assert resp.status_code == 400
        assert "inativo" in resp.get_json()["erro"].lower()
        assert _um("SELECT COUNT(*) FROM compras_aparelhos WHERE cliente_id=?", (cliente_id,))[0] == 0
        assert _um("SELECT COUNT(*) FROM movimentacoes_caixa")[0] == caixa_antes

    def test_listagem_padrao_esconde_inativo_e_filtros_o_mostram(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        client.post(f"/api/clientes/{cliente_id}/inativar")

        def ids(qs):
            return [c["id"] for c in client.get(f"/api/clientes?per_page=500{qs}").get_json()["items"]]

        assert cliente_id not in ids("")
        assert cliente_id not in ids("&status=ativos")
        assert cliente_id in ids("&status=inativos")
        assert cliente_id in ids("&status=todos")
        nome = _um("SELECT nome FROM clientes WHERE id=?", (cliente_id,))[0]
        assert cliente_id not in ids(f"&q={nome}")
        assert cliente_id in ids(f"&q={nome}&status=inativos")

    def test_status_invalido_responde_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        assert client.get("/api/clientes?status=apagados").status_code == 400

    def test_itens_da_listagem_trazem_ativo(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        item = next(c for c in client.get("/api/clientes?per_page=500").get_json()["items"] if c["id"] == cliente_id)
        assert item["ativo"] is True


# ── F: permissões validadas no servidor ──────────────────────────────────────


class TestPermissoes:
    @pytest.mark.parametrize(
        "fixture_usuario", ["usuario_financeiro", "usuario_vendedor", "usuario_tecnico", "usuario_estoque"]
    )
    def test_so_admin_inativa_e_reativa(self, client, login_como, request, cliente_id, fixture_usuario):
        login_como(client, request.getfixturevalue(fixture_usuario))
        assert client.post(f"/api/clientes/{cliente_id}/inativar").status_code == 403
        assert _ativo_no_banco(cliente_id) == 1
        _executar("UPDATE clientes SET ativo=0 WHERE id=?", (cliente_id,))
        assert client.post(f"/api/clientes/{cliente_id}/reativar").status_code == 403
        assert _ativo_no_banco(cliente_id) == 0

    def test_nao_autenticado_recebe_403(self, client, cliente_id):
        assert client.post(f"/api/clientes/{cliente_id}/inativar").status_code == 403
        assert client.post(f"/api/clientes/{cliente_id}/reativar").status_code == 403
        assert _ativo_no_banco(cliente_id) == 1

    def test_admin_inativa(self, client, login_como, usuario_admin, cliente_id):
        login_como(client, usuario_admin)
        assert client.post(f"/api/clientes/{cliente_id}/inativar").status_code == 200
