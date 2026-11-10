"""
fluxoly_dados_loja_controller.py

Camada HTTP do domínio Dados da Loja (BR-094), prefixo `/api/dados-loja`.
Leitura para qualquer usuário autenticado (os documentos da OS dependem dos
dados); escrita só para `admin`. Sem regra de negócio nem SQL aqui
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_dados_loja_service as service
from fluxoly_validation import safe_json


def create_dados_loja_blueprint(deps: dict):
    conectar = deps["conectar"]

    dados_loja_api = Blueprint("dados_loja_api", __name__, url_prefix="/api/dados-loja")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    @dados_loja_api.route("")
    def obter_dados_loja():
        if not session.get("usuario_id"):
            return err("Não autenticado.", 401)
        return jsonify({"ok": True, "dados_loja": service.obter_dados_loja(conectar)})

    @dados_loja_api.route("", methods=["PUT"])
    def salvar_dados_loja():
        if not session.get("usuario_id"):
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") != "admin":
            return err("Acesso negado.", 403)

        dados, erro = service.salvar_dados_loja(conectar, session.get("usuario_id"), safe_json(request))
        if erro:
            return err(erro)
        return jsonify({"ok": True, "dados_loja": dados})

    return dados_loja_api
