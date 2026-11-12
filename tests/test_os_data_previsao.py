"""
Data de previsão de entrega da OS e destaque de atrasada (BR-101,
docs/engineering/plans/PLAN-os-data-previsao.md).
"""

from datetime import date

import app as _app
from fluxoly_core import normalizar_data_previsao, os_atrasada


def _limpar_os(os_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
    finally:
        conn.close()


class TestRegras:
    def test_normaliza_data_ou_vazio(self):
        assert normalizar_data_previsao("2026-11-20") == ("2026-11-20", None)
        assert normalizar_data_previsao("") == (None, None)
        assert normalizar_data_previsao(None) == (None, None)
        data, erro = normalizar_data_previsao("20/11/2026")
        assert data is None and erro

    def test_atrasada_so_quando_aberta_e_previsao_passou(self):
        hoje = date(2026, 11, 11)
        assert os_atrasada("Em andamento", "2026-11-10", hoje) is True
        assert os_atrasada("Aguardando peça", "2026-11-01", hoje) is True
        assert os_atrasada("Em andamento", "2026-11-11", hoje) is False  # vence no fim do dia
        assert os_atrasada("Em andamento", "2026-11-12", hoje) is False
        assert os_atrasada("Finalizado", "2026-11-01", hoje) is False
        assert os_atrasada("Cancelado", "2026-11-01", hoje) is False
        assert os_atrasada("Em andamento", "", hoje) is False


class TestApi:
    def test_cria_com_previsao_e_lista_como_atrasada(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(data_previsao="2000-01-10"))
        assert resp.status_code == 201, resp.get_json()
        os_id = resp.get_json()["os_id"]
        try:
            ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
            assert ordem["data_previsao"] == "2000-01-10"
            assert ordem["atrasada"] is True

            item = next(o for o in client.get("/api/ordens").get_json()["ordens"] if o["id"] == os_id)
            assert item["data_previsao"] == "2000-01-10" and item["atrasada"] is True
        finally:
            _limpar_os(os_id)

    def test_previsao_invalida_rejeita(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(data_previsao="amanhã"))
        assert resp.status_code == 400

    def test_edicao_sem_o_campo_mantem_previsao_e_com_vazio_limpa(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        os_id = client.post("/api/ordens", json=payload_os_valido(data_previsao="2099-01-01")).get_json()["os_id"]
        try:
            payload = payload_os_valido(status="Em andamento")
            assert client.put(f"/api/ordens/{os_id}", json=payload).status_code == 200
            assert client.get(f"/api/ordens/{os_id}").get_json()["ordem"]["data_previsao"] == "2099-01-01"

            payload["data_previsao"] = ""
            assert client.put(f"/api/ordens/{os_id}", json=payload).status_code == 200
            ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
            assert ordem["data_previsao"] == "" and ordem["atrasada"] is False
        finally:
            _limpar_os(os_id)

    def test_finalizar_tira_o_atraso(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = client.post("/api/ordens", json=payload_os_valido(data_previsao="2000-01-10")).get_json()["os_id"]
        try:
            resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Finalizado"))
            assert resp.status_code == 200, resp.get_json()
            assert client.get(f"/api/ordens/{os_id}").get_json()["ordem"]["atrasada"] is False
        finally:
            _limpar_os(os_id)

    def test_dashboard_conta_os_atrasadas(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        antes = client.get("/api/dashboard").get_json()["ordens_atrasadas"]
        os_id = client.post("/api/ordens", json=payload_os_valido(data_previsao="2000-01-10")).get_json()["os_id"]
        try:
            assert client.get("/api/dashboard").get_json()["ordens_atrasadas"] == antes + 1
        finally:
            _limpar_os(os_id)
