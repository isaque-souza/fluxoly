"""
fluxoly_termos_garantia_controller.py

Camada HTTP do cadastro Termos de Garantia (Blueprint Flask, prefixo
`/api/termos-garantia`, BR-105). Só valida a forma do payload e chama o
service (`docs/engineering/ENGINEERING_GUIDE.md` §3.1). Mesmo formato de
`fluxoly_tipos_garantia_controller.py`.
"""

from flask import Blueprint, request

import fluxoly_termos_garantia_service as service
from fluxoly_api_helpers import err, ok, usuario_admin, usuario_logado
from fluxoly_validation import safe_json


def create_termos_garantia_blueprint(deps: dict):
    conectar = deps["conectar"]

    termos_garantia_api = Blueprint("termos_garantia_api", __name__, url_prefix="/api/termos-garantia")

    @termos_garantia_api.route("")
    def listar_termos_garantia():
        """Aberta a qualquer autenticado: popula o select na conclusão da OS.
        `incluir_inativos` só tem efeito para `admin` (tela de cadastro)."""
        if not usuario_logado():
            return err("Não autenticado.", 401)
        incluir_inativos = usuario_admin() and (request.args.get("incluir_inativos") or "").strip() in (
            "1",
            "true",
        )
        return ok(items=service.listar_termos_garantia(conectar, incluir_inativos))

    @termos_garantia_api.route("", methods=["POST"])
    def criar_termo_garantia():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_admin():
            return err("Permissão negada.", 403)
        body = safe_json(request)
        termo_id, erro = service.criar_termo_garantia(conectar, body.get("nome"), body.get("texto"))
        if erro:
            return err(erro)
        return ok(id=termo_id), 201

    @termos_garantia_api.route("/<int:termo_id>", methods=["PUT"])
    def atualizar_termo_garantia(termo_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_admin():
            return err("Permissão negada.", 403)
        body = safe_json(request)
        sucesso, erro = service.atualizar_termo_garantia(
            conectar, termo_id, body.get("nome"), body.get("texto"), bool(body.get("ativo", True))
        )
        if not sucesso:
            return err(erro, 404 if erro == service.TERMO_NAO_ENCONTRADO else 400)
        return ok(id=termo_id)

    return termos_garantia_api
