"""
Testes de criação e consulta de Ordens de Serviço via API JSON (Sprint 2.4).

Escopo: POST /api/ordens, GET /api/ordens, GET /api/ordens/<id>,
GET /api/ordens/historico-cliente.

Cliente e aparelho são campos de texto livre — não existem tabelas
`clientes`/`aparelhos` no schema (ver DATABASE.md). "Cliente/aparelho
inexistente" não é um caso rejeitável neste sistema: qualquer texto é
aceito, e "aparelho" é derivado do modelo informado. As dependências com
validação referencial real são reparo (`validar_reparo_ids`) e vendedor
(`vendedor_valido`, contra a whitelist `VENDEDORES`). Técnico é obrigatório
mas não validado contra a lista `TECNICOS` — ver relatório final da sprint.
"""

import uuid
from datetime import datetime

import app as _app


def _limpar_os(os_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
        conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
    finally:
        conn.close()


def _obter_os_no_banco(os_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT tipo, cliente, aparelho, tecnico, status, valor_cobrado, valor_descontado, vendedor, data "
            "FROM os WHERE id=?",
            (os_id,),
        ).fetchone()
    finally:
        conn.close()


# ============================================================================
# POST /api/ordens — criação válida, status inicial, valores padrão
# ============================================================================


class TestCriarOrdemValida:
    def test_criacao_valida_retorna_201_e_persiste_dados(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        payload = payload_os_valido(cliente="Cliente Novo Sem Cadastro Previo")

        resp = client.post("/api/ordens", json=payload)

        assert resp.status_code == 201
        os_id = resp.get_json()["os_id"]
        try:
            row = _obter_os_no_banco(os_id)
            assert row[1] == "Cliente Novo Sem Cadastro Previo"
            assert row[3] == "ISAQUE SOUZA"
            assert row[7] == "Camila"
        finally:
            _limpar_os(os_id)

    def test_cliente_sem_cadastro_previo_e_aceito(self, client, login_como, usuario_tecnico, payload_os_valido):
        """
        Não há tabela de clientes — qualquer texto novo, nunca visto antes, é
        aceito como cliente. Não existe conceito de "cliente inexistente"
        rejeitável neste sistema.
        """
        login_como(client, usuario_tecnico)
        cliente_inedito = f"Cliente Nunca Visto {uuid.uuid4().hex[:8]}"

        resp = client.post("/api/ordens", json=payload_os_valido(cliente=cliente_inedito))

        assert resp.status_code == 201
        _limpar_os(resp.get_json()["os_id"])

    def test_aparelho_e_derivado_do_modelo_informado_mesmo_desconhecido(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        """
        Não há catálogo de aparelhos — modelo_para_os() mantém o texto original
        quando não reconhece um iPhone conhecido. Não existe "aparelho
        inexistente" rejeitável.
        """
        login_como(client, usuario_tecnico)
        modelo_desconhecido = "Aparelho Genérico XPTO 3000"

        resp = client.post("/api/ordens", json=payload_os_valido(modelo=modelo_desconhecido))

        assert resp.status_code == 201
        os_id = resp.get_json()["os_id"]
        row = _obter_os_no_banco(os_id)
        assert row[2] == modelo_desconhecido
        _limpar_os(os_id)

    def test_status_inicial_padrao_e_em_andamento_quando_omitido(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_os_valido())

        os_id = resp.get_json()["os_id"]
        row = _obter_os_no_banco(os_id)
        assert row[4] == "Em andamento"
        _limpar_os(os_id)

    def test_valores_financeiros_padrao_sao_zero_quando_omitidos(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_os_valido())

        os_id = resp.get_json()["os_id"]
        row = _obter_os_no_banco(os_id)
        assert row[5] == 0
        assert row[6] == 0
        _limpar_os(os_id)

    def test_data_padrao_e_hoje_quando_omitida(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_os_valido())

        os_id = resp.get_json()["os_id"]
        row = _obter_os_no_banco(os_id)
        assert row[8] == datetime.now().strftime("%Y-%m-%d")
        _limpar_os(os_id)

    def test_multiplos_reparos_sao_persistidos(self, client, login_como, usuario_tecnico, payload_os_valido, dois_reparos_ids):
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_os_valido(reparo_ids=dois_reparos_ids))

        os_id = resp.get_json()["os_id"]
        detalhe = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
        assert sorted(detalhe["reparo_ids"]) == sorted(dois_reparos_ids)
        _limpar_os(os_id)

    def test_tipo_upgrade_nao_sobrescreve_o_cliente(self, client, login_como, usuario_tecnico, payload_os_valido):
        """ADR-014: a conversão "Upgrade → OS interna IR Phones" foi removida -- o cliente informado é mantido."""
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_os_valido(tipo="Upgrade", cliente="Qualquer Um"))

        os_id = resp.get_json()["os_id"]
        row = _obter_os_no_banco(os_id)
        assert row[1] == "Qualquer Um"
        _limpar_os(os_id)

    def test_flag_interna_ir_phones_e_ignorada(self, client, login_como, usuario_tecnico, payload_os_valido):
        """ADR-014: o campo legado `interna_ir_phones` não altera mais cliente nem vendedor."""
        login_como(client, usuario_tecnico)

        resp = client.post(
            "/api/ordens",
            json=payload_os_valido(interna_ir_phones=True, cliente="Cliente Real", vendedor="Camila"),
        )

        os_id = resp.get_json()["os_id"]
        row = _obter_os_no_banco(os_id)
        assert row[0] == "Assistencia"
        assert row[1] == "Cliente Real"
        assert row[7] == "Camila"
        _limpar_os(os_id)


# ============================================================================
# POST /api/ordens — campos obrigatórios
# ============================================================================


class TestCriarOrdemCamposObrigatorios:
    def test_sem_tipo_retorna_400(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(tipo=""))
        assert resp.status_code == 400

    def test_sem_cliente_retorna_400(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(cliente=""))
        assert resp.status_code == 400

    def test_sem_modelo_retorna_400(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(modelo=""))
        assert resp.status_code == 400

    def test_sem_tecnico_retorna_400(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(tecnico=""))
        assert resp.status_code == 400

    def test_sem_reparo_ids_retorna_400(self, client, login_como, usuario_tecnico, payload_os_valido):
        login_como(client, usuario_tecnico)
        resp = client.post("/api/ordens", json=payload_os_valido(reparo_ids=[]))
        assert resp.status_code == 400


# ============================================================================
# POST /api/ordens — dependências (reparo, vendedor, técnico, peças)
# ============================================================================


class TestCriarOrdemDependencias:
    def test_reparo_id_inexistente_retorna_400_e_nao_cria_os(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        total_antes = self._contar_os()

        resp = client.post("/api/ordens", json=payload_os_valido(reparo_ids=[9_999_999]))

        assert resp.status_code == 400
        assert self._contar_os() == total_antes

    def test_vendedor_invalido_retorna_400_quando_cliente_nao_e_ir_phones(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)

        resp = client.post(
            "/api/ordens", json=payload_os_valido(cliente="Cliente Comum", vendedor="Vendedor Inexistente")
        )

        assert resp.status_code == 400

    def test_vendedor_invalido_rejeitado_mesmo_com_cliente_ir_phones(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        """ADR-014: a exceção que pulava vendedor_valido() para o cliente 'IR Phones' foi removida."""
        login_como(client, usuario_tecnico)

        resp = client.post(
            "/api/ordens", json=payload_os_valido(cliente="IR Phones", vendedor="Vendedor Que Nao Existe")
        )

        assert resp.status_code == 400

    def test_tecnico_fora_da_lista_canonica_e_aceito(self, client, login_como, usuario_tecnico, payload_os_valido):
        """
        Diferente de vendedor, técnico não é validado contra a lista TECNICOS
        (fluxoly_reference_data.py) — só precisa ser não-vazio.
        """
        login_como(client, usuario_tecnico)

        resp = client.post("/api/ordens", json=payload_os_valido(tecnico="Técnico Fora Da Lista Canonica"))

        assert resp.status_code == 201
        os_id = resp.get_json()["os_id"]
        assert _obter_os_no_banco(os_id)[3] == "Técnico Fora Da Lista Canonica"
        _limpar_os(os_id)

    def test_peca_inexistente_retorna_400_e_nao_cria_os(
        self, client, login_como, usuario_tecnico, payload_os_valido
    ):
        login_como(client, usuario_tecnico)
        total_antes = self._contar_os()

        resp = client.post("/api/ordens", json=payload_os_valido(pecas_ids=[9_999_999]))

        assert resp.status_code == 400
        assert self._contar_os() == total_antes

    def test_peca_incompativel_com_modelo_retorna_400(
        self, client, login_como, usuario_tecnico, payload_os_valido, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(modelo="iPhone 8", quantidade=3)
        total_antes = self._contar_os()

        resp = client.post("/api/ordens", json=payload_os_valido(modelo="iPhone 13", pecas_ids=[item_id]))

        assert resp.status_code == 400
        assert self._contar_os() == total_antes

    def test_peca_sem_estoque_retorna_400(
        self, client, login_como, usuario_tecnico, payload_os_valido, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(modelo="iPhone 13", quantidade=0)

        resp = client.post("/api/ordens", json=payload_os_valido(modelo="iPhone 13", pecas_ids=[item_id]))

        assert resp.status_code == 400

    def test_peca_compativel_e_consumida_do_estoque(
        self, client, login_como, usuario_tecnico, payload_os_valido, criar_item_estoque
    ):
        login_como(client, usuario_tecnico)
        item_id = criar_item_estoque(modelo="iPhone 13", quantidade=3, valor=80.0)

        resp = client.post("/api/ordens", json=payload_os_valido(modelo="iPhone 13", pecas_ids=[item_id]))

        assert resp.status_code == 201
        os_id = resp.get_json()["os_id"]

        conn = _app.conectar()
        try:
            quantidade_restante = conn.execute("SELECT quantidade FROM estoque WHERE id=?", (item_id,)).fetchone()[0]
            custo_pecas = conn.execute("SELECT custo_pecas FROM os WHERE id=?", (os_id,)).fetchone()[0]
        finally:
            conn.close()
        assert quantidade_restante == 2
        assert custo_pecas == 80.0
        _limpar_os(os_id)

    @staticmethod
    def _contar_os():
        conn = _app.conectar()
        try:
            return conn.execute("SELECT COUNT(*) FROM os").fetchone()[0]
        finally:
            conn.close()


class TestCriarOrdemSemSessao:
    def test_sem_sessao_retorna_401(self, client, payload_os_valido):
        resp = client.post("/api/ordens", json=payload_os_valido())
        assert resp.status_code == 401


# ============================================================================
# GET /api/ordens — listagem e filtros
# ============================================================================


class TestListarOrdens:
    def test_sem_sessao_retorna_401(self, client):
        resp = client.get("/api/ordens")
        assert resp.status_code == 401

    def test_listar_inclui_os_criada(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(cliente="Cliente Listagem Unico")

        resp = client.get("/api/ordens")

        assert resp.status_code == 200
        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_id in ids

    def test_totais_abertas_e_finalizadas_no_payload(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        criar_os(status="Em andamento")
        criar_os(status="Finalizado")

        body = client.get("/api/ordens").get_json()

        assert body["total"] >= 2
        assert body["abertas"] >= 1
        assert body["finalizadas"] >= 1

    def test_filtro_por_status(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        os_finalizada = criar_os(cliente=marcador, status="Finalizado")
        os_andamento = criar_os(cliente=marcador, status="Em andamento")

        resp = client.get("/api/ordens", query_string={"status": "Finalizado", "q": marcador})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_finalizada in ids
        assert os_andamento not in ids

    def test_filtro_por_tecnico(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        os_alvo = criar_os(cliente=marcador, tecnico="RUAM SOARES")
        os_outro = criar_os(cliente=marcador, tecnico="ISAQUE SOUZA")

        resp = client.get("/api/ordens", query_string={"tecnico": "RUAM SOARES", "q": marcador})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_alvo in ids
        assert os_outro not in ids

    def test_filtro_por_vendedor(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        os_alvo = criar_os(cliente=marcador, vendedor="Kauany")
        os_outro = criar_os(cliente=marcador, vendedor="Camila")

        resp = client.get("/api/ordens", query_string={"vendedor": "Kauany", "q": marcador})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_alvo in ids
        assert os_outro not in ids

    def test_filtro_por_modelo(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        os_alvo = criar_os(cliente=marcador, modelo="iPhone 15")
        os_outro = criar_os(cliente=marcador, modelo="iPhone 11")

        resp = client.get("/api/ordens", query_string={"modelo": "iPhone 15", "q": marcador})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_alvo in ids
        assert os_outro not in ids

    def test_filtro_por_tipo(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        os_alvo = criar_os(cliente=marcador, tipo="Garantia")
        os_outro = criar_os(cliente=marcador, tipo="Assistencia")

        resp = client.get("/api/ordens", query_string={"tipo": "Garantia", "q": marcador})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_alvo in ids
        assert os_outro not in ids

    def test_filtro_texto_busca_por_cliente(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"BuscaUnica{uuid.uuid4().hex[:8]}"
        os_alvo = criar_os(cliente=marcador)

        resp = client.get("/api/ordens", query_string={"q": marcador.lower()})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_alvo in ids

    def test_filtro_data_ini_data_fim(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        os_antiga = criar_os(cliente=marcador, data="2020-01-01")
        os_recente = criar_os(cliente=marcador, data="2030-01-01")

        resp = client.get(
            "/api/ordens", query_string={"q": marcador, "data_ini": "2025-01-01", "data_fim": "2035-01-01"}
        )

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_recente in ids
        assert os_antiga not in ids

    def test_sem_filtros_nao_ha_paginacao_retorna_todas_de_uma_vez(self, client, login_como, usuario_tecnico, criar_os):
        """
        GET /api/ordens não aceita page/per_page — busca a tabela inteira e
        filtra em memória (KI-005/TD-09: sem paginação, ver PROJECT_STATUS.md).
        """
        login_como(client, usuario_tecnico)
        marcador = f"Cliente {uuid.uuid4().hex[:8]}"
        for _ in range(3):
            criar_os(cliente=marcador)

        resp = client.get("/api/ordens", query_string={"q": marcador, "page": "1", "per_page": "1"})

        assert len([o for o in resp.get_json()["ordens"] if o["cliente"] == marcador]) == 3


# ============================================================================
# GET /api/ordens/<id> — obter por id
# ============================================================================


class TestObterOrdem:
    def test_sem_sessao_retorna_401(self, client, criar_os):
        os_id = criar_os()
        resp = client.get(f"/api/ordens/{os_id}")
        assert resp.status_code == 401

    def test_obter_inexistente_retorna_404(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/ordens/9999999")
        assert resp.status_code == 404

    def test_obter_por_id_retorna_dados_completos(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os(cliente="Cliente Detalhe", tecnico="RUAM SOARES", modelo="iPhone 14")

        resp = client.get(f"/api/ordens/{os_id}")

        assert resp.status_code == 200
        ordem = resp.get_json()["ordem"]
        assert ordem["id"] == os_id
        assert ordem["cliente"] == "Cliente Detalhe"
        assert ordem["tecnico"] == "RUAM SOARES"
        assert ordem["modelo"] == "iPhone 14"
        assert ordem["pecas_usadas"] == []


# ============================================================================
# GET /api/ordens/historico-cliente
# ============================================================================


class TestHistoricoCliente:
    def test_sem_sessao_retorna_401(self, client):
        resp = client.get("/api/ordens/historico-cliente", query_string={"cliente": "Alguem"})
        assert resp.status_code == 401

    def test_sem_cliente_retorna_lista_vazia(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/ordens/historico-cliente")
        assert resp.status_code == 200
        assert resp.get_json()["ordens"] == []

    def test_retorna_ordens_do_mesmo_cliente(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        cliente = f"Cliente Historico {uuid.uuid4().hex[:8]}"
        os_1 = criar_os(cliente=cliente)
        os_2 = criar_os(cliente=cliente)

        resp = client.get("/api/ordens/historico-cliente", query_string={"cliente": cliente})

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert {os_1, os_2} <= ids

    def test_exclui_id_informado(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        cliente = f"Cliente Historico {uuid.uuid4().hex[:8]}"
        os_1 = criar_os(cliente=cliente)
        os_2 = criar_os(cliente=cliente)

        resp = client.get(
            "/api/ordens/historico-cliente", query_string={"cliente": cliente, "excluir_id": os_2}
        )

        ids = {o["id"] for o in resp.get_json()["ordens"]}
        assert os_1 in ids
        assert os_2 not in ids
