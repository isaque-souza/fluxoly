"""
fluxoly_tipos_garantia_controller.py

Camada HTTP do cadastro Tipos de Garantia (Blueprint Flask, prefixo
`/api/tipos-garantia`). Recebe request, valida forma do payload, chama o
service, formata resposta -- nunca contém regra de negócio nem acessa o
banco diretamente (`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Módulo compartilhado entre Vendas (Garantia de Venda) e Assistência
(Garantia de Reparo, `fluxoly_os.py`) -- não pertence a nenhum dos dois
domínios, por isso nasce como blueprint próprio (ADR-008, prefixo
`fluxoly_`, `PLAN-V1.5-Garantia.md`).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_tipos_garantia_service as service
from fluxoly_validation import parse_int, safe_json


def create_tipos_garantia_blueprint(deps: dict):
    conectar = deps["conectar"]

    tipos_garantia_api = Blueprint("tipos_garantia_api", __name__, url_prefix="/api/tipos-garantia")

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def usuario_admin():
        return session.get("usuario_perfil") == "admin"

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @tipos_garantia_api.route("")
    def listar_tipos_garantia():
        """Lista aberta a qualquer autenticado -- popula o select nas telas
        de Nova Venda e conclusão de OS (BR-055). `incluir_inativos` só tem
        efeito para `admin` (tela de cadastro) -- qualquer outro perfil
        sempre vê só os tipos ativos, mesmo que envie o parâmetro."""
        if not usuario_logado():
            return err("Não autenticado.", 401)

        incluir_inativos = usuario_admin() and (request.args.get("incluir_inativos") or "").strip() in (
            "1", "true",
        )
        return ok(items=service.listar_tipos_garantia(conectar, incluir_inativos))

    @tipos_garantia_api.route("", methods=["POST"])
    def criar_tipo_garantia():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_admin():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        duracao_meses = parse_int(body.get("duracao_meses"), default=None)
        tipo_garantia_id, erro = service.criar_tipo_garantia(
            conectar, body.get("nome"), duracao_meses, body.get("texto") or ""
        )
        if erro:
            return err(erro)
        return ok(id=tipo_garantia_id), 201

    @tipos_garantia_api.route("/<int:tipo_garantia_id>", methods=["PUT"])
    def atualizar_tipo_garantia(tipo_garantia_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if not usuario_admin():
            return err("Permissão negada.", 403)

        body = safe_json(request)
        duracao_meses = parse_int(body.get("duracao_meses"), default=None)
        ativo = bool(body.get("ativo", True))
        sucesso, erro = service.atualizar_tipo_garantia(
            conectar, tipo_garantia_id, body.get("nome"), duracao_meses, ativo, body.get("texto")
        )
        if not sucesso:
            code = 404 if erro == "Tipo de Garantia não encontrado." else 400
            return err(erro, code)
        return ok(id=tipo_garantia_id)

    return tipos_garantia_api
