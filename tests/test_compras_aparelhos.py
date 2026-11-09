"""
Testes do domínio Compra de Aparelhos (BR-083 a BR-089,
docs/engineering/plans/PLAN-compra-aparelhos.md).

Exercita a API real (`/api/compras-aparelhos`) e confere no banco o que a
compra cria na mesma transação: a unidade serializada (BR-084) e a saída de
caixa (BR-086); e o caminho inverso no cancelamento (BR-087).
"""

import uuid

import pytest

import app as _app
import fluxoly_caixa_repository as caixa_repo
import fluxoly_compras_aparelhos_service as compras_service


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


def _consultar(sql, params=()):
    conn = _app.conectar()
    try:
        return conn.execute(sql, params).fetchone()
    finally:
        conn.close()


@pytest.fixture
def produto_id():
    pid = _executar(
        "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('iPhone', 'Apple', ?, 'Seminovo', 3500.0, 0, 1)",
        (f"iPhone 13 Compra {uuid.uuid4().hex[:6]}",),
    )
    yield pid


@pytest.fixture
def produto_sem_rastreio_id():
    return _executar(
        "INSERT INTO produtos (categoria, marca, modelo, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('Acessorio', 'Apple', 'Capinha', 100.0, 5, 0)"
    )


@pytest.fixture
def cliente_id():
    return _executar(
        "INSERT INTO clientes (nome, telefone) VALUES (?, '11988887777')",
        (f"Cliente Troca {uuid.uuid4().hex[:6]}",),
    )


def _payload(produto, **extra):
    dados = {
        "produto_id": produto,
        "imei": _imei(),
        "origem": "marketplace",
        "valor_pago": 1200.50,
        "forma_pagamento": "pix",
        "estado": "Tela trincada, carcaça boa",
        "defeito": "Tela quebrada",
        "vendedor_nome": "Fulano do Marketplace",
        "vendedor_telefone": "11977776666",
    }
    dados.update(extra)
    return dados


def _saida_ativa(compra_id):
    conn = _app.conectar()
    try:
        return caixa_repo.buscar_ativa_por_origem(conn.cursor(), "compra_aparelho", compra_id)
    finally:
        conn.close()


class TestPermissoes:
    def test_nao_autenticado_recebe_401(self, client, produto_id):
        assert client.get("/api/compras-aparelhos").status_code == 401
        assert client.post("/api/compras-aparelhos", json=_payload(produto_id)).status_code == 401

    @pytest.mark.parametrize("fixture_usuario", ["usuario_tecnico", "usuario_estoque"])
    def test_perfis_fora_da_regra_recebem_403(self, client, login_como, request, produto_id, fixture_usuario):
        login_como(client, request.getfixturevalue(fixture_usuario))
        assert client.get("/api/compras-aparelhos").status_code == 403
        assert client.post("/api/compras-aparelhos", json=_payload(produto_id)).status_code == 403

    @pytest.mark.parametrize("fixture_usuario", ["usuario_admin", "usuario_financeiro", "usuario_vendedor"])
    def test_admin_financeiro_e_vendedor_registram_compra(
        self, client, login_como, request, produto_id, fixture_usuario
    ):
        """BR-089."""
        login_como(client, request.getfixturevalue(fixture_usuario))
        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id))
        assert resp.status_code == 201, resp.get_json()


class TestRegistrarCompra:
    def test_compra_com_defeito_cria_unidade_em_reparo_e_saida_de_caixa(
        self, client, login_como, usuario_vendedor, produto_id
    ):
        login_como(client, usuario_vendedor)
        payload = _payload(produto_id)

        resp = client.post("/api/compras-aparelhos", json=payload)

        assert resp.status_code == 201
        compra_id = resp.get_json()["id"]
        compra = client.get(f"/api/compras-aparelhos/{compra_id}").get_json()["compra"]
        assert compra["status"] == "ativa"
        assert compra["imei"] == payload["imei"]
        assert compra["valor_pago"] == 1200.5
        assert compra["vendedor_nome"] == "Fulano do Marketplace"
        assert compra["unidade_status"] == "em_reparo"  # BR-084
        unidade = _consultar(
            "SELECT produto_id, estoque_id, status FROM unidades_serializadas WHERE id = ?",
            (compra["unidade_serializada_id"],),
        )
        assert unidade == (produto_id, None, "em_reparo")
        saida = _saida_ativa(compra_id)  # BR-086
        assert saida is not None
        assert saida[1] == "saida" and saida[2] == 1200.5

    def test_compra_sem_defeito_cria_unidade_disponivel(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, defeito=""))

        compra = client.get(f"/api/compras-aparelhos/{resp.get_json()['id']}").get_json()["compra"]
        assert compra["unidade_status"] == "disponivel"

    @pytest.mark.parametrize(
        ("campo", "valor", "mensagem"),
        [
            ("imei", "", "IMEI é obrigatório."),
            ("origem", "loja", "Origem inválida."),
            ("valor_pago", 0, "Valor pago deve ser maior que zero."),
            ("valor_pago", "abc", "Valor pago deve ser maior que zero."),
            ("forma_pagamento", "cheque", "Forma de pagamento inválida."),
            ("estado", "  ", "Informe o estado do aparelho."),
            ("produto_id", None, "Selecione o modelo do aparelho."),
        ],
    )
    def test_validacoes_br083(self, client, login_como, usuario_admin, produto_id, campo, valor, mensagem):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, **{campo: valor}))

        assert resp.status_code == 400
        assert resp.get_json()["erro"] == mensagem

    def test_imei_repetido_e_rejeitado_sem_deixar_rastro(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)
        imei = _imei()
        assert client.post("/api/compras-aparelhos", json=_payload(produto_id, imei=imei)).status_code == 201
        compras_antes = _consultar("SELECT COUNT(*) FROM compras_aparelhos")[0]

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, imei=imei))

        assert resp.status_code == 400
        assert resp.get_json()["erro"] == "IMEI já cadastrado."
        assert _consultar("SELECT COUNT(*) FROM compras_aparelhos")[0] == compras_antes

    def test_produto_sem_rastreio_por_unidade_e_rejeitado(
        self, client, login_como, usuario_admin, produto_sem_rastreio_id
    ):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_sem_rastreio_id))

        assert resp.status_code == 400
        assert "rastreamento por unidade" in resp.get_json()["erro"]

    def test_produto_inexistente_responde_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(99999999))

        assert resp.status_code == 404

    def test_falha_depois_da_unidade_desfaz_tudo(self, client, login_como, usuario_admin, produto_id, monkeypatch):
        """Atomicidade: se a saída de caixa falhar, nem compra nem unidade ficam no banco."""
        login_como(client, usuario_admin)
        imei = _imei()

        def _explodir(*_args, **_kwargs):
            raise compras_service._CompraConflitoError("falha simulada no caixa")

        monkeypatch.setattr(compras_service.caixa_service, "registrar_saida_de_compra_aparelho", _explodir)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, imei=imei))

        assert resp.status_code == 400
        assert _consultar("SELECT COUNT(*) FROM unidades_serializadas WHERE imei = ?", (imei,))[0] == 0


class TestTroca:
    def test_troca_exige_cliente(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, origem="troca"))

        assert resp.status_code == 400
        assert "cliente" in resp.get_json()["erro"]

    def test_abatido_na_venda_so_vale_para_troca(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, forma_pagamento="abatido_na_venda"))

        assert resp.status_code == 400

    def test_troca_abatida_na_venda_gera_saida_de_caixa_cheia(
        self, client, login_como, usuario_admin, produto_id, cliente_id
    ):
        """BR-086: mesmo 'abatido na venda' sai do caixa -- a venda entrou cheia."""
        login_como(client, usuario_admin)

        resp = client.post(
            "/api/compras-aparelhos",
            json=_payload(
                produto_id,
                origem="troca",
                cliente_id=cliente_id,
                forma_pagamento="abatido_na_venda",
                valor_pago=2000,
            ),
        )

        assert resp.status_code == 201, resp.get_json()
        compra = client.get(f"/api/compras-aparelhos/{resp.get_json()['id']}").get_json()["compra"]
        assert compra["cliente_id"] == cliente_id
        assert _saida_ativa(compra["id"])[2] == 2000

    def test_venda_inexistente_e_rejeitada(self, client, login_como, usuario_admin, produto_id, cliente_id):
        login_como(client, usuario_admin)

        resp = client.post(
            "/api/compras-aparelhos",
            json=_payload(produto_id, origem="troca", cliente_id=cliente_id, venda_id=99999999),
        )

        assert resp.status_code == 404

    def test_marketplace_nao_pode_ter_venda(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, venda_id=1))

        assert resp.status_code == 400


class TestCancelarCompra:
    def _registrar(self, client, produto_id, **extra):
        resp = client.post("/api/compras-aparelhos", json=_payload(produto_id, **extra))
        assert resp.status_code == 201, resp.get_json()
        return resp.get_json()["id"]

    def test_cancelar_estorna_caixa_e_devolve_unidade(self, client, login_como, usuario_financeiro, produto_id):
        login_como(client, usuario_financeiro)
        compra_id = self._registrar(client, produto_id)

        resp = client.post(f"/api/compras-aparelhos/{compra_id}/cancelar", json={"motivo": "Vendedor desistiu"})

        assert resp.status_code == 200
        compra = client.get(f"/api/compras-aparelhos/{compra_id}").get_json()["compra"]
        assert compra["status"] == "cancelada"
        assert compra["motivo_cancelamento"] == "Vendedor desistiu"
        assert compra["unidade_status"] == "devolvido"
        assert _saida_ativa(compra_id) is None
        estornada = _consultar(
            "SELECT estornada FROM movimentacoes_caixa WHERE origem = 'compra_aparelho' AND origem_id = ?",
            (compra_id,),
        )
        assert estornada == (1,)  # nunca apaga a linha

    def test_cancelar_exige_motivo(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)
        compra_id = self._registrar(client, produto_id)

        resp = client.post(f"/api/compras-aparelhos/{compra_id}/cancelar", json={})

        assert resp.status_code == 400

    def test_nao_cancela_duas_vezes(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)
        compra_id = self._registrar(client, produto_id)
        client.post(f"/api/compras-aparelhos/{compra_id}/cancelar", json={"motivo": "x"})

        resp = client.post(f"/api/compras-aparelhos/{compra_id}/cancelar", json={"motivo": "x"})

        assert resp.status_code == 400

    def test_nao_cancela_compra_de_aparelho_ja_vendido(self, client, login_como, usuario_admin, produto_id):
        login_como(client, usuario_admin)
        compra_id = self._registrar(client, produto_id, defeito="")
        compra = client.get(f"/api/compras-aparelhos/{compra_id}").get_json()["compra"]
        _executar(
            "UPDATE unidades_serializadas SET status = 'vendido' WHERE id = ?", (compra["unidade_serializada_id"],)
        )

        resp = client.post(f"/api/compras-aparelhos/{compra_id}/cancelar", json={"motivo": "x"})

        assert resp.status_code == 400
        assert "vendido" in resp.get_json()["erro"]
        assert client.get(f"/api/compras-aparelhos/{compra_id}").get_json()["compra"]["status"] == "ativa"
        assert _saida_ativa(compra_id) is not None

    def test_compra_inexistente_responde_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.post("/api/compras-aparelhos/99999999/cancelar", json={"motivo": "x"})

        assert resp.status_code == 404


class TestListar:
    def test_lista_filtra_por_origem_e_busca_por_imei(self, client, login_como, usuario_admin, produto_id, cliente_id):
        login_como(client, usuario_admin)
        imei = _imei()
        client.post("/api/compras-aparelhos", json=_payload(produto_id, imei=imei))
        client.post("/api/compras-aparelhos", json=_payload(produto_id, origem="troca", cliente_id=cliente_id))

        por_imei = client.get(f"/api/compras-aparelhos?q={imei}").get_json()
        so_troca = client.get("/api/compras-aparelhos?origem=troca&per_page=100").get_json()

        assert por_imei["total"] == 1 and por_imei["items"][0]["imei"] == imei
        assert so_troca["items"] and all(c["origem"] == "troca" for c in so_troca["items"])
