"""
fluxoly_unidades_serializadas_controller.py

Camada HTTP do domínio `unidades_serializadas` (Blueprint Flask, prefixo
`/api/unidades-serializadas`). Recebe request, valida forma do payload,
chama o service, formata resposta — nunca contém regra de negócio nem
acessa o banco diretamente (`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Mesmo contrato de resposta do resto da API (`{"ok": ...}` /
`{"ok": false, "erro": ...}`), mesma justificativa de
`fluxoly_clientes_controller.py`.
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_compras_aparelhos_service as compras_aparelhos_service
import fluxoly_unidades_serializadas_service as service
from fluxoly_validation import parse_int, safe_json


def create_unidades_serializadas_blueprint(deps: dict):
    conectar = deps["conectar"]

    unidades_serializadas_api = Blueprint(
        "unidades_serializadas_api", __name__, url_prefix="/api/unidades-serializadas"
    )

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def perfil_pode_escrever():
        return session.get("usuario_perfil") in ("admin", "tecnico")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @unidades_serializadas_api.route("")
    def listar_unidades():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        # "q" é o nome novo (C1.3.3, busca combinada); "imei" segue aceito por
        # compatibilidade — ambos alimentam a mesma busca combinada no service.
        termo = (request.args.get("q") or request.args.get("imei") or "").strip()
        estoque_id = parse_int(request.args.get("estoque_id"), default=None)
        produto_id = parse_int(request.args.get("produto_id"), default=None)
        origem = (request.args.get("origem") or "").strip() or None
        status = (request.args.get("status") or "").strip()
        saude_bateria_faixa = (request.args.get("saude_bateria_faixa") or "").strip()
        localizacao = (request.args.get("localizacao") or "").strip()
        sort = (request.args.get("sort") or "recente").strip()
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_unidades(
            conectar, termo, estoque_id, produto_id, origem, status,
            saude_bateria_faixa, localizacao, sort, page, per_page,
        )
        return ok(**resultado)

    @unidades_serializadas_api.route("/<int:unidade_id>")
    def obter_unidade(unidade_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        unidade = service.obter_unidade(conectar, unidade_id)
        if not unidade:
            return err("Unidade não encontrada.", 404)
        # BR-092 -- custo do aparelho comprado, só para admin/financeiro (mesmo critério de BR-047).
        if session.get("usuario_perfil") in ("admin", "financeiro"):
            unidade["custo_aparelho"] = compras_aparelhos_service.obter_custo_aparelho(conectar, unidade_id)
        return ok(unidade=unidade)

    @unidades_serializadas_api.route("", methods=["POST"])
    def criar_unidade():
        if not usuario_logado() or not perfil_pode_escrever():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        estoque_id = parse_int(body.get("estoque_id"), default=None)
        produto_id = parse_int(body.get("produto_id"), default=None)
        unidade_id, erro = service.criar_unidade(
            conectar,
            session.get("usuario_id"),
            estoque_id,
            produto_id,
            body.get("imei"),
            body.get("lote_id"),
        )
        if erro:
            code = 404 if erro in ("Item de estoque não encontrado.", "Produto não encontrado.") else 400
            return err(erro, code)
        return ok(id=unidade_id)

    @unidades_serializadas_api.route("/<int:unidade_id>/historico")
    def obter_historico(unidade_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        unidade = service.obter_unidade(conectar, unidade_id)
        if not unidade:
            return err("Unidade não encontrada.", 404)
        return ok(historico=service.obter_historico(conectar, unidade_id))

    @unidades_serializadas_api.route("/<int:unidade_id>/status", methods=["PATCH"])
    def atualizar_status(unidade_id):
        if not usuario_logado() or not perfil_pode_escrever():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        novo_status = (body.get("status") or "").strip()
        sucesso, erro = service.transicionar_status(conectar, session.get("usuario_id"), unidade_id, novo_status)
        if not sucesso:
            code = 404 if erro == "Unidade não encontrada." else 400
            return err(erro, code)
        return ok(id=unidade_id, status=novo_status)

    @unidades_serializadas_api.route("/<int:unidade_id>", methods=["PATCH"])
    def atualizar_unidade(unidade_id):
        if not usuario_logado() or not perfil_pode_escrever():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        campos_bloqueados_enviados = service.CAMPOS_BLOQUEADOS & set(body.keys())
        if campos_bloqueados_enviados:
            return err(
                f"Campo(s) não editável(is) por esta rota: {', '.join(sorted(campos_bloqueados_enviados))}. "
                "Origem é fixa após o cadastro; status usa PATCH /<id>/status."
            )

        sucesso, erro = service.atualizar_campos(
            conectar, session.get("usuario_id"), unidade_id,
            body.get("localizacao"), body.get("saude_bateria"),
        )
        if not sucesso:
            code = 404 if erro == "Unidade não encontrada." else 400
            return err(erro, code)
        return ok(id=unidade_id)

    return unidades_serializadas_api
