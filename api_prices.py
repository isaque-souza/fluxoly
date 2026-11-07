"""
Fluxoly - API Blueprint (Tabelas de Preço)
Rotas /api/precos* -- consumidas pelo frontend React (Precos.jsx, Vendas.jsx).
Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 4º domínio extraído).
"""

from flask import Blueprint, request

from fluxoly_api_helpers import err, ok, usuario_admin, usuario_logado
from fluxoly_price_tables import sugerir_preco_tabela
from fluxoly_validation import parse_float, safe_json


def create_api_prices_blueprint(deps):
    api_prices = Blueprint("api_prices", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    carregar_tabelas_preco = deps["carregar_tabelas_preco"]
    salvar_tabelas_preco = deps["salvar_tabelas_preco"]

    @api_prices.route("/precos")
    def listar_precos():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        return ok(tabelas=carregar_tabelas_preco())

    @api_prices.route("/precos", methods=["POST"])
    def salvar_preco():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        tabela = (body.get("tabela") or "").strip()
        servico = (body.get("servico") or "").strip().upper()
        modelo = (body.get("modelo") or "").strip()
        valor = parse_float(body.get("valor"), default=-1.0)

        if tabela != "clientes":
            return err("Tabela inválida.")
        if not servico or not modelo or valor is None or valor < 0:
            return err("Preencha serviço, modelo e valor.")

        tabelas = carregar_tabelas_preco()
        tabelas.setdefault(tabela, {}).setdefault(servico, {})[modelo] = valor
        salvar_tabelas_preco(tabelas)
        return ok()

    @api_prices.route("/precos/excluir", methods=["POST"])
    def excluir_preco():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        tabela = (body.get("tabela") or "").strip()
        servico = (body.get("servico") or "").strip()
        modelo = (body.get("modelo") or "").strip()

        if tabela != "clientes":
            return err("Tabela inválida.")

        tabelas = carregar_tabelas_preco()
        if tabela in tabelas and servico in tabelas[tabela] and modelo in tabelas[tabela][servico]:
            del tabelas[tabela][servico][modelo]
            if not tabelas[tabela][servico]:
                del tabelas[tabela][servico]
            salvar_tabelas_preco(tabelas)
            return ok()

        return err("Entrada não encontrada.", 404)

    @api_prices.route("/precos/sugerir")
    def sugerir_preco():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        modelo = (request.args.get("modelo") or "").strip()
        tabela = (request.args.get("tabela") or "clientes").strip()
        reparo_ids_raw = (request.args.get("reparo_ids") or "").strip()

        if not modelo or not reparo_ids_raw:
            return ok(valor=0, encontrado=False)

        reparo_ids = [int(x) for x in reparo_ids_raw.split(",") if x.strip().isdigit()]
        if not reparo_ids:
            return ok(valor=0, encontrado=False)

        if tabela != "clientes":
            tabela = "clientes"

        conn = conectar()
        cursor = conn.cursor()
        placeholders = ",".join("?" * len(reparo_ids))
        cursor.execute(f"SELECT nome FROM reparos WHERE id IN ({placeholders})", reparo_ids)
        nomes = [r[0].upper() for r in cursor.fetchall()]
        conn.close()

        tabelas = carregar_tabelas_preco()
        total, encontrou = sugerir_preco_tabela(tabelas, tabela, modelo, nomes)
        return ok(valor=round(total, 2), encontrado=encontrou)

    return api_prices
