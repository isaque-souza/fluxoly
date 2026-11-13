"""
Fluxoly - API Blueprint (Ordens de Servico)
Rotas /api/ordens*, /api/checklist/<token>, /api/reparos* -- consumidas pelo
frontend React (CRUD de OS, checklist de qualidade, garantia por reparo,
catalogo de tipos de reparo). Extraido de fluxoly_blueprints_api.py (TD-01,
Phase 2 -- 12o e ultimo dominio extraido).
"""

import json
import secrets
from datetime import date, datetime

from flask import Blueprint, request, session

import fluxoly_clientes_service as clientes_service
import fluxoly_compras_aparelhos_service as compras_aparelhos_service
import fluxoly_dados_loja_service as dados_loja_service
import fluxoly_unidades_serializadas_service as unidades_service
from fluxoly_api_helpers import _texto_limpo_local, err, ok, usuario_admin, usuario_logado
from fluxoly_core import (
    CAMPOS_TEXTO_OS,
    CLIENTE_OS_INTERNA,
    TIPO_OS_INTERNA,
    normalizar_data_previsao,
    os_atrasada,
)
from fluxoly_mercadophone import atualizar_runtime_mercadophone, carregar_config_mercadophone
from fluxoly_os import TIPOS_DOCUMENTO_CLIENTE, buscar_os_para_documento, montar_documento_cliente
from fluxoly_validation import parse_float, parse_int, safe_json


# BR-102 -- SQL literal por coluna (sem montar nome de coluna em tempo de execução).
_SQL_GRAVAR_TEXTO_OS = {
    "relato_cliente": "UPDATE os SET relato_cliente=? WHERE id=?",
    "laudo_tecnico": "UPDATE os SET laudo_tecnico=? WHERE id=?",
    "observacao_interna": "UPDATE os SET observacao_interna=? WHERE id=?",
}


def create_api_os_blueprint(deps):
    api_os = Blueprint("api_os", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    normalizar_status_os = deps["normalizar_status_os"]
    status_finalizado = deps["status_finalizado"]
    status_cancelado = deps["status_cancelado"]
    status_aberto = deps["status_aberto"]
    calcular_faturamento_os = deps["calcular_faturamento_os"]
    calcular_lucro_os = deps["calcular_lucro_os"]
    carregar_os_com_relacoes = deps["carregar_os_com_relacoes"]
    validar_reparo_ids = deps["validar_reparo_ids"]
    vendedor_valido = deps["vendedor_valido"]
    salvar_reparos_os = deps["salvar_reparos_os"]
    modelo_compativel = deps["modelo_compativel"]
    consumir_peca_da_os = deps["consumir_peca_da_os"]
    adicionar_peca_os_sem_consumir = deps["adicionar_peca_os_sem_consumir"]
    devolver_pecas_da_os = deps["devolver_pecas_da_os"]
    obter_reparos_por_os = deps["obter_reparos_por_os"]
    buscar_reparo_ids_da_os = deps["buscar_reparo_ids_da_os"]
    resolver_garantias_reparo = deps["resolver_garantias_reparo"]
    gravar_garantias_reparo = deps["gravar_garantias_reparo"]
    buscar_linhas_com_garantia_da_os = deps["buscar_linhas_com_garantia_da_os"]
    zerar_garantia_reparo = deps["zerar_garantia_reparo"]
    buscar_garantia_reparo = deps["buscar_garantia_reparo"]
    corrigir_garantia_reparo = deps["corrigir_garantia_reparo"]
    buscar_historico_garantia_reparo = deps["buscar_historico_garantia_reparo"]
    obter_tipo_garantia = deps["obter_tipo_garantia"]
    registrar_log_auditoria = deps["registrar_log_auditoria"]
    modelo_para_os = deps["modelo_para_os"]
    normalizar_imei = deps["normalizar_imei"]
    texto_reparos_os = deps["texto_reparos_os"]
    parse_data_ymd = deps["parse_data_ymd"]
    vendedores = deps["vendedores"]
    mercado_phone_runtime_config = deps["mercado_phone_runtime_config"]
    public_base_url = deps.get("public_base_url", "")
    integrations_config_path = deps["integrations_config_path"]
    carregar_configuracoes_integracoes = deps["carregar_configuracoes_integracoes"]

    def _parse_checklist_json(value):
        texto = (value or "").strip()
        if not texto:
            return {}
        try:
            parsed = json.loads(texto)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}

    def _checklist_status(value):
        texto = (value or "").strip().lower().replace(" ", "_")
        aliases = {
            "": "nao_testado",
            "nao": "reprovado",
            "nao_testado": "nao_testado",
            "nao-testado": "nao_testado",
            "pendente": "nao_testado",
            "ok": "aprovado",
            "passou": "aprovado",
            "aprovado": "aprovado",
            "falhou": "reprovado",
            "falha": "reprovado",
            "reprovado": "reprovado",
        }
        return aliases.get(texto, "nao_testado")

    def _serialize_checklist(cursor, row):
        if not row:
            return None

        resultado = _parse_checklist_json(row[10])
        return {
            "id": row[0],
            "os_id": row[1],
            "access_token": row[2] or "",
            "status_touch": _checklist_status(row[3]),
            "status_audio": _checklist_status(row[4]),
            "status_microfone": _checklist_status(row[5]),
            "status_camera": _checklist_status(row[6]),
            "status_botoes": _checklist_status(row[7]),
            "observacoes": row[8] or "",
            "executado_por": row[9] or "",
            "resultado": resultado,
            "origem": row[11] or "",
            "criado_em": row[12] or "",
            "atualizado_em": row[13] or "",
        }

    def _resolve_public_base_url():
        if public_base_url:
            return public_base_url
        return request.host_url.rstrip("/")

    def _enriquecer_checklist_urls(checklist):
        if not checklist:
            return None
        enriched = dict(checklist)
        token = enriched.get("access_token") or ""
        if token:
            enriched["public_url"] = f"{_resolve_public_base_url()}/app/checklist/{token}"
        else:
            enriched["public_url"] = ""
        return enriched

    def _buscar_checklist_por_os(cursor, os_id):
        cursor.execute(
            """
            SELECT id, os_id, COALESCE(access_token, ''), COALESCE(status_touch, 'nao_testado'),
                   COALESCE(status_audio, 'nao_testado'), COALESCE(status_microfone, 'nao_testado'),
                   COALESCE(status_camera, 'nao_testado'), COALESCE(status_botoes, 'nao_testado'),
                   COALESCE(observacoes, ''), COALESCE(executado_por, ''), COALESCE(resultado_json, '{}'),
                   COALESCE(origem, ''), COALESCE(criado_em, ''), COALESCE(atualizado_em, '')
            FROM os_checklists
            WHERE os_id=?
            """,
            (os_id,),
        )
        return _enriquecer_checklist_urls(_serialize_checklist(cursor, cursor.fetchone()))

    def _buscar_checklist_por_token(cursor, token):
        cursor.execute(
            """
            SELECT id, os_id, COALESCE(access_token, ''), COALESCE(status_touch, 'nao_testado'),
                   COALESCE(status_audio, 'nao_testado'), COALESCE(status_microfone, 'nao_testado'),
                   COALESCE(status_camera, 'nao_testado'), COALESCE(status_botoes, 'nao_testado'),
                   COALESCE(observacoes, ''), COALESCE(executado_por, ''), COALESCE(resultado_json, '{}'),
                   COALESCE(origem, ''), COALESCE(criado_em, ''), COALESCE(atualizado_em, '')
            FROM os_checklists
            WHERE access_token=?
            """,
            (token,),
        )
        return _enriquecer_checklist_urls(_serialize_checklist(cursor, cursor.fetchone()))

    def _garantir_checklist_os(cursor, os_id):
        checklist = _buscar_checklist_por_os(cursor, os_id)
        if checklist:
            return checklist

        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            INSERT INTO os_checklists (os_id, criado_em, atualizado_em)
            VALUES (?, ?, ?)
            """,
            (os_id, agora, agora),
        )
        return _buscar_checklist_por_os(cursor, os_id)

    # ── SERVICE ORDERS ─────────────────────────────────────────────────────

    def _outra_os_interna_aberta(cursor, unidade_id, os_id):
        cursor.execute(
            "SELECT status FROM os WHERE tipo=? AND unidade_serializada_id=? AND id != ?",
            (TIPO_OS_INTERNA, unidade_id, os_id),
        )
        return any(status_aberto(normalizar_status_os(r[0])) for r in cursor.fetchall())

    def _sincronizar_aparelho_da_os_interna(cursor, os_id, unidade_id, status_novo, status_antigo):
        """BR-091 / BR-090 -- mantém o status do aparelho comprado alinhado com a OS interna.
        Finalizou -> aparelho `disponivel` (se não há outra OS interna aberta para ele).
        Reaberta depois de finalizada/cancelada -> aparelho volta a `em_reparo`.
        Retorna mensagem de erro ou None."""
        usuario_id = session.get("usuario_id")
        if status_finalizado(status_novo) and not status_finalizado(status_antigo):
            if not _outra_os_interna_aberta(cursor, unidade_id, os_id):
                unidades_service.concluir_reparo_interno(cursor, unidade_id, usuario_id)
            return None
        reaberta = status_finalizado(status_antigo) or status_cancelado(status_antigo)
        if reaberta and not status_finalizado(status_novo) and not status_cancelado(status_novo):
            _imei, erro = compras_aparelhos_service.abrir_reparo_interno(cursor, unidade_id, usuario_id)
            return erro
        return None

    def _os_row_to_dict(row, reparos_por_os, custos):
        os_id = row[0]
        tipo = row[1]
        status = normalizar_status_os(row[6])
        valor_cobrado = row[7]
        valor_descontado = row[8]
        custo = custos.get(os_id, row[9] or 0)
        reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
        return {
            "id": os_id,
            "tipo": tipo or "",
            "cliente": row[2] or "",
            "aparelho": row[3] or "",
            "tecnico": row[4] or "",
            "status": status,
            "reparos": reparos_info.get("nomes", []),
            "reparo_ids": reparos_info.get("ids", []),
            "reparo": texto_reparos_os(reparos_info, tipo or "—"),
            "vendedor": row[13] or "",
            "cor": row[14] or "" if len(row) > 14 else "",
            "imei": row[15] or "" if len(row) > 15 else "",
            "modelo": row[12] or "" if len(row) > 12 else "",
            "valor_cobrado": round(valor_cobrado or 0, 2),
            "valor_descontado": round(valor_descontado or 0, 2),
            "custo_pecas": round(custo or 0, 2),
            "faturamento": round(calcular_faturamento_os(valor_cobrado, valor_descontado), 2),
            "lucro": round(calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo), 2),
            "data": row[10] or "",
            "observacoes": row[11] or "" if len(row) > 11 else "",
            "origem_integracao": row[16] or "" if len(row) > 16 else "",
            "id_externo_integracao": row[17] or "" if len(row) > 17 else "",
            "data_previsao": row[18] or "" if len(row) > 18 else "",
            "atrasada": os_atrasada(status, row[18] if len(row) > 18 else ""),
        }

    def _gravar_textos_os(cursor, os_id, body):
        """BR-102 -- grava só os campos de texto presentes no payload (cliente antigo não apaga)."""
        for campo in CAMPOS_TEXTO_OS:
            if campo in body:
                cursor.execute(_SQL_GRAVAR_TEXTO_OS[campo], ((body.get(campo) or "").strip(), os_id))

    def _ordem_lista_por_id_desc(item):
        origem = (item.get("origem_integracao") or "").strip().lower()
        externo = (item.get("id_externo_integracao") or "").strip()
        interno = int(item.get("id") or 0)

        if origem == "mercado_phone" and externo.isdigit():
            return int(externo)
        return interno

    @api_os.route("/ordens")
    def listar_ordens():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        q = (request.args.get("q") or "").strip().lower()
        filtro_status = (request.args.get("status") or "").strip()
        filtro_tipo = (request.args.get("tipo") or "").strip()
        filtro_tecnico = (request.args.get("tecnico") or "").strip()
        filtro_vendedor = (request.args.get("vendedor") or "").strip()
        filtro_modelo = (request.args.get("modelo") or "").strip()
        data_ini = (request.args.get("data_ini") or "").strip()
        data_fim = (request.args.get("data_fim") or "").strip()

        _, mp_cfg = carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path)
        atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config)
        mp_sync_start_date = _texto_limpo_local(mercado_phone_runtime_config.get("sync_start_date") or "")

        conn = conectar()
        cursor = conn.cursor()
        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")
        conn.close()

        result = []
        for row in dados:
            os_id = row[0]
            status = normalizar_status_os(row[6])
            tipo = row[1] or ""
            tecnico = row[4] or ""
            vendedor = row[13] or ""
            modelo = row[12] or ""
            data = row[10] or ""
            origem_integracao = (row[16] or "") if len(row) > 16 else ""
            reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
            reparo_nome = texto_reparos_os(reparos_info, tipo)

            # Mantém OS antigas da integração no banco, mas oculta da listagem.
            if (
                origem_integracao == "mercado_phone"
                and mp_sync_start_date
                and ((not data) or (data < mp_sync_start_date))
            ):
                continue

            if q:
                haystack = f"{os_id} {row[2]} {row[3]} {tecnico} {status} {reparo_nome} {modelo} {vendedor} {row[14] or ''} {row[15] or ''} {row[16] or ''} {row[17] or ''}".lower()
                if q not in haystack:
                    continue
            if filtro_status and status != filtro_status:
                continue
            if filtro_tipo and tipo != filtro_tipo:
                continue
            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if filtro_vendedor and vendedor != filtro_vendedor:
                continue
            if filtro_modelo and modelo != filtro_modelo:
                continue
            if data_ini and (not data or data < data_ini):
                continue
            if data_fim and (not data or data > data_fim):
                continue

            result.append(_os_row_to_dict(row, reparos_por_os, custos))

        result.sort(key=_ordem_lista_por_id_desc, reverse=True)

        return ok(
            ordens=result,
            total=len(result),
            abertas=len([o for o in result if status_aberto(o["status"])]),
            finalizadas=len([o for o in result if status_finalizado(o["status"])]),
        )

    @api_os.route("/ordens/<int:os_id>")
    def obter_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id, tipo, cliente, aparelho, tecnico, reparo_id, status,
                COALESCE(valor_cobrado, 0), COALESCE(valor_descontado, 0),
                COALESCE(custo_pecas, 0), COALESCE(data, ''),
                COALESCE(observacoes, ''), COALESCE(modelo, ''),
                COALESCE(vendedor, ''), COALESCE(cor, ''),
                COALESCE(imei, ''), COALESCE(origem_integracao, ''),
                COALESCE(id_externo_integracao, ''),
                COALESCE(data_finalizado, ''),
                unidade_serializada_id,
                COALESCE(data_previsao, ''),
                COALESCE(relato_cliente, ''),
                COALESCE(laudo_tecnico, ''),
                COALESCE(observacao_interna, '')
            FROM os
            WHERE id=?
            """,
            (os_id,),
        )
        row = cursor.fetchone()
        if not row:
            conn.close()
            return err("OS não encontrada.", 404)

        reparos_por_os = obter_reparos_por_os(cursor)
        cursor.execute(
            """
            SELECT estoque_id, COALESCE(peca_descricao,''), COALESCE(valor,0),
                   COALESCE(peca_fornecedor,''), COALESCE(quantidade,1), COALESCE(peca_modelo,'')
            FROM os_pecas WHERE os_id=? ORDER BY id
            """,
            (os_id,),
        )
        pecas_usadas = [
            {
                "estoque_id": p[0],
                "descricao": p[1],
                "valor": p[2],
                "fornecedor": p[3],
                "quantidade": p[4],
                "modelo": p[5],
            }
            for p in cursor.fetchall()
        ]
        conn.close()

        reparos_info = reparos_por_os.get(os_id, {"ids": [], "nomes": []})
        status = normalizar_status_os(row[6])
        tipo = row[1] or ""
        custo = row[9] or 0
        return ok(
            ordem={
                "id": row[0],
                "tipo": tipo,
                "cliente": row[2] or "",
                "aparelho": row[3] or "",
                "tecnico": row[4] or "",
                "status": status,
                "reparos": reparos_info.get("nomes", []),
                "reparo_ids": reparos_info.get("ids", []),
                "vendedor": row[13] or "",
                "cor": row[14] or "",
                "imei": row[15] or "",
                "modelo": row[12] or "",
                "valor_cobrado": row[7] or 0,
                "valor_descontado": row[8] or 0,
                "custo_pecas": custo,
                "faturamento": round(calcular_faturamento_os(row[7], row[8]), 2),
                "lucro": round(calcular_lucro_os(tipo, row[7], row[8], custo), 2),
                "data": row[10] or "",
                "observacoes": row[11] or "",
                "origem_integracao": row[16] or "",
                "id_externo_integracao": row[17] or "",
                "data_finalizado": row[18] or "",
                "unidade_serializada_id": row[19],
                "data_previsao": row[20] or "",
                "atrasada": os_atrasada(status, row[20]),
                **dict(zip(CAMPOS_TEXTO_OS, (t or "" for t in row[21:24]), strict=True)),  # BR-102
                "pecas_usadas": pecas_usadas,
            }
        )

    @api_os.route("/ordens/<int:os_id>/documento")
    def documento_cliente_os(os_id):
        """Conteúdo do comprovante de entrada/entrega para o cliente (BR-095 a
        BR-098). Só o que `montar_documento_cliente` monta sai daqui (BR-097);
        o PDF é desenhado no frontend."""
        if not usuario_logado():
            return err("Não autenticado.", 401)

        tipo_documento = (request.args.get("tipo") or "").strip().lower()
        if tipo_documento not in TIPOS_DOCUMENTO_CLIENTE:
            return err("Tipo de documento inválido. Use 'entrada' ou 'entrega'.", 400)

        conn = conectar()
        try:
            cursor = conn.cursor()
            os_dados = buscar_os_para_documento(cursor, os_id)
            loja = dados_loja_service.obter_dados_loja_com_cursor(cursor)
        finally:
            conn.close()
        if not os_dados:
            return err("OS não encontrada.", 404)

        cliente_cadastro = None
        if os_dados["cliente_id"]:
            cliente_cadastro = clientes_service.obter_cliente(conectar, os_dados["cliente_id"])
            # KI-045: CPF/CNPJ só para quem pode lê-lo -- o documento sai sem ele para os demais.
            if cliente_cadastro and session.get("usuario_perfil") not in ("admin", "financeiro"):
                cliente_cadastro = {**cliente_cadastro, "cpf_cnpj": ""}

        documento, erro = montar_documento_cliente(
            tipo_documento,
            os_dados,
            loja,
            cliente_cadastro,
            normalizar_status_os(os_dados["status"]),
            calcular_faturamento_os(os_dados["valor_cobrado"], os_dados["valor_descontado"]),
        )
        if erro:
            return err(erro, 409)
        return ok(documento=documento)

    @api_os.route("/ordens/<int:os_id>/checklist")
    def obter_checklist_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        # INC-001: conexão sem try/except/finally — mesmo padrão do hotfix de auth_login.
        conn = conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, cliente, COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(imei, ''), COALESCE(status, ''), COALESCE(origem_integracao, ''), COALESCE(id_externo_integracao, '') FROM os WHERE id=?",
                (os_id,),
            )
            ordem = cursor.fetchone()
            if not ordem:
                return err("OS não encontrada.", 404)

            checklist = _garantir_checklist_os(cursor, os_id)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(
            checklist=checklist,
            ordem={
                "id": ordem[0],
                "cliente": ordem[1] or "",
                "modelo": ordem[2] or "",
                "cor": ordem[3] or "",
                "imei": ordem[4] or "",
                "status": normalizar_status_os(ordem[5]),
                "origem_integracao": ordem[6] or "",
                "id_externo_integracao": ordem[7] or "",
            },
        )

    @api_os.route("/ordens/<int:os_id>/checklist/token", methods=["POST"])
    def gerar_token_checklist_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)

        # INC-001: conexão sem try/except/finally — mesmo padrão do hotfix de auth_login.
        conn = conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, cliente, COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(imei, ''), COALESCE(status, '') FROM os WHERE id=?",
                (os_id,),
            )
            ordem = cursor.fetchone()
            if not ordem:
                return err("OS não encontrada.", 404)

            checklist = _garantir_checklist_os(cursor, os_id)
            token = checklist.get("access_token") or secrets.token_urlsafe(18)
            agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute(
                """
                UPDATE os_checklists
                SET access_token=?, atualizado_em=?
                WHERE os_id=?
                """,
                (token, agora, os_id),
            )
            conn.commit()
            checklist = _buscar_checklist_por_os(cursor, os_id)
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(
            checklist=checklist,
            ordem={
                "id": ordem[0],
                "cliente": ordem[1] or "",
                "modelo": ordem[2] or "",
                "cor": ordem[3] or "",
                "imei": ordem[4] or "",
                "status": normalizar_status_os(ordem[5]),
            },
        )

    @api_os.route("/checklist/<token>")
    def obter_checklist_publico(token):
        token = (token or "").strip()
        if not token:
            return err("Token inválido.", 404)

        # INC-001: conexão sem try/except/finally — mesmo padrão do hotfix de auth_login.
        # Rota pública, sem login — nenhuma proteção anterior contra exceção.
        conn = conectar()
        try:
            cursor = conn.cursor()
            checklist = _buscar_checklist_por_token(cursor, token)
            if not checklist:
                return err("Checklist não encontrado.", 404)

            cursor.execute(
                """
                SELECT id, cliente, COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(imei, ''), COALESCE(status, ''),
                       COALESCE(origem_integracao, ''), COALESCE(id_externo_integracao, '')
                FROM os
                WHERE id=?
                """,
                (checklist["os_id"],),
            )
            ordem = cursor.fetchone()
            if not ordem:
                return err("OS não encontrada.", 404)
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(
            checklist=checklist,
            ordem={
                "id": ordem[0],
                "cliente": ordem[1] or "",
                "modelo": ordem[2] or "",
                "cor": ordem[3] or "",
                "imei": ordem[4] or "",
                "status": normalizar_status_os(ordem[5]),
                "origem_integracao": ordem[6] or "",
                "id_externo_integracao": ordem[7] or "",
            },
        )

    @api_os.route("/checklist/<token>", methods=["POST"])
    def salvar_checklist_publico(token):
        token = (token or "").strip()
        if not token:
            return err("Token inválido.", 404)

        body = safe_json(request)
        testes = body.get("testes") or {}
        if not isinstance(testes, dict):
            return err("Formato do checklist inválido.")

        status_touch = _checklist_status((testes.get("touch") or {}).get("status"))
        status_audio = _checklist_status((testes.get("audio") or {}).get("status"))
        status_microfone = _checklist_status((testes.get("microfone") or {}).get("status"))
        status_camera = _checklist_status((testes.get("camera") or {}).get("status"))
        status_botoes = _checklist_status((testes.get("botoes") or {}).get("status"))
        executado_por = (body.get("executado_por") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        origem = (body.get("origem") or "qr_publico").strip() or "qr_publico"
        agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            # P1-1: rota pública -- Infinity/NaN em qualquer nível do checklist é recusado.
            resultado_json = json.dumps({"testes": testes}, ensure_ascii=True, allow_nan=False)
        except ValueError:
            return err("Formato do checklist inválido.")

        # INC-001: conexão sem try/except/finally — mesmo padrão do hotfix de auth_login.
        # Rota pública, sem login, escreve dado enviado por cliente final — maior risco
        # restante identificado na investigação.
        conn = conectar()
        try:
            cursor = conn.cursor()
            checklist = _buscar_checklist_por_token(cursor, token)
            if not checklist:
                return err("Checklist não encontrado.", 404)

            cursor.execute(
                """
                UPDATE os_checklists
                SET status_touch=?, status_audio=?, status_microfone=?, status_camera=?, status_botoes=?,
                    observacoes=?, executado_por=?, origem=?, resultado_json=?, atualizado_em=?
                WHERE access_token=?
                """,
                (
                    status_touch,
                    status_audio,
                    status_microfone,
                    status_camera,
                    status_botoes,
                    observacoes,
                    executado_por,
                    origem,
                    resultado_json,
                    agora,
                    token,
                ),
            )
            conn.commit()
            checklist_atualizado = _buscar_checklist_por_token(cursor, token)
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(checklist=checklist_atualizado)

    @api_os.route("/ordens", methods=["POST"])
    def criar_ordem():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)

        body = safe_json(request)

        tipo = (body.get("tipo") or "").strip()
        cliente = (body.get("cliente") or "").strip()
        modelo_raw = body.get("modelo") or ""
        modelo = modelo_para_os(modelo_raw)
        cor = (body.get("cor") or "").strip()
        imei = normalizar_imei(body.get("imei"))
        aparelho = modelo
        tecnico = (body.get("tecnico") or "").strip()
        vendedor = (body.get("vendedor") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        reparo_ids = [int(x) for x in (body.get("reparo_ids") or []) if str(x).isdigit()]
        pecas_ids = [int(x) for x in (body.get("pecas_ids") or []) if str(x).isdigit()]
        valor_cobrado = parse_float(body.get("valor_cobrado"), default=0.0)
        valor_descontado = parse_float(body.get("valor_descontado"), default=0.0)
        data = (body.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        status_raw = (body.get("status") or "Em andamento").strip()
        data_previsao, erro_previsao = normalizar_data_previsao(body.get("data_previsao"))
        if erro_previsao:
            return err(erro_previsao)

        status = normalizar_status_os(status_raw)

        # BR-090 -- OS interna: sem cliente, vendedor nem valor cobrado; ligada a um aparelho comprado.
        interna = tipo == TIPO_OS_INTERNA
        unidade_serializada_id = None
        if interna:
            unidade_serializada_id = parse_int(body.get("unidade_serializada_id"), default=None)
            cliente = CLIENTE_OS_INTERNA
            vendedor = ""
            valor_cobrado = 0.0
            valor_descontado = 0.0

        if not tipo or not cliente or not modelo or not tecnico or valor_cobrado is None or valor_descontado is None:
            return err("Preencha tipo, cliente, modelo, técnico e valores válidos.")
        if not reparo_ids:
            return err("Selecione ao menos um reparo.")
        if not vendedor_valido(vendedor, vendedores):
            return err("Vendedor inválido.")
        if interna and status_cancelado(status):
            return err("Não é possível abrir uma OS interna já cancelada.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if not validar_reparo_ids(cursor, reparo_ids):
                return err("Um ou mais reparos não existem.")

            if interna:
                imei_aparelho, erro_aparelho = compras_aparelhos_service.abrir_reparo_interno(
                    cursor, unidade_serializada_id, session.get("usuario_id")
                )
                if erro_aparelho:
                    conn.rollback()
                    return err(erro_aparelho)
                imei = normalizar_imei(imei_aparelho) or imei

            cursor.execute(
                """
                INSERT INTO os (tipo, cliente, aparelho, tecnico, reparo_id, status,
                    valor_cobrado, valor_descontado, custo_pecas, data, observacoes, modelo, vendedor, cor, imei,
                    unidade_serializada_id, data_previsao)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    tipo,
                    cliente,
                    aparelho,
                    tecnico,
                    reparo_ids[0],
                    status,
                    valor_cobrado,
                    valor_descontado,
                    0,
                    data,
                    observacoes,
                    modelo,
                    vendedor,
                    cor,
                    imei,
                    unidade_serializada_id,
                    data_previsao,
                ),
            )
            novo_id = cursor.lastrowid
            _gravar_textos_os(cursor, novo_id, body)
            salvar_reparos_os(cursor, novo_id, reparo_ids)

            custo_total = 0.0
            for peca_id in pecas_ids:
                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row else ""
                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    return err("Peça incompatível com o modelo da OS.")
                ok_peca, erro_peca = consumir_peca_da_os(cursor, novo_id, peca_id)
                if not ok_peca:
                    conn.rollback()
                    return err(erro_peca)
                custo_total += valor_peca

            cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(custo_total, 2), novo_id))
            if interna and status_finalizado(status):
                _sincronizar_aparelho_da_os_interna(cursor, novo_id, unidade_serializada_id, status, "")
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(os_id=novo_id), 201

    @api_os.route("/ordens/<int:os_id>", methods=["PUT"])
    def atualizar_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)

        body = safe_json(request)

        tipo = (body.get("tipo") or "").strip()
        cliente = (body.get("cliente") or "").strip()
        modelo_raw = body.get("modelo") or ""
        modelo = modelo_para_os(modelo_raw)
        cor = (body.get("cor") or "").strip()
        imei = normalizar_imei(body.get("imei"))
        tecnico = (body.get("tecnico") or "").strip()
        vendedor = (body.get("vendedor") or "").strip()
        observacoes = (body.get("observacoes") or "").strip()
        reparo_ids = [int(x) for x in (body.get("reparo_ids") or []) if str(x).isdigit()]
        pecas_ids = [int(x) for x in (body.get("pecas_ids") or []) if str(x).isdigit()]
        valor_cobrado = parse_float(body.get("valor_cobrado"), default=0.0)
        valor_descontado = parse_float(body.get("valor_descontado"), default=0.0)
        data_os = (body.get("data_os") or "").strip() or datetime.now().strftime("%Y-%m-%d")
        status = normalizar_status_os(body.get("status") or "", status_padrao="")
        aparelho = modelo
        # BR-101 -- só mexe na previsão quando o cliente manda o campo (cliente antigo não apaga).
        atualizar_previsao = "data_previsao" in body
        data_previsao, erro_previsao = normalizar_data_previsao(body.get("data_previsao"))
        if erro_previsao:
            return err(erro_previsao)

        # BR-090 -- OS interna: mesmos campos forçados da criação (ver criar_ordem).
        interna = tipo == TIPO_OS_INTERNA
        if interna:
            cliente = CLIENTE_OS_INTERNA
            vendedor = ""
            valor_cobrado = 0.0
            valor_descontado = 0.0

        if (
            not tipo
            or not cliente
            or not modelo
            or not tecnico
            or not status
            or valor_cobrado is None
            or valor_descontado is None
        ):
            return err("Preencha todos os campos obrigatórios.")
        if not reparo_ids:
            return err("Selecione ao menos um reparo.")
        if not vendedor_valido(vendedor, vendedores):
            return err("Vendedor inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            if not validar_reparo_ids(cursor, reparo_ids):
                return err("Um ou mais reparos não existem.")

            cursor.execute(
                "SELECT status, COALESCE(data_finalizado,''), COALESCE(tipo,''), unidade_serializada_id, "
                "COALESCE(imei,'') FROM os WHERE id=?",
                (os_id,),
            )
            row_atual = cursor.fetchone()
            if not row_atual:
                return err("OS não encontrada.", 404)

            status_atual = normalizar_status_os(row_atual[0])
            data_finalizado_atual = row_atual[1]
            if (row_atual[2] == TIPO_OS_INTERNA) != interna:
                return err("Uma OS não pode virar interna, nem deixar de ser, depois de criada.")
            unidade_serializada_id = row_atual[3] if interna else None
            if interna:
                imei = row_atual[4]  # IMEI vem do aparelho comprado, não do formulário

            data_finalizado_valor = None
            if status_finalizado(status):
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            # V1.5 -- Garantia de Reparo (BR-061): mesma exigência de
            # atualizar_status_os -- este formulário completo também pode
            # levar a OS a Finalizado, não só o botão de status dedicado.
            # Valida contra os `reparo_ids` NOVOS (pós-edição), já que
            # `salvar_reparos_os` abaixo pode ter mudado a lista.
            resolvidos = []
            # BR-090 -- OS interna não concede Garantia de Reparo (não há cliente).
            if status_finalizado(status) and not status_finalizado(status_atual) and not interna:
                garantias_payload = body.get("garantias") or {}
                resolvidos, erro_garantia = resolver_garantias_reparo(
                    garantias_payload, reparo_ids, lambda tid: obter_tipo_garantia(conectar, tid)
                )
                if erro_garantia:
                    conn.rollback()
                    return err(erro_garantia)

            cursor.execute(
                """
                UPDATE os SET tipo=?,cliente=?,aparelho=?,tecnico=?,reparo_id=?,status=?,
                    valor_cobrado=?,valor_descontado=?,data=?,observacoes=?,modelo=?,vendedor=?,
                    cor=?,imei=?,data_finalizado=?
                WHERE id=?
                """,
                (
                    tipo,
                    cliente,
                    aparelho,
                    tecnico,
                    reparo_ids[0],
                    status,
                    valor_cobrado,
                    valor_descontado,
                    data_os,
                    observacoes,
                    modelo,
                    vendedor,
                    cor,
                    imei,
                    data_finalizado_valor,
                    os_id,
                ),
            )
            if atualizar_previsao:
                cursor.execute("UPDATE os SET data_previsao=? WHERE id=?", (data_previsao, os_id))
            _gravar_textos_os(cursor, os_id, body)
            salvar_reparos_os(cursor, os_id, reparo_ids)

            if resolvidos:
                data_ref = parse_data_ymd(data_finalizado_valor)
                data_inicio = data_ref.date() if data_ref else date.today()
                gravar_garantias_reparo(cursor, os_id, resolvidos, data_inicio)
                for reparo_id, tipo_garantia in resolvidos:
                    registrar_log_auditoria(
                        cursor,
                        "os_reparo",
                        os_id,
                        session.get("usuario_id"),
                        "garantia_concedida",
                        depois={
                            "reparo_id": reparo_id,
                            "tipo_garantia_id": tipo_garantia["id"],
                            "garantia_nome": tipo_garantia["nome"],
                            "garantia_duracao_meses": tipo_garantia["duracao_meses"],
                        },
                    )

            if status_cancelado(status) and not status_cancelado(status_atual):
                # BR-064 -- zera a Garantia de Reparo de qualquer linha já
                # concedida, na mesma transação do cancelamento.
                for linha in buscar_linhas_com_garantia_da_os(cursor, os_id):
                    (
                        reparo_id_linha,
                        tipo_garantia_id,
                        garantia_nome,
                        garantia_duracao_meses,
                        garantia_data_inicio,
                        garantia_data_fim,
                    ) = linha
                    zerar_garantia_reparo(cursor, os_id, reparo_id_linha)
                    registrar_log_auditoria(
                        cursor,
                        "os_reparo",
                        os_id,
                        session.get("usuario_id"),
                        "garantia_alterada",
                        antes={
                            "reparo_id": reparo_id_linha,
                            "tipo_garantia_id": tipo_garantia_id,
                            "garantia_nome": garantia_nome,
                            "garantia_duracao_meses": garantia_duracao_meses,
                            "garantia_data_inicio": garantia_data_inicio,
                            "garantia_data_fim": garantia_data_fim,
                        },
                        depois=None,
                    )

            if not status_cancelado(status_atual):
                devolver_pecas_da_os(cursor, os_id, "devolucao-edicao")
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))

            custo_total = 0.0
            for peca_id in pecas_ids:
                cursor.execute("SELECT valor, modelo FROM estoque WHERE id=?", (peca_id,))
                row = cursor.fetchone()
                valor_peca = float(row[0]) if row and row[0] is not None else 0.0
                modelo_peca = row[1] if row else ""
                if not modelo_compativel(modelo_peca, modelo):
                    conn.rollback()
                    return err("Peça incompatível com o modelo da OS.")
                if status_cancelado(status):
                    ok_peca, erro_peca = adicionar_peca_os_sem_consumir(cursor, os_id, peca_id)
                else:
                    ok_peca, erro_peca = consumir_peca_da_os(cursor, os_id, peca_id)
                if not ok_peca:
                    conn.rollback()
                    return err(erro_peca)
                custo_total += valor_peca

            cursor.execute("UPDATE os SET custo_pecas=? WHERE id=?", (round(custo_total, 2), os_id))
            if interna and unidade_serializada_id:
                erro_aparelho = _sincronizar_aparelho_da_os_interna(
                    cursor, os_id, unidade_serializada_id, status, status_atual
                )
                if erro_aparelho:
                    conn.rollback()
                    return err(erro_aparelho)
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_os.route("/ordens/<int:os_id>", methods=["DELETE"])
    def deletar_ordem(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT status, COALESCE(origem_integracao, ''), COALESCE(id_externo_integracao, '')
                FROM os
                WHERE id=?
                """,
                (os_id,),
            )
            row = cursor.fetchone()
            if row:
                s = normalizar_status_os(row[0])
                if not status_finalizado(s) and not status_cancelado(s):
                    devolver_pecas_da_os(cursor, os_id, "devolucao")

                origem_integracao = (row[1] or "").strip().lower()
                id_externo_integracao = (row[2] or "").strip()
                if origem_integracao == "mercado_phone" and id_externo_integracao:
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO integracao_os_vistas (origem, id_externo, primeira_visualizacao)
                        VALUES (?, ?, ?)
                        """,
                        (
                            "mercado_phone_bloqueada",
                            id_externo_integracao,
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        ),
                    )
            cursor.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os_checklists WHERE os_id=?", (os_id,))
            cursor.execute("DELETE FROM os WHERE id=?", (os_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_os.route("/ordens/<int:os_id>/status", methods=["PATCH"])
    def atualizar_status_os(os_id):
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "tecnico"):
            return err("Permissão negada.", 403)

        body = safe_json(request)
        status = normalizar_status_os(body.get("status") or "", status_padrao="")
        if not status:
            return err("Status inválido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT status, COALESCE(data_finalizado,''), COALESCE(tipo,''), unidade_serializada_id "
                "FROM os WHERE id=?",
                (os_id,),
            )
            row = cursor.fetchone()
            if not row:
                return err("OS não encontrada.", 404)
            status_atual = normalizar_status_os(row[0])
            data_finalizado_atual = row[1]
            interna = row[2] == TIPO_OS_INTERNA
            unidade_serializada_id = row[3]

            data_finalizado_valor = None
            if status_finalizado(status):
                data_finalizado_valor = data_finalizado_atual or datetime.now().strftime("%Y-%m-%d")

            # V1.5 -- Garantia de Reparo (BR-061): exige um Tipo de Garantia por
            # linha de reparo só na transição PARA Finalizado, nunca em toda
            # atualização subsequente que mantiver o status já finalizado.
            resolvidos = []
            # BR-090 -- OS interna não concede Garantia de Reparo (não há cliente).
            if status_finalizado(status) and not status_finalizado(status_atual) and not interna:
                reparo_ids = buscar_reparo_ids_da_os(cursor, os_id)
                garantias_payload = body.get("garantias") or {}
                resolvidos, erro_garantia = resolver_garantias_reparo(
                    garantias_payload, reparo_ids, lambda tid: obter_tipo_garantia(conectar, tid)
                )
                if erro_garantia:
                    conn.rollback()
                    return err(erro_garantia)

            cursor.execute(
                "UPDATE os SET status=?, data_finalizado=? WHERE id=?",
                (status, data_finalizado_valor, os_id),
            )

            if resolvidos:
                data_ref = parse_data_ymd(data_finalizado_valor)
                data_inicio = data_ref.date() if data_ref else date.today()
                gravar_garantias_reparo(cursor, os_id, resolvidos, data_inicio)
                for reparo_id, tipo_garantia in resolvidos:
                    registrar_log_auditoria(
                        cursor,
                        "os_reparo",
                        os_id,
                        session.get("usuario_id"),
                        "garantia_concedida",
                        depois={
                            "reparo_id": reparo_id,
                            "tipo_garantia_id": tipo_garantia["id"],
                            "garantia_nome": tipo_garantia["nome"],
                            "garantia_duracao_meses": tipo_garantia["duracao_meses"],
                        },
                    )

            if status_cancelado(status) and not status_cancelado(status_atual):
                devolver_pecas_da_os(cursor, os_id, "devolucao")
                # BR-064 -- zera a Garantia de Reparo de qualquer linha já
                # concedida, na mesma transação do cancelamento.
                for linha in buscar_linhas_com_garantia_da_os(cursor, os_id):
                    (
                        reparo_id,
                        tipo_garantia_id,
                        garantia_nome,
                        garantia_duracao_meses,
                        garantia_data_inicio,
                        garantia_data_fim,
                    ) = linha
                    zerar_garantia_reparo(cursor, os_id, reparo_id)
                    registrar_log_auditoria(
                        cursor,
                        "os_reparo",
                        os_id,
                        session.get("usuario_id"),
                        "garantia_alterada",
                        antes={
                            "reparo_id": reparo_id,
                            "tipo_garantia_id": tipo_garantia_id,
                            "garantia_nome": garantia_nome,
                            "garantia_duracao_meses": garantia_duracao_meses,
                            "garantia_data_inicio": garantia_data_inicio,
                            "garantia_data_fim": garantia_data_fim,
                        },
                        depois=None,
                    )

            if interna and unidade_serializada_id:
                erro_aparelho = _sincronizar_aparelho_da_os_interna(
                    cursor, os_id, unidade_serializada_id, status, status_atual
                )
                if erro_aparelho:
                    conn.rollback()
                    return err(erro_aparelho)

            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_os.route("/ordens/<int:os_id>/reparos/<int:reparo_id>/garantia", methods=["PATCH"])
    def corrigir_garantia_reparo_route(os_id, reparo_id):
        """V1.5 -- Garantia de Reparo (BR-065) -- só `admin`, sem motivo
        obrigatório, mesmo padrão de `corrigir_garantia_item` (Vendas)."""
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") != "admin":
            return err("Permissão negada.", 403)

        body = safe_json(request)
        tipo_garantia_id = parse_int(body.get("tipo_garantia_id"), default=None)
        if tipo_garantia_id is None:
            return err("tipo_garantia_id é obrigatório.")

        tipo_garantia = obter_tipo_garantia(conectar, tipo_garantia_id)
        if not tipo_garantia or not tipo_garantia["ativo"]:
            return err("Tipo de Garantia inválido ou inativo.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            linha = buscar_garantia_reparo(cursor, os_id, reparo_id)
            if not linha:
                conn.rollback()
                return err("Reparo não encontrado nesta OS.", 404)
            (
                tipo_garantia_id_anterior,
                garantia_nome_anterior,
                garantia_duracao_meses_anterior,
                garantia_data_inicio_anterior,
                garantia_data_fim_anterior,
            ) = linha

            data_ref = parse_data_ymd(garantia_data_inicio_anterior)
            data_inicio = data_ref.date() if data_ref else date.today()

            linhas_afetadas = corrigir_garantia_reparo(cursor, os_id, reparo_id, tipo_garantia, data_inicio)
            if linhas_afetadas == 0:
                conn.rollback()
                return err("OS não pode ser corrigida (cancelada ou em outro estado).")

            registrar_log_auditoria(
                cursor,
                "os_reparo",
                os_id,
                session.get("usuario_id"),
                "garantia_alterada",
                antes={
                    "reparo_id": reparo_id,
                    "tipo_garantia_id": tipo_garantia_id_anterior,
                    "garantia_nome": garantia_nome_anterior,
                    "garantia_duracao_meses": garantia_duracao_meses_anterior,
                    "garantia_data_inicio": garantia_data_inicio_anterior,
                    "garantia_data_fim": garantia_data_fim_anterior,
                },
                depois={
                    "reparo_id": reparo_id,
                    "tipo_garantia_id": tipo_garantia["id"],
                    "garantia_nome": tipo_garantia["nome"],
                    "garantia_duracao_meses": tipo_garantia["duracao_meses"],
                    "garantia_data_inicio": data_inicio.isoformat(),
                },
            )
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(os_id=os_id, reparo_id=reparo_id)

    @api_os.route("/ordens/<int:os_id>/reparos/<int:reparo_id>/historico-garantia")
    def historico_garantia_reparo_route(os_id, reparo_id):
        """Histórico de correções/zeragens da Garantia de Reparo da linha
        (BR-065) -- aberto a qualquer autenticado, mesmo padrão do histórico
        de desconto/garantia de Vendas."""
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        try:
            rows = buscar_historico_garantia_reparo(cursor, os_id, reparo_id)
        finally:
            conn.close()

        historico = [
            {
                "id": r[0],
                "acao": r[1],
                "valor_anterior": r[2],
                "valor_novo": r[3],
                "criado_em": r[4],
                "usuario_nome": r[5] or "",
            }
            for r in rows
        ]
        return ok(historico=historico)

    @api_os.route("/ordens/historico-cliente")
    def historico_cliente():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        cliente = (request.args.get("cliente") or "").strip()
        excluir_id = request.args.get("excluir_id", type=int)
        if not cliente:
            return ok(ordens=[])

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, tipo, modelo, data, status
            FROM os
            WHERE lower(cliente) = lower(?) AND id != ?
            ORDER BY id DESC LIMIT 10
            """,
            (cliente, excluir_id or -1),
        )
        rows = cursor.fetchall()
        reparos_por_os = obter_reparos_por_os(cursor)
        conn.close()

        ordens = []
        for r in rows:
            rinfo = reparos_por_os.get(r[0], {"nomes": []})
            ordens.append(
                {
                    "id": r[0],
                    "tipo": r[1] or "",
                    "modelo": r[2] or "",
                    "data": r[3] or "",
                    "status": normalizar_status_os(r[4]),
                    "reparos": rinfo.get("nomes", []),
                }
            )
        return ok(ordens=ordens)

    # ── REPAIR TYPES ───────────────────────────────────────────────────────

    @api_os.route("/reparos")
    def listar_reparos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nome FROM reparos ORDER BY nome")
        rows = cursor.fetchall()
        conn.close()
        return ok(reparos=[{"id": r[0], "nome": r[1]} for r in rows])

    @api_os.route("/reparos", methods=["POST"])
    def criar_reparo():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        nome = (body.get("nome") or "").strip()
        if not nome:
            return err("Informe o nome do reparo.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?)", (nome,))
            if cursor.fetchone():
                return err("Esse tipo de reparo já existe.")
            cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (nome,))
            novo_id = cursor.lastrowid
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok(id=novo_id), 201

    @api_os.route("/reparos/<int:reparo_id>", methods=["PUT"])
    def atualizar_reparo(reparo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        body = safe_json(request)
        nome = (body.get("nome") or "").strip()
        if not nome:
            return err("Informe um nome válido.")

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM reparos WHERE lower(nome)=lower(?) AND id<>?", (nome, reparo_id))
            if cursor.fetchone():
                return err("Já existe um reparo com esse nome.")
            cursor.execute("UPDATE reparos SET nome=? WHERE id=?", (nome, reparo_id))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    @api_os.route("/reparos/<int:reparo_id>", methods=["DELETE"])
    def deletar_reparo(reparo_id):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        conn = conectar()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT COUNT(*) FROM os_reparos WHERE reparo_id=?", (reparo_id,))
            if (cursor.fetchone()[0] or 0) > 0:
                return err("Não é possível excluir: reparo vinculado a OS.")
            cursor.execute("DELETE FROM reparos WHERE id=?", (reparo_id,))
            conn.commit()
        except Exception as exc:
            conn.rollback()
            return err(str(exc))
        finally:
            conn.close()

        return ok()

    return api_os
