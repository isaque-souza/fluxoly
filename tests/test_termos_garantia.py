"""
Termos de garantia cadastrados e escolhidos na OS (BR-105,
docs/engineering/plans/PLAN-termos-garantia-os.md).

Cobre o cadastro `/api/termos-garantia`, a escolha opcional do termo ao
finalizar a OS (PATCH de status e PUT completo), o snapshot, o fallback para o
texto padrão de Dados da Loja no comprovante de entrega, o cancelamento e a
troca do termo por admin.
"""

import pytest

import app as _app


def _inserir_termo(nome="Termo Teste", texto="Texto do termo teste.", ativo=1):
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO termos_garantia_modelos (nome, texto, ativo) VALUES (?, ?, ?)",
            (nome, texto, ativo),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _limpar_termos_e_loja():
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute(
            "INSERT INTO dados_loja (id, nome_fantasia, termos_entrada, termos_garantia) "
            "VALUES (1, 'Loja Termos Teste', 'Entrada padrão.', 'Garantia padrão da loja.')"
        )
        conn.commit()
    finally:
        conn.close()
    yield
    conn = _app.conectar()
    try:
        conn.execute("UPDATE os SET termo_garantia_id=NULL, termo_garantia_nome=NULL, termo_garantia_texto=NULL")
        conn.execute("DELETE FROM termos_garantia_modelos")
        conn.execute("DELETE FROM dados_loja")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def termo_id():
    return _inserir_termo("Assistência 90 dias", "Cobre defeito do serviço executado por 90 dias.")


def _snapshot(os_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT termo_garantia_id, termo_garantia_nome, termo_garantia_texto FROM os WHERE id=?", (os_id,)
        ).fetchone()
    finally:
        conn.close()


def _finalizar(client, os_id, reparo_id, tipo_garantia_id, **extra):
    return client.patch(
        f"/api/ordens/{os_id}/status",
        json={"status": "Finalizado", "garantias": {str(reparo_id): tipo_garantia_id}, **extra},
    )


def _termos_do_documento(client, os_id):
    resp = client.get(f"/api/ordens/{os_id}/documento?tipo=entrega")
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["documento"]["termos"]


class TestCadastro:
    def test_admin_cria_lista_e_edita(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/termos-garantia", json={"nome": "  Troca de tela ", "texto": " Texto. "})
        assert resp.status_code == 201
        novo_id = resp.get_json()["id"]

        itens = client.get("/api/termos-garantia").get_json()["items"]
        assert {"id": novo_id, "nome": "Troca de tela", "texto": "Texto.", "ativo": True} in itens

        resp = client.put(
            f"/api/termos-garantia/{novo_id}", json={"nome": "Troca de tela", "texto": "Novo.", "ativo": False}
        )
        assert resp.status_code == 200
        assert all(t["id"] != novo_id for t in client.get("/api/termos-garantia").get_json()["items"])
        inativos = client.get("/api/termos-garantia?incluir_inativos=1").get_json()["items"]
        assert any(t["id"] == novo_id and t["ativo"] is False for t in inativos)

    @pytest.mark.parametrize(
        "payload",
        [{"nome": "", "texto": "x"}, {"nome": "x", "texto": "  "}, {"nome": "x", "texto": "a" * 4001}],
    )
    def test_validacao(self, client, login_como, usuario_admin, payload):
        login_como(client, usuario_admin)
        assert client.post("/api/termos-garantia", json=payload).status_code == 400

    def test_editar_inexistente_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.put("/api/termos-garantia/999999", json={"nome": "x", "texto": "y"})
        assert resp.status_code == 404

    def test_nao_admin_so_le_ativos(self, client, login_como, usuario_tecnico):
        _inserir_termo("Inativo", ativo=0)
        login_como(client, usuario_tecnico)
        assert client.post("/api/termos-garantia", json={"nome": "x", "texto": "y"}).status_code == 403
        assert client.put("/api/termos-garantia/1", json={"nome": "x", "texto": "y"}).status_code == 403
        itens = client.get("/api/termos-garantia?incluir_inativos=1").get_json()["items"]
        assert all(t["ativo"] for t in itens)

    def test_sem_login_401(self, client):
        assert client.get("/api/termos-garantia").status_code == 401


class TestFinalizacao:
    def test_sem_termo_usa_texto_padrao_da_loja(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        assert _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id).status_code == 200
        assert _snapshot(os_id) == (None, None, None)
        assert _termos_do_documento(client, os_id) == "Garantia padrão da loja."

    def test_com_termo_grava_snapshot_e_sai_no_documento(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, termo_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id, termo_garantia_id=termo_id)
        assert resp.status_code == 200
        assert _snapshot(os_id) == (
            termo_id,
            "Assistência 90 dias",
            "Cobre defeito do serviço executado por 90 dias.",
        )
        assert _termos_do_documento(client, os_id) == "Cobre defeito do serviço executado por 90 dias."
        ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
        assert ordem["termo_garantia"] == {"id": termo_id, "nome": "Assistência 90 dias"}

    def test_documento_de_entrada_nao_muda(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, termo_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id, termo_garantia_id=termo_id)
        resp = client.get(f"/api/ordens/{os_id}/documento?tipo=entrada")
        assert resp.get_json()["documento"]["termos"] == "Entrada padrão."

    def test_editar_termo_depois_nao_altera_os_finalizada(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, termo_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id, termo_garantia_id=termo_id)
        client.put(f"/api/termos-garantia/{termo_id}", json={"nome": "Outro", "texto": "Texto novo.", "ativo": False})
        assert _termos_do_documento(client, os_id) == "Cobre defeito do serviço executado por 90 dias."

    @pytest.mark.parametrize("valor", ["abc", True, 999999])
    def test_termo_invalido_recusa_e_nao_finaliza(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, valor
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id, termo_garantia_id=valor)
        assert resp.status_code == 400
        assert client.get(f"/api/ordens/{os_id}").get_json()["ordem"]["status"] == "Em andamento"

    def test_termo_inativo_recusa(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        inativo = _inserir_termo("Inativo", ativo=0)
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id, termo_garantia_id=inativo)
        assert resp.status_code == 400

    def test_finalizar_via_put_grava_snapshot(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, termo_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.put(
            f"/api/ordens/{os_id}", json=payload_os_valido(status="Finalizado", termo_garantia_id=termo_id)
        )
        assert resp.status_code == 200, resp.get_json()
        assert _snapshot(os_id)[0] == termo_id

    def test_editar_os_finalizada_via_put_preserva_termo(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, termo_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Finalizado", termo_garantia_id=termo_id))
        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Finalizado", observacoes="depois"))
        assert resp.status_code == 200
        assert _snapshot(os_id)[0] == termo_id

    def test_cancelar_zera_o_termo_e_audita(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, termo_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id, termo_garantia_id=termo_id)
        assert client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"}).status_code == 200
        assert _snapshot(os_id) == (None, None, None)
        conn = _app.conectar()
        try:
            acoes = [
                r[0]
                for r in conn.execute(
                    "SELECT acao FROM audit_log WHERE entidade='os' AND entidade_id=? ORDER BY id", (os_id,)
                ).fetchall()
            ]
        finally:
            conn.close()
        assert "termo_garantia_definido" in acoes
        assert "termo_garantia_alterado" in acoes


class TestTrocaPorAdmin:
    def test_admin_troca_e_remove(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, termo_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)
        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"termo_garantia_id": termo_id})
        assert resp.status_code == 200
        assert resp.get_json()["termo_garantia"] == {"id": termo_id, "nome": "Assistência 90 dias"}
        assert _snapshot(os_id)[0] == termo_id

        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"termo_garantia_id": None})
        assert resp.status_code == 200
        assert _snapshot(os_id) == (None, None, None)
        assert _termos_do_documento(client, os_id) == "Garantia padrão da loja."

    def test_nao_admin_403(self, client, login_como, usuario_tecnico, criar_os, termo_id):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado")
        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"termo_garantia_id": termo_id})
        assert resp.status_code == 403

    def test_os_nao_finalizada_409(self, client, login_como, usuario_admin, criar_os, termo_id):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento")
        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"termo_garantia_id": termo_id})
        assert resp.status_code == 409

    def test_os_inexistente_404(self, client, login_como, usuario_admin, termo_id):
        login_como(client, usuario_admin)
        resp = client.patch("/api/ordens/999999/termo-garantia", json={"termo_garantia_id": termo_id})
        assert resp.status_code == 404
