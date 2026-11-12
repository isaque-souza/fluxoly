"""
Custo e lucro por aparelho comprado (BR-092) e relatório mensal de compra e
revenda (BR-093) -- docs/engineering/plans/PLAN-compra-aparelhos.md, PR 4.

O banco de teste é compartilhado pela sessão, então os totais do relatório são
conferidos por diferença (antes/depois), nunca por valor absoluto.
"""

import uuid
from datetime import UTC, datetime

import pytest

import app as _app


def _imei():
    return f"35{uuid.uuid4().int % 10**13:013d}"


def _executar(sql, params=()):
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


MES_ATUAL = datetime.now().strftime("%Y-%m")


@pytest.fixture
def cenario(client, login_como, usuario_admin, reparo_padrao_id, criar_item_estoque, tipo_garantia_padrao_id):
    """Compra de R$ 1.000 + OS interna finalizada com peça de R$ 300 → custo R$ 1.300."""
    produto_id = _executar(
        "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('iPhone', 'Apple', 'iPhone 13', 'Seminovo', 3500.0, 0, 1)"
    )
    cliente_id = _executar(
        "INSERT INTO clientes (nome, telefone) VALUES (?, '11911112222')", (f"Comprador {uuid.uuid4().hex[:6]}",)
    )
    login_como(client, usuario_admin)

    def _comprar_e_consertar(valor_pago=1000, valor_peca=300.0):
        resp = client.post(
            "/api/compras-aparelhos",
            json={
                "produto_id": produto_id,
                "imei": _imei(),
                "origem": "marketplace",
                "valor_pago": valor_pago,
                "forma_pagamento": "pix",
                "estado": "Usado",
                "defeito": "Tela quebrada",
            },
        )
        assert resp.status_code == 201, resp.get_json()
        unidade_id = client.get(f"/api/compras-aparelhos/{resp.get_json()['id']}").get_json()["compra"][
            "unidade_serializada_id"
        ]
        peca_id = criar_item_estoque(modelo="iPhone 13", valor=valor_peca)
        resp_os = client.post(
            "/api/ordens",
            json={
                "tipo": "Interna",
                "modelo": "iPhone 13",
                "tecnico": "ISAQUE SOUZA",
                "reparo_ids": [reparo_padrao_id],
                "unidade_serializada_id": unidade_id,
                "pecas_ids": [peca_id],
            },
        )
        assert resp_os.status_code == 201, resp_os.get_json()
        os_id = resp_os.get_json()["os_id"]
        assert client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"}).status_code == 200
        return unidade_id, os_id

    def _vender(unidade_id, valor=3500):
        resp = client.post(
            "/api/vendas",
            json={
                "cliente_id": cliente_id,
                "unidade_serializada_id": unidade_id,
                "forma_pagamento": "pix",
                "valor_unitario": valor,
                "tipo_garantia_id": tipo_garantia_padrao_id,
            },
        )
        assert resp.status_code == 201, resp.get_json()
        return resp.get_json()["id"]

    return _comprar_e_consertar, _vender


class TestCustoDoAparelho:
    def test_custo_soma_compra_e_pecas_da_os_interna(self, client, cenario):
        comprar_e_consertar, _vender = cenario
        unidade_id, _os_id = comprar_e_consertar()

        unidade = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]

        assert unidade["custo_aparelho"] == {"valor_compra": 1000.0, "custo_pecas": 300.0, "custo_total": 1300.0}

    def test_os_interna_cancelada_nao_entra_no_custo(self, client, cenario):
        comprar_e_consertar, _vender = cenario
        unidade_id, os_id = comprar_e_consertar()
        client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"})

        unidade = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]

        assert unidade["custo_aparelho"]["custo_pecas"] == 0.0
        assert unidade["custo_aparelho"]["custo_total"] == 1000.0

    def test_aparelho_que_nao_veio_de_compra_tem_custo_nulo(self, client, login_como, usuario_admin):
        produto_id = _executar(
            "INSERT INTO produtos (categoria, marca, modelo, preco_venda, quantidade, requer_rastreio_unidade) "
            "VALUES ('iPhone', 'Apple', 'iPhone 15', 6000.0, 0, 1)"
        )
        unidade_id = _executar(
            "INSERT INTO unidades_serializadas (produto_id, imei) VALUES (?, ?)", (produto_id, _imei())
        )
        login_como(client, usuario_admin)

        unidade = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]

        assert unidade["custo_aparelho"] is None

    def test_vendedor_e_tecnico_nao_veem_custo(self, client, login_como, usuario_vendedor, usuario_tecnico, cenario):
        comprar_e_consertar, _vender = cenario
        unidade_id, _os_id = comprar_e_consertar()

        for usuario in (usuario_vendedor, usuario_tecnico):
            login_como(client, usuario)
            unidade = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]
            assert "custo_aparelho" not in unidade


class TestLucroNaVenda:
    def test_admin_ve_custo_e_lucro_no_detalhe_da_venda(self, client, cenario):
        comprar_e_consertar, vender = cenario
        unidade_id, _os_id = comprar_e_consertar()
        venda_id = vender(unidade_id, valor=3500)

        item = client.get(f"/api/vendas/{venda_id}").get_json()["itens"][0]

        assert item["custo_aparelho"]["custo_total"] == 1300.0
        assert item["lucro"] == 2200.0

    def test_financeiro_ve_lucro(self, client, login_como, usuario_financeiro, cenario):
        comprar_e_consertar, vender = cenario
        unidade_id, _os_id = comprar_e_consertar()
        venda_id = vender(unidade_id)
        login_como(client, usuario_financeiro)

        item = client.get(f"/api/vendas/{venda_id}").get_json()["itens"][0]

        assert item["lucro"] == 2200.0

    def test_vendedor_nao_ve_custo_nem_lucro(self, client, login_como, usuario_vendedor, cenario):
        comprar_e_consertar, vender = cenario
        unidade_id, _os_id = comprar_e_consertar()
        venda_id = vender(unidade_id)
        login_como(client, usuario_vendedor)

        item = client.get(f"/api/vendas/{venda_id}").get_json()["itens"][0]

        assert "lucro" not in item and "custo_aparelho" not in item


class TestRelatorioMensal:
    def _relatorio(self, client, mes=MES_ATUAL):
        resp = client.get(f"/api/compras-aparelhos/relatorio?mes={mes}")
        assert resp.status_code == 200, resp.get_json()
        return resp.get_json()["relatorio"]

    def test_totais_do_mes_mudam_pelo_que_foi_comprado_consertado_e_vendido(self, client, cenario):
        comprar_e_consertar, vender = cenario
        antes = self._relatorio(client)

        vendido, _ = comprar_e_consertar(valor_pago=1000, valor_peca=300.0)
        comprar_e_consertar(valor_pago=800, valor_peca=200.0)  # fica parado
        venda_id = vender(vendido, valor=3500)
        depois = self._relatorio(client)

        assert depois["compras"]["quantidade"] - antes["compras"]["quantidade"] == 2
        assert round(depois["compras"]["total_pago"] - antes["compras"]["total_pago"], 2) == 1800.0
        assert round(depois["pecas_os_internas"] - antes["pecas_os_internas"], 2) == 500.0
        assert round(depois["total_investido"] - antes["total_investido"], 2) == 2300.0
        assert depois["vendas"]["quantidade"] - antes["vendas"]["quantidade"] == 1
        assert round(depois["vendas"]["lucro"] - antes["vendas"]["lucro"], 2) == 2200.0
        item = next(i for i in depois["vendas"]["itens"] if i["venda_id"] == venda_id)
        assert item["custo_total"] == 1300.0 and item["lucro"] == 2200.0
        assert depois["estoque_atual"]["quantidade"] - antes["estoque_atual"]["quantidade"] == 1
        assert round(depois["estoque_atual"]["capital_parado"] - antes["estoque_atual"]["capital_parado"], 2) == 1000.0

    def test_mes_sem_movimento_vem_zerado(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        relatorio = self._relatorio(client, mes="2001-01")

        assert relatorio["compras"] == {"quantidade": 0, "total_pago": 0.0}
        assert relatorio["vendas"]["quantidade"] == 0 and relatorio["vendas"]["itens"] == []

    @pytest.mark.parametrize("mes", ["", "2026-13", "2026/11", "26-11"])
    def test_mes_invalido(self, client, login_como, usuario_admin, mes):
        login_como(client, usuario_admin)

        resp = client.get(f"/api/compras-aparelhos/relatorio?mes={mes}")

        assert resp.status_code == 400

    def test_so_admin_e_financeiro(self, client, login_como, usuario_vendedor, usuario_financeiro):
        login_como(client, usuario_vendedor)
        assert client.get(f"/api/compras-aparelhos/relatorio?mes={MES_ATUAL}").status_code == 403

        login_como(client, usuario_financeiro)
        assert client.get(f"/api/compras-aparelhos/relatorio?mes={MES_ATUAL}").status_code == 200


class TestFiltroOrigemCompra:
    """Picker da OS interna (PR 5): técnico não lista compras (BR-088), então usa
    /api/unidades-serializadas?origem=compra, que só traz aparelhos de compra ativa."""

    def test_lista_so_unidades_de_compra_ativa(self, client, login_como, usuario_tecnico, cenario):
        comprar_e_consertar, _vender = cenario
        unidade_compra, _os_id = comprar_e_consertar()
        produto_id = _executar(
            "INSERT INTO produtos (categoria, marca, modelo, preco_venda, quantidade, requer_rastreio_unidade) "
            "VALUES ('iPhone', 'Apple', 'iPhone 14', 5000.0, 0, 1)"
        )
        unidade_avulsa = _executar(
            "INSERT INTO unidades_serializadas (produto_id, imei) VALUES (?, ?)", (produto_id, _imei())
        )
        login_como(client, usuario_tecnico)

        resp = client.get("/api/unidades-serializadas?origem=compra&per_page=100")

        assert resp.status_code == 200
        ids = {u["id"] for u in resp.get_json()["items"]}
        assert unidade_compra in ids
        assert unidade_avulsa not in ids


class TestAlertasDeDados:
    """Alertas de dados no relatório mensal (PLAN-alertas-dados.md)."""

    # `vendas.criado_em` é UTC (KI-061); o mês do relatório é comparado sem conversão.
    MES_UTC = datetime.now(UTC).strftime("%Y-%m")

    def _alertas(self, client):
        resp = client.get(f"/api/compras-aparelhos/relatorio?mes={self.MES_UTC}")
        assert resp.status_code == 200, resp.get_json()
        return resp.get_json()["relatorio"]["alertas"]

    def test_aparelho_comprado_vendido_abaixo_do_custo_gera_alerta(self, client, cenario):
        comprar_e_consertar, vender = cenario
        unidade_id, _ = comprar_e_consertar(valor_pago=1000, valor_peca=300.0)
        venda_id = vender(unidade_id, valor=1000)

        alerta = next(a for a in self._alertas(client)["vendas_abaixo_do_custo"] if a["venda_id"] == venda_id)

        assert alerta["base_custo"] == "compra"
        assert alerta["custo"] == 1300.0 and alerta["prejuizo"] == 300.0

    def test_venda_com_lucro_nao_gera_alerta(self, client, cenario):
        comprar_e_consertar, vender = cenario
        unidade_id, _ = comprar_e_consertar()
        venda_id = vender(unidade_id, valor=3500)

        assert all(a["venda_id"] != venda_id for a in self._alertas(client)["vendas_abaixo_do_custo"])

    def test_sem_compra_usa_preco_custo_do_cadastro(self, client, cenario):
        _comprar, vender = cenario
        produto_id = _executar(
            "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, preco_custo, quantidade, "
            "requer_rastreio_unidade) VALUES ('iPhone', 'Apple', 'iPhone 14', 'Novo', 4000.0, 2000.0, 0, 1)"
        )
        unidade_id = _executar(
            "INSERT INTO unidades_serializadas (produto_id, imei) VALUES (?, ?)", (produto_id, _imei())
        )
        venda_id = vender(unidade_id, valor=1500)

        alerta = next(a for a in self._alertas(client)["vendas_abaixo_do_custo"] if a["venda_id"] == venda_id)

        assert alerta["base_custo"] == "catalogo"
        assert alerta["custo"] == 2000.0 and alerta["prejuizo"] == 500.0

    def test_aparelho_sem_compra_e_sem_preco_custo_conta_como_sem_custo(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        antes = self._alertas(client)["aparelhos_sem_custo"]["total"]
        produto_id = _executar(
            "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, "
            "requer_rastreio_unidade) VALUES ('iPhone', 'Apple', 'iPhone 12', 'Seminovo', 2000.0, 0, 1)"
        )
        _executar("INSERT INTO unidades_serializadas (produto_id, imei) VALUES (?, ?)", (produto_id, _imei()))

        assert self._alertas(client)["aparelhos_sem_custo"]["total"] == antes + 1
