"""
Testes do domínio Vendas MVP (docs/product/features/VENDAS.md,
docs/operations/SPRINTS/SPRINT_COMERCIAL_VENDAS_MVP.md).

Escopo: POST/GET /api/vendas. Venda de um único aparelho (unidade
serializada) por vez, sem desconto/comissão/garantia/troca/reserva com
timeout -- dependem de decisões de negócio ainda pendentes do Product Owner.

O teste mais importante desta suíte é a corrida real (threads, não só
chamada sequencial): duas vendas concorrentes da mesma unidade nunca podem
ambas ter sucesso -- garantido em duas camadas (UNIQUE em
vendas_itens.unidade_serializada_id + WHERE status='disponivel' no UPDATE
de marcar_como_vendida), a mesma classe de proteção que faltou no INC-002.
"""

import threading
import uuid

import pytest
from werkzeug.security import generate_password_hash

import app as _app
import fluxoly_vendas_repository as vendas_repo
import fluxoly_unidades_serializadas_service as unidades_service

SENHA_PADRAO = "senha_teste_123"


def _criar_cliente(**overrides):
    dados = {"nome": f"Cliente Teste {uuid.uuid4().hex[:8]}", "telefone": "11999998888"}
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO clientes (nome, telefone) VALUES (?, ?)",
            (dados["nome"], dados["telefone"]),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _limpar_cliente(cliente_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_item_estoque_rastreavel(**overrides):
    dados = {
        "descricao": "iPhone 13 Seminovo",
        "valor": 3000.0,
        "fornecedor": "Fornecedor Teste",
        "quantidade": 1,
        "modelo": "iPhone 13",
        "sku": f"SKU-{uuid.uuid4().hex[:8]}",
        "tipo": "Aparelho",
        "qualidade": "Novo",
    }
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade, requer_imei)
            VALUES (?,?,?,?,?,?,?,?,1)
            """,
            (
                dados["descricao"], dados["valor"], dados["fornecedor"], dados["quantidade"],
                dados["modelo"], dados["sku"], dados["tipo"], dados["qualidade"],
            ),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _criar_produto_rastreavel(**overrides):
    dados = {
        "categoria": "iPhone",
        "marca": "Apple",
        "modelo": "iPhone 14",
        "preco_venda": 4500.0,
        "quantidade": 1,
    }
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO produtos (categoria, marca, modelo, preco_venda, quantidade, requer_rastreio_unidade)
            VALUES (?,?,?,?,?,1)
            """,
            (dados["categoria"], dados["marca"], dados["modelo"], dados["preco_venda"], dados["quantidade"]),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _limpar_produto(produto_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_tipo_garantia(**overrides):
    dados = {"nome": f"Tipo Garantia Teste {uuid.uuid4().hex[:8]}", "duracao_meses": 12, "ativo": 1}
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_garantia (nome, duracao_meses, ativo) VALUES (?, ?, ?)",
            (dados["nome"], dados["duracao_meses"], dados["ativo"]),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _remover_tipo_garantia(tipo_garantia_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (tipo_garantia_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_unidade_disponivel(estoque_id=None, produto_id=None, imei=None):
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO unidades_serializadas (estoque_id, produto_id, imei, status) VALUES (?, ?, ?, 'disponivel')",
            (estoque_id, produto_id, imei),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _valor_tabela_do_item(unidade_id):
    conn = _app.conectar()
    try:
        row = conn.execute(
            "SELECT vi.valor_tabela, vi.valor_unitario, v.observacoes FROM vendas_itens vi "
            "JOIN vendas v ON v.id = vi.venda_id WHERE vi.unidade_serializada_id=?",
            (unidade_id,),
        ).fetchone()
        return row
    finally:
        conn.close()


def _status_unidade(unidade_id):
    conn = _app.conectar()
    try:
        return conn.execute("SELECT status FROM unidades_serializadas WHERE id=?", (unidade_id,)).fetchone()[0]
    finally:
        conn.close()


def _criar_usuario(nome, perfil):
    """Segundo usuário de um perfil, distinto dos fixtures `usuario_*` -- usado
    para provar isolamento entre vendedores (BR-031)."""
    login = f"user_{uuid.uuid4().hex[:10]}"
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, 1)",
            (nome, login, generate_password_hash(SENHA_PADRAO), perfil),
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
    return {"id": user_id, "nome": nome, "usuario": login, "senha": SENHA_PADRAO}


def _remover_usuario(user_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def _venda_status_e_cancelamento(venda_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT status, motivo_cancelamento, observacao_cancelamento, cancelado_por, cancelado_em "
            "FROM vendas WHERE id=?",
            (venda_id,),
        ).fetchone()
    finally:
        conn.close()


def _item_ativo(unidade_id, venda_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT ativo FROM vendas_itens WHERE unidade_serializada_id=? AND venda_id=?",
            (unidade_id, venda_id),
        ).fetchone()[0]
    finally:
        conn.close()


def _definir_limite_desconto(usuario_id, valor):
    """V1.3 -- Descontos (BR-037). `valor=None` deixa explicitamente 'não
    configurado' (default dos fixtures `usuario_*`)."""
    conn = _app.conectar()
    try:
        conn.execute("UPDATE usuarios SET limite_desconto_livre=? WHERE id=?", (valor, usuario_id))
        conn.commit()
    finally:
        conn.close()


def _item_desconto_info(unidade_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT id, motivo_desconto, desconto_aprovado_em FROM vendas_itens WHERE unidade_serializada_id=?",
            (unidade_id,),
        ).fetchone()
    finally:
        conn.close()


def _limpar_tudo(cliente_id=None, estoque_id=None, unidade_id=None, produto_id=None):
    conn = _app.conectar()
    try:
        if unidade_id:
            venda_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT DISTINCT venda_id FROM vendas_itens WHERE unidade_serializada_id=?", (unidade_id,)
                ).fetchall()
            ]
            item_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT id FROM vendas_itens WHERE unidade_serializada_id=?", (unidade_id,)
                ).fetchall()
            ]
            for venda_id in venda_ids:
                conn.execute("DELETE FROM audit_log WHERE entidade='venda' AND entidade_id=?", (venda_id,))
            for item_id in item_ids:
                conn.execute("DELETE FROM audit_log WHERE entidade='venda_item' AND entidade_id=?", (item_id,))
            conn.execute("DELETE FROM vendas_itens WHERE unidade_serializada_id=?", (unidade_id,))
            if venda_ids:
                conn.execute(
                    f"DELETE FROM vendas WHERE id IN ({','.join('?' * len(venda_ids))})", venda_ids
                )
            conn.execute("DELETE FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id=?", (unidade_id,))
            conn.execute("DELETE FROM unidades_serializadas WHERE id=?", (unidade_id,))
        if estoque_id:
            conn.execute("DELETE FROM estoque WHERE id=?", (estoque_id,))
        if produto_id:
            conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        if cliente_id:
            conn.execute("DELETE FROM clientes WHERE id=?", (cliente_id,))
        conn.commit()
    finally:
        conn.close()


_TIPO_GARANTIA_PADRAO_ID = None


@pytest.fixture(scope="module", autouse=True)
def _tipo_garantia_padrao():
    """V1.5 -- Garantia de Venda (BR-056): toda venda passa a exigir
    `tipo_garantia_id`. Um único Tipo de Garantia compartilhado por toda a
    suíte deste módulo -- não é o objeto sob teste (isso é
    tests/test_tipos_garantia.py, quando existir), só um dado de apoio
    necessário para criar qualquer venda via `_payload`/`_criar_venda_via_api`."""
    global _TIPO_GARANTIA_PADRAO_ID
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_garantia (nome, duracao_meses) VALUES (?, ?)",
            ("Garantia Teste Padrão", 12),
        )
        conn.commit()
        _TIPO_GARANTIA_PADRAO_ID = cursor.lastrowid
    finally:
        conn.close()
    yield
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (_TIPO_GARANTIA_PADRAO_ID,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def cenario_venda():
    """Cliente + item de estoque rastreável + unidade disponível, prontos
    para uma venda. Limpa tudo ao final, inclusive a venda/item se criados."""
    cliente_id = _criar_cliente()
    estoque_id = _criar_item_estoque_rastreavel()
    unidade_id = _criar_unidade_disponivel(estoque_id)
    yield {"cliente_id": cliente_id, "estoque_id": estoque_id, "unidade_id": unidade_id}
    _limpar_tudo(cliente_id, estoque_id, unidade_id)


def _payload(cenario, **overrides):
    base = {
        "cliente_id": cenario["cliente_id"],
        "unidade_serializada_id": cenario["unidade_id"],
        "forma_pagamento": "pix",
        "valor_unitario": 3200.0,
        "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
    }
    base.update(overrides)
    return base


class TestCriarVenda:
    def test_sem_autenticacao_retorna_401(self, client, cenario_venda):
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 401

    def test_tecnico_nao_pode_vender(self, client, login_como, usuario_tecnico, cenario_venda):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 403

    def test_vendedor_pode_vender(self, client, login_como, usuario_vendedor, cenario_venda):
        login_como(client, usuario_vendedor)
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 201

    def test_criacao_valida_persiste_venda_item_e_marca_unidade_vendida(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        login_como(client, usuario_admin)

        resp = client.post("/api/vendas", json=_payload(cenario_venda))

        assert resp.status_code == 201
        venda_id = resp.get_json()["id"]

        conn = _app.conectar()
        try:
            venda = conn.execute(
                "SELECT cliente_id, vendedor_id, forma_pagamento, valor_total, status FROM vendas WHERE id=?",
                (venda_id,),
            ).fetchone()
            item = conn.execute(
                "SELECT unidade_serializada_id, produto_nome, produto_sku, quantidade, valor_tabela, "
                "valor_unitario, subtotal FROM vendas_itens WHERE venda_id=?",
                (venda_id,),
            ).fetchone()
        finally:
            conn.close()

        assert venda[0] == cenario_venda["cliente_id"]
        assert venda[2] == "pix"
        assert venda[3] == 3200.0
        assert venda[4] == "concluida"

        assert item[0] == cenario_venda["unidade_id"]
        assert item[1] == "iPhone 13"  # snapshot: origem_label vem do modelo do estoque
        assert item[2]  # snapshot de SKU presente
        assert item[3] == 1
        # valor_tabela (preço de catálogo, estoque.valor=3000) != valor_unitario (preço
        # efetivo da venda, 3200 no payload) -- prova de que o vendedor pode negociar sem
        # um sobrescrever o outro.
        assert item[4] == 3000.0
        assert item[5] == 3200.0
        assert item[6] == 3200.0

        assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"

    def test_valor_tabela_via_origem_produto(self, client, login_como, usuario_admin):
        """valor_tabela também é derivado corretamente quando a unidade tem
        origem em produtos (preco_venda), não só em estoque (valor)."""
        cliente_id = _criar_cliente()
        produto_id = _criar_produto_rastreavel(preco_venda=4500.0)
        unidade_id = _criar_unidade_disponivel(produto_id=produto_id)
        login_como(client, usuario_admin)
        try:
            resp = client.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente_id,
                    "unidade_serializada_id": unidade_id,
                    "forma_pagamento": "pix",
                    "valor_unitario": 4500.0,
                    "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
                },
            )
            assert resp.status_code == 201
            valor_tabela, valor_unitario, _ = _valor_tabela_do_item(unidade_id)
            assert valor_tabela == 4500.0
            assert valor_unitario == 4500.0
        finally:
            _limpar_tudo(cliente_id, unidade_id=unidade_id, produto_id=produto_id)

    def test_valor_tabela_nulo_quando_item_sem_preco_cadastrado(
        self, client, login_como, usuario_admin
    ):
        """Item de estoque genuinamente sem valor cadastrado (NULL, nunca
        preenchido) -- valor_tabela fica NULL, a venda continua funcionando
        normalmente (não é bloqueante)."""
        cliente_id = _criar_cliente()
        estoque_id = _criar_item_estoque_rastreavel(valor=None)
        unidade_id = _criar_unidade_disponivel(estoque_id=estoque_id)
        login_como(client, usuario_admin)
        try:
            resp = client.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente_id,
                    "unidade_serializada_id": unidade_id,
                    "forma_pagamento": "pix",
                    "valor_unitario": 3200.0,
                    "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
                },
            )
            assert resp.status_code == 201
            valor_tabela, valor_unitario, _ = _valor_tabela_do_item(unidade_id)
            assert valor_tabela is None
            assert valor_unitario == 3200.0
        finally:
            _limpar_tudo(cliente_id, estoque_id=estoque_id, unidade_id=unidade_id)

    def test_valor_tabela_zero_e_preservado_nao_tratado_como_ausente(
        self, client, login_como, usuario_admin
    ):
        """Prova direta do ajuste pedido: valor=0 é um preço real (ainda que
        incomum), não deve cair no fallback como se estivesse ausente --
        `is not None`, nunca `or`."""
        cliente_id = _criar_cliente()
        estoque_id = _criar_item_estoque_rastreavel(valor=0)
        unidade_id = _criar_unidade_disponivel(estoque_id=estoque_id)
        login_como(client, usuario_admin)
        try:
            resp = client.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente_id,
                    "unidade_serializada_id": unidade_id,
                    "forma_pagamento": "pix",
                    "valor_unitario": 100.0,
                    "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
                },
            )
            assert resp.status_code == 201
            valor_tabela, _, _ = _valor_tabela_do_item(unidade_id)
            assert valor_tabela == 0
        finally:
            _limpar_tudo(cliente_id, estoque_id=estoque_id, unidade_id=unidade_id)

    def test_observacoes_persistidas(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, observacoes="Retirada amanhã"))
        assert resp.status_code == 201
        _, _, observacoes = _valor_tabela_do_item(cenario_venda["unidade_id"])
        assert observacoes == "Retirada amanhã"

    def test_observacoes_omitidas_persiste_string_vazia(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda))
        assert resp.status_code == 201
        _, _, observacoes = _valor_tabela_do_item(cenario_venda["unidade_id"])
        assert observacoes == ""

    def test_cliente_inexistente_retorna_404(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, cliente_id=999999))
        assert resp.status_code == 404

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, unidade_serializada_id=999999))
        assert resp.status_code == 404

    def test_unidade_ja_vendida_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        primeira = client.post("/api/vendas", json=_payload(cenario_venda))
        assert primeira.status_code == 201

        segunda = client.post("/api/vendas", json=_payload(cenario_venda))
        assert segunda.status_code == 400

    def test_forma_pagamento_invalida_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, forma_pagamento="boleto"))
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_valor_zero_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=0))
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_sem_tipo_garantia_id_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        """BR-056 -- toda venda exige um Tipo de Garantia atribuído ao item;
        sem default vindo do produto do catálogo."""
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, tipo_garantia_id=None))
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_tipo_garantia_id_inexistente_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, tipo_garantia_id=999999))
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_tipo_garantia_inativo_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        tipo_garantia_id = _criar_tipo_garantia(ativo=0)
        try:
            login_como(client, usuario_admin)
            resp = client.post("/api/vendas", json=_payload(cenario_venda, tipo_garantia_id=tipo_garantia_id))
            assert resp.status_code == 400
            assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"
        finally:
            _remover_tipo_garantia(tipo_garantia_id)

    def test_garantia_de_venda_snapshot_correto_na_criacao(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """BR-057 -- snapshot completo (id/nome/duração/datas) congelado no
        item no momento da criação, calculado a partir da duração do Tipo de
        Garantia usado (12 meses, `_tipo_garantia_padrao`)."""
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}")
        item = resp.get_json()["itens"][0]
        assert item["tipo_garantia_id"] == _TIPO_GARANTIA_PADRAO_ID
        assert item["garantia_nome"] == "Garantia Teste Padrão"
        assert item["garantia_duracao_meses"] == 12
        assert item["garantia_data_inicio"] is not None
        assert item["garantia_data_fim"] is not None
        assert item["garantia_data_fim"] > item["garantia_data_inicio"]

    def test_erro_na_criacao_do_item_causa_rollback_unidade_continua_disponivel(
        self, client, login_como, usuario_admin, cenario_venda, monkeypatch
    ):
        """Prova de atomicidade: uma exceção real dentro da transação (após a
        venda já ter sido inserida, antes da unidade ser marcada) reverte
        tudo -- nenhuma venda órfã, unidade continua disponível."""

        def _falha(*args, **kwargs):
            raise RuntimeError("falha simulada na criação do item")

        monkeypatch.setattr(vendas_repo, "inserir_item", _falha)
        login_como(client, usuario_admin)

        resp = client.post("/api/vendas", json=_payload(cenario_venda))

        assert resp.status_code in (400, 500)
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

        conn = _app.conectar()
        try:
            vendas_do_cliente = conn.execute(
                "SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cenario_venda["cliente_id"],)
            ).fetchone()[0]
            vendas_da_unidade = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert vendas_do_cliente == 0
        assert vendas_da_unidade == 0

    def test_erro_em_marcar_como_vendida_causa_rollback_sem_venda_orfa(
        self, client, login_como, usuario_admin, cenario_venda, monkeypatch
    ):
        """Segunda variação da prova de atomicidade: a exceção ocorre no passo
        seguinte da transação (INSERT venda e INSERT item já rodaram, sem
        commit, quando a marcação da unidade falha) -- mesmo resultado, nada
        persiste."""

        def _falha(*args, **kwargs):
            raise RuntimeError("falha simulada em marcar_como_vendida")

        monkeypatch.setattr(unidades_service, "marcar_como_vendida", _falha)
        login_como(client, usuario_admin)

        resp = client.post("/api/vendas", json=_payload(cenario_venda))

        assert resp.status_code in (400, 500)
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

        conn = _app.conectar()
        try:
            vendas_do_cliente = conn.execute(
                "SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cenario_venda["cliente_id"],)
            ).fetchone()[0]
            vendas_da_unidade = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert vendas_do_cliente == 0
        assert vendas_da_unidade == 0

    def test_patch_status_generico_continua_rejeitando_vendido(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """Prova de que a rota genérica de transição não abriu uma porta
        lateral para 'vendido' -- só fluxoly_vendas_service.py pode chegar lá."""
        login_como(client, usuario_admin)
        resp = client.patch(
            f"/api/unidades-serializadas/{cenario_venda['unidade_id']}/status",
            json={"status": "vendido"},
        )
        assert resp.status_code == 400
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_duas_vendas_concorrentes_mesma_unidade_so_uma_sucede(
        self, app, login_como, usuario_vendedor, cenario_venda
    ):
        client_a = app.test_client()
        client_b = app.test_client()
        login_como(client_a, usuario_vendedor)
        login_como(client_b, usuario_vendedor)

        payload = _payload(cenario_venda)
        resultados = {}

        def _post(nome, client):
            resultados[nome] = client.post("/api/vendas", json=payload)

        t_a = threading.Thread(target=_post, args=("a", client_a))
        t_b = threading.Thread(target=_post, args=("b", client_b))
        t_a.start()
        t_b.start()
        t_a.join()
        t_b.join()

        codigos = sorted(r.status_code for r in resultados.values())
        assert codigos == [201, 400]
        assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"

        conn = _app.conectar()
        try:
            total_itens = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert total_itens == 1


class TestObterVenda:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/vendas/1")
        assert resp.status_code == 401

    def test_venda_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.get("/api/vendas/999999")
        assert resp.status_code == 404

    def test_obter_venda_existente(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post(
            "/api/vendas", json=_payload(cenario_venda, observacoes="Retirada amanhã")
        ).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}")

        assert resp.status_code == 200
        corpo = resp.get_json()
        venda = corpo["venda"]
        assert venda["id"] == venda_id
        assert venda["status"] == "concluida"
        assert venda["forma_pagamento"] == "pix"
        assert venda["observacoes"] == "Retirada amanhã"

        # itens vem como lista separada, não achatado dentro de venda -- já
        # pensado para múltiplos itens por venda, mesmo com 1 item hoje.
        itens = corpo["itens"]
        assert isinstance(itens, list)
        assert len(itens) == 1
        assert itens[0]["unidade_serializada_id"] == cenario_venda["unidade_id"]
        assert itens[0]["valor_tabela"] == 3000.0
        assert itens[0]["valor_unitario"] == 3200.0

    def test_detalhe_inclui_nomes_de_cliente_vendedor_imei_e_desconto(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """Sprint Vendas 1.1: o detalhe passa a expor os campos de exibição
        (join) além dos já existentes -- cliente_nome/vendedor_nome na venda,
        imei/desconto em cada item."""
        login_como(client, usuario_admin)
        cliente_nome = client.get(f"/api/clientes/{cenario_venda['cliente_id']}").get_json()["cliente"]["nome"]
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}")

        assert resp.status_code == 200
        corpo = resp.get_json()
        venda = corpo["venda"]
        assert venda["cliente_nome"] == cliente_nome
        assert venda["vendedor_nome"] == usuario_admin["nome"]

        item = corpo["itens"][0]
        assert len(item["imei"]) == 15
        assert item["desconto"] == round(3000.0 - 3200.0, 2)


def _criar_venda_via_api(client, login_como, usuario, **overrides):
    """Cria cliente + item de estoque rastreável + unidade disponível e
    vende via API, autenticado como `usuario`. Devolve um dict com os ids e
    a resposta da criação, para os testes de listagem/detalhe montarem
    cenários com várias vendas."""
    cliente_id = _criar_cliente(nome=overrides.pop("cliente_nome", None) or f"Cliente Teste {uuid.uuid4().hex[:8]}")
    estoque_id = _criar_item_estoque_rastreavel()
    unidade_id = _criar_unidade_disponivel(estoque_id)
    login_como(client, usuario)
    resp = client.post(
        "/api/vendas",
        json={
            "cliente_id": cliente_id,
            "unidade_serializada_id": unidade_id,
            "forma_pagamento": overrides.pop("forma_pagamento", "pix"),
            "valor_unitario": overrides.pop("valor_unitario", 3200.0),
            "tipo_garantia_id": overrides.pop("tipo_garantia_id", _TIPO_GARANTIA_PADRAO_ID),
            **overrides,
        },
    )
    return {
        "cliente_id": cliente_id,
        "estoque_id": estoque_id,
        "unidade_id": unidade_id,
        "venda_id": resp.get_json()["id"] if resp.status_code == 201 else None,
        "resp": resp,
    }


class TestListarVendas:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/vendas")
        assert resp.status_code == 401

    def test_tecnico_pode_listar_historico(
        self, client, login_como, usuario_admin, usuario_tecnico, cenario_venda
    ):
        """A restrição admin/vendedor vale só para criar venda -- o histórico
        (só consulta) é liberado para qualquer perfil autenticado."""
        login_como(client, usuario_admin)
        client.post("/api/vendas", json=_payload(cenario_venda))

        login_como(client, usuario_tecnico)
        resp = client.get("/api/vendas", query_string={"cliente_id": cenario_venda["cliente_id"]})

        assert resp.status_code == 200
        assert resp.get_json()["total"] == 1

    def test_filtro_por_cliente_id_isola_a_venda_certa(self, client, login_como, usuario_admin):
        a = _criar_venda_via_api(client, login_como, usuario_admin)
        b = _criar_venda_via_api(client, login_como, usuario_admin)
        try:
            resp = client.get("/api/vendas", query_string={"cliente_id": a["cliente_id"]})
            corpo = resp.get_json()
            assert corpo["total"] == 1
            assert corpo["items"][0]["id"] == a["venda_id"]
            assert corpo["items"][0]["id"] != b["venda_id"]
        finally:
            _limpar_tudo(a["cliente_id"], a["estoque_id"], a["unidade_id"])
            _limpar_tudo(b["cliente_id"], b["estoque_id"], b["unidade_id"])

    def test_filtro_por_forma_pagamento(self, client, login_como, usuario_admin):
        pix = _criar_venda_via_api(client, login_como, usuario_admin, forma_pagamento="pix")
        dinheiro = _criar_venda_via_api(client, login_como, usuario_admin, forma_pagamento="dinheiro")
        try:
            resp = client.get(
                "/api/vendas",
                query_string={"forma_pagamento": "dinheiro", "cliente_id": dinheiro["cliente_id"]},
            )
            corpo = resp.get_json()
            assert corpo["total"] == 1
            assert corpo["items"][0]["id"] == dinheiro["venda_id"]
            assert corpo["items"][0]["id"] != pix["venda_id"]
        finally:
            _limpar_tudo(pix["cliente_id"], pix["estoque_id"], pix["unidade_id"])
            _limpar_tudo(dinheiro["cliente_id"], dinheiro["estoque_id"], dinheiro["unidade_id"])

    def test_busca_por_termo_nome_do_cliente(self, client, login_como, usuario_admin):
        nome_unico = f"Zeferino {uuid.uuid4().hex[:8]}"
        alvo = _criar_venda_via_api(client, login_como, usuario_admin, cliente_nome=nome_unico)
        outro = _criar_venda_via_api(client, login_como, usuario_admin)
        try:
            resp = client.get("/api/vendas", query_string={"q": "Zeferino"})
            corpo = resp.get_json()
            ids = [v["id"] for v in corpo["items"]]
            assert alvo["venda_id"] in ids
            assert outro["venda_id"] not in ids
        finally:
            _limpar_tudo(alvo["cliente_id"], alvo["estoque_id"], alvo["unidade_id"])
            _limpar_tudo(outro["cliente_id"], outro["estoque_id"], outro["unidade_id"])

    def test_busca_por_termo_imei(self, client, login_como, usuario_admin):
        cliente_id = _criar_cliente()
        estoque_id = _criar_item_estoque_rastreavel()
        imei_unico = "9" * 15
        unidade_id = _criar_unidade_disponivel(estoque_id, imei=imei_unico)
        login_como(client, usuario_admin)
        venda_id = client.post(
            "/api/vendas",
            json={
                "cliente_id": cliente_id,
                "unidade_serializada_id": unidade_id,
                "forma_pagamento": "pix",
                "valor_unitario": 3200.0,
                "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
            },
        ).get_json()["id"]
        try:
            resp = client.get("/api/vendas", query_string={"q": imei_unico})
            corpo = resp.get_json()
            assert corpo["total"] == 1
            assert corpo["items"][0]["id"] == venda_id
        finally:
            _limpar_tudo(cliente_id, estoque_id, unidade_id)

    def test_paginacao_e_total(self, client, login_como, usuario_admin):
        cliente_id = _criar_cliente()
        criados = []
        try:
            for _ in range(3):
                estoque_id = _criar_item_estoque_rastreavel()
                unidade_id = _criar_unidade_disponivel(estoque_id)
                login_como(client, usuario_admin)
                venda_id = client.post(
                    "/api/vendas",
                    json={
                        "cliente_id": cliente_id,
                        "unidade_serializada_id": unidade_id,
                        "forma_pagamento": "pix",
                        "valor_unitario": 3200.0,
                        "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
                    },
                ).get_json()["id"]
                criados.append((estoque_id, unidade_id, venda_id))

            pagina_1 = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "page": 1, "per_page": 2}
            ).get_json()
            pagina_2 = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "page": 2, "per_page": 2}
            ).get_json()

            assert pagina_1["total"] == 3
            assert len(pagina_1["items"]) == 2
            assert pagina_1["page"] == 1
            assert pagina_1["per_page"] == 2
            assert len(pagina_2["items"]) == 1
            ids_das_duas_paginas = {v["id"] for v in pagina_1["items"]} | {v["id"] for v in pagina_2["items"]}
            assert ids_das_duas_paginas == {venda_id for _, _, venda_id in criados}
        finally:
            for estoque_id, unidade_id, _ in criados:
                _limpar_tudo(unidade_id=unidade_id, estoque_id=estoque_id)
            _limpar_tudo(cliente_id=cliente_id)

    def test_ordenacao_recente_e_antigo(self, client, login_como, usuario_admin):
        cliente_id = _criar_cliente()
        criados = []
        try:
            for _ in range(3):
                estoque_id = _criar_item_estoque_rastreavel()
                unidade_id = _criar_unidade_disponivel(estoque_id)
                login_como(client, usuario_admin)
                venda_id = client.post(
                    "/api/vendas",
                    json={
                        "cliente_id": cliente_id,
                        "unidade_serializada_id": unidade_id,
                        "forma_pagamento": "pix",
                        "valor_unitario": 3200.0,
                        "tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID,
                    },
                ).get_json()["id"]
                criados.append((estoque_id, unidade_id, venda_id))
            ids_em_ordem_de_criacao = [venda_id for _, _, venda_id in criados]

            recente = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "sort": "recente", "per_page": 10}
            ).get_json()
            antigo = client.get(
                "/api/vendas", query_string={"cliente_id": cliente_id, "sort": "antigo", "per_page": 10}
            ).get_json()

            assert [v["id"] for v in recente["items"]] == list(reversed(ids_em_ordem_de_criacao))
            assert [v["id"] for v in antigo["items"]] == ids_em_ordem_de_criacao
        finally:
            for estoque_id, unidade_id, _ in criados:
                _limpar_tudo(unidade_id=unidade_id, estoque_id=estoque_id)
            _limpar_tudo(cliente_id=cliente_id)

    def test_itens_resumo_inclui_desconto_calculado(self, client, login_como, usuario_admin):
        # V1.3 (BR-037/BR-038): usuario_admin sem limite configurado (NULL = R$0
        # efetivo) -- este desconto de R$200 exige desconto_aprovado explícito.
        venda = _criar_venda_via_api(
            client, login_como, usuario_admin, valor_unitario=2800.0, desconto_aprovado=True
        )
        try:
            resp = client.get("/api/vendas", query_string={"cliente_id": venda["cliente_id"]})
            item = resp.get_json()["items"][0]["itens_resumo"][0]
            assert item["valor_tabela"] == 3000.0
            assert item["valor_unitario"] == 2800.0
            assert item["desconto"] == 200.0
        finally:
            _limpar_tudo(venda["cliente_id"], venda["estoque_id"], venda["unidade_id"])


class TestCancelarVenda:
    """V1.2 -- Cancelamento (BR-031 a BR-036, docs/product/features/VENDAS.md
    "V1.2 -- Cancelamento"). O teste mais importante desta classe é
    `test_revenda_da_mesma_unidade_apos_cancelamento` -- prova de que o
    índice único parcial (`idx_vendas_itens_unidade_ativa`) permite revenda
    sem violar a proteção original contra a mesma unidade em duas vendas
    vigentes simultâneas."""

    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.post("/api/vendas/1/cancelar", json={"motivo": "cliente_desistiu"})
        assert resp.status_code == 401

    def test_tecnico_nao_pode_cancelar(
        self, client, login_como, usuario_admin, usuario_tecnico, cenario_venda
    ):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        login_como(client, usuario_tecnico)
        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        assert resp.status_code == 403
        status, *_ = _venda_status_e_cancelamento(venda_id)
        assert status == "concluida"

    def test_admin_cancela_qualquer_venda(
        self, client, login_como, usuario_vendedor, usuario_admin, cenario_venda
    ):
        login_como(client, usuario_vendedor)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        login_como(client, usuario_admin)
        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        assert resp.status_code == 200
        assert resp.get_json()["status"] == "cancelada"
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"
        assert _item_ativo(cenario_venda["unidade_id"], venda_id) == 0

        status, motivo, observacao, cancelado_por, cancelado_em = _venda_status_e_cancelamento(venda_id)
        assert status == "cancelada"
        assert motivo == "cliente_desistiu"
        assert observacao in (None, "")
        assert cancelado_por == usuario_admin["id"]
        assert cancelado_em is not None

        conn = _app.conectar()
        try:
            log = conn.execute(
                "SELECT valor_anterior, valor_novo FROM audit_log "
                "WHERE entidade='venda' AND entidade_id=? AND acao='status_change'",
                (venda_id,),
            ).fetchone()
        finally:
            conn.close()
        assert log is not None
        assert log[0] == "concluida"
        assert "cancelada" in log[1]

    def test_vendedor_cancela_a_propria_venda(self, client, login_como, usuario_vendedor, cenario_venda):
        login_como(client, usuario_vendedor)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "erro_lancamento"})

        assert resp.status_code == 200
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

    def test_vendedor_nao_pode_cancelar_venda_de_outro_vendedor(
        self, client, login_como, usuario_vendedor, cenario_venda
    ):
        outro_vendedor = _criar_usuario("Outro Vendedor", "vendedor")
        try:
            login_como(client, usuario_vendedor)
            venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

            login_como(client, outro_vendedor)
            resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

            assert resp.status_code == 403
            status, *_ = _venda_status_e_cancelamento(venda_id)
            assert status == "concluida"
            assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"
        finally:
            _remover_usuario(outro_vendedor["id"])

    def test_motivo_invalido_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "motivo_que_nao_existe"})

        assert resp.status_code == 400
        status, *_ = _venda_status_e_cancelamento(venda_id)
        assert status == "concluida"

    def test_motivo_outro_sem_observacao_retorna_400(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "outro"})

        assert resp.status_code == 400
        status, *_ = _venda_status_e_cancelamento(venda_id)
        assert status == "concluida"

    def test_motivo_outro_com_observacao_persiste(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.post(
            f"/api/vendas/{venda_id}/cancelar",
            json={"motivo": "outro", "observacao": "Motivo específico não listado"},
        )

        assert resp.status_code == 200
        _, motivo, observacao, _, _ = _venda_status_e_cancelamento(venda_id)
        assert motivo == "outro"
        assert observacao == "Motivo específico não listado"

    def test_cancelar_venda_ja_cancelada_retorna_erro(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        primeira = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})
        assert primeira.status_code == 200

        segunda = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})
        assert segunda.status_code == 400

    def test_cancelar_venda_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas/999999/cancelar", json={"motivo": "cliente_desistiu"})
        assert resp.status_code == 404

    def test_revenda_da_mesma_unidade_apos_cancelamento(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """Prova de que o índice único parcial (idx_vendas_itens_unidade_ativa)
        funciona -- BR-033: cancelar libera a unidade para uma venda nova,
        sem violar a proteção contra a mesma unidade em duas vendas vigentes
        simultâneas, e sem apagar o histórico da venda cancelada."""
        login_como(client, usuario_admin)
        primeira_venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        cancelar = client.post(
            f"/api/vendas/{primeira_venda_id}/cancelar", json={"motivo": "cliente_desistiu"}
        )
        assert cancelar.status_code == 200
        assert _status_unidade(cenario_venda["unidade_id"]) == "disponivel"

        segunda = client.post("/api/vendas", json=_payload(cenario_venda))
        assert segunda.status_code == 201
        segunda_venda_id = segunda.get_json()["id"]
        assert segunda_venda_id != primeira_venda_id
        assert _status_unidade(cenario_venda["unidade_id"]) == "vendido"

        conn = _app.conectar()
        try:
            total_itens = conn.execute(
                "SELECT COUNT(*) FROM vendas_itens WHERE unidade_serializada_id=?",
                (cenario_venda["unidade_id"],),
            ).fetchone()[0]
        finally:
            conn.close()
        assert total_itens == 2  # histórico preservado: a linha cancelada não é apagada
        assert _item_ativo(cenario_venda["unidade_id"], primeira_venda_id) == 0
        assert _item_ativo(cenario_venda["unidade_id"], segunda_venda_id) == 1

    def test_historico_inclui_canceladas_por_padrao(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]
        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        resp = client.get("/api/vendas", query_string={"cliente_id": cenario_venda["cliente_id"]})

        assert venda_id in [v["id"] for v in resp.get_json()["items"]]

    def test_historico_filtra_por_status(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]
        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        canceladas = client.get(
            "/api/vendas", query_string={"cliente_id": cenario_venda["cliente_id"], "status": "cancelada"}
        ).get_json()
        concluidas = client.get(
            "/api/vendas", query_string={"cliente_id": cenario_venda["cliente_id"], "status": "concluida"}
        ).get_json()

        assert canceladas["total"] == 1
        assert concluidas["total"] == 0

    def test_detalhe_expoe_campos_de_cancelamento(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        antes = client.get(f"/api/vendas/{venda_id}").get_json()["venda"]
        assert antes["motivo_cancelamento"] is None
        assert antes["cancelado_em"] is None

        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "imei_incorreto"})

        depois = client.get(f"/api/vendas/{venda_id}").get_json()["venda"]
        assert depois["status"] == "cancelada"
        assert depois["motivo_cancelamento"] == "imei_incorreto"
        assert depois["cancelado_por"] == usuario_admin["id"]
        assert depois["cancelado_em"] is not None


class TestDescontoEAprovacao:
    """Desconto (BR-039, BR-053, docs/product/features/VENDAS.md "Revisão do
    modelo de desconto"). `cenario_venda` tem `valor_tabela = 3000.0` (ver
    `_criar_item_estoque_rastreavel`).

    BR-037/BR-038 (limite por vendedor + aprovação obrigatória acima do
    limite) foram implementadas na V1.3 e revogadas no dia seguinte -- a loja
    não opera com bloqueio preventivo. Os testes que existiam para essas
    regras foram substituídos pelos abaixo, que provam a regra vigente."""

    def test_desconto_zero_nao_exige_aprovacao(self, client, login_como, usuario_vendedor, cenario_venda):
        login_como(client, usuario_vendedor)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=3000.0))
        assert resp.status_code == 201

    def test_desconto_de_qualquer_valor_e_sempre_aceito(
        self, client, login_como, usuario_vendedor, cenario_venda
    ):
        """BR-053 -- mesmo um desconto muito grande (R$ 2.000 numa venda de
        R$ 3.000) é aceito sem exigir nenhum campo de aprovação."""
        login_como(client, usuario_vendedor)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=1000.0))
        assert resp.status_code == 201

    def test_venda_nunca_exige_aprovacao_mesmo_com_limite_legado_configurado(
        self, client, login_como, usuario_vendedor, cenario_venda
    ):
        """Regressão: `limite_desconto_livre` (coluna deprecada da V1.3) pode
        continuar com um valor herdado de antes da revisão -- confirma que
        ele não tem efeito algum sobre a venda."""
        _definir_limite_desconto(usuario_vendedor["id"], 50.0)
        login_como(client, usuario_vendedor)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=1000.0))
        assert resp.status_code == 201

    def test_valor_do_desconto_continua_persistido(self, client, login_como, usuario_admin, cenario_venda):
        """O campo `desconto` (valor_tabela - valor_unitario) continua sendo
        calculado e exposto -- indicadores futuros (V1.4.1/V1.5) dependem
        dele existir, mesmo sem bloqueio nenhum sobre o valor."""
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=2500.0))
        assert resp.status_code == 201
        venda_id = resp.get_json()["id"]

        detalhe = client.get(f"/api/vendas/{venda_id}")
        item = detalhe.get_json()["itens"][0]
        assert item["valor_tabela"] == 3000.0
        assert item["valor_unitario"] == 2500.0
        assert item["desconto"] == 500.0

    def test_motivo_desconto_opcional_ausente(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=3000.0))
        assert resp.status_code == 201
        _id, motivo, _aprovado_em = _item_desconto_info(cenario_venda["unidade_id"])
        assert motivo == ""

    def test_motivo_desconto_persistido_quando_enviado(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/vendas",
            json=_payload(cenario_venda, valor_unitario=3000.0, motivo_desconto="Negociação final"),
        )
        assert resp.status_code == 201
        _id, motivo, _aprovado_em = _item_desconto_info(cenario_venda["unidade_id"])
        assert motivo == "Negociação final"

    def test_desconto_aprovado_em_nunca_mais_e_gravado(
        self, client, login_como, usuario_vendedor, cenario_venda
    ):
        """BR-054 -- `desconto_aprovado_em` (coluna deprecada) permanece
        sempre `NULL` para vendas novas, mesmo com um desconto grande."""
        login_como(client, usuario_vendedor)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=1000.0))
        assert resp.status_code == 201
        _id, _motivo, aprovado_em = _item_desconto_info(cenario_venda["unidade_id"])
        assert aprovado_em is None


class TestAjusteComercial:
    """Ajuste Comercial Autorizado (BR-043) -- única exceção formalmente
    definida ao Princípio da Imutabilidade da Venda (BR-034, que continua
    válido para todo o resto)."""

    def _criar_venda_concluida(self, client, login_como, usuario, cenario_venda, valor_unitario=3000.0):
        login_como(client, usuario)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=valor_unitario))
        assert resp.status_code == 201
        venda_id = resp.get_json()["id"]
        item_id = _item_desconto_info(cenario_venda["unidade_id"])[0]
        return venda_id, item_id

    def test_admin_ajusta_com_sucesso(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            json={"valor_unitario": 2700.0, "motivo": "Negociação pós-venda"},
        )

        assert resp.status_code == 200
        conn = _app.conectar()
        try:
            item = conn.execute(
                "SELECT valor_unitario, subtotal FROM vendas_itens WHERE id=?", (item_id,)
            ).fetchone()
            venda = conn.execute("SELECT valor_total FROM vendas WHERE id=?", (venda_id,)).fetchone()
            auditoria = conn.execute(
                "SELECT valor_anterior, valor_novo FROM audit_log "
                "WHERE entidade='venda_item' AND entidade_id=? ORDER BY id DESC LIMIT 1",
                (item_id,),
            ).fetchone()
        finally:
            conn.close()
        assert item[0] == 2700.0
        assert item[1] == 2700.0
        assert venda[0] == 2700.0
        assert auditoria is not None
        assert "3000" in auditoria[0]
        assert "2700" in auditoria[1]
        assert "Negociação pós-venda" in auditoria[1]

    def test_vendedor_nao_pode_ajustar(self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_vendedor)
        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            json={"valor_unitario": 2700.0, "motivo": "Tentativa"},
        )
        assert resp.status_code == 403

    def test_ajuste_sem_motivo_e_rejeitado(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            json={"valor_unitario": 2700.0},
        )
        assert resp.status_code == 400

    def test_ajuste_em_venda_cancelada_e_rejeitado(self, client, login_como, usuario_admin, cenario_venda):
        """Também cobre o caso de 'estado obsoleto' do plano técnico: o admin
        poderia ter aberto a tela vendo a venda concluída; se ela foi
        cancelada nesse meio-tempo, o PATCH deve falhar -- revalida
        `status='concluida'` no momento da escrita, nunca confia no estado
        lido antes."""
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            json={"valor_unitario": 2700.0, "motivo": "Tarde demais"},
        )
        assert resp.status_code == 400

    def test_ajuste_nao_altera_outros_campos_da_venda(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        antes = client.get(f"/api/vendas/{venda_id}").get_json()["venda"]

        client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            json={"valor_unitario": 2700.0, "motivo": "Ajuste"},
        )

        depois = client.get(f"/api/vendas/{venda_id}").get_json()["venda"]
        assert depois["cliente_id"] == antes["cliente_id"]
        assert depois["vendedor_id"] == antes["vendedor_id"]
        assert depois["forma_pagamento"] == antes["forma_pagamento"]
        assert depois["status"] == antes["status"] == "concluida"
        assert depois["criado_em"] == antes["criado_em"]

    def test_historico_desconto_expoe_o_ajuste(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/ajuste-desconto",
            json={"valor_unitario": 2700.0, "motivo": "Ajuste histórico"},
        )

        resp = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-desconto")

        assert resp.status_code == 200
        historico = resp.get_json()["historico"]
        assert len(historico) == 1
        assert historico[0]["acao"] == "ajuste_desconto"


class TestComissao:
    """V1.4 -- Comissão (BR-044 a BR-051, VENDAS.md "V1.4 -- Comissão")."""

    def _criar_venda_concluida(self, client, login_como, usuario, cenario_venda, valor_unitario=3000.0):
        login_como(client, usuario)
        resp = client.post("/api/vendas", json=_payload(cenario_venda, valor_unitario=valor_unitario))
        assert resp.status_code == 201
        venda_id = resp.get_json()["id"]
        item_id = _item_desconto_info(cenario_venda["unidade_id"])[0]
        return venda_id, item_id

    def test_admin_atribui_comissao_com_sucesso(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})

        assert resp.status_code == 200
        conn = _app.conectar()
        try:
            comissao = conn.execute(
                "SELECT comissao_valor FROM vendas_itens WHERE id=?", (item_id,)
            ).fetchone()
        finally:
            conn.close()
        assert comissao[0] == 150.0

    def test_financeiro_atribui_comissao_com_sucesso(
        self, client, login_como, usuario_admin, usuario_financeiro, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_financeiro)
        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 200.0})

        assert resp.status_code == 200

    def test_vendedor_nao_pode_atribuir_comissao(
        self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_vendedor)
        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})
        assert resp.status_code == 403

    def test_tecnico_nao_pode_atribuir_comissao(
        self, client, login_como, usuario_admin, usuario_tecnico, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_tecnico)
        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})
        assert resp.status_code == 403

    def test_estoque_nao_pode_atribuir_comissao(
        self, client, login_como, usuario_admin, usuario_estoque, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_estoque)
        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})
        assert resp.status_code == 403

    def test_valor_negativo_e_rejeitado(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": -10.0})
        assert resp.status_code == 400

    def test_comissao_zero_e_aceita(self, client, login_como, usuario_admin, cenario_venda):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 0})
        assert resp.status_code == 200

    def test_atribuir_comissao_em_venda_cancelada_e_rejeitado(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})
        assert resp.status_code == 400

    def test_editar_comissao_duas_vezes_gera_dois_eventos_de_auditoria(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 100.0})
        client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 180.0})

        resp = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-comissao")
        assert resp.status_code == 200
        historico = resp.get_json()["historico"]
        assert len(historico) == 2
        assert all(evento["acao"] == "comissao_alterada" for evento in historico)

    def test_cancelar_venda_com_comissao_zera_automaticamente(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})

        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})
        assert resp.status_code == 200

        conn = _app.conectar()
        try:
            comissao = conn.execute(
                "SELECT comissao_valor FROM vendas_itens WHERE id=?", (item_id,)
            ).fetchone()
        finally:
            conn.close()
        assert comissao[0] == 0

        historico = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-comissao").get_json()["historico"]
        assert any(evento["acao"] == "comissao_alterada" for evento in historico)

    def test_get_venda_esconde_comissao_para_vendedor(
        self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})

        login_como(client, usuario_vendedor)
        resp = client.get(f"/api/vendas/{venda_id}")
        assert resp.status_code == 200
        assert "comissao_valor" not in resp.get_json()["itens"][0]

    def test_get_venda_mostra_comissao_para_admin_e_financeiro(
        self, client, login_como, usuario_admin, usuario_financeiro, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})

        resp = client.get(f"/api/vendas/{venda_id}")
        assert resp.get_json()["itens"][0]["comissao_valor"] == 150.0

        login_como(client, usuario_financeiro)
        resp = client.get(f"/api/vendas/{venda_id}")
        assert resp.get_json()["itens"][0]["comissao_valor"] == 150.0

    def test_listar_vendas_esconde_comissao_para_vendedor(
        self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/comissao", json={"valor": 150.0})

        login_como(client, usuario_vendedor)
        resp = client.get("/api/vendas")
        assert resp.status_code == 200
        venda = next(v for v in resp.get_json()["items"] if v["id"] == venda_id)
        assert all("comissao_valor" not in item for item in venda["itens_resumo"])

    def test_historico_comissao_e_restrito_a_admin_e_financeiro(
        self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_vendedor)
        resp = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-comissao")
        assert resp.status_code == 403

    def test_criar_usuario_com_perfil_financeiro_e_aceito(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/usuarios",
            json={
                "nome": "Financeiro Novo",
                "usuario": f"financeiro_{uuid.uuid4().hex[:8]}",
                "senha": SENHA_PADRAO,
                "perfil": "financeiro",
            },
        )
        assert resp.status_code == 201
        novo_id = resp.get_json()["id"]
        conn = _app.conectar()
        try:
            perfil = conn.execute("SELECT perfil FROM usuarios WHERE id=?", (novo_id,)).fetchone()[0]
        finally:
            conn.close()
        assert perfil == "financeiro"
        _remover_usuario(novo_id)


class TestGarantiaDeVenda:
    """V1.5 -- Garantia de Venda (BR-056 a BR-059, VENDAS.md "V1.5 -- Garantia")."""

    def _criar_venda_concluida(self, client, login_como, usuario, cenario_venda, tipo_garantia_id=None):
        login_como(client, usuario)
        resp = client.post(
            "/api/vendas", json=_payload(cenario_venda, tipo_garantia_id=tipo_garantia_id or _TIPO_GARANTIA_PADRAO_ID)
        )
        assert resp.status_code == 201
        venda_id = resp.get_json()["id"]
        item_id = _item_desconto_info(cenario_venda["unidade_id"])[0]
        return venda_id, item_id

    def test_cancelar_venda_zera_garantia_com_auditoria(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """BR-058 -- cancelar zera o snapshot inteiro do item, mesmo padrão
        já usado para a comissão (BR-051)."""
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})
        assert resp.status_code == 200

        conn = _app.conectar()
        try:
            row = conn.execute(
                """
                SELECT tipo_garantia_id, garantia_nome, garantia_duracao_meses,
                       garantia_data_inicio, garantia_data_fim
                FROM vendas_itens WHERE id=?
                """,
                (item_id,),
            ).fetchone()
        finally:
            conn.close()
        assert row == (None, None, None, None, None)

        historico = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-garantia").get_json()["historico"]
        assert any(evento["acao"] == "garantia_alterada" for evento in historico)

    def test_admin_corrige_garantia_com_sucesso(self, client, login_como, usuario_admin, cenario_venda):
        """BR-059 -- correção só `admin`, sem motivo, recalcula
        `garantia_data_fim` a partir da nova duração."""
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        tipo_novo = _criar_tipo_garantia(nome="Garantia Estendida", duracao_meses=24)
        try:
            resp = client.patch(
                f"/api/vendas/{venda_id}/itens/{item_id}/garantia", json={"tipo_garantia_id": tipo_novo}
            )
            assert resp.status_code == 200

            venda = client.get(f"/api/vendas/{venda_id}").get_json()
            item = venda["itens"][0]
            assert item["tipo_garantia_id"] == tipo_novo
            assert item["garantia_nome"] == "Garantia Estendida"
            assert item["garantia_duracao_meses"] == 24
        finally:
            _remover_tipo_garantia(tipo_novo)

    def test_vendedor_nao_pode_corrigir_garantia(
        self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_vendedor)
        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/garantia",
            json={"tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID},
        )
        assert resp.status_code == 403

    def test_tecnico_nao_pode_corrigir_garantia(
        self, client, login_como, usuario_admin, usuario_tecnico, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_tecnico)
        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/garantia",
            json={"tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID},
        )
        assert resp.status_code == 403

    def test_corrigir_garantia_com_tipo_invalido_retorna_400(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        resp = client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/garantia", json={"tipo_garantia_id": 999999})
        assert resp.status_code == 400

    def test_corrigir_garantia_em_venda_cancelada_e_rejeitado(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})

        resp = client.patch(
            f"/api/vendas/{venda_id}/itens/{item_id}/garantia",
            json={"tipo_garantia_id": _TIPO_GARANTIA_PADRAO_ID},
        )
        assert resp.status_code == 400

    def test_corrigir_garantia_duas_vezes_gera_dois_eventos_de_correcao(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        """O histórico inclui também o evento de concessão original
        (`garantia_concedida`, gravado na criação da venda) -- este teste
        confere só os eventos de correção (`garantia_alterada`)."""
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)
        tipo_a = _criar_tipo_garantia(nome="Garantia A", duracao_meses=6)
        tipo_b = _criar_tipo_garantia(nome="Garantia B", duracao_meses=18)
        try:
            client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/garantia", json={"tipo_garantia_id": tipo_a})
            client.patch(f"/api/vendas/{venda_id}/itens/{item_id}/garantia", json={"tipo_garantia_id": tipo_b})

            resp = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-garantia")
            assert resp.status_code == 200
            historico = resp.get_json()["historico"]
            assert len(historico) == 3
            correcoes = [e for e in historico if e["acao"] == "garantia_alterada"]
            concessoes = [e for e in historico if e["acao"] == "garantia_concedida"]
            assert len(correcoes) == 2
            assert len(concessoes) == 1
        finally:
            _remover_tipo_garantia(tipo_a)
            _remover_tipo_garantia(tipo_b)

    def test_historico_garantia_e_aberto_a_qualquer_autenticado(
        self, client, login_como, usuario_admin, usuario_vendedor, cenario_venda
    ):
        """Diferente do histórico de comissão (restrito), o de garantia segue
        o mesmo padrão aberto do histórico de desconto -- qualquer usuário
        autenticado que vê a venda vê a garantia (BR-057)."""
        venda_id, item_id = self._criar_venda_concluida(client, login_como, usuario_admin, cenario_venda)

        login_como(client, usuario_vendedor)
        resp = client.get(f"/api/vendas/{venda_id}/itens/{item_id}/historico-garantia")
        assert resp.status_code == 200


class TestPainelGarantiasVenda:
    """Painel de garantias unificado (PLAN-painel-garantias-unificado.md)."""

    def _imei(self, cenario):
        conn = _app.conectar()
        try:
            return conn.execute(
                "SELECT imei FROM unidades_serializadas WHERE id=?", (cenario["unidade_id"],)
            ).fetchone()[0]
        finally:
            conn.close()

    def test_anonimo_recebe_401(self, client):
        assert client.get("/api/vendas/garantias").status_code == 401

    def test_lista_garantia_ativa_e_some_quando_venda_cancela(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]
        imei = self._imei(cenario_venda)

        resp = client.get(f"/api/vendas/garantias?q={imei}").get_json()
        assert resp["ok"] is True
        itens = [i for i in resp["items"] if i["venda_id"] == venda_id]
        assert len(itens) == 1
        assert itens[0]["status_garantia"] == "ativa"
        assert itens[0]["garantia_nome"] == "Garantia Teste Padrão"
        assert 360 <= itens[0]["dias_restantes"] <= 366
        assert resp["ativa"] >= 1

        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "cliente_desistiu"})
        resp = client.get(f"/api/vendas/garantias?q={imei}").get_json()
        assert [i for i in resp["items"] if i["venda_id"] == venda_id] == []

    def test_vendedor_tambem_consulta(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        assert client.get("/api/vendas/garantias").status_code == 200


def test_classificar_garantia_usa_mesmo_limiar_da_os():
    from fluxoly_vendas_service import classificar_garantia

    assert classificar_garantia(None) == "desconhecida"
    assert classificar_garantia(-1) == "vencida"
    assert classificar_garantia(0) == "vencendo"
    assert classificar_garantia(7) == "vencendo"
    assert classificar_garantia(8) == "ativa"


class TestDashboardVendasOS:
    """Dashboard somando vendas e OS (PLAN-dashboard-vendas-os.md)."""

    @staticmethod
    def _hoje():
        # `vendas.criado_em` é CURRENT_TIMESTAMP (UTC); o filtro do dashboard compara com a data
        # pedida sem converter fuso -- comportamento atual de todo o sistema (KNOWN_ISSUES, fuso).
        from datetime import UTC, datetime

        return datetime.now(UTC).date().isoformat()

    def _dashboard(self, client):
        hoje = self._hoje()
        return client.get(f"/api/dashboard?start_date={hoje}&end_date={hoje}").get_json()

    def test_venda_concluida_entra_no_faturamento_de_vendas_e_no_consolidado(
        self, client, login_como, usuario_admin, cenario_venda
    ):
        login_como(client, usuario_admin)
        antes = self._dashboard(client)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]
        depois = self._dashboard(client)

        assert depois["vendas"]["quantidade"] == antes["vendas"]["quantidade"] + 1
        assert round(depois["vendas"]["faturamento"] - antes["vendas"]["faturamento"], 2) == 3200.0
        # Chaves antigas continuam sendo só de OS (compatibilidade).
        assert depois["faturamento_total"] == antes["faturamento_total"]
        assert depois["consolidado"]["faturamento"] == round(
            depois["faturamento_total"] + depois["vendas"]["faturamento"], 2
        )
        assert any(v["vendedor"] == "Admin Teste" for v in depois["vendas"]["por_vendedor"])

        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "erro_lancamento"})
        cancelada = self._dashboard(client)
        assert cancelada["vendas"]["quantidade"] == antes["vendas"]["quantidade"]

    def test_lucro_de_aparelho_so_para_admin_e_financeiro(
        self, client, login_como, usuario_vendedor, usuario_financeiro
    ):
        login_como(client, usuario_vendedor)
        assert "lucro_aparelhos" not in self._dashboard(client)["vendas"]
        login_como(client, usuario_financeiro)
        assert "lucro_aparelhos" in self._dashboard(client)["vendas"]

    def test_vendedor_nao_recebe_custo_lucro_nem_resultado(self, client, login_como, usuario_vendedor):
        """PLAN-esconder-lucro-vendedor.md."""
        from api_system import CHAVES_CUSTO_LUCRO_DASHBOARD

        login_como(client, usuario_vendedor)
        resp = self._dashboard(client)

        assert resp["ok"] is True
        for chave in CHAVES_CUSTO_LUCRO_DASHBOARD:
            assert chave not in resp, chave
        assert all("lucro" not in linha for linha in resp["resumo_por_vendedor"])
        assert "faturamento_total" in resp and "ordens_finalizadas" in resp

    def test_admin_financeiro_e_tecnico_continuam_vendo_lucro(
        self, client, login_como, usuario_admin, usuario_financeiro, usuario_tecnico
    ):
        for usuario in (usuario_admin, usuario_financeiro, usuario_tecnico):
            login_como(client, usuario)
            resp = self._dashboard(client)
            assert "lucro_total" in resp and "resultado_liquido" in resp

    def test_periodo_fora_nao_conta_venda(self, client, login_como, usuario_admin, cenario_venda):
        login_como(client, usuario_admin)
        client.post("/api/vendas", json=_payload(cenario_venda))
        resp = client.get("/api/dashboard?start_date=2000-01-01&end_date=2000-01-31").get_json()
        assert resp["vendas"]["quantidade"] == 0
        assert resp["vendas"]["ticket_medio"] == 0


@pytest.fixture
def loja_para_recibo():
    """Recibo exige Dados da Loja (mesmo padrão de tests/test_os_documento.py)."""
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute(
            "INSERT INTO dados_loja (id, nome_fantasia, termos_garantia) VALUES (1, 'Loja Recibo Teste', 'Termos.')"
        )
        conn.commit()
        yield
        conn.execute("DELETE FROM dados_loja")
        conn.commit()
    finally:
        conn.close()


class TestReciboVenda:
    """Recibo de venda para o cliente (BR-103, PLAN-recibo-venda.md)."""

    def _cpf(self, cenario, cpf="123.456.789-09"):
        conn = _app.conectar()
        try:
            conn.execute("UPDATE clientes SET cpf_cnpj=? WHERE id=?", (cpf, cenario["cliente_id"]))
            conn.commit()
        finally:
            conn.close()

    def test_anonimo_recebe_401(self, client):
        assert client.get("/api/vendas/1/recibo").status_code == 401

    def test_recibo_traz_item_garantia_e_total_sem_custo_nem_comissao(
        self, client, login_como, usuario_admin, cenario_venda, loja_para_recibo
    ):
        login_como(client, usuario_admin)
        self._cpf(cenario_venda)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}/recibo")

        assert resp.status_code == 200, resp.get_json()
        recibo = resp.get_json()["recibo"]
        assert recibo["loja"]["nome_fantasia"] == "Loja Recibo Teste"
        assert recibo["termos"] == "Termos."
        assert recibo["cliente"]["cpf_cnpj"] == "123.456.789-09"
        assert recibo["venda"]["valor_total"] == 3200.0
        assert recibo["venda"]["forma_pagamento"] == "Pix"
        item = recibo["venda"]["itens"][0]
        assert item["valor"] == 3200.0
        assert item["garantia"]["nome"] == "Garantia Teste Padrão"
        texto = resp.get_data(as_text=True)
        for proibido in ("custo", "lucro", "comissao", "valor_tabela", "motivo_desconto"):
            assert proibido not in texto, proibido

    def test_vendedor_recebe_recibo_sem_cpf(
        self, client, login_como, usuario_vendedor, cenario_venda, loja_para_recibo
    ):
        login_como(client, usuario_vendedor)
        self._cpf(cenario_venda)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        recibo = client.get(f"/api/vendas/{venda_id}/recibo").get_json()["recibo"]

        assert recibo["cliente"]["cpf_cnpj"] == ""

    def test_venda_cancelada_nao_gera_recibo(
        self, client, login_como, usuario_admin, cenario_venda, loja_para_recibo
    ):
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]
        client.post(f"/api/vendas/{venda_id}/cancelar", json={"motivo": "erro_lancamento"})

        resp = client.get(f"/api/vendas/{venda_id}/recibo")

        assert resp.status_code == 409
        assert "cancelada" in resp.get_json()["erro"]

    def test_sem_dados_da_loja_pede_cadastro(self, client, login_como, usuario_admin, cenario_venda):
        conn = _app.conectar()
        try:
            conn.execute("DELETE FROM dados_loja")
            conn.commit()
        finally:
            conn.close()
        login_como(client, usuario_admin)
        venda_id = client.post("/api/vendas", json=_payload(cenario_venda)).get_json()["id"]

        resp = client.get(f"/api/vendas/{venda_id}/recibo")

        assert resp.status_code == 409
        assert "Dados da Loja" in resp.get_json()["erro"]

    def test_venda_inexistente_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        assert client.get("/api/vendas/999999999/recibo").status_code == 404
