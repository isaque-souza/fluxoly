"""
fluxoly_compras_aparelhos_controller.py

Camada HTTP do domínio Compra de Aparelhos (Blueprint Flask, prefixo
`/api/compras-aparelhos`). Recebe request, valida forma do payload, chama o
service, formata resposta -- nunca contém regra de negócio nem acessa o banco
diretamente (ENGINEERING_GUIDE.md §3.1).

Perfis (BR-089): `admin`, `financeiro` e `vendedor` -- em todas as rotas,
inclusive leitura, porque a compra carrega nome/telefone de quem vendeu o
aparelho (dado pessoal, BR-088).
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_compras_aparelhos_service as service
from fluxoly_validation import parse_float, parse_int, safe_json

PERFIS_PERMITIDOS = ("admin", "financeiro", "vendedor")


def create_compras_aparelhos_blueprint(deps: dict):
    conectar = deps["conectar"]

    compras_api = Blueprint("compras_aparelhos_api", __name__, url_prefix="/api/compras-aparelhos")

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    def _negar_se_sem_permissao():
        if not session.get("usuario_id"):
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in PERFIS_PERMITIDOS:
            return err("Permissão negada.", 403)
        return None

    @compras_api.route("")
    def listar_compras():
        negado = _negar_se_sem_permissao()
        if negado:
            return negado

        data_fim = (request.args.get("data_fim") or "").strip() or None
        # Mesmo ajuste de Vendas: data sem hora vira limite de fim de dia.
        if data_fim and len(data_fim) == 10:
            data_fim = f"{data_fim} 23:59:59"
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")

        resultado = service.listar_compras(
            conectar,
            origem=(request.args.get("origem") or "").strip().lower() or None,
            status=(request.args.get("status") or "").strip().lower() or None,
            data_inicio=(request.args.get("data_inicio") or "").strip() or None,
            data_fim=data_fim,
            termo=(request.args.get("q") or "").strip(),
            page=page,
            per_page=min(per_page, 100),
        )
        return ok(**resultado)

    @compras_api.route("", methods=["POST"])
    def registrar_compra():
        negado = _negar_se_sem_permissao()
        if negado:
            return negado

        body = safe_json(request)
        produto_id = parse_int(body.get("produto_id"), default=None)
        cliente_id = parse_int(body.get("cliente_id"), default=None)
        venda_id = parse_int(body.get("venda_id"), default=None)
        valor_pago = parse_float(body.get("valor_pago"), default=None)

        compra_id, erro = service.registrar_compra(
            conectar,
            session.get("usuario_id"),
            produto_id,
            body.get("imei"),
            body.get("origem"),
            valor_pago,
            body.get("forma_pagamento"),
            body.get("estado"),
            defeito=body.get("defeito"),
            cliente_id=cliente_id,
            venda_id=venda_id,
            vendedor_nome=body.get("vendedor_nome"),
            vendedor_telefone=body.get("vendedor_telefone"),
        )
        if erro:
            code = (
                404 if erro in ("Produto não encontrado.", "Cliente não encontrado.", "Venda não encontrada.") else 400
            )
            return err(erro, code)
        return ok(id=compra_id), 201

    @compras_api.route("/<int:compra_id>")
    def obter_compra(compra_id):
        negado = _negar_se_sem_permissao()
        if negado:
            return negado

        compra = service.obter_compra(conectar, compra_id)
        if not compra:
            return err("Compra não encontrada.", 404)
        return ok(compra=compra)

    @compras_api.route("/<int:compra_id>/cancelar", methods=["POST"])
    def cancelar_compra(compra_id):
        negado = _negar_se_sem_permissao()
        if negado:
            return negado

        body = safe_json(request)
        sucesso, erro = service.cancelar_compra(conectar, compra_id, session.get("usuario_id"), body.get("motivo"))
        if not sucesso:
            return err(erro, 404 if erro == "Compra não encontrada." else 400)
        return ok(id=compra_id, status="cancelada")

    return compras_api
