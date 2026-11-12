"""
Pendências da tela inicial (docs/engineering/plans/PLAN-pendencias-tela-inicial.md): contas a pagar e
a receber pendentes vencidas e que vencem hoje. Banco de teste compartilhado: totais por diferença.
"""

import pytest

import app as _app
import fluxoly_contas_pagar_service as pagar_service
import fluxoly_contas_receber_service as receber_service

USUARIO_ID_TESTE = 999031
HOJE = "2099-06-15"


def _limpar(tabela, entidade, ids):
    conn = _app.conectar()
    try:
        for conta_id in ids:
            conn.execute("DELETE FROM audit_log WHERE entidade=? AND entidade_id=?", (entidade, conta_id))
            conn.execute(f"DELETE FROM {tabela} WHERE id=?", (conta_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def contas_pagar():
    ids = []

    def criar(valor, vencimento):
        conta_id, erro = pagar_service.criar_conta_pagar(
            _app.conectar, USUARIO_ID_TESTE, "Pendência Teste", "outros", valor, vencimento
        )
        assert erro is None, erro
        ids.append(conta_id)
        return conta_id

    yield criar
    _limpar("contas_pagar", "conta_pagar", ids)


@pytest.fixture
def contas_receber():
    ids = []

    def criar(valor, vencimento):
        conta_id, erro = receber_service.criar_conta_receber(
            _app.conectar, USUARIO_ID_TESTE, "Pendência Teste", "outros", valor, vencimento
        )
        assert erro is None, erro
        ids.append(conta_id)
        return conta_id

    yield criar
    _limpar("contas_receber", "conta_receber", ids)


def _delta(depois, antes, grupo):
    return (
        depois[grupo]["quantidade"] - antes[grupo]["quantidade"],
        round(depois[grupo]["total"] - antes[grupo]["total"], 2),
    )


class TestResumoContasPagar:
    def test_separa_vencidas_das_que_vencem_hoje_e_ignora_futuras(self, contas_pagar):
        antes = pagar_service.resumir_pendencias(_app.conectar, HOJE)
        contas_pagar(100.0, "2099-06-10")
        contas_pagar(50.0, "2099-06-14")
        contas_pagar(30.0, HOJE)
        contas_pagar(999.0, "2099-06-16")
        contas_pagar(999.0, None)
        depois = pagar_service.resumir_pendencias(_app.conectar, HOJE)

        assert _delta(depois, antes, "vencidas") == (2, 150.0)
        assert _delta(depois, antes, "vencem_hoje") == (1, 30.0)

    def test_conta_paga_ou_cancelada_sai_das_pendencias(self, contas_pagar):
        antes = pagar_service.resumir_pendencias(_app.conectar, HOJE)
        cancelada = contas_pagar(70.0, "2099-06-01")
        pagar_service.cancelar_conta_pagar(_app.conectar, USUARIO_ID_TESTE, cancelada)
        depois = pagar_service.resumir_pendencias(_app.conectar, HOJE)

        assert _delta(depois, antes, "vencidas") == (0, 0.0)


class TestResumoContasReceber:
    def test_separa_vencidas_das_que_vencem_hoje(self, contas_receber):
        antes = receber_service.resumir_pendencias(_app.conectar, HOJE)
        contas_receber(200.0, "2099-01-01")
        contas_receber(80.0, HOJE)
        depois = receber_service.resumir_pendencias(_app.conectar, HOJE)

        assert _delta(depois, antes, "vencidas") == (1, 200.0)
        assert _delta(depois, antes, "vencem_hoje") == (1, 80.0)


class TestEndpointPendencias:
    def test_anonimo_recebe_401(self, client):
        assert client.get("/api/pendencias").status_code == 401

    def test_vendedor_e_tecnico_recebem_403(self, client, login_como, usuario_vendedor, usuario_tecnico):
        for usuario in (usuario_vendedor, usuario_tecnico):
            login_como(client, usuario)
            assert client.get("/api/pendencias").status_code == 403

    def test_admin_e_financeiro_recebem_os_dois_resumos(self, client, login_como, usuario_admin, usuario_financeiro):
        for usuario in (usuario_admin, usuario_financeiro):
            login_como(client, usuario)
            resp = client.get("/api/pendencias")
            assert resp.status_code == 200
            body = resp.get_json()
            assert set(body["contas_pagar"]) == {"vencidas", "vencem_hoje"}
            assert set(body["contas_receber"]) == {"vencidas", "vencem_hoje"}
