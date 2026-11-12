"""
fluxoly_auditoria_controller.py

Camada HTTP da tela de Auditoria (prefixo `/api/auditoria`,
`docs/engineering/plans/PLAN-tela-auditoria.md`). Só GET: não existe rota
para editar ou apagar log. Acesso restrito a admin/financeiro -- mesmo
conjunto de `usuario_pode_financeiro()` de Vendas (TD-14).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_auditoria_service as service
from fluxoly_validation import parse_int

PERFIS_AUDITORIA = ("admin", "financeiro")


def create_auditoria_blueprint(deps: dict):
    conectar = deps["conectar"]

    auditoria_api = Blueprint("auditoria_api", __name__, url_prefix="/api/auditoria")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    @auditoria_api.route("")
    def listar_auditoria():
        if not session.get("usuario_id"):
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in PERFIS_AUDITORIA:
            return err("Permissão negada.", 403)

        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=50)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado, erro = service.listar_auditoria(
            conectar,
            entidade=(request.args.get("entidade") or "").strip() or None,
            entidade_id=parse_int(request.args.get("entidade_id"), default=None),
            usuario_id=parse_int(request.args.get("usuario_id"), default=None),
            acao=(request.args.get("acao") or "").strip() or None,
            data_inicio=(request.args.get("data_inicio") or "").strip() or None,
            data_fim=(request.args.get("data_fim") or "").strip() or None,
            page=page,
            per_page=per_page,
        )
        if erro:
            return err(erro)
        return jsonify({"ok": True, **resultado})

    return auditoria_api
