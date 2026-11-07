"""
Testes de tabela de preços (Sprint 2 — Restante).

Escopo: lógica pura de sugestão de preço (`fluxoly_price_tables.py`) e o endpoint
GET /api/precos/sugerir, mais os endpoints administrativos GET/POST /api/precos e
POST /api/precos/excluir.

Divide-se em duas frentes, seguindo `ENGINEERING_GUIDE.md` (testar regra de negócio pura
sem subir servidor sempre que possível):
- Testes unitários diretos de `fluxoly_price_tables.py` — sem Flask, sem banco.
- Testes de integração via `client` — confirmam autenticação, autorização e o contrato
  HTTP da rota, não repetem a cobertura de regra já feita nos testes unitários.
"""

import json
import uuid

import app as _app
from fluxoly_price_tables import (
    carregar_tabelas_preco,
    encontrar_servico_tabela,
    salvar_tabelas_preco,
    sugerir_preco_tabela,
    tabelas_preco_vazias,
)

# ============================================================================
# Unitários — fluxoly_price_tables.py
# ============================================================================


class TestTabelasPrecoVazias:
    def test_estrutura_padrao_tem_so_a_tabela_clientes(self):
        """ADR-014: a tabela interna `ir_phones` foi removida."""
        vazio = tabelas_preco_vazias()
        assert vazio == {"clientes": {}}

    def test_tabela_ir_phones_legada_no_arquivo_e_descartada_na_leitura(self, tmp_path):
        caminho = tmp_path / "precos.json"
        bruto = {"clientes": {}, "ir_phones": {"TROCA DE TELA": {"iPhone 13": 100.0}}}
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(bruto, f)

        assert "ir_phones" not in carregar_tabelas_preco(str(caminho))


class TestCarregarTabelasPreco:
    def test_arquivo_inexistente_retorna_estrutura_vazia(self, tmp_path):
        caminho = tmp_path / "nao_existe.json"
        assert carregar_tabelas_preco(str(caminho)) == tabelas_preco_vazias()

    def test_arquivo_com_json_invalido_retorna_estrutura_vazia(self, tmp_path):
        caminho = tmp_path / "corrompido.json"
        caminho.write_text("{nao e json valido", encoding="utf-8")
        assert carregar_tabelas_preco(str(caminho)) == tabelas_preco_vazias()

    def test_round_trip_salvar_e_carregar_preserva_valor(self, tmp_path):
        caminho = tmp_path / "precos.json"
        tabelas = {"clientes": {"TROCA DE TELA": {"iPhone 13": 350.0}}}

        salvar_tabelas_preco(str(caminho), tabelas)
        carregado = carregar_tabelas_preco(str(caminho))

        assert carregado["clientes"]["TROCA DE TELA"]["iPhone 13"] == 350.0

    def test_carregar_normaliza_modelo_e_servico(self, tmp_path):
        caminho = tmp_path / "precos.json"
        # servico em minusculo, modelo com variacao de escrita — devem ser normalizados na leitura
        bruto = {"clientes": {"troca de tela": {"iphone 13 pro max": 450.0}}}
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(bruto, f)

        carregado = carregar_tabelas_preco(str(caminho))

        assert carregado["clientes"]["TROCA DE TELA"]["iPhone 13 Pro Max"] == 450.0


class TestSugerirPrecoTabela:
    def test_encontra_preco_para_modelo_e_reparo_exatos(self):
        tabelas = {"clientes": {"TROCA DE TELA": {"iPhone 13": 350.0}}}

        total, encontrou = sugerir_preco_tabela(tabelas, "clientes", "iPhone 13", ["Troca de Tela"])

        assert encontrou is True
        assert total == 350.0

    def test_modelo_sem_entrada_na_tabela_nao_encontra(self):
        tabelas = {"clientes": {"TROCA DE TELA": {"iPhone 13": 350.0}}}

        total, encontrou = sugerir_preco_tabela(tabelas, "clientes", "iPhone 15 Pro Max", ["Troca de Tela"])

        assert encontrou is False
        assert total == 0.0

    def test_soma_multiplos_reparos_do_mesmo_orcamento(self):
        tabelas = {
            "clientes": {
                "TROCA DE TELA": {"iPhone 13": 350.0},
                "TROCA DE BATERIA": {"iPhone 13": 120.0},
            }
        }

        total, encontrou = sugerir_preco_tabela(
            tabelas, "clientes", "iPhone 13", ["Troca de Tela", "Troca de Bateria"]
        )

        assert encontrou is True
        assert total == 470.0

    def test_reparo_que_resolve_para_o_mesmo_servico_nao_e_somado_duas_vezes(self):
        # "Troca de Tela" e "Tela" devem resolver para o mesmo servico cadastrado —
        # sugerir_preco_tabela usa `servicos_usados` para nao contar o mesmo servico 2x.
        tabelas = {"clientes": {"TROCA DE TELA": {"iPhone 13": 350.0}}}

        total, encontrou = sugerir_preco_tabela(tabelas, "clientes", "iPhone 13", ["Troca de Tela", "Tela"])

        assert encontrou is True
        assert total == 350.0

    def test_tabela_ausente_no_dicionario_de_tabelas_nao_quebra(self):
        total, encontrou = sugerir_preco_tabela({}, "clientes", "iPhone 13", ["Troca de Tela"])

        assert encontrou is False
        assert total == 0.0

    def test_modelo_vazio_nao_encontra(self):
        tabelas = {"clientes": {"TROCA DE TELA": {"iPhone 13": 350.0}}}

        total, encontrou = sugerir_preco_tabela(tabelas, "clientes", "", ["Troca de Tela"])

        assert encontrou is False
        assert total == 0.0


class TestEncontrarServicoTabela:
    def test_correspondencia_exata_apos_normalizacao(self):
        tabela = {"BATERIA": {"IPHONE 13": 120.0}}

        assert encontrar_servico_tabela("Bateria", tabela) == "BATERIA"

    def test_correspondencia_por_candidato_derivado_do_nome_do_reparo(self):
        # "Troca de Bateria" nao bate literal com "BATERIA", mas o candidato derivado bate
        tabela = {"BATERIA": {"IPHONE 13": 120.0}}

        assert encontrar_servico_tabela("Troca de Bateria", tabela) == "BATERIA"

    def test_sem_correspondencia_retorna_vazio(self):
        tabela = {"BATERIA": {"IPHONE 13": 120.0}}

        assert encontrar_servico_tabela("Troca de Placa Mae", tabela) == ""

    def test_nome_reparo_vazio_retorna_vazio(self):
        tabela = {"BATERIA": {"IPHONE 13": 120.0}}

        assert encontrar_servico_tabela("", tabela) == ""

    def test_tabela_nao_dict_retorna_vazio(self):
        assert encontrar_servico_tabela("Bateria", None) == ""


# ============================================================================
# Integração — /api/precos*
# ============================================================================


def _limpar_preco(client, tabela, servico, modelo):
    client.post("/api/precos/excluir", json={"tabela": tabela, "servico": servico, "modelo": modelo})


class TestGetPrecosSugerir:
    def test_sem_autenticacao_retorna_401(self, client):
        resp = client.get("/api/precos/sugerir?modelo=iPhone+13&reparo_ids=1")
        assert resp.status_code == 401

    def test_sem_modelo_retorna_nao_encontrado_sem_erro(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/precos/sugerir?reparo_ids=1")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["encontrado"] is False
        assert body["valor"] == 0

    def test_sem_reparo_ids_retorna_nao_encontrado_sem_erro(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/precos/sugerir?modelo=iPhone+13")

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["encontrado"] is False
        assert body["valor"] == 0

    def test_reparo_ids_nao_numericos_sao_ignorados_sem_erro_500(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)

        resp = client.get("/api/precos/sugerir?modelo=iPhone+13&reparo_ids=abc,def")

        assert resp.status_code == 200
        assert resp.get_json()["encontrado"] is False

    def test_tabela_desconhecida_cai_para_clientes(
        self, client, login_como, usuario_admin, usuario_tecnico, reparo_padrao_id
    ):
        login_como(client, usuario_admin)
        modelo = f"iPhone Teste {uuid.uuid4().hex[:6]}"
        # descobre o nome real do reparo seed para casar com o servico salvo
        conn = _app.conectar()
        nome_reparo = conn.execute("SELECT nome FROM reparos WHERE id=?", (reparo_padrao_id,)).fetchone()[0]
        conn.close()

        client.post(
            "/api/precos",
            json={"tabela": "clientes", "servico": nome_reparo, "modelo": modelo, "valor": 199.0},
        )
        login_como(client, usuario_tecnico)

        resp = client.get(
            f"/api/precos/sugerir?modelo={modelo}&reparo_ids={reparo_padrao_id}&tabela=inexistente"
        )

        assert resp.status_code == 200
        body = resp.get_json()
        assert body["encontrado"] is True
        assert body["valor"] == 199.0

        _limpar_preco(client, "clientes", nome_reparo.upper(), modelo)


class TestPrecosAdmin:
    def test_listar_precos_exige_admin(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.get("/api/precos")
        assert resp.status_code == 403

    def test_listar_precos_sem_autenticacao_retorna_403(self, client):
        # usuario_logado() falso -> cai direto no "acesso negado", nao 401 (comportamento real da rota)
        resp = client.get("/api/precos")
        assert resp.status_code == 403

    def test_salvar_preco_exige_admin(self, client, login_como, usuario_tecnico):
        login_como(client, usuario_tecnico)
        resp = client.post(
            "/api/precos", json={"tabela": "clientes", "servico": "Bateria", "modelo": "iPhone 13", "valor": 1}
        )
        assert resp.status_code == 403

    def test_salvar_preco_com_tabela_invalida_e_rejeitado(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/precos",
            json={"tabela": "tabela_que_nao_existe", "servico": "Bateria", "modelo": "iPhone 13", "valor": 1},
        )
        assert resp.status_code == 400

    def test_salvar_e_excluir_preco_round_trip(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        modelo = f"iPhone Teste {uuid.uuid4().hex[:6]}"

        criar = client.post(
            "/api/precos",
            json={"tabela": "clientes", "servico": "Bateria Teste", "modelo": modelo, "valor": 77.0},
        )
        assert criar.status_code == 200

        listar = client.get("/api/precos")
        assert listar.get_json()["tabelas"]["clientes"]["BATERIA TESTE"][modelo] == 77.0

        excluir = client.post(
            "/api/precos/excluir", json={"tabela": "clientes", "servico": "BATERIA TESTE", "modelo": modelo}
        )
        assert excluir.status_code == 200

    def test_excluir_preco_inexistente_retorna_404(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/precos/excluir",
            json={"tabela": "clientes", "servico": "NAO EXISTE", "modelo": "Nao Existe"},
        )
        assert resp.status_code == 404


class TestTabelaIrPhonesRemovida:
    """ADR-014: a tabela de preço interna `ir_phones` deixou de existir."""

    def test_salvar_na_tabela_ir_phones_retorna_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/precos",
            json={"tabela": "ir_phones", "servico": "TROCA DE TELA", "modelo": "iPhone 13", "valor": 100.0},
        )
        assert resp.status_code == 400

    def test_excluir_da_tabela_ir_phones_retorna_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post(
            "/api/precos/excluir",
            json={"tabela": "ir_phones", "servico": "TROCA DE TELA", "modelo": "iPhone 13"},
        )
        assert resp.status_code == 400


class TestRelatorioIrPhonesRemovido:
    """ADR-014: o relatório mensal IR Phones (JSON e PDF) foi removido."""

    def test_rotas_do_relatorio_ir_phones_nao_existem(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        for rota in ("/api/relatorios/ir-phones", "/api/relatorios/pdf/ir-phones", "/relatorios/pdf/ir-phones"):
            assert client.get(rota).status_code == 404, rota
