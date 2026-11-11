"""
Documento da OS para o cliente (BR-095 a BR-098,
docs/engineering/plans/PLAN-documentos-os-cliente.md):
GET /api/ordens/<id>/documento?tipo=entrada|entrega.

O ponto mais sensível é a allowlist (BR-097): custo, lucro, peças, fornecedor,
vendedor e dados de integração nunca saem por esta rota.
"""

import json
import uuid

import pytest

import app as _app

CAMPOS_PROIBIDOS = (
    "custo_pecas",
    "lucro",
    "pecas_usadas",
    "fornecedor",
    "vendedor",
    "origem_integracao",
    "id_externo_integracao",
    "faturamento",
)


def _salvar_loja(nome="Loja Documento Teste"):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute(
            """
            INSERT INTO dados_loja (id, nome_fantasia, cnpj, telefone, termos_entrada, termos_garantia)
            VALUES (1, ?, '12.345.678/0001-90', '(11) 4000-0000', 'Termos de entrada.', 'Termos de garantia.')
            """,
            (nome,),
        )
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _loja_cadastrada():
    _salvar_loja()
    yield
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def cliente_vinculado():
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, telefone, email, cpf_cnpj, observacoes) VALUES (?, ?, ?, ?, '')",
            (f"Cliente Cadastro {uuid.uuid4().hex[:6]}", "(11) 98888-7777", "cliente@teste.com", "123.456.789-00"),
        )
        conn.commit()
        cliente_id = cursor.lastrowid
    finally:
        conn.close()
    yield cliente_id
    conn = _app.conectar()
    try:
        conn.execute("UPDATE os SET cliente_id=NULL WHERE cliente_id=?", (cliente_id,))
        conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.commit()
    finally:
        conn.close()


def _atualizar_os(os_id, **campos):
    conn = _app.conectar()
    try:
        sets = ", ".join(f"{c}=?" for c in campos)
        conn.execute(f"UPDATE os SET {sets} WHERE id=?", (*campos.values(), os_id))
        conn.commit()
    finally:
        conn.close()


def _documento(client, os_id, tipo):
    return client.get(f"/api/ordens/{os_id}/documento?tipo={tipo}")


def _finalizar(client, os_id, reparo_id, tipo_garantia_id):
    resp = client.patch(
        f"/api/ordens/{os_id}/status",
        json={"status": "Finalizado", "garantias": {str(reparo_id): tipo_garantia_id}},
    )
    assert resp.status_code == 200, resp.get_json()


class TestEntrada:
    def test_caso_feliz(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(cliente="Maria Souza", tecnico="ISAQUE SOUZA", valor_cobrado=350.0)
        _atualizar_os(os_id, aparelho="iPhone 13 azul", cor="Azul", imei="356789012345678", observacoes="Tela trincada")

        resp = _documento(client, os_id, "entrada")
        assert resp.status_code == 200
        doc = resp.get_json()["documento"]
        assert doc["tipo"] == "entrada"
        assert doc["loja"]["nome_fantasia"] == "Loja Documento Teste"
        assert doc["termos"] == "Termos de entrada."
        assert doc["cliente"] == {"nome": "Maria Souza", "telefone": "", "email": "", "cpf_cnpj": ""}
        ordem = doc["ordem"]
        assert ordem["id"] == os_id
        assert ordem["tecnico"] == "ISAQUE SOUZA"
        assert ordem["imei"] == "356789012345678"
        assert ordem["observacoes"] == "Tela trincada"
        assert ordem["valor_total"] == 350.0
        assert ordem["servicos"] and "garantia" not in ordem["servicos"][0]
        assert ordem["data_finalizado"] == ""

    def test_valor_total_usa_a_mesma_regra_da_listagem(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(valor_cobrado=0.0, valor_descontado=280.0)
        assert _documento(client, os_id, "entrada").get_json()["documento"]["ordem"]["valor_total"] == 280.0

    def test_gerada_em_qualquer_status_aberto(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Aguardando peca")
        assert _documento(client, os_id, "entrada").status_code == 200


class TestEntrega:
    def test_so_para_os_finalizada(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento")
        resp = _documento(client, os_id, "entrega")
        assert resp.status_code == 409
        assert "finalizada" in resp.get_json()["erro"]

    def test_caso_feliz_com_garantia_do_snapshot(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id], valor_cobrado=500.0)
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        # BR-062: editar o tipo depois da conclusão não muda a garantia já concedida.
        conn = _app.conectar()
        try:
            conn.execute(
                "UPDATE tipos_garantia SET nome='Nome Alterado', duracao_meses=1 WHERE id=?",
                (tipo_garantia_padrao_id,),
            )
            conn.commit()
        finally:
            conn.close()

        resp = _documento(client, os_id, "entrega")
        assert resp.status_code == 200
        doc = resp.get_json()["documento"]
        assert doc["termos"] == "Termos de garantia."
        assert doc["ordem"]["valor_total"] == 500.0
        assert doc["ordem"]["data_finalizado"]
        garantia = doc["ordem"]["servicos"][0]["garantia"]
        assert garantia["nome"] == "Garantia Teste Padrão (Reparo)"
        assert garantia["duracao_meses"] == 12
        assert garantia["data_fim"]


class TestAllowlist:
    @pytest.mark.parametrize("tipo", ["entrada", "entrega"])
    def test_nunca_expoe_dados_internos(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id, tipo
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id], valor_cobrado=400.0)
        _atualizar_os(os_id, custo_pecas=123.45, origem_integracao="mercado_phone", id_externo_integracao="999")
        if tipo == "entrega":
            _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        resp = _documento(client, os_id, tipo)
        assert resp.status_code == 200
        corpo = resp.get_data(as_text=True)
        doc = resp.get_json()["documento"]
        for campo in CAMPOS_PROIBIDOS:
            assert campo not in json.dumps(doc), campo
        assert "123.45" not in corpo
        assert "Camila" not in corpo  # vendedor do fixture criar_os
        assert "mercado_phone" not in corpo


class TestCliente:
    def test_cliente_vinculado_traz_contato_e_cpf_para_admin(
        self, client, login_como, usuario_admin, criar_os, cliente_vinculado
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _atualizar_os(os_id, cliente_id=cliente_vinculado)
        cliente = _documento(client, os_id, "entrada").get_json()["documento"]["cliente"]
        assert cliente["telefone"] == "(11) 98888-7777"
        assert cliente["email"] == "cliente@teste.com"
        assert cliente["cpf_cnpj"] == "123.456.789-00"

    def test_cpf_omitido_para_quem_nao_pode_ler(self, client, login_como, usuario_tecnico, criar_os, cliente_vinculado):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        _atualizar_os(os_id, cliente_id=cliente_vinculado)
        resp = _documento(client, os_id, "entrada")
        cliente = resp.get_json()["documento"]["cliente"]
        assert cliente["telefone"] == "(11) 98888-7777"
        assert cliente["email"] == "cliente@teste.com"
        assert cliente["cpf_cnpj"] == ""
        assert "123.456.789-00" not in resp.get_data(as_text=True)


class TestRecusas:
    def test_sem_login_401(self, client, criar_os):
        os_id = criar_os()
        assert _documento(client, os_id, "entrada").status_code == 401

    def test_os_inexistente_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        assert _documento(client, 99999999, "entrada").status_code == 404

    @pytest.mark.parametrize("tipo", ["", "orcamento", "ENTRADA ; drop"])
    def test_tipo_invalido_400(self, client, login_como, usuario_tecnico, criar_os, tipo):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        assert _documento(client, os_id, tipo).status_code == 400

    def test_os_interna_409(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(tipo="Interna")
        assert _documento(client, os_id, "entrada").status_code == 409

    def test_os_cancelada_409(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Cancelado")
        assert _documento(client, os_id, "entrada").status_code == 409

    def test_sem_dados_da_loja_409(self, client, login_como, usuario_tecnico, criar_os):
        _salvar_loja(nome="")
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = _documento(client, os_id, "entrada")
        assert resp.status_code == 409
        assert "Dados da Loja" in resp.get_json()["erro"]
