"""
ADR-014 -- integração MercadoPhone desligada por padrão (MERCADO_PHONE_INTEGRATION_ENABLED).

A suíte liga a flag no conftest.py para continuar cobrindo as rotas existentes; aqui ela é desligada via
monkeypatch no atributo de fluxoly_config, que integracao_mercadophone_habilitada() lê a cada chamada.
"""

import app as _app
import fluxoly_config

ROTAS_POST = [
    "/api/integracoes/mercadophone/sincronizar",
    "/api/integracoes/mercadophone/reprocessar",
    "/api/integracoes/mercadophone/reimportar",
    "/api/integracoes/mercadophone/config",
    "/api/integracoes/mercadophone/os",
]
ROTAS_GET = [
    "/api/integracoes/mercadophone/status",
    "/api/integracoes/mercadophone/reprocessar/status",
    "/api/integracoes/mercadophone/reimportar/status",
]


def _login_legado(client, usuario):
    return client.post("/login", data={"usuario": usuario["usuario"], "senha": usuario["senha"]})


class TestRotasComIntegracaoDesligada:
    def test_todas_as_rotas_respondem_404_para_admin(self, client, usuario_admin, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "MERCADO_PHONE_INTEGRATION_ENABLED", False)
        _login_legado(client, usuario_admin)

        for rota in ROTAS_POST:
            assert client.post(rota, json={}).status_code == 404, rota
        for rota in ROTAS_GET:
            assert client.get(rota).status_code == 404, rota

    def test_webhook_responde_404_mesmo_sem_sessao(self, client, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "MERCADO_PHONE_INTEGRATION_ENABLED", False)

        resp = client.post("/api/integracoes/mercadophone/os", json={"id": 1})

        assert resp.status_code == 404

    def test_config_nao_grava_token_com_integracao_desligada(self, client, usuario_admin, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "MERCADO_PHONE_INTEGRATION_ENABLED", False)
        _login_legado(client, usuario_admin)

        resp = client.post("/api/integracoes/mercadophone/config", json={"api_token": "nao-pode-ser-salvo"})

        assert resp.status_code == 404
        config = _app.carregar_configuracoes_integracoes(_app.INTEGRATIONS_CONFIG_PATH)
        assert (config.get("mercado_phone") or {}).get("api_token") != "nao-pode-ser-salvo"

    def test_rotas_voltam_a_existir_com_a_flag_ligada(self, client, usuario_admin, monkeypatch):
        monkeypatch.setattr(fluxoly_config, "MERCADO_PHONE_INTEGRATION_ENABLED", True)
        _login_legado(client, usuario_admin)

        assert client.get("/api/integracoes/mercadophone/status").status_code != 404


class _ThreadFalsa:
    iniciadas = []

    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs

    def start(self):
        _ThreadFalsa.iniciadas.append(self.kwargs.get("name"))


class TestSyncEmBackground:
    def _preparar_sync_que_iniciaria(self, monkeypatch):
        """Tudo que antes bastava para subir o sync: jobs ligados, sync habilitado e token presente."""
        _ThreadFalsa.iniciadas = []
        monkeypatch.setattr(_app, "BACKGROUND_JOBS_ENABLED", True)
        monkeypatch.setattr(_app, "MERCADO_PHONE_SYNC_ENABLED", True)
        monkeypatch.setattr(_app, "MERCADO_PHONE_API_TOKEN", "token-de-teste")
        monkeypatch.setattr(_app, "_MERCADO_PHONE_SYNC_THREAD_STARTED", False)
        monkeypatch.setattr(_app.threading, "Thread", _ThreadFalsa)

    def test_sync_nao_inicia_com_integracao_desligada_mesmo_com_token(self, monkeypatch):
        self._preparar_sync_que_iniciaria(monkeypatch)
        monkeypatch.setattr(fluxoly_config, "MERCADO_PHONE_INTEGRATION_ENABLED", False)

        _app.iniciar_sync_mercadophone_se_habilitado()

        assert _ThreadFalsa.iniciadas == []
        assert _app._MERCADO_PHONE_SYNC_THREAD_STARTED is False

    def test_sync_inicia_com_integracao_ligada(self, monkeypatch):
        self._preparar_sync_que_iniciaria(monkeypatch)
        monkeypatch.setattr(fluxoly_config, "MERCADO_PHONE_INTEGRATION_ENABLED", True)

        _app.iniciar_sync_mercadophone_se_habilitado()

        assert _ThreadFalsa.iniciadas == ["mercadophone-sync"]
