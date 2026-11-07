"""
Fluxoly - API Blueprint (MercadoPhone)
Rotas /api/integracoes/mercadophone/* -- consumidas pelo frontend React
(Integracoes.jsx). Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 --
9º domínio extraído).

TD-02 Fatia 4 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md): ganhou a
rota de webhook POST /integracoes/mercadophone/os, movida de app.py. Único
ponto deste blueprint que NÃO autentica via usuario_logado()/sessão -- é
chamado pelo servidor externo da Mercado Phone, autenticado por token
compartilhado (MERCADO_PHONE_WEBHOOK_TOKEN, hmac.compare_digest), sem sessão
de usuário. Ver autenticar_integracao_mercado_phone() abaixo.
"""

import hmac
import threading
from datetime import datetime

from flask import Blueprint, abort, jsonify, request, session

from fluxoly_api_helpers import _texto_limpo_local, err, ok, usuario_admin, usuario_logado
import fluxoly_config
from fluxoly_config import MERCADO_PHONE_WEBHOOK_TOKEN, integracao_externa_bloqueada_neste_ambiente
from fluxoly_core import texto_limpo
from fluxoly_logging import get_logger
from fluxoly_mercadophone import (
    atualizar_runtime_mercadophone,
    carregar_config_mercadophone,
    detalhar_os_mercado_phone,
    importar_os_mercado_phone,
)
from fluxoly_validation import parse_int, safe_json

logger = get_logger("api_mercadophone")


def create_api_mercadophone_blueprint(deps):
    api_mercadophone = Blueprint("api_mercadophone", __name__, url_prefix="/api")

    @api_mercadophone.before_request
    def _bloquear_se_integracao_desligada():
        # ADR-014: integração desligada por padrão -- todas as rotas do blueprint (inclusive o
        # webhook) respondem 404, como se não existissem.
        if not fluxoly_config.integracao_mercadophone_habilitada():
            abort(404)

    conectar = deps["conectar"]
    sincronizar_mercado_phone = deps["sincronizar_mercado_phone"]
    reimportar_todas_os_mercado_phone = deps["reimportar_todas_os_mercado_phone"]
    reprocessar_todas_os_mercado_phone = deps["reprocessar_todas_os_mercado_phone"]
    mercado_phone_runtime_config = deps["mercado_phone_runtime_config"]
    mercado_phone_helpers = deps["mercado_phone_helpers"]
    integrations_config_path = deps["integrations_config_path"]
    carregar_configuracoes_integracoes = deps["carregar_configuracoes_integracoes"]
    salvar_configuracoes_integracoes = deps["salvar_configuracoes_integracoes"]

    def _to_bool(valor, padrao=False):
        if valor is None:
            return padrao
        if isinstance(valor, bool):
            return valor
        return str(valor).strip().lower() not in {"", "0", "false", "nao", "off"}

    reprocessamento_mp_lock = threading.Lock()
    reprocessamento_mp_estado = {
        "rodando": False,
        "iniciado_em": None,
        "finalizado_em": None,
        "atualizadas": 0,
        "erros": 0,
        "total": 0,
        "erro": "",
    }

    def _snapshot_reprocessamento_mp():
        with reprocessamento_mp_lock:
            return dict(reprocessamento_mp_estado)

    def _executar_reprocessamento_mp_async():
        try:
            resultado = reprocessar_todas_os_mercado_phone(
                conectar, mercado_phone_runtime_config, mercado_phone_helpers
            )
            with reprocessamento_mp_lock:
                reprocessamento_mp_estado["rodando"] = False
                reprocessamento_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["total"] = int(resultado.get("total") or 0)
                reprocessamento_mp_estado["atualizadas"] = int(resultado.get("atualizadas") or 0)
                reprocessamento_mp_estado["erros"] = int(resultado.get("erros") or 0)
                reprocessamento_mp_estado["erro"] = ""
        except Exception as exc:
            with reprocessamento_mp_lock:
                reprocessamento_mp_estado["rodando"] = False
                reprocessamento_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["erro"] = str(exc)

    reimportacao_mp_lock = threading.Lock()
    reimportacao_mp_estado = {
        "rodando": False,
        "iniciado_em": None,
        "finalizado_em": None,
        "removidas": 0,
        "importadas": 0,
        "atualizadas": 0,
        "erro": "",
    }

    def _snapshot_reimportacao_mp():
        with reimportacao_mp_lock:
            return dict(reimportacao_mp_estado)

    def _executar_reimportacao_mp_async():
        try:
            resultado = reimportar_todas_os_mercado_phone(conectar, mercado_phone_runtime_config, mercado_phone_helpers)
            with reimportacao_mp_lock:
                reimportacao_mp_estado["rodando"] = False
                reimportacao_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["removidas"] = int(resultado.get("removidas") or 0)
                reimportacao_mp_estado["importadas"] = int(resultado.get("importadas") or 0)
                reimportacao_mp_estado["atualizadas"] = int(resultado.get("atualizadas") or 0)
                reimportacao_mp_estado["erro"] = ""
        except Exception as exc:
            with reimportacao_mp_lock:
                reimportacao_mp_estado["rodando"] = False
                reimportacao_mp_estado["finalizado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["erro"] = str(exc)

    @api_mercadophone.route("/integracoes/mercadophone/sincronizar", methods=["POST"])
    def sincronizar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        if integracao_externa_bloqueada_neste_ambiente():
            return err("Integração externa desabilitada neste ambiente (preview/demo).", 403)
        try:
            _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
            status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            resultado = sincronizar_mercado_phone(conectar, mercado_phone_runtime_config, mercado_phone_helpers)
            return ok(resultado=resultado)
        except Exception as exc:
            return err(str(exc))

    @api_mercadophone.route("/integracoes/mercadophone/reprocessar", methods=["POST", "OPTIONS"])
    def reprocessar_mercadophone():
        if request.method == "OPTIONS":
            return ("", 204)
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        if integracao_externa_bloqueada_neste_ambiente():
            return err("Integração externa desabilitada neste ambiente (preview/demo).", 403)
        try:
            _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
            status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            with reprocessamento_mp_lock:
                if reprocessamento_mp_estado["rodando"]:
                    estado = dict(reprocessamento_mp_estado)
                    return ok(iniciado=False, reprocessamento=estado)

                reprocessamento_mp_estado["rodando"] = True
                reprocessamento_mp_estado["iniciado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reprocessamento_mp_estado["finalizado_em"] = None
                reprocessamento_mp_estado["atualizadas"] = 0
                reprocessamento_mp_estado["erros"] = 0
                reprocessamento_mp_estado["total"] = 0
                reprocessamento_mp_estado["erro"] = ""
                estado = dict(reprocessamento_mp_estado)

            threading.Thread(target=_executar_reprocessamento_mp_async, daemon=True).start()
            return ok(iniciado=True, reprocessamento=estado), 202
        except Exception as exc:
            return err(str(exc))

    @api_mercadophone.route("/integracoes/mercadophone/reprocessar/status")
    def status_reprocessar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(reprocessamento=_snapshot_reprocessamento_mp())

    @api_mercadophone.route("/integracoes/mercadophone/reimportar", methods=["POST", "OPTIONS"])
    def reimportar_mercadophone():
        if request.method == "OPTIONS":
            return ("", 204)
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)
        if integracao_externa_bloqueada_neste_ambiente():
            return err("Integração externa desabilitada neste ambiente (preview/demo).", 403)
        try:
            _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
            status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
            if not status_cfg["configurado"]:
                return err("Mercado Phone não configurado. Informe o token da API.", 400)

            with reimportacao_mp_lock:
                if reimportacao_mp_estado["rodando"]:
                    estado = dict(reimportacao_mp_estado)
                    return ok(iniciado=False, reimportacao=estado)

                reimportacao_mp_estado["rodando"] = True
                reimportacao_mp_estado["iniciado_em"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                reimportacao_mp_estado["finalizado_em"] = None
                reimportacao_mp_estado["removidas"] = 0
                reimportacao_mp_estado["importadas"] = 0
                reimportacao_mp_estado["atualizadas"] = 0
                reimportacao_mp_estado["erro"] = ""
                estado = dict(reimportacao_mp_estado)

            threading.Thread(target=_executar_reimportacao_mp_async, daemon=True).start()
            return ok(iniciado=True, reimportacao=estado), 202
        except Exception as exc:
            return err(str(exc))

    @api_mercadophone.route("/integracoes/mercadophone/reimportar/status")
    def status_reimportar_mercadophone():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        return ok(reimportacao=_snapshot_reimportacao_mp())

    @api_mercadophone.route("/integracoes/mercadophone/status")
    def status_mercadophone():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
        status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)

        return ok(
            mercado_phone={
                **status_cfg,
                "tem_token": status_cfg["configurado"],
            }
        )

    @api_mercadophone.route("/integracoes/mercadophone/config", methods=["POST"])
    def salvar_config_mercadophone():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        if integracao_externa_bloqueada_neste_ambiente():
            return err("Integração externa desabilitada neste ambiente (preview/demo).", 403)

        body = safe_json(request)
        dados, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)

        if "api_token" in body:
            mp_cfg["api_token"] = _texto_limpo_local(body.get("api_token"))

        if "sync_enabled" in body:
            mp_cfg["sync_enabled"] = _to_bool(body.get("sync_enabled"), padrao=True)

        if "sync_interval_seconds" in body:
            parsed_interval = parse_int(body.get("sync_interval_seconds"), default=180)
            if parsed_interval is None:
                return err("sync_interval_seconds inválido.", 400)
            mp_cfg["sync_interval_seconds"] = max(30, parsed_interval)

        if "sync_timeout_seconds" in body:
            parsed_timeout = parse_int(body.get("sync_timeout_seconds"), default=20)
            if parsed_timeout is None:
                return err("sync_timeout_seconds inválido.", 400)
            mp_cfg["sync_timeout_seconds"] = max(5, parsed_timeout)

        if "sync_start_date" in body:
            mp_cfg["sync_start_date"] = _texto_limpo_local(body.get("sync_start_date")) or "2026-04-01"

        dados["mercado_phone"] = mp_cfg
        salvar_configuracoes_integracoes(integrations_config_path, dados)

        status_cfg = atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
        return ok(mercado_phone=status_cfg)

    # ========================================================================
    # WEBHOOK (TD-02 Fatia 4) -- autenticação por token compartilhado, NÃO por
    # sessão. Chamado pelo servidor externo da Mercado Phone, sem usuario_logado().
    # ========================================================================

    def autenticar_integracao_mercado_phone():
        """Valida token de autenticação do webhook Mercado Phone.

        Sem MERCADO_PHONE_WEBHOOK_TOKEN configurado, nenhum candidato pode
        corresponder — a rota fica bloqueada por padrão (fail secure) em vez de
        aberta sem autenticação.
        """

        def _mascarar_token(valor):
            texto = texto_limpo(valor)
            if not texto:
                return "<vazio>"
            if len(texto) <= 8:
                return "*" * len(texto)
            return f"{texto[:4]}...{texto[-4:]} (len={len(texto)})"

        auth_header = texto_limpo(request.headers.get("Authorization"))
        token_header = texto_limpo(request.headers.get("X-Webhook-Token"))
        payload = request.get_json(silent=True)

        candidatos = []

        if token_header:
            candidatos.append(token_header)

        # Alguns provedores enviam em headers alternativos.
        for header_name in ("X-Api-Key", "X-Auth-Token", "X-Token", "Mp-Auth-Code"):
            valor = texto_limpo(request.headers.get(header_name))
            if valor:
                candidatos.append(valor)

        if auth_header:
            if auth_header.lower().startswith("bearer "):
                candidatos.append(auth_header[7:].strip())
            else:
                candidatos.append(auth_header.strip())

        for query_name in ("token", "webhook_token", "security_token"):
            valor = texto_limpo(request.args.get(query_name))
            if valor:
                candidatos.append(valor)

        if isinstance(payload, dict):
            for body_key in ("token", "webhook_token", "security_token"):
                valor = texto_limpo(payload.get(body_key))
                if valor:
                    candidatos.append(valor)

        for form_key in ("token", "webhook_token", "security_token"):
            valor = texto_limpo(request.form.get(form_key))
            if valor:
                candidatos.append(valor)

        autenticado = any(hmac.compare_digest(MERCADO_PHONE_WEBHOOK_TOKEN, candidato) for candidato in candidatos)
        if not autenticado:
            logger.warning(
                "mercadophone_webhook_token_invalido",
                extra={
                    "esperado": _mascarar_token(MERCADO_PHONE_WEBHOOK_TOKEN),
                    "candidatos": [_mascarar_token(c) for c in candidatos],
                    "headers": sorted(request.headers.keys()),
                    "query_keys": sorted(request.args.keys()),
                },
            )
            abort(401)

    @api_mercadophone.route("/integracoes/mercadophone/os", methods=["POST"])
    def receber_os_mercado_phone():
        """Recebe OS do Mercado Phone via webhook."""
        autenticar_integracao_mercado_phone()

        payload = request.get_json(silent=True) or {}
        payload_evento = payload if isinstance(payload, dict) else {}
        if isinstance(payload_evento, dict) and isinstance(payload_evento.get("ordem_servico"), dict):
            payload = payload_evento["ordem_servico"]

        external_id = ""
        if isinstance(payload, dict):
            external_id = texto_limpo(
                payload.get("codigo")
                or payload.get("id")
                or payload.get("id_externo")
                or payload.get("os_id")
                or payload.get("ordem_servico_id")
            )
        if not external_id and isinstance(payload_evento, dict):
            external_id = texto_limpo(
                payload_evento.get("codigo")
                or payload_evento.get("id")
                or payload_evento.get("id_externo")
                or payload_evento.get("os_id")
                or payload_evento.get("ordem_servico_id")
                or payload_evento.get("ordem_servico", {}).get("id")
                or payload_evento.get("ordem_servico", {}).get("codigo")
            )

        conn = conectar()
        cursor = conn.cursor()

        try:
            resultado = importar_os_mercado_phone(cursor, payload, mercado_phone_runtime_config, mercado_phone_helpers)
            conn.commit()
            status_code = 200 if resultado["duplicada"] else 201
            return (
                jsonify(
                    {
                        "ok": True,
                        "duplicada": resultado["duplicada"],
                        "os_id": resultado["os_id"],
                    }
                ),
                status_code,
            )
        except ValueError as exc:
            # Alguns webhooks de edição vêm com payload parcial (apenas id/status).
            # Nesses casos, busca o detalhe por ID para salvar corretamente no Fluxoly.
            if (
                external_id
                and "dados suficientes" in str(exc).lower()
                and texto_limpo(mercado_phone_runtime_config.get("api_token"))
            ):
                try:
                    detalhes = detalhar_os_mercado_phone(external_id, mercado_phone_runtime_config)
                    payload_detalhado = detalhes.get("data") if isinstance(detalhes, dict) else None
                    if isinstance(payload_detalhado, dict):
                        resultado = importar_os_mercado_phone(
                            cursor,
                            payload_detalhado,
                            mercado_phone_runtime_config,
                            mercado_phone_helpers,
                            fallback_external_id=external_id,
                        )
                        conn.commit()
                        status_code = 200 if resultado["duplicada"] else 201
                        return (
                            jsonify(
                                {
                                    "ok": True,
                                    "duplicada": resultado["duplicada"],
                                    "os_id": resultado["os_id"],
                                    "fallback_por_id": True,
                                }
                            ),
                            status_code,
                        )
                except Exception:
                    pass

            conn.rollback()
            return jsonify({"ok": False, "erro": str(exc)}), 400
        finally:
            conn.close()

    return api_mercadophone
