"""
Testes da tela de Auditoria (`GET /api/auditoria`,
docs/engineering/plans/PLAN-tela-auditoria.md).

Cobre: permissão (admin/financeiro sim; vendedor/técnico não; anônimo 401),
filtros, diff campo a campo, paginação e ausência de rota de escrita.
"""

import json

import app as _app
from fluxoly_audit import registrar_log_auditoria
from fluxoly_auditoria_service import _diff

ENTIDADE = "teste_tela_auditoria"


def _gravar(entidade_id, acao, antes=None, depois=None, usuario_id=None):
    conn = _app.conectar()
    try:
        registrar_log_auditoria(conn.cursor(), ENTIDADE, entidade_id, usuario_id, acao, antes=antes, depois=depois)
        conn.commit()
    finally:
        conn.close()


def _limpar():
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade = ?", (ENTIDADE,))
        conn.commit()
    finally:
        conn.close()


class TestPermissao:
    def test_anonimo_recebe_401(self, client):
        assert client.get("/api/auditoria").status_code == 401

    def test_vendedor_recebe_403(self, client, usuario_vendedor, login_como):
        login_como(client, usuario_vendedor)
        assert client.get("/api/auditoria").status_code == 403

    def test_tecnico_recebe_403(self, client, usuario_tecnico, login_como):
        login_como(client, usuario_tecnico)
        assert client.get("/api/auditoria").status_code == 403

    def test_admin_e_financeiro_podem_ler(self, client, usuario_admin, usuario_financeiro, login_como):
        login_como(client, usuario_admin)
        assert client.get("/api/auditoria").status_code == 200
        client.post("/api/auth/logout")
        login_como(client, usuario_financeiro)
        assert client.get("/api/auditoria").status_code == 200

    def test_nao_existe_rota_de_escrita(self, client, usuario_admin, login_como):
        login_como(client, usuario_admin)
        for metodo in (client.post, client.put, client.patch, client.delete):
            assert metodo("/api/auditoria").status_code == 405


class TestListagem:
    def setup_method(self):
        _limpar()

    def teardown_method(self):
        _limpar()

    def test_filtra_por_entidade_e_registro_e_traz_nome_do_usuario(self, client, usuario_admin, login_como):
        _gravar(1, "update", antes={"nome": "A", "telefone": "1"}, depois={"nome": "B", "telefone": "1"},
                usuario_id=usuario_admin["id"])
        _gravar(2, "create", depois={"nome": "C"})
        login_como(client, usuario_admin)

        resp = client.get(f"/api/auditoria?entidade={ENTIDADE}&entidade_id=1").get_json()

        assert resp["ok"] is True
        assert resp["total"] == 1
        item = resp["items"][0]
        assert item["acao"] == "update"
        assert item["usuario_nome"] == "Admin Teste"
        assert item["alteracoes"] == [{"campo": "nome", "antes": "A", "depois": "B"}]
        assert ENTIDADE in resp["entidades"]

    def test_filtra_por_acao_e_rejeita_acao_invalida(self, client, usuario_admin, login_como):
        _gravar(1, "update", antes={"x": 1}, depois={"x": 2})
        _gravar(1, "delete", antes={"x": 2})
        login_como(client, usuario_admin)

        resp = client.get(f"/api/auditoria?entidade={ENTIDADE}&acao=delete").get_json()
        assert [i["acao"] for i in resp["items"]] == ["delete"]
        assert client.get("/api/auditoria?acao=apagar_tudo").status_code == 400

    def test_paginacao_mais_recente_primeiro_e_limite(self, client, usuario_admin, login_como):
        for i in range(3):
            _gravar(i, "create", depois={"n": i})
        login_como(client, usuario_admin)

        pagina1 = client.get(f"/api/auditoria?entidade={ENTIDADE}&per_page=2").get_json()
        pagina2 = client.get(f"/api/auditoria?entidade={ENTIDADE}&per_page=2&page=2").get_json()

        assert pagina1["total"] == 3
        assert [i["entidade_id"] for i in pagina1["items"]] == [2, 1]
        assert [i["entidade_id"] for i in pagina2["items"]] == [0]
        assert client.get("/api/auditoria?per_page=5000").get_json()["per_page"] == 100

    def test_snapshot_devolvido_como_gravado(self, client, usuario_admin, login_como):
        _gravar(9, "update", antes={"telefone": "***"}, depois={"telefone": "***"})
        login_como(client, usuario_admin)

        item = client.get(f"/api/auditoria?entidade={ENTIDADE}").get_json()["items"][0]

        assert item["antes"] == {"telefone": "***"}
        assert item["alteracoes"] == []


class TestDiff:
    def test_create_lista_campos_do_lado_novo(self):
        assert _diff(None, {"a": 1}) == [{"campo": "a", "antes": None, "depois": 1}]

    def test_valores_nao_dict_nao_geram_diff(self):
        assert _diff("texto", json.dumps([1])) == []
