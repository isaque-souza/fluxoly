"""
OS interna -- conserto de aparelho comprado pela loja (BR-090, BR-091;
docs/engineering/plans/PLAN-compra-aparelhos.md, PR 3).

Cobre: criação ligada a um aparelho com compra ativa (sem cliente, vendedor nem
valor), aparelho `disponivel` indo para `em_reparo`, finalização devolvendo o
aparelho para `disponivel` sem exigir garantia, reabertura, peças entrando no
custo da OS, e a exclusão da OS interna do dashboard, dos relatórios e de
Garantias.
"""

import uuid

import pytest

import app as _app
import fluxoly_reports


def _imei():
    return f"35{uuid.uuid4().int % 10**13:013d}"


def _consultar(sql, params=()):
    conn = _app.conectar()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


def _executar(sql, params=()):
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _status_aparelho(unidade_id):
    return _consultar("SELECT status FROM unidades_serializadas WHERE id = ?", (unidade_id,))[0]


@pytest.fixture
def aparelho_comprado(client, login_como, usuario_admin):
    """Factory: registra uma compra pela API e devolve o id da unidade criada."""
    produto_id = _executar(
        "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('iPhone', 'Apple', 'iPhone 13', 'Seminovo', 3500.0, 0, 1)"
    )

    def _comprar(defeito="Tela quebrada"):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/compras-aparelhos",
            json={
                "produto_id": produto_id,
                "imei": _imei(),
                "origem": "marketplace",
                "valor_pago": 1000,
                "forma_pagamento": "pix",
                "estado": "Usado",
                "defeito": defeito,
            },
        )
        assert resp.status_code == 201, resp.get_json()
        compra = client.get(f"/api/compras-aparelhos/{resp.get_json()['id']}").get_json()["compra"]
        return compra["unidade_serializada_id"]

    return _comprar


@pytest.fixture
def payload_interna(reparo_padrao_id):
    def _payload(unidade_id, **extra):
        dados = {
            "tipo": "Interna",
            "modelo": "iPhone 13",
            "tecnico": "ISAQUE SOUZA",
            "reparo_ids": [reparo_padrao_id],
            "unidade_serializada_id": unidade_id,
            # Enviados de propósito: o backend tem que ignorar (BR-090).
            "cliente": "Alguém",
            "vendedor": "Camila",
            "valor_cobrado": 500,
            "valor_descontado": 400,
        }
        dados.update(extra)
        return dados

    return _payload


def _criar_os_interna(client, login_como, usuario_tecnico, payload):
    login_como(client, usuario_tecnico)
    resp = client.post("/api/ordens", json=payload)
    assert resp.status_code == 201, resp.get_json()
    return resp.get_json()["os_id"]


class TestCriarOsInterna:
    def test_forca_cliente_vendedor_e_valores_e_liga_ao_aparelho(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado()
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))

        ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
        assert ordem["tipo"] == "Interna"
        assert ordem["cliente"] == "Estoque próprio"
        assert ordem["vendedor"] == ""
        assert ordem["valor_cobrado"] == 0 and ordem["valor_descontado"] == 0
        assert ordem["unidade_serializada_id"] == unidade_id
        imei_aparelho = _consultar("SELECT imei FROM unidades_serializadas WHERE id = ?", (unidade_id,))[0]
        assert ordem["imei"] == imei_aparelho
        assert _status_aparelho(unidade_id) == "em_reparo"

    def test_aparelho_disponivel_vai_para_em_reparo(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado(defeito="")
        assert _status_aparelho(unidade_id) == "disponivel"

        _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))

        assert _status_aparelho(unidade_id) == "em_reparo"

    def test_exige_aparelho(self, client, login_como, usuario_tecnico, payload_interna):
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_interna(None))

        assert resp.status_code == 400
        assert "aparelho" in resp.get_json()["erro"]

    def test_aparelho_sem_compra_e_recusado(self, client, login_como, usuario_tecnico, payload_interna):
        produto_id = _executar(
            "INSERT INTO produtos (categoria, marca, modelo, preco_venda, quantidade, requer_rastreio_unidade) "
            "VALUES ('iPhone', 'Apple', 'iPhone 12', 3000.0, 0, 1)"
        )
        unidade_id = _executar(
            "INSERT INTO unidades_serializadas (produto_id, imei) VALUES (?, ?)", (produto_id, _imei())
        )
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_interna(unidade_id))

        assert resp.status_code == 400
        assert "compra ativa" in resp.get_json()["erro"]

    def test_aparelho_vendido_e_recusado_sem_criar_os(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado()
        _executar("UPDATE unidades_serializadas SET status = 'vendido' WHERE id = ?", (unidade_id,))
        total_antes = _consultar("SELECT COUNT(*) FROM os")[0]
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_interna(unidade_id))

        assert resp.status_code == 400
        assert _consultar("SELECT COUNT(*) FROM os")[0] == total_antes

    def test_vendedor_nao_abre_os_interna(
        self, client, login_como, usuario_vendedor, aparelho_comprado, payload_interna
    ):
        """BR-030 continua valendo: OS é de admin/tecnico."""
        unidade_id = aparelho_comprado()
        login_como(client, usuario_vendedor)

        resp = client.post("/api/ordens", json=payload_interna(unidade_id))

        assert resp.status_code == 403


class TestFinalizarOsInterna:
    def test_finalizar_sem_garantia_deixa_aparelho_disponivel(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        """BR-091 + BR-090 (sem garantia de reparo)."""
        unidade_id = aparelho_comprado()
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})

        assert resp.status_code == 200, resp.get_json()
        assert _status_aparelho(unidade_id) == "disponivel"
        garantias = _consultar(
            "SELECT COUNT(*) FROM os_reparos WHERE os_id = ? AND tipo_garantia_id IS NOT NULL", (os_id,)
        )
        assert garantias == (0,)

    def test_finalizar_pelo_formulario_completo_tambem_libera(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado()
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))

        resp = client.put(f"/api/ordens/{os_id}", json=payload_interna(unidade_id, status="Finalizado"))

        assert resp.status_code == 200, resp.get_json()
        assert _status_aparelho(unidade_id) == "disponivel"
        ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
        assert ordem["cliente"] == "Estoque próprio" and ordem["valor_cobrado"] == 0

    def test_com_outra_os_interna_aberta_aparelho_continua_em_reparo(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado()
        primeira = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))
        _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))

        client.patch(f"/api/ordens/{primeira}/status", json={"status": "Finalizado"})

        assert _status_aparelho(unidade_id) == "em_reparo"

    def test_reabrir_os_finalizada_volta_aparelho_para_em_reparo(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado()
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))
        client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Em andamento"})

        assert resp.status_code == 200
        assert _status_aparelho(unidade_id) == "em_reparo"

    def test_nao_reabre_se_aparelho_ja_foi_vendido(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna
    ):
        unidade_id = aparelho_comprado()
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))
        client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})
        _executar("UPDATE unidades_serializadas SET status = 'vendido' WHERE id = ?", (unidade_id,))

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Em andamento"})

        assert resp.status_code == 400
        assert _consultar("SELECT status FROM os WHERE id = ?", (os_id,)) == ("Finalizado",)

    def test_os_de_cliente_continua_exigindo_garantia(self, client, login_como, usuario_tecnico, criar_os):
        """Regressão: a dispensa de garantia é só para a OS interna (BR-061 intacta)."""
        os_id = criar_os()
        login_como(client, usuario_tecnico)

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})

        assert resp.status_code == 400


class TestTipoNaoMuda:
    def test_os_de_cliente_nao_vira_interna(self, client, login_como, usuario_tecnico, criar_os, payload_interna):
        os_id = criar_os()
        login_como(client, usuario_tecnico)

        resp = client.put(f"/api/ordens/{os_id}", json=payload_interna(None, status="Em andamento"))

        assert resp.status_code == 400

    def test_os_interna_nao_vira_de_cliente(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, payload_os_valido
    ):
        unidade_id = aparelho_comprado()
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id))

        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Em andamento"))

        assert resp.status_code == 400


class TestForaDosNumerosDeAssistencia:
    def _os_interna_finalizada_com_peca(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
    ):
        unidade_id = aparelho_comprado()
        peca_id = criar_item_estoque(modelo="iPhone 13", valor=300.0)
        os_id = _criar_os_interna(client, login_como, usuario_tecnico, payload_interna(unidade_id, pecas_ids=[peca_id]))
        client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})
        return os_id

    def test_peca_entra_no_custo_da_os_interna(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
    ):
        os_id = self._os_interna_finalizada_com_peca(
            client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
        )

        assert client.get(f"/api/ordens/{os_id}").get_json()["ordem"]["custo_pecas"] == 300.0

    def test_dashboard_ignora_os_interna(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        antes = client.get("/api/dashboard").get_json()

        self._os_interna_finalizada_com_peca(
            client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
        )
        login_como(client, usuario_tecnico)
        depois = client.get("/api/dashboard").get_json()

        for chave in ("lucro_total", "faturamento_total", "ordens_finalizadas"):
            assert depois[chave] == antes[chave], chave

    def test_garantias_ignora_os_interna(
        self, client, login_como, usuario_admin, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
    ):
        os_id = self._os_interna_finalizada_com_peca(
            client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
        )
        login_como(client, usuario_admin)

        resp = client.get("/api/garantias")

        assert resp.status_code == 200
        corpo = resp.get_json()
        assert all(g["id"] != os_id for g in corpo["ordens"])

    def test_relatorios_ignoram_os_interna(
        self, client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
    ):
        os_id = self._os_interna_finalizada_com_peca(
            client, login_como, usuario_tecnico, aparelho_comprado, payload_interna, criar_item_estoque
        )

        ordens, _custos, _reparos = fluxoly_reports.buscar_dados_relatorios(_app.conectar)

        assert all(o[0] != os_id for o in ordens)
