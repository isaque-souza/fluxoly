"""
P1-1 (QA 2026-11-12) -- Infinity, NaN e números que estouram o float (1e400) não podem entrar.

`parse_float` aceitava qualquer coisa que `float()` aceita: os tokens JSON `Infinity`/`NaN`
(o `json` do Python os lê), as strings "Infinity"/"NaN"/"inf" e `1e400` (vira `inf`). O valor
era gravado no banco e na auditoria, e toda resposta que o incluía saía com `Infinity`, que
não é JSON válido -- Dashboard, Estoque, Vendas, Caixa, Contas e Auditoria quebravam no
navegador. `parse_int` recebendo `1e400` levantava OverflowError (500).

Cada caso: entrada inválida -> 4xx, nenhuma linha criada ou alterada, auditoria sem valor
não finito. Antes de cada caso inválido, o mesmo payload com valor válido passa (prova de que
a recusa vem do número, não de outro campo faltando).
"""

import json
import math
import uuid

import pytest

import app as _app
import fluxoly_validation as validation

RAW_1E400 = "__RAW_1E400__"

# nome do caso -> valor a enviar no JSON
NAO_FINITOS = {
    "token_Infinity": float("inf"),
    "token_-Infinity": float("-inf"),
    "token_NaN": float("nan"),
    "numero_1e400": RAW_1E400,
    "texto_Infinity": "Infinity",
    "texto_-Infinity": "-Infinity",
    "texto_NaN": "NaN",
    "texto_inf": "inf",
    "texto_1e400": "1e400",
}
INVALIDOS_TEXTO = {"texto_abc": "abc", "texto_virgula": "10,5"}
TODOS_INVALIDOS = {**NAO_FINITOS, **INVALIDOS_TEXTO}


def _corpo(payload):
    texto = json.dumps(payload)  # allow_nan=True: gera os tokens Infinity/NaN de propósito
    return texto.replace(f'"{RAW_1E400}"', "1e400")


def _enviar(client, metodo, url, payload):
    return client.open(url, method=metodo, data=_corpo(payload), content_type="application/json")


def _consulta(sql, params=()):
    conn = _app.conectar()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _executar(sql, params=()):
    conn = _app.conectar()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _contagem(tabela):
    return _consulta(f"SELECT COUNT(*) FROM {tabela}")[0][0]


def _linha(tabela, row_id):
    return _consulta(f"SELECT * FROM {tabela} WHERE id=?", (row_id,))


def _auditoria_total():
    return _contagem("audit_log")


def _auditoria_com_nao_finito():
    return _consulta(
        "SELECT id FROM audit_log WHERE COALESCE(valor_novo,'') || COALESCE(valor_anterior,'') "
        "LIKE '%Infinity%' OR COALESCE(valor_novo,'') || COALESCE(valor_anterior,'') LIKE '%NaN%'"
    )


@pytest.fixture
def admin(client, login_como, usuario_admin):
    assert login_como(client, usuario_admin).status_code == 200
    return client


def _assert_recusado_sem_efeito(client, metodo, url, payload, tabela, row_id=None):
    antes_total = _contagem(tabela)
    antes_linha = _linha(tabela, row_id) if row_id else None
    antes_audit = _auditoria_total()

    resp = _enviar(client, metodo, url, payload)

    assert 400 <= resp.status_code < 500, (url, payload, resp.status_code, resp.get_data(as_text=True))
    assert _contagem(tabela) == antes_total
    if row_id:
        assert _linha(tabela, row_id) == antes_linha
    assert _auditoria_total() == antes_audit
    assert not _auditoria_com_nao_finito()


# ---------------------------------------------------------------------------
# Unidade: fluxoly_validation
# ---------------------------------------------------------------------------


class TestParsers:
    @pytest.mark.parametrize(
        "valor", [float("inf"), float("-inf"), float("nan"), "Infinity", "-Infinity", "NaN", "nan", "inf", "1e400"]
    )
    def test_parse_float_recusa_nao_finito(self, valor):
        assert validation.parse_float(valor) is None
        assert validation.parse_float(valor, default=None) is None

    @pytest.mark.parametrize("valor", [float("inf"), float("-inf"), float("nan"), 1e400, "1e400", "Infinity"])
    def test_parse_int_recusa_nao_finito_sem_estourar(self, valor):
        assert validation.parse_int(valor) is None

    @pytest.mark.parametrize("valor,esperado", [("10.5", 10.5), (3, 3.0), ("-2", -2.0), (1e308, 1e308)])
    def test_parse_float_continua_aceitando_finitos(self, valor, esperado):
        assert validation.parse_float(valor) == esperado

    def test_ausente_continua_virando_default(self):
        assert validation.parse_float(None, default=0.0) == 0.0
        assert validation.parse_float("", default=None) is None
        assert validation.parse_int(None, default=7) == 7

    @pytest.mark.parametrize("valor", [float("inf"), float("nan"), "Infinity"])
    def test_validate_positive_number_recusa_nao_finito(self, valor):
        assert validation.validate_positive_number(valor) is False


# ---------------------------------------------------------------------------
# Endpoints de escrita com campo numérico
# ---------------------------------------------------------------------------


def _payload_estoque(**kw):
    return {"descricao": f"Peca P1-1 {uuid.uuid4().hex[:6]}", "modelo": "iPhone 13", "valor": 50, "quantidade": 2, **kw}


class TestEstoque:
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_valor(self, admin, caso):
        _assert_recusado_sem_efeito(
            admin, "POST", "/api/estoque", _payload_estoque(valor=TODOS_INVALIDOS[caso]), "estoque"
        )
        assert admin.post("/api/estoque", json=_payload_estoque()).status_code in (200, 201)

    @pytest.mark.parametrize("caso", ["numero_1e400", "token_Infinity", "token_NaN", "texto_1e400", "texto_abc"])
    def test_post_quantidade(self, admin, caso):
        payload = _payload_estoque(quantidade=TODOS_INVALIDOS[caso])
        _assert_recusado_sem_efeito(admin, "POST", "/api/estoque", payload, "estoque")

    @pytest.mark.parametrize("valor", [-10, 0, None])
    def test_post_valor_negativo_zero_ou_nulo(self, admin, valor):
        _assert_recusado_sem_efeito(admin, "POST", "/api/estoque", _payload_estoque(valor=valor), "estoque")

    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_put_valor(self, admin, caso):
        item_id = admin.post("/api/estoque", json=_payload_estoque()).get_json()["id"]
        payload = _payload_estoque(valor=TODOS_INVALIDOS[caso])
        _assert_recusado_sem_efeito(admin, "PUT", f"/api/estoque/{item_id}", payload, "estoque", item_id)

    @pytest.mark.parametrize("caso", ["numero_1e400", "token_Infinity", "token_NaN"])
    def test_put_quantidade(self, admin, caso):
        item_id = admin.post("/api/estoque", json=_payload_estoque()).get_json()["id"]
        payload = _payload_estoque(quantidade=TODOS_INVALIDOS[caso])
        _assert_recusado_sem_efeito(admin, "PUT", f"/api/estoque/{item_id}", payload, "estoque", item_id)


class TestCustosOperacionais:
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_e_put(self, admin, caso):
        base = {"descricao": "Aluguel P1-1", "valor": 100}
        _assert_recusado_sem_efeito(
            admin, "POST", "/api/custos", {**base, "valor": TODOS_INVALIDOS[caso]}, "custos_operacionais"
        )
        resp = admin.post("/api/custos", json=base)
        assert resp.status_code in (200, 201)
        custo_id = _consulta("SELECT MAX(id) FROM custos_operacionais")[0][0]
        _assert_recusado_sem_efeito(
            admin,
            "PUT",
            f"/api/custos/{custo_id}",
            {**base, "valor": TODOS_INVALIDOS[caso]},
            "custos_operacionais",
            custo_id,
        )

    @pytest.mark.parametrize("valor", [-5, 0, None])
    def test_negativo_zero_ou_nulo(self, admin, valor):
        _assert_recusado_sem_efeito(
            admin, "POST", "/api/custos", {"descricao": "X", "valor": valor}, "custos_operacionais"
        )


class TestTabelaDePrecos:
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_valor(self, admin, caso):
        servico = f"SERVICO P11 {uuid.uuid4().hex[:6]}".upper()
        payload = {"tabela": "clientes", "servico": servico, "modelo": "iPhone 13", "valor": TODOS_INVALIDOS[caso]}
        resp = _enviar(admin, "POST", "/api/precos", payload)
        assert 400 <= resp.status_code < 500
        precos = admin.get("/api/precos")
        assert precos.status_code == 200
        assert servico not in precos.get_data(as_text=True)


class TestOrdemDeServico:
    @pytest.mark.parametrize("campo", ["valor_cobrado", "valor_descontado"])
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post(self, admin, payload_os_valido, campo, caso):
        _assert_recusado_sem_efeito(
            admin, "POST", "/api/ordens", payload_os_valido(**{campo: TODOS_INVALIDOS[caso]}), "os"
        )

    def test_post_valido_controle(self, admin, payload_os_valido):
        assert admin.post("/api/ordens", json=payload_os_valido()).status_code in (200, 201)

    @pytest.mark.parametrize("campo", ["valor_cobrado", "valor_descontado"])
    @pytest.mark.parametrize("caso", ["token_Infinity", "token_NaN", "numero_1e400", "texto_Infinity", "texto_abc"])
    def test_put(self, admin, payload_os_valido, campo, caso):
        os_id = admin.post("/api/ordens", json=payload_os_valido()).get_json()["os_id"]
        payload = {**payload_os_valido(**{campo: TODOS_INVALIDOS[caso]}), "status": "Em andamento"}
        _assert_recusado_sem_efeito(admin, "PUT", f"/api/ordens/{os_id}", payload, "os", os_id)


class TestCaixa:
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post(self, admin, caso):
        base = {"tipo": "entrada", "descricao": "Suprimento P1-1"}
        _assert_recusado_sem_efeito(
            admin, "POST", "/api/caixa", {**base, "valor": TODOS_INVALIDOS[caso]}, "movimentacoes_caixa"
        )
        assert admin.post("/api/caixa", json={**base, "valor": 10}).status_code in (200, 201)

    @pytest.mark.parametrize("valor", [-1, 0, None])
    def test_negativo_zero_ou_nulo(self, admin, valor):
        payload = {"tipo": "entrada", "descricao": "X", "valor": valor}
        _assert_recusado_sem_efeito(admin, "POST", "/api/caixa", payload, "movimentacoes_caixa")

    def test_campo_ausente(self, admin):
        _assert_recusado_sem_efeito(admin, "POST", "/api/caixa", {"tipo": "entrada"}, "movimentacoes_caixa")


@pytest.mark.parametrize(
    "rota,tabela", [("/api/contas-pagar", "contas_pagar"), ("/api/contas-receber", "contas_receber")]
)
class TestContas:
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_e_put(self, admin, rota, tabela, caso):
        base = {"descricao": "Conta P1-1", "valor": 80, "data_vencimento": "2026-12-31"}
        _assert_recusado_sem_efeito(admin, "POST", rota, {**base, "valor": TODOS_INVALIDOS[caso]}, tabela)
        resp = admin.post(rota, json=base)
        assert resp.status_code == 201
        conta_id = resp.get_json()["id"]
        _assert_recusado_sem_efeito(
            admin, "PUT", f"{rota}/{conta_id}", {**base, "valor": TODOS_INVALIDOS[caso]}, tabela, conta_id
        )

    @pytest.mark.parametrize("valor", [-1, 0, None])
    def test_negativo_zero_ou_nulo(self, admin, rota, tabela, valor):
        payload = {"descricao": "X", "valor": valor, "data_vencimento": "2026-12-31"}
        _assert_recusado_sem_efeito(admin, "POST", rota, payload, tabela)


class TestProdutos:
    def _base(self):
        return {
            "categoria": "Acessorio",
            "marca": "Apple",
            "modelo": f"Capa {uuid.uuid4().hex[:6]}",
            "preco_venda": 100,
        }

    @pytest.mark.parametrize("campo", ["preco_venda", "preco_custo"])
    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_e_put(self, admin, campo, caso):
        _assert_recusado_sem_efeito(
            admin, "POST", "/api/produtos", {**self._base(), campo: TODOS_INVALIDOS[caso]}, "produtos"
        )
        base = self._base()
        resp = admin.post("/api/produtos", json=base)
        assert resp.status_code in (200, 201)
        produto_id = resp.get_json()["id"]
        _assert_recusado_sem_efeito(
            admin, "PUT", f"/api/produtos/{produto_id}", {**base, campo: TODOS_INVALIDOS[caso]}, "produtos", produto_id
        )

    @pytest.mark.parametrize("caso", ["numero_1e400", "token_Infinity", "token_NaN"])
    def test_quantidade(self, admin, caso):
        payload = {**self._base(), "quantidade": TODOS_INVALIDOS[caso]}
        _assert_recusado_sem_efeito(admin, "POST", "/api/produtos", payload, "produtos")

    @pytest.mark.parametrize(
        "campo,valor", [("preco_venda", -1), ("preco_venda", 0), ("preco_venda", None), ("preco_custo", -1)]
    )
    def test_negativo_zero_ou_nulo(self, admin, campo, valor):
        _assert_recusado_sem_efeito(admin, "POST", "/api/produtos", {**self._base(), campo: valor}, "produtos")


@pytest.fixture
def cliente_id():
    return _executar(
        "INSERT INTO clientes (nome, telefone) VALUES (?, '11988887777')", (f"Cliente P1-1 {uuid.uuid4().hex[:6]}",)
    )


@pytest.fixture
def produto_rastreavel_id():
    return _executar(
        "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('iPhone', 'Apple', ?, 'Seminovo', 3500.0, 0, 1)",
        (f"iPhone 13 P1-1 {uuid.uuid4().hex[:6]}",),
    )


def _imei():
    return f"35{uuid.uuid4().int % 10**13:013d}"


class TestComprasAparelhos:
    def _payload(self, produto_id, **kw):
        return {
            "produto_id": produto_id,
            "imei": _imei(),
            "origem": "marketplace",
            "valor_pago": 1200,
            "forma_pagamento": "pix",
            "estado": "bom",
            "defeito": "",
            "vendedor_nome": "Fulano",
            "vendedor_telefone": "11977776666",
            **kw,
        }

    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_valor_pago(self, admin, produto_rastreavel_id, caso):
        payload = self._payload(produto_rastreavel_id, valor_pago=TODOS_INVALIDOS[caso])
        antes_caixa = _contagem("movimentacoes_caixa")
        antes_unidades = _contagem("unidades_serializadas")
        _assert_recusado_sem_efeito(admin, "POST", "/api/compras-aparelhos", payload, "compras_aparelhos")
        assert _contagem("movimentacoes_caixa") == antes_caixa
        assert _contagem("unidades_serializadas") == antes_unidades

    def test_post_valido_controle(self, admin, produto_rastreavel_id):
        resp = admin.post("/api/compras-aparelhos", json=self._payload(produto_rastreavel_id))
        assert resp.status_code == 201, resp.get_data(as_text=True)

    @pytest.mark.parametrize("valor", [-100, 0, None])
    def test_negativo_zero_ou_nulo(self, admin, produto_rastreavel_id, valor):
        payload = self._payload(produto_rastreavel_id, valor_pago=valor)
        _assert_recusado_sem_efeito(admin, "POST", "/api/compras-aparelhos", payload, "compras_aparelhos")


@pytest.fixture
def unidade_disponivel_id():
    estoque_id = _executar(
        "INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade, requer_imei) "
        "VALUES ('iPhone 13 P1-1', 3000, 'F', 1, 'iPhone 13', ?, 'Aparelho', 'Novo', 1)",
        (f"SKU-{uuid.uuid4().hex[:8]}",),
    )
    return _executar(
        "INSERT INTO unidades_serializadas (estoque_id, imei, status) VALUES (?, ?, 'disponivel')",
        (estoque_id, _imei()),
    )


@pytest.fixture
def tipo_garantia_id(tipo_garantia_padrao_id):
    return tipo_garantia_padrao_id


class TestVendas:
    def _payload(self, cliente_id, unidade_id, tipo_garantia_id, **kw):
        return {
            "cliente_id": cliente_id,
            "unidade_serializada_id": unidade_id,
            "forma_pagamento": "pix",
            "valor_unitario": 3200,
            "tipo_garantia_id": tipo_garantia_id,
            **kw,
        }

    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_post_valor_unitario(self, admin, cliente_id, unidade_disponivel_id, tipo_garantia_id, caso):
        payload = self._payload(
            cliente_id, unidade_disponivel_id, tipo_garantia_id, valor_unitario=TODOS_INVALIDOS[caso]
        )
        antes_caixa = _contagem("movimentacoes_caixa")
        _assert_recusado_sem_efeito(admin, "POST", "/api/vendas", payload, "vendas")
        assert _contagem("movimentacoes_caixa") == antes_caixa
        assert _consulta("SELECT status FROM unidades_serializadas WHERE id=?", (unidade_disponivel_id,))[0][0] == (
            "disponivel"
        )

    @pytest.mark.parametrize("valor", [-1, 0, None])
    def test_negativo_zero_ou_nulo(self, admin, cliente_id, unidade_disponivel_id, tipo_garantia_id, valor):
        payload = self._payload(cliente_id, unidade_disponivel_id, tipo_garantia_id, valor_unitario=valor)
        _assert_recusado_sem_efeito(admin, "POST", "/api/vendas", payload, "vendas")

    def _venda(self, admin, cliente_id, unidade_id, tipo_garantia_id):
        resp = admin.post("/api/vendas", json=self._payload(cliente_id, unidade_id, tipo_garantia_id))
        assert resp.status_code == 201, resp.get_data(as_text=True)
        venda_id = resp.get_json()["id"]
        item_id = _consulta("SELECT id FROM vendas_itens WHERE venda_id=?", (venda_id,))[0][0]
        return venda_id, item_id

    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_patch_ajuste_desconto(self, admin, cliente_id, unidade_disponivel_id, tipo_garantia_id, caso):
        venda_id, item_id = self._venda(admin, cliente_id, unidade_disponivel_id, tipo_garantia_id)
        venda_antes = _linha("vendas", venda_id)
        _assert_recusado_sem_efeito(
            admin,
            "PATCH",
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            {"valor_unitario": TODOS_INVALIDOS[caso], "motivo": "teste"},
            "vendas_itens",
            item_id,
        )
        assert _linha("vendas", venda_id) == venda_antes

    @pytest.mark.parametrize("caso", TODOS_INVALIDOS)
    def test_patch_comissao(self, admin, cliente_id, unidade_disponivel_id, tipo_garantia_id, caso):
        venda_id, item_id = self._venda(admin, cliente_id, unidade_disponivel_id, tipo_garantia_id)
        _assert_recusado_sem_efeito(
            admin,
            "PATCH",
            f"/api/vendas/{venda_id}/itens/{item_id}/comissao",
            {"valor": TODOS_INVALIDOS[caso]},
            "vendas_itens",
            item_id,
        )


class TestCamposInteiros:
    @pytest.mark.parametrize("caso", ["numero_1e400", "token_Infinity", "token_-Infinity", "token_NaN", "texto_1e400"])
    def test_lista_de_compras_quantidade(self, admin, caso):
        payload = {"produto_nome": "Tela P1-1", "quantidade_solicitada": TODOS_INVALIDOS[caso]}
        _assert_recusado_sem_efeito(admin, "POST", "/api/shopping-list", payload, "shopping_list")

    @pytest.mark.parametrize("caso", ["numero_1e400", "token_Infinity", "token_NaN", "texto_1e400"])
    def test_tipo_garantia_duracao(self, admin, caso):
        payload = {"nome": f"Garantia P1-1 {uuid.uuid4().hex[:6]}", "duracao_meses": TODOS_INVALIDOS[caso]}
        _assert_recusado_sem_efeito(admin, "POST", "/api/tipos-garantia", payload, "tipos_garantia")

    @pytest.mark.parametrize("caso", ["numero_1e400", "token_Infinity", "token_NaN"])
    def test_query_string_e_corpo_nao_estouram(self, admin, caso):
        payload = {"sync_interval_seconds": TODOS_INVALIDOS[caso]}
        resp = _enviar(admin, "POST", "/api/integracoes/mercadophone/config", payload)
        assert 400 <= resp.status_code < 500


class TestChecklistPublico:
    @pytest.mark.parametrize("caso", ["token_Infinity", "token_NaN", "numero_1e400"])
    def test_testes_com_numero_nao_finito_sao_recusados(self, admin, criar_os, caso):
        os_id = criar_os()
        token = admin.post(f"/api/ordens/{os_id}/checklist/token").get_json()["checklist"]["access_token"]
        antes = _consulta("SELECT * FROM os_checklists WHERE os_id=?", (os_id,))

        publico = _app.app.test_client()
        payload = {"testes": {"touch": {"status": "ok", "nota": TODOS_INVALIDOS[caso]}}}
        resp = _enviar(publico, "POST", f"/api/checklist/{token}", payload)

        assert 400 <= resp.status_code < 500
        assert _consulta("SELECT * FROM os_checklists WHERE os_id=?", (os_id,)) == antes


# ---------------------------------------------------------------------------
# Saída: nenhuma resposta sai com Infinity/NaN, mesmo com dado antigo já gravado
# ---------------------------------------------------------------------------


GETS_PRINCIPAIS = [
    "/api/estoque",
    "/api/dashboard",
    "/api/ordens",
    "/api/vendas",
    "/api/caixa",
    "/api/contas-pagar",
    "/api/contas-receber",
    "/api/produtos",
    "/api/custos",
    "/api/compras-aparelhos",
    "/api/auditoria",
]


def _json_estrito(texto):
    def _recusar(token):
        raise ValueError(f"token não finito na resposta: {token}")

    return json.loads(texto, parse_constant=_recusar)


class TestRespostasComDadoAntigoNaoFinito:
    """Dado gravado antes da correção (o QA achou em Estoque, Vendas, Caixa, Contas, Produtos e
    Auditoria). A correção não altera o banco; a resposta sai como JSON válido."""

    @pytest.fixture
    def dados_legados(self):
        inf = float("inf")
        ids = {
            "estoque": _executar(
                "INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade) "
                "VALUES ('Legado P1-1', ?, 'F', 1, 'iPhone 13', ?, 'Tela', 'Padrao')",
                (inf, f"SKU-{uuid.uuid4().hex[:8]}"),
            ),
            "caixa": _executar(
                "INSERT INTO movimentacoes_caixa (tipo, valor, descricao, origem, criado_em) "
                "VALUES ('entrada', ?, 'Legado P1-1', 'manual', datetime('now'))",
                (inf,),
            ),
            "conta": _executar(
                "INSERT INTO contas_pagar (descricao, valor, data_vencimento, status) VALUES ('Legado', ?, '2026-12-31', 'aberta')",
                (inf,),
            ),
            "audit": _executar(
                "INSERT INTO audit_log (entidade, entidade_id, acao, valor_novo, criado_em) "
                "VALUES ('movimentacao_caixa', '0', 'create', ?, datetime('now'))",
                ('{"tipo": "entrada", "valor": Infinity}',),
            ),
        }
        yield ids
        _executar("DELETE FROM estoque WHERE id=?", (ids["estoque"],))
        _executar("DELETE FROM movimentacoes_caixa WHERE id=?", (ids["caixa"],))
        _executar("DELETE FROM contas_pagar WHERE id=?", (ids["conta"],))
        _executar("DELETE FROM audit_log WHERE id=?", (ids["audit"],))

    @pytest.mark.parametrize("url", GETS_PRINCIPAIS)
    def test_get_devolve_json_valido(self, admin, dados_legados, url):
        resp = admin.get(url)
        assert resp.status_code < 500, (url, resp.status_code)
        _json_estrito(resp.get_data(as_text=True))

    def test_banco_nao_e_alterado(self, admin, dados_legados):
        for url in GETS_PRINCIPAIS:
            admin.get(url)
        assert math.isinf(_consulta("SELECT valor FROM estoque WHERE id=?", (dados_legados["estoque"],))[0][0])
        assert "Infinity" in _consulta("SELECT valor_novo FROM audit_log WHERE id=?", (dados_legados["audit"],))[0][0]

    def test_auditoria_mostra_o_valor_original_como_texto(self, admin, dados_legados):
        corpo = _json_estrito(admin.get("/api/auditoria?per_page=100").get_data(as_text=True))
        registros = [r for r in corpo["items"] if r["id"] == dados_legados["audit"]]
        assert registros, corpo.keys()
        assert registros[0]["depois"]["valor"] == "Infinity"


class TestWebhookMercadoPhone:
    """A integração já ignora valor inválido (fica 0); não finito agora segue o mesmo caminho."""

    @pytest.mark.parametrize("caso", ["token_Infinity", "token_NaN", "numero_1e400", "texto_Infinity"])
    def test_valor_nao_finito_e_ignorado(self, client, monkeypatch, caso):
        import api_mercadophone

        monkeypatch.setattr(api_mercadophone, "MERCADO_PHONE_WEBHOOK_TOKEN", "token-p11")
        codigo = f"MP-P11-{uuid.uuid4().hex[:8]}"
        valor = TODOS_INVALIDOS[caso]
        payload = {
            "codigo": codigo,
            "cliente": "Cliente P1-1",
            "aparelho": "iPhone 13",
            "valorTotal": valor,
            "servicos": [{"valorCobranca": valor, "valorCusto": valor}],
        }
        resp = client.post(
            "/api/integracoes/mercadophone/os",
            data=_corpo(payload),
            content_type="application/json",
            headers={"X-Webhook-Token": "token-p11"},
        )

        assert resp.status_code < 500
        _json_estrito(resp.get_data(as_text=True))
        linhas = _consulta("SELECT valor_cobrado, custo_pecas FROM os WHERE id_externo_integracao=?", (codigo,))
        for valor_cobrado, custo_pecas in linhas:
            assert valor_cobrado is None or math.isfinite(valor_cobrado)
            assert custo_pecas is None or math.isfinite(custo_pecas)
        assert not _auditoria_com_nao_finito()
