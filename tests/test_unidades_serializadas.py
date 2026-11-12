"""
Testes do domínio `unidades_serializadas` — rastreamento individual por
IMEI/serial, evoluído de `estoque_unidades` na migração ADR-007
(docs/engineering/migrations/MIGRATION_unidades_serializadas.md).

Escopo: `GET/POST /api/unidades-serializadas*` e
`PATCH /api/unidades-serializadas/<id>/status`. Uma unidade tem origem em
`estoque_id` OU `produto_id`, nunca os dois (invariante validada no
service). `reservado`/`vendido` existem no schema
(`docs/product/features/IMEI.md`) mas nenhum endpoint desta sprint produz
ou aceita esses estados — reservados para o futuro módulo de Vendas.
"""

import uuid

import app as _app


def _criar_item_estoque(requer_imei=1, **overrides):
    conn = _app.conectar()
    cursor = conn.cursor()
    dados = {
        "descricao": "iPhone Teste",
        "valor": 3000.0,
        "fornecedor": "Fornecedor Teste",
        "quantidade": 1,
        "modelo": "iPhone 13",
        "sku": f"SKU-{uuid.uuid4().hex[:8]}",
        "tipo": "Aparelho",
        "qualidade": "Novo",
    }
    dados.update(overrides)
    cursor.execute(
        """
        INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade, requer_imei)
        VALUES (?,?,?,?,?,?,?,?,?)
        """,
        (
            dados["descricao"], dados["valor"], dados["fornecedor"], dados["quantidade"],
            dados["modelo"], dados["sku"], dados["tipo"], dados["qualidade"], requer_imei,
        ),
    )
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return item_id


def _limpar_item_estoque(estoque_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id IN (SELECT id FROM unidades_serializadas WHERE estoque_id=?)", (estoque_id,))
        conn.execute("DELETE FROM unidades_serializadas WHERE estoque_id=?", (estoque_id,))
        conn.execute("DELETE FROM estoque WHERE id=?", (estoque_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_produto(requer_rastreio_unidade=True, **overrides):
    conn = _app.conectar()
    cursor = conn.cursor()
    dados = {
        "categoria": "iPhone",
        "marca": None,
        "modelo": f"iPhone Teste {uuid.uuid4().hex[:8]}",
        "condicao": "Seminovo",
        "preco_custo": 2000.0,
        "preco_venda": 2999.0,
        "quantidade": 1,
    }
    dados.update(overrides)
    cursor.execute(
        """
        INSERT INTO produtos (categoria, marca, modelo, condicao, preco_custo, preco_venda, quantidade, requer_rastreio_unidade)
        VALUES (?,?,?,?,?,?,?,?)
        """,
        (
            dados["categoria"], dados["marca"], dados["modelo"], dados["condicao"], dados["preco_custo"],
            dados["preco_venda"], dados["quantidade"], 1 if requer_rastreio_unidade else 0,
        ),
    )
    conn.commit()
    produto_id = cursor.lastrowid
    conn.close()
    return produto_id


def _limpar_produto(produto_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id IN (SELECT id FROM unidades_serializadas WHERE produto_id=?)", (produto_id,))
        conn.execute("DELETE FROM unidades_serializadas WHERE produto_id=?", (produto_id,))
        conn.execute("DELETE FROM audit_log WHERE entidade='produto' AND entidade_id=?", (produto_id,))
        conn.execute("DELETE FROM produtos WHERE id=?", (produto_id,))
        conn.commit()
    finally:
        conn.close()


def _criar_unidade(client, estoque_id=None, imei=None):
    estoque_id = estoque_id or _criar_item_estoque()
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    resp = client.post("/api/unidades-serializadas", json={"estoque_id": estoque_id, "imei": imei})
    return resp, estoque_id


def _criar_unidade_de_produto(client, produto_id=None, imei=None):
    produto_id = produto_id or _criar_produto()
    imei = imei or "".join(str((int(uuid.uuid4().hex[:1], 16) + i) % 10) for i in range(15))
    resp = client.post("/api/unidades-serializadas", json={"produto_id": produto_id, "imei": imei})
    return resp, produto_id


class TestListarUnidades:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/unidades-serializadas")
        assert resp.status_code == 401

    def test_listagem_padrao_retorna_estrutura_paginada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/unidades-serializadas")

        assert resp.status_code == 200
        body = resp.get_json()
        assert "items" in body and "total" in body

    def test_busca_por_imei_parcial(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client, imei="352099001761481")

        resp = client.get("/api/unidades-serializadas?imei=176148")

        imeis = [u["imei"] for u in resp.get_json()["items"]]
        assert "352099001761481" in imeis
        _limpar_item_estoque(estoque_id)

    def test_filtro_por_produto_id(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client)
        assert criado.status_code == 200

        resp = client.get(f"/api/unidades-serializadas?produto_id={produto_id}")

        body = resp.get_json()
        assert body["total"] == 1
        assert body["items"][0]["produto_id"] == produto_id
        assert body["items"][0]["estoque_id"] is None
        _limpar_produto(produto_id)

    def test_listagem_inclui_origem_de_estoque(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        estoque_id = _criar_item_estoque(modelo="iPhone 13 Pro")
        criado, _ = _criar_unidade(client, estoque_id=estoque_id)
        assert criado.status_code == 200

        resp = client.get(f"/api/unidades-serializadas?estoque_id={estoque_id}")

        item = resp.get_json()["items"][0]
        assert item["origem_tipo"] == "estoque"
        assert item["origem_label"] == "iPhone 13 Pro"
        _limpar_item_estoque(estoque_id)

    def test_listagem_inclui_origem_de_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        produto_id = _criar_produto(modelo="iPhone 15 Pro Max")
        criado, _ = _criar_unidade_de_produto(client, produto_id=produto_id)
        assert criado.status_code == 200

        resp = client.get(f"/api/unidades-serializadas?produto_id={produto_id}")

        item = resp.get_json()["items"][0]
        assert item["origem_tipo"] == "produto"
        assert item["origem_label"] == "iPhone 15 Pro Max"
        assert item["produto_categoria"] == "iPhone"
        _limpar_produto(produto_id)


class TestObterUnidade:
    def test_unidade_existente(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.get(f"/api/unidades-serializadas/{unidade_id}")

        assert resp.status_code == 200
        assert resp.get_json()["unidade"]["status"] == "disponivel"
        _limpar_item_estoque(estoque_id)

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/unidades-serializadas/999999")
        assert resp.status_code == 404


class TestCriarUnidade:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.post("/api/unidades-serializadas", json={"estoque_id": 1, "imei": "123"})
        assert resp.status_code == 403

    def test_vendedor_nao_pode_criar(self, client, login_como, usuario_vendedor):
        login_como(client, usuario_vendedor)
        resp = client.post("/api/unidades-serializadas", json={"estoque_id": 1, "imei": "123"})
        assert resp.status_code == 403

    def test_item_sem_requer_imei_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        estoque_id = _criar_item_estoque(requer_imei=0)

        resp = client.post("/api/unidades-serializadas", json={"estoque_id": estoque_id, "imei": "123456789012345"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_item_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/unidades-serializadas", json={"estoque_id": 999999, "imei": "123456789012345"})
        assert resp.status_code == 404

    def test_criacao_valida_com_sucesso(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp, estoque_id = _criar_unidade(client)

        assert resp.status_code == 200
        assert resp.get_json()["id"]
        _limpar_item_estoque(estoque_id)

    def test_imei_duplicado_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        imei = "999888777666555"
        primeiro, estoque_id = _criar_unidade(client, imei=imei)
        assert primeiro.status_code == 200

        segundo_estoque = _criar_item_estoque()
        segundo = client.post("/api/unidades-serializadas", json={"estoque_id": segundo_estoque, "imei": imei})

        assert segundo.status_code == 400
        _limpar_item_estoque(estoque_id)
        _limpar_item_estoque(segundo_estoque)

    def test_criacao_registra_auditoria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp, estoque_id = _criar_unidade(client)
        unidade_id = resp.get_json()["id"]

        conn = _app.conectar()
        try:
            logs = conn.execute(
                "SELECT acao FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id=?", (unidade_id,)
            ).fetchall()
        finally:
            conn.close()

        assert [row[0] for row in logs] == ["create"]
        _limpar_item_estoque(estoque_id)

    def test_sem_origem_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/unidades-serializadas", json={"imei": "123456789012345"})
        assert resp.status_code == 400

    def test_ambas_origens_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        estoque_id = _criar_item_estoque()
        produto_id = _criar_produto()

        resp = client.post(
            "/api/unidades-serializadas",
            json={"estoque_id": estoque_id, "produto_id": produto_id, "imei": "123456789012345"},
        )

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)
        _limpar_produto(produto_id)

    def test_produto_sem_requer_rastreio_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        produto_id = _criar_produto(requer_rastreio_unidade=False)

        resp = client.post(
            "/api/unidades-serializadas", json={"produto_id": produto_id, "imei": "123456789012345"}
        )

        assert resp.status_code == 400
        _limpar_produto(produto_id)

    def test_produto_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post(
            "/api/unidades-serializadas", json={"produto_id": 999999, "imei": "123456789012345"}
        )
        assert resp.status_code == 404

    def test_criacao_valida_via_produto_com_sucesso(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp, produto_id = _criar_unidade_de_produto(client)

        assert resp.status_code == 200
        assert resp.get_json()["id"]
        _limpar_produto(produto_id)


class TestIntegracaoEstoqueViaApiC135:
    """CA-5 (KI-020/C1.3.5): antes desta sprint, não existia nenhum caminho via API
    para marcar um item de estoque como rastreável -- item_estoque era sempre
    seedado direto no banco (`_criar_item_estoque`, requer_imei=1 hardcoded) nos
    testes acima. Estes dois testes fecham o fluxo real ponta a ponta: criar o
    item via POST /api/estoque (perfil estoque) e, com o mesmo item, criar a
    unidade via POST /api/unidades-serializadas (perfil técnico)."""

    def test_fluxo_completo_item_rastreavel_criado_via_api_permite_unidade(
        self, client, login_como, usuario_estoque, usuario_tecnico
    ):
        login_como(client, usuario_estoque)
        resp_item = client.post(
            "/api/estoque",
            json={"descricao": "iPhone 13 Seminovo", "valor": 3000, "quantidade": 1, "requer_imei": True},
        )
        assert resp_item.status_code == 201
        estoque_id = resp_item.get_json()["id"]

        login_como(client, usuario_tecnico)
        resp_unidade = client.post(
            "/api/unidades-serializadas", json={"estoque_id": estoque_id, "imei": "111222333444555"}
        )

        assert resp_unidade.status_code == 200
        assert resp_unidade.get_json()["id"]
        _limpar_item_estoque(estoque_id)

    def test_item_criado_via_api_sem_marcar_rastreavel_continua_rejeitado(
        self, client, login_como, usuario_estoque, usuario_tecnico
    ):
        """Regressão: o mesmo payload de sempre (sem requer_imei) continua
        criando um item não-rastreável, e a criação de unidade a partir dele
        continua rejeitada -- exatamente o comportamento anterior a esta sprint."""
        login_como(client, usuario_estoque)
        resp_item = client.post(
            "/api/estoque", json={"descricao": "Tela Generica", "valor": 50, "quantidade": 10}
        )
        estoque_id = resp_item.get_json()["id"]

        login_como(client, usuario_tecnico)
        resp_unidade = client.post(
            "/api/unidades-serializadas", json={"estoque_id": estoque_id, "imei": "555444333222111"}
        )

        assert resp_unidade.status_code == 400
        _limpar_item_estoque(estoque_id)


class TestTransicaoStatus:
    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.patch("/api/unidades-serializadas/1/status", json={"status": "em_reparo"})
        assert resp.status_code == 403

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.patch("/api/unidades-serializadas/999999/status", json={"status": "em_reparo"})
        assert resp.status_code == 404

    def test_disponivel_para_em_reparo_e_valido(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        assert resp.status_code == 200
        assert client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]["status"] == "em_reparo"
        _limpar_item_estoque(estoque_id)

    def test_em_reparo_para_devolvido_e_valido(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "devolvido"})

        assert resp.status_code == 200
        _limpar_item_estoque(estoque_id)

    def test_devolvido_para_disponivel_e_direto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "devolvido"})

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "disponivel"})

        assert resp.status_code == 200
        _limpar_item_estoque(estoque_id)

    def test_disponivel_para_devolvido_direto_e_invalido(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "devolvido"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_transicao_para_reservado_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "reservado"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_transicao_registra_auditoria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        conn = _app.conectar()
        try:
            acoes = [
                row[0]
                for row in conn.execute(
                    "SELECT acao FROM audit_log WHERE entidade='unidade_serializada' AND entidade_id=? ORDER BY id",
                    (unidade_id,),
                ).fetchall()
            ]
        finally:
            conn.close()

        assert acoes == ["create", "status_change"]
        _limpar_item_estoque(estoque_id)

    def test_transicao_via_unidade_de_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        assert resp.status_code == 200
        _limpar_produto(produto_id)


class TestObterUnidadeComOrigem:
    """C1.3.2 (Detalhes da Unidade) — GET /<id> passou a incluir origem (mesmo
    enriquecimento já usado na listagem), para o painel de detalhe mostrar o
    produto/peça de origem sem uma segunda chamada."""

    def test_detalhe_de_unidade_com_origem_estoque(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client, estoque_id=_criar_item_estoque(modelo="iPhone 12"))
        unidade_id = criado.get_json()["id"]

        resp = client.get(f"/api/unidades-serializadas/{unidade_id}")

        unidade = resp.get_json()["unidade"]
        assert unidade["origem_tipo"] == "estoque"
        assert unidade["origem_label"] == "iPhone 12"
        _limpar_item_estoque(estoque_id)

    def test_detalhe_de_unidade_com_origem_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client, produto_id=_criar_produto(modelo="iPhone 15 Pro"))
        unidade_id = criado.get_json()["id"]

        resp = client.get(f"/api/unidades-serializadas/{unidade_id}")

        unidade = resp.get_json()["unidade"]
        assert unidade["origem_tipo"] == "produto"
        assert unidade["origem_label"] == "iPhone 15 Pro"
        assert unidade["produto_categoria"] == "iPhone"
        _limpar_produto(produto_id)


class TestHistoricoUnidade:
    """C1.3.2 (Detalhes da Unidade) — GET /<id>/historico expõe audit_log já
    gravado por criar_unidade/transicionar_status, nunca lido de volta antes."""

    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/unidades-serializadas/1/historico")
        assert resp.status_code == 401

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/unidades-serializadas/999999/historico")
        assert resp.status_code == 404

    def test_historico_inclui_criacao_e_mudanca_de_status(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]
        client.patch(f"/api/unidades-serializadas/{unidade_id}/status", json={"status": "em_reparo"})

        resp = client.get(f"/api/unidades-serializadas/{unidade_id}/historico")

        assert resp.status_code == 200
        historico = resp.get_json()["historico"]
        # mais recente primeiro
        assert [h["acao"] for h in historico] == ["status_change", "create"]
        assert historico[0]["valor_anterior"] == "disponivel"
        assert historico[0]["valor_novo"] == "em_reparo"
        assert historico[0]["usuario_nome"] == "Tecnico Teste"


def _definir_saude_localizacao(unidade_id, saude_bateria=None, localizacao=None):
    """Sem endpoint de escrita ainda (C1.3.4) — grava direto no banco para
    testar o filtro, mesmo padrão já usado para requer_imei/requer_rastreio."""
    conn = _app.conectar()
    conn.execute(
        "UPDATE unidades_serializadas SET saude_bateria=?, localizacao=? WHERE id=?",
        (saude_bateria, localizacao, unidade_id),
    )
    conn.commit()
    conn.close()


class TestFiltrosAvancados:
    """C1.3.3 — busca combinada, origem, faixa de bateria, localização e
    ordenação, todos resolvidos no backend (nunca só no frontend)."""

    def test_busca_combinada_encontra_por_modelo_de_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client, produto_id=_criar_produto(modelo="iPhone 15 Pro Max"))
        unidade_id = criado.get_json()["id"]

        resp = client.get("/api/unidades-serializadas?q=15+Pro+Max")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert unidade_id in ids
        _limpar_produto(produto_id)

    def test_busca_combinada_encontra_por_marca_de_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(
            client, produto_id=_criar_produto(modelo="iPhone Teste Marca", marca="Apple")
        )
        unidade_id = criado.get_json()["id"]

        resp = client.get("/api/unidades-serializadas?q=Apple")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert unidade_id in ids
        _limpar_produto(produto_id)

    def test_busca_combinada_encontra_por_localizacao(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]
        _definir_saude_localizacao(unidade_id, localizacao="Gaveta 3")

        resp = client.get("/api/unidades-serializadas?q=gaveta")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert unidade_id in ids
        _limpar_item_estoque(estoque_id)

    def test_parametro_imei_legado_continua_funcionando(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client, imei="352099001761481")

        resp = client.get("/api/unidades-serializadas?imei=176148")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert criado.get_json()["id"] in ids
        _limpar_item_estoque(estoque_id)

    def test_filtro_origem_estoque(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado_estoque, estoque_id = _criar_unidade(client)
        criado_produto, produto_id = _criar_unidade_de_produto(client)

        resp = client.get("/api/unidades-serializadas?origem=estoque")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert criado_estoque.get_json()["id"] in ids
        assert criado_produto.get_json()["id"] not in ids
        _limpar_item_estoque(estoque_id)
        _limpar_produto(produto_id)

    def test_filtro_origem_produto(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado_estoque, estoque_id = _criar_unidade(client)
        criado_produto, produto_id = _criar_unidade_de_produto(client)

        resp = client.get("/api/unidades-serializadas?origem=produto")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert criado_produto.get_json()["id"] in ids
        assert criado_estoque.get_json()["id"] not in ids
        _limpar_item_estoque(estoque_id)
        _limpar_produto(produto_id)

    def test_filtro_faixa_saude_bateria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado_alta, estoque_id_alta = _criar_unidade(client)
        criado_baixa, estoque_id_baixa = _criar_unidade(client)
        _definir_saude_localizacao(criado_alta.get_json()["id"], saude_bateria="97")
        _definir_saude_localizacao(criado_baixa.get_json()["id"], saude_bateria="80")

        resp = client.get("/api/unidades-serializadas?saude_bateria_faixa=100-95")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert criado_alta.get_json()["id"] in ids
        assert criado_baixa.get_json()["id"] not in ids
        _limpar_item_estoque(estoque_id_alta)
        _limpar_item_estoque(estoque_id_baixa)

    def test_filtro_saude_bateria_nao_informado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado_sem, estoque_id_sem = _criar_unidade(client)
        criado_com, estoque_id_com = _criar_unidade(client)
        _definir_saude_localizacao(criado_com.get_json()["id"], saude_bateria="90")

        resp = client.get("/api/unidades-serializadas?saude_bateria_faixa=nao_informado")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert criado_sem.get_json()["id"] in ids
        assert criado_com.get_json()["id"] not in ids
        _limpar_item_estoque(estoque_id_sem)
        _limpar_item_estoque(estoque_id_com)

    def test_filtro_localizacao(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        _definir_saude_localizacao(criado.get_json()["id"], localizacao="Bancada 2")

        resp = client.get("/api/unidades-serializadas?localizacao=bancada")

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert criado.get_json()["id"] in ids
        _limpar_item_estoque(estoque_id)

    def test_ordenacao_por_imei(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado_a, estoque_id_a = _criar_unidade(client, imei="111111111111111")
        criado_b, estoque_id_b = _criar_unidade(client, imei="222222222222222")

        resp = client.get("/api/unidades-serializadas?sort=imei&per_page=500")

        imeis = [u["imei"] for u in resp.get_json()["items"] if u["imei"] in ("111111111111111", "222222222222222")]
        assert imeis == ["111111111111111", "222222222222222"]
        _limpar_item_estoque(estoque_id_a)
        _limpar_item_estoque(estoque_id_b)

    def test_ordenacao_por_status(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/unidades-serializadas?sort=status")
        assert resp.status_code == 200

    def test_filtros_combinados(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, produto_id = _criar_unidade_de_produto(client, produto_id=_criar_produto(modelo="iPhone Combinado"))
        unidade_id = criado.get_json()["id"]
        _definir_saude_localizacao(unidade_id, saude_bateria="96", localizacao="Loja")

        resp = client.get(
            "/api/unidades-serializadas?q=Combinado&origem=produto&status=disponivel"
            "&saude_bateria_faixa=100-95&localizacao=loja&sort=recente"
        )

        ids = [u["id"] for u in resp.get_json()["items"]]
        assert unidade_id in ids
        _limpar_produto(produto_id)


class TestAtualizarUnidade:
    """C1.3.4 — PATCH /<id> edita localizacao/saude_bateria. status usa o
    endpoint próprio (/status, já testado em TestTransicaoStatus); origem/
    imei são imutáveis após o cadastro (decisão do usuário/CTO, 2026-07-22).
    Não há teste de "observações": o campo não existe no schema — não é
    editável porque não existe, não por bloqueio de regra."""

    def test_sem_autenticacao_retorna_403(self, client):
        resp = client.patch("/api/unidades-serializadas/1", json={"localizacao": "Loja"})
        assert resp.status_code == 403

    def test_unidade_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.patch("/api/unidades-serializadas/999999", json={"localizacao": "Loja"})
        assert resp.status_code == 404

    def test_atualizar_localizacao(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"localizacao": "Bancada 4"})

        assert resp.status_code == 200
        detalhe = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]
        assert detalhe["localizacao"] == "Bancada 4"
        _limpar_item_estoque(estoque_id)

    def test_atualizar_saude_bateria(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"saude_bateria": "88"})

        assert resp.status_code == 200
        detalhe = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]
        assert detalhe["saude_bateria"] == "88"
        _limpar_item_estoque(estoque_id)

    def test_saude_bateria_invalida_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"saude_bateria": "150"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_saude_bateria_nao_numerica_e_rejeitada(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"saude_bateria": "boa"})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_editar_campo_bloqueado_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"imei": "000000000000000"})

        assert resp.status_code == 400
        detalhe = client.get(f"/api/unidades-serializadas/{unidade_id}").get_json()["unidade"]
        assert detalhe["imei"] != "000000000000000"
        _limpar_item_estoque(estoque_id)

    def test_editar_origem_e_rejeitado(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        resp = client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"produto_id": 999})

        assert resp.status_code == 400
        _limpar_item_estoque(estoque_id)

    def test_atualizacao_grava_audit_log(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        criado, estoque_id = _criar_unidade(client)
        unidade_id = criado.get_json()["id"]

        client.patch(f"/api/unidades-serializadas/{unidade_id}", json={"localizacao": "Laboratório"})

        conn = _app.conectar()
        try:
            linha = conn.execute(
                "SELECT acao, valor_novo FROM audit_log WHERE entidade='unidade_serializada' "
                "AND entidade_id=? AND acao='update' ORDER BY id DESC LIMIT 1",
                (unidade_id,),
            ).fetchone()
        finally:
            conn.close()

        assert linha is not None
        assert "Laborat" in linha[1]
        _limpar_item_estoque(estoque_id)


class TestDiasEmEstoque:
    """Dias em estoque na listagem de unidades (PLAN-dias-em-estoque.md)."""

    def test_calculo_conta_so_status_em_estoque(self):
        from datetime import date

        from fluxoly_unidades_serializadas_service import calcular_dias_em_estoque

        hoje = date(2026, 11, 11)
        assert calcular_dias_em_estoque("2026-11-01 10:00:00", "disponivel", hoje) == 10
        assert calcular_dias_em_estoque("2026-11-11 23:00:00", "em_reparo", hoje) == 0
        assert calcular_dias_em_estoque("2026-08-13 08:00:00", "reservado", hoje) == 90
        assert calcular_dias_em_estoque("2026-11-01 10:00:00", "vendido", hoje) is None
        assert calcular_dias_em_estoque("2026-11-01 10:00:00", "devolvido", hoje) is None
        assert calcular_dias_em_estoque("", "disponivel", hoje) is None
        assert calcular_dias_em_estoque("lixo", "disponivel", hoje) is None
        # Cadastro "no futuro" (UTC à frente do relógio local) não vira número negativo.
        assert calcular_dias_em_estoque("2026-11-12 01:00:00", "disponivel", hoje) == 0

    def test_listagem_traz_dias_em_estoque(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        produto_id = _criar_produto(modelo="iPhone 16")
        criado, _ = _criar_unidade_de_produto(client, produto_id=produto_id)
        assert criado.status_code == 200

        item = client.get(f"/api/unidades-serializadas?produto_id={produto_id}").get_json()["items"][0]

        assert item["status"] == "disponivel"
        assert item["dias_em_estoque"] in (0, 1)
        _limpar_produto(produto_id)
