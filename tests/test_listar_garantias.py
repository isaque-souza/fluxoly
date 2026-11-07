"""
Testes de GET /api/garantias após a reescrita da V1.5 (BR-062/BR-063,
docs/engineering/plans/PLAN-V1.5-Garantia.md).

Escopo: a resposta passa a ter uma entrada por linha de `os_reparos`, não
mais uma por OS inteira -- uma OS com vários reparos gera várias entradas,
cada uma com seu próprio prazo. Linhas com `tipo_garantia_id` gravado (dado
novo, pós-V1.5) usam o snapshot (`garantia_data_fim`); linhas sem isso (dado
histórico, ou isentas por BR-061 como sync do Mercado Phone) caem no
fallback do prazo fixo de 90 dias a partir de `data_finalizado`.
"""

from datetime import date, timedelta

import app as _app
from fluxoly_core import GARANTIA_REPARO_DIAS_PADRAO


def _gravar_garantia_reparo(os_id, reparo_id, duracao_meses, data_inicio, data_fim):
    conn = _app.conectar()
    try:
        conn.execute(
            """
            UPDATE os_reparos
            SET tipo_garantia_id=1, garantia_nome='Garantia Teste',
                garantia_duracao_meses=?, garantia_data_inicio=?, garantia_data_fim=?
            WHERE os_id=? AND reparo_id=?
            """,
            (duracao_meses, data_inicio, data_fim, os_id, reparo_id),
        )
        conn.commit()
    finally:
        conn.close()


def _nome_reparo(reparo_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT nome FROM reparos WHERE id=?", (reparo_id,)).fetchone()[0]
    finally:
        conn.close()


class TestListarGarantiasPorLinhaDeReparo:
    def test_uma_os_com_dois_reparos_gera_duas_entradas(
        self, client, login_como, usuario_tecnico, criar_os, dois_reparos_ids
    ):
        login_como(client, usuario_tecnico)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_a, reparo_b])

        resp = client.get("/api/garantias")
        assert resp.status_code == 200
        entradas = [g for g in resp.get_json()["ordens"] if g["id"] == os_id]
        assert len(entradas) == 2
        assert {e["reparo_id"] for e in entradas} == {reparo_a, reparo_b}

    def test_dado_novo_usa_snapshot_gravado(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_padrao_id])
        hoje = date.today()
        data_fim = hoje + timedelta(days=200)
        _gravar_garantia_reparo(os_id, reparo_padrao_id, 12, hoje.isoformat(), data_fim.isoformat())

        resp = client.get("/api/garantias")
        entrada = next(g for g in resp.get_json()["ordens"] if g["id"] == os_id)
        assert entrada["garantia"]["dias_restantes"] == 200
        assert entrada["garantia"]["color"] == "green"

    def test_dado_historico_cai_no_fallback_90_dias(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        """tipo_garantia_id NULL (criar_os não concede garantia por padrão) --
        mesmo comportamento de uma OS concluída antes da V1.5 existir."""
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_padrao_id])

        resp = client.get("/api/garantias")
        entrada = next(g for g in resp.get_json()["ordens"] if g["id"] == os_id)
        assert entrada["garantia"]["dias_restantes"] <= GARANTIA_REPARO_DIAS_PADRAO

    def test_multiplos_reparos_com_prazos_diferentes(
        self, client, login_como, usuario_tecnico, criar_os, dois_reparos_ids
    ):
        """BR-062 -- cada linha mantém seu próprio prazo, mesmo dentro da
        mesma OS: uma com snapshot novo, outra caindo no fallback histórico."""
        login_como(client, usuario_tecnico)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_a, reparo_b])
        hoje = date.today()
        _gravar_garantia_reparo(os_id, reparo_a, 24, hoje.isoformat(), (hoje + timedelta(days=700)).isoformat())

        resp = client.get("/api/garantias")
        entradas = {g["reparo_id"]: g for g in resp.get_json()["ordens"] if g["id"] == os_id}
        assert entradas[reparo_a]["garantia"]["dias_restantes"] == 700
        assert entradas[reparo_b]["garantia"]["dias_restantes"] <= GARANTIA_REPARO_DIAS_PADRAO

    def test_busca_por_nome_do_reparo(self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_padrao_id])
        nome = _nome_reparo(reparo_padrao_id)

        resp = client.get(f"/api/garantias?q={nome}")
        assert any(g["id"] == os_id for g in resp.get_json()["ordens"])

    def test_cliente_ir_phones_tratado_como_cliente_comum(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        """ADR-014: a exclusão do cliente 'IR Phones' da lista de garantias foi removida."""
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado", cliente="IR Phones", reparo_ids=[reparo_padrao_id])

        resp = client.get("/api/garantias")
        assert any(g["id"] == os_id for g in resp.get_json()["ordens"])

    def test_os_nao_finalizada_nao_aparece(self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])

        resp = client.get("/api/garantias")
        assert all(g["id"] != os_id for g in resp.get_json()["ordens"])

    def test_contadores_refletem_granularidade_por_linha(
        self, client, login_como, usuario_tecnico, criar_os, dois_reparos_ids
    ):
        """total/ativas/vencendo/vencidas contam linhas de reparo, não OS --
        uma OS com 2 reparos concedidos e ativos soma 2 no total, não 1."""
        login_como(client, usuario_tecnico)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_a, reparo_b])
        hoje = date.today()
        fim_ativo = (hoje + timedelta(days=300)).isoformat()
        _gravar_garantia_reparo(os_id, reparo_a, 12, hoje.isoformat(), fim_ativo)
        _gravar_garantia_reparo(os_id, reparo_b, 12, hoje.isoformat(), fim_ativo)

        resp = client.get("/api/garantias")
        body = resp.get_json()
        entradas_desta_os = [g for g in body["ordens"] if g["id"] == os_id]
        assert len(entradas_desta_os) == 2
        assert body["total"] >= 2
