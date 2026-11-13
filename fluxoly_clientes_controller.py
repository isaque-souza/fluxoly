"""
fluxoly_clientes_controller.py

Camada HTTP do domínio Clientes (Blueprint Flask, prefixo `/api/clientes`).
Recebe request, valida forma do payload, chama o service, formata resposta
— nunca contém regra de negócio nem acessa o banco diretamente
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Contrato de resposta segue o padrão real já usado no resto da API
(`{"ok": ...}` / `{"ok": false, "erro": ...}`, `fluxoly_blueprints_api.py`),
não o exemplo `{"data": ...}` do `ENGINEERING_GUIDE.md` — inconsistência
pré-existente entre a documentação e o código, fora de escopo corrigir
nesta sprint.
"""

from flask import Blueprint, jsonify, request, session

import fluxoly_clientes_service as service
from fluxoly_validation import parse_int, safe_json


def create_clientes_blueprint(deps: dict):
    conectar = deps["conectar"]

    clientes_api = Blueprint("clientes_api", __name__, url_prefix="/api/clientes")

    def usuario_logado():
        return bool(session.get("usuario_id"))

    def usuario_admin():
        return session.get("usuario_perfil") == "admin"

    def usuario_pode_ver_cpf():
        # KI-045: leitura de CPF/CNPJ restrita a admin/financeiro -- escrita (criar/atualizar) segue
        # liberada a todo perfil autenticado, decisão explícita do CTO (docs/engineering/plans/
        # PLAN-LGPD-Compliance.md) para não travar o cadastro no balcão.
        return session.get("usuario_perfil") in ("admin", "financeiro")

    def _sem_cpf(cliente):
        if not cliente:
            return cliente
        cliente = dict(cliente)
        cliente.pop("cpf_cnpj", None)
        return cliente

    def err(msg, code=400):
        return jsonify({"ok": False, "erro": msg}), code

    def ok(data=None, **kwargs):
        payload = {"ok": True}
        if data is not None:
            payload.update(data if isinstance(data, dict) else {"data": data})
        payload.update(kwargs)
        return jsonify(payload)

    @clientes_api.route("")
    def listar_clientes():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        termo = (request.args.get("q") or "").strip()
        page = parse_int(request.args.get("page"), default=1)
        per_page = parse_int(request.args.get("per_page"), default=20)
        if page is None or per_page is None:
            return err("Parâmetros page/per_page inválidos.")
        # KI-066: padrão "ativos" -- seletores de nova operação não oferecem cliente inativo.
        status = (request.args.get("status") or service.STATUS_PADRAO).strip().lower()
        if status not in service.STATUS_VALIDOS:
            return err("Parâmetro status inválido (use ativos, inativos ou todos).")

        resultado = service.listar_clientes(conectar, termo, page, per_page, status)
        if not usuario_pode_ver_cpf():
            resultado["items"] = [_sem_cpf(c) for c in resultado["items"]]
        return ok(**resultado)

    @clientes_api.route("/<int:cliente_id>")
    def obter_cliente(cliente_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        cliente = service.obter_cliente(conectar, cliente_id)
        if not cliente:
            return err("Cliente não encontrado.", 404)
        if not usuario_pode_ver_cpf():
            cliente = _sem_cpf(cliente)
        return ok(cliente=cliente)

    @clientes_api.route("", methods=["POST"])
    def criar_cliente():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = safe_json(request)
        cliente_id, erro = service.criar_cliente(
            conectar,
            session.get("usuario_id"),
            body.get("nome"),
            body.get("telefone"),
            body.get("email"),
            body.get("cpf_cnpj"),
            body.get("observacoes"),
        )
        if erro:
            return err(erro)
        return ok(id=cliente_id)

    @clientes_api.route("/<int:cliente_id>", methods=["PUT"])
    def atualizar_cliente(cliente_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        body = safe_json(request)
        # KI-045: chave ausente no body (frontend a omite quando quem edita não pode ver o CPF atual)
        # vira o sentinel "preservar valor atual" -- distinto de cpf_cnpj="" enviado explicitamente,
        # que continua limpando o campo normalmente (comportamento inalterado para admin/financeiro).
        cpf_cnpj = body.get("cpf_cnpj", service.CPF_NAO_INFORMADO)
        sucesso, erro = service.atualizar_cliente(
            conectar,
            session.get("usuario_id"),
            cliente_id,
            body.get("nome"),
            body.get("telefone"),
            body.get("email"),
            cpf_cnpj,
            body.get("observacoes"),
        )
        if not sucesso:
            code = 404 if erro == "Cliente não encontrado." else 400
            return err(erro, code)
        return ok(id=cliente_id)

    @clientes_api.route("/<int:cliente_id>", methods=["DELETE"])
    def deletar_cliente(cliente_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        sucesso, erro, vinculos = service.excluir_cliente(conectar, session.get("usuario_id"), cliente_id)
        if not sucesso:
            if erro == "Cliente não encontrado.":
                return err(erro, 404)
            # BR-024 / KI-066: com histórico, a exclusão física é recusada -- a resposta diz o porquê.
            return jsonify({"ok": False, "erro": erro, "vinculos": vinculos}), 409
        return ok()

    def _mudar_situacao(cliente_id, acao):
        # BR-024d: mesma matriz do DELETE -- só admin inativa/reativa.
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        alterado, erro = acao(conectar, session.get("usuario_id"), cliente_id)
        if erro:
            return err(erro, 404 if erro == "Cliente não encontrado." else 400)
        cliente = service.obter_cliente(conectar, cliente_id)
        return ok(alterado=alterado, ativo=cliente["ativo"])

    @clientes_api.route("/<int:cliente_id>/inativar", methods=["POST"])
    def inativar_cliente(cliente_id):
        return _mudar_situacao(cliente_id, service.inativar_cliente)

    @clientes_api.route("/<int:cliente_id>/reativar", methods=["POST"])
    def reativar_cliente(cliente_id):
        return _mudar_situacao(cliente_id, service.reativar_cliente)

    @clientes_api.route("/<int:cliente_id>/anonimizar", methods=["POST"])
    def anonimizar_cliente(cliente_id):
        # KI-044: admin-only, mesmo padrão de DELETE -- complementa, não substitui, a exclusão (que
        # continua servindo só para clientes órfãos, sem histórico vinculado).
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        sucesso, erro = service.anonimizar_cliente(conectar, session.get("usuario_id"), cliente_id)
        if not sucesso:
            code = 404 if erro == "Cliente não encontrado." else 400
            return err(erro, code)
        return ok()

    return clientes_api
