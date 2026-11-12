"""
Relato do cliente, laudo técnico e observação interna da OS (BR-102,
docs/engineering/plans/PLAN-os-relato-laudo.md).
"""

import pytest

import app as _app
from api_os import _SQL_GRAVAR_TEXTO_OS
from fluxoly_core import CAMPOS_TEXTO_OS


def _limpar_os(os_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
    finally:
        conn.close()


def _textos():
    return {
        "relato_cliente": "Cliente diz que a tela apaga sozinha",
        "laudo_tecnico": "Flex da tela rompido",
        "observacao_interna": "Cliente difícil, ligar só depois das 18h",
    }


@pytest.fixture
def loja_cadastrada():
    """Mesmo padrão de tests/test_os_documento.py: documento exige Dados da Loja."""
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute("INSERT INTO dados_loja (id, nome_fantasia) VALUES (1, 'Loja Relato Teste')")
        conn.commit()
        yield
        conn.execute("DELETE FROM dados_loja")
        conn.commit()
    finally:
        conn.close()


def test_sql_cobre_exatamente_os_campos():
    assert set(_SQL_GRAVAR_TEXTO_OS) == set(CAMPOS_TEXTO_OS)


class TestApi:
    def test_cria_e_le_os_tres_textos(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = client.post("/api/ordens", json=payload_os_valido(**_textos())).get_json()["os_id"]
        try:
            ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
            for campo, valor in _textos().items():
                assert ordem[campo] == valor
        finally:
            _limpar_os(os_id)

    def test_edicao_sem_os_campos_nao_apaga(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        os_id = client.post("/api/ordens", json=payload_os_valido(**_textos())).get_json()["os_id"]
        try:
            assert client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Em andamento")).status_code == 200
            ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
            assert ordem["laudo_tecnico"] == "Flex da tela rompido"

            payload = payload_os_valido(status="Em andamento", laudo_tecnico="  Trocado flex  ")
            assert client.put(f"/api/ordens/{os_id}", json=payload).status_code == 200
            ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
            assert ordem["laudo_tecnico"] == "Trocado flex"
            assert ordem["relato_cliente"] == "Cliente diz que a tela apaga sozinha"
        finally:
            _limpar_os(os_id)

    def test_documento_do_cliente_leva_relato_e_laudo_mas_nunca_observacao_interna(
        self, client, login_como, usuario_admin, payload_os_valido, loja_cadastrada
    ):
        login_como(client, usuario_admin)
        os_id = client.post("/api/ordens", json=payload_os_valido(**_textos())).get_json()["os_id"]
        try:
            resp = client.get(f"/api/ordens/{os_id}/documento?tipo=entrada")
            assert resp.status_code == 200, resp.get_json()
            ordem = resp.get_json()["documento"]["ordem"]
            assert ordem["relato_cliente"] == "Cliente diz que a tela apaga sozinha"
            assert ordem["laudo_tecnico"] == "Flex da tela rompido"
            assert "observacao_interna" not in ordem
            assert "ligar só depois" not in resp.get_data(as_text=True)
        finally:
            _limpar_os(os_id)
