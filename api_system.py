"""
Fluxoly - API Blueprint (Sistema)
Rotas /api/constantes, /api/alertas, /api/dashboard -- consumidas pelo
frontend React (constantes de referência, alertas de sistema e agregados do
dashboard). Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 10º
domínio extraído).
"""

from datetime import date, timedelta

from flask import Blueprint, request, session

import fluxoly_compras_aparelhos_service as compras_aparelhos_service
import fluxoly_contas_pagar_service as contas_pagar_service
import fluxoly_contas_receber_service as contas_receber_service
import fluxoly_vendas_service as vendas_service

from fluxoly_api_helpers import err, ok, usuario_logado
from fluxoly_core import TIPO_OS_INTERNA


def create_api_system_blueprint(deps):
    api_system = Blueprint("api_system", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    normalizar_status_os = deps["normalizar_status_os"]
    status_finalizado = deps["status_finalizado"]
    status_cancelado = deps["status_cancelado"]
    status_aberto = deps["status_aberto"]
    calcular_faturamento_os = deps["calcular_faturamento_os"]
    calcular_lucro_os = deps["calcular_lucro_os"]
    carregar_os_com_relacoes = deps["carregar_os_com_relacoes"]
    listar_custos_operacionais = deps["listar_custos_operacionais"]
    obter_alertas_sistema = deps["obter_alertas_sistema"]
    iphone_models = deps["iphone_models"]
    iphone_colors = deps["iphone_colors"]
    vendedores = deps["vendedores"]
    tecnicos = deps["tecnicos"]
    status_os_opcoes = deps["status_os_opcoes"]
    os_tipos_opcoes = deps["os_tipos_opcoes"]
    garantia_reparo_dias_padrao = deps["garantia_reparo_dias_padrao"]
    categorias_custos = deps["categorias_custos"]
    reparos_padrao = deps["reparos_padrao"]
    produtos_categorias = deps["produtos_categorias"]
    produtos_condicoes = deps["produtos_condicoes"]
    estoque_tipos = deps["estoque_tipos"]
    estoque_qualidades = deps["estoque_qualidades"]

    def _sanitize_list(arr):
        if not isinstance(arr, list | tuple):
            return arr
        out = []
        for v in arr:
            if v is None:
                continue
            if isinstance(v, str):
                s = v.strip()
                if s == "":
                    continue
                out.append(s)
            else:
                out.append(v)
        return out

    def _sanitize_nested_obj(obj):
        if not isinstance(obj, dict):
            return obj
        out = {}
        for k, v in obj.items():
            if isinstance(v, list | tuple):
                out[k] = _sanitize_list(v)
            else:
                out[k] = v
        return out

    @api_system.route("/constantes")
    def constantes():
        payload = {
            "iphone_models": _sanitize_list(iphone_models),
            "iphone_colors": _sanitize_nested_obj(iphone_colors),
            "vendedores": _sanitize_list(vendedores),
            "tecnicos": _sanitize_list(tecnicos),
            "status_opcoes": _sanitize_list(status_os_opcoes),
            "os_tipos": _sanitize_list(os_tipos_opcoes),
            "categorias_custos": _sanitize_list(categorias_custos),
            "estoque_tipos": _sanitize_list(estoque_tipos),
            "estoque_qualidades": _sanitize_list(estoque_qualidades),
            "reparos_padrao": _sanitize_list(reparos_padrao),
            "produtos_categorias": _sanitize_list(produtos_categorias),
            "produtos_condicoes": _sanitize_list(produtos_condicoes),
            "garantia_dias": garantia_reparo_dias_padrao,
        }
        return ok(**payload)

    # ── ALERTS ─────────────────────────────────────────────────────────────

    @api_system.route("/alertas")
    def alertas():
        if not usuario_logado():
            return ok(alertas=[])
        try:
            alerts = obter_alertas_sistema(limit=20)
        except Exception:
            alerts = []
        return ok(alertas=alerts)

    # ── PENDÊNCIAS DA TELA INICIAL ─────────────────────────────────────────

    @api_system.route("/pendencias")
    def pendencias():
        """PLAN-pendencias-tela-inicial.md -- contas a pagar/receber vencidas e que vencem hoje.
        Valor financeiro: só admin/financeiro (mesmo critério do módulo Financeiro). `hoje` é a data
        do servidor (UTC em produção -- KI-061)."""
        if not usuario_logado():
            return err("Não autenticado.", 401)
        if session.get("usuario_perfil") not in ("admin", "financeiro"):
            return err("Permissão negada.", 403)
        hoje = date.today().isoformat()
        return ok(
            hoje=hoje,
            contas_pagar=contas_pagar_service.resumir_pendencias(conectar, hoje),
            contas_receber=contas_receber_service.resumir_pendencias(conectar, hoje),
        )

    # ── DASHBOARD ──────────────────────────────────────────────────────────

    @api_system.route("/dashboard")
    def dashboard():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        filtro_tecnico = (request.args.get("tecnico") or "").strip()

        conn = conectar()
        cursor = conn.cursor()
        dados, reparos_por_os, custos = carregar_os_com_relacoes(cursor, order_by="os.id DESC")

        lucro_total = faturamento_total = custo_consumido_periodo = 0.0
        ordens_finalizadas = ordens_abertas = 0
        lucro_por_tecnico = {}
        resumo_por_vendedor = {}
        servicos_mais_feitos = {}
        faturamento_por_dia = {}

        for os_item in dados:
            os_id = os_item[0]
            tipo = os_item[1]
            tecnico = os_item[4]
            status = normalizar_status_os(os_item[6])
            valor_cobrado = os_item[7]
            valor_descontado = os_item[8]
            data = os_item[10]
            vendedor = os_item[13]

            # BR-090 -- OS interna (conserto de aparelho comprado) não é serviço para cliente:
            # fora do faturamento, do lucro e dos totais de assistência.
            if tipo == TIPO_OS_INTERNA:
                continue

            custo = custos.get(os_id, 0)
            lucro = calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo)
            faturamento_os = calcular_faturamento_os(valor_cobrado, valor_descontado)

            if filtro_tecnico and tecnico != filtro_tecnico:
                continue
            if (start_date or end_date) and not data:
                continue
            if start_date and data and data < start_date:
                continue
            if end_date and data and data > end_date:
                continue

            if not status_cancelado(status):
                custo_consumido_periodo += custo

            if status_finalizado(status):
                lucro_total += lucro
                faturamento_total += faturamento_os
                ordens_finalizadas += 1
                if data:
                    faturamento_por_dia[data] = faturamento_por_dia.get(data, 0) + faturamento_os
            elif status_aberto(status):
                ordens_abertas += 1

            for reparo_nome in reparos_por_os.get(os_id, {}).get("nomes", []) or [tipo]:
                if reparo_nome:
                    servicos_mais_feitos[reparo_nome] = servicos_mais_feitos.get(reparo_nome, 0) + 1

            if tecnico and status_finalizado(status):
                lucro_por_tecnico[tecnico] = lucro_por_tecnico.get(tecnico, 0) + lucro

            if vendedor:
                if vendedor not in resumo_por_vendedor:
                    resumo_por_vendedor[vendedor] = {"os_total": 0, "faturamento": 0, "lucro": 0}
                resumo_por_vendedor[vendedor]["os_total"] += 1
                if status_finalizado(status):
                    resumo_por_vendedor[vendedor]["lucro"] += lucro
                    resumo_por_vendedor[vendedor]["faturamento"] += faturamento_os

        cursor.execute("SELECT COALESCE(SUM(valor * quantidade), 0) FROM estoque")
        gasto_total = cursor.fetchone()[0] or 0
        conn.close()

        resumo_custos = listar_custos_operacionais(start_date, end_date)
        custos_operacionais_periodo = resumo_custos["total_periodo"]
        resultado_liquido = lucro_total - custos_operacionais_periodo
        ticket_medio = round(faturamento_total / ordens_finalizadas, 2) if ordens_finalizadas else 0

        dias_ordenados = sorted(faturamento_por_dia.keys())
        servicos_sorted = sorted(servicos_mais_feitos.items(), key=lambda x: x[1], reverse=True)
        lucro_tecnicos_sorted = sorted(lucro_por_tecnico.items(), key=lambda x: x[1], reverse=True)

        # Contadores de shopping list
        try:
            conn2 = conectar()
            cur2 = conn2.cursor()
            cur2.execute("SELECT COUNT(1) FROM shopping_list WHERE status='PENDENTE'")
            shopping_pendentes = int(cur2.fetchone()[0] or 0)
            cur2.execute("SELECT COUNT(1) FROM shopping_list WHERE prioridade='URGENTE' AND status!='CANCELADO'")
            shopping_urgentes = int(cur2.fetchone()[0] or 0)
            conn2.close()
        except Exception:
            shopping_pendentes = 0
            shopping_urgentes = 0

        # Dashboard somando vendas e OS (PLAN-dashboard-vendas-os.md). `faturamento_total`,
        # `lucro_total` e `ticket_medio` continuam sendo só de OS (compatibilidade); vendas e o
        # consolidado vêm em chaves próprias. Lucro de aparelho (BR-092) só para admin/financeiro.
        inicio_vendas = f"{start_date} 00:00:00" if start_date else None
        fim_vendas = None
        if end_date:
            try:
                fim_vendas = f"{date.fromisoformat(end_date) + timedelta(days=1)} 00:00:00"
            except ValueError:
                fim_vendas = None
        resumo_vendas = vendas_service.resumir_vendas_periodo(conectar, inicio_vendas, fim_vendas)
        if session.get("usuario_perfil") in ("admin", "financeiro"):
            resumo_vendas["lucro_aparelhos"] = compras_aparelhos_service.resumir_lucro_aparelhos_vendidos(
                conectar, inicio_vendas or "0000-01-01 00:00:00", fim_vendas or "9999-12-31 23:59:59"
            )
        faturamento_consolidado = round(faturamento_total + resumo_vendas["faturamento"], 2)
        atendimentos = ordens_finalizadas + resumo_vendas["quantidade"]

        return ok(
            vendas=resumo_vendas,
            consolidado={
                "faturamento": faturamento_consolidado,
                "faturamento_os": round(faturamento_total, 2),
                "faturamento_vendas": resumo_vendas["faturamento"],
                "ticket_medio": round(faturamento_consolidado / atendimentos, 2) if atendimentos else 0,
            },
            faturamento_total=round(faturamento_total, 2),
            lucro_total=round(lucro_total, 2),
            custo_consumido_periodo=round(custo_consumido_periodo, 2),
            custos_operacionais_periodo=round(custos_operacionais_periodo, 2),
            resultado_liquido=round(resultado_liquido, 2),
            ticket_medio=ticket_medio,
            gasto_total_estoque=round(gasto_total, 2),
            ordens_finalizadas=ordens_finalizadas,
            ordens_abertas=ordens_abertas,
            shopping_pendentes=shopping_pendentes,
            shopping_urgentes=shopping_urgentes,
            faturamento_por_dia=[{"date": d, "value": round(faturamento_por_dia[d], 2)} for d in dias_ordenados],
            lucro_por_tecnico=[{"name": k, "value": round(v, 2)} for k, v in lucro_tecnicos_sorted],
            servicos_mais_feitos=[{"name": k, "value": v} for k, v in servicos_sorted[:10]],
            resumo_por_vendedor=[
                {"vendedor": k, **{kk: round(vv, 2) if isinstance(vv, float) else vv for kk, vv in v.items()}}
                for k, v in sorted(resumo_por_vendedor.items(), key=lambda x: x[1]["faturamento"], reverse=True)
            ],
            custos_por_categoria=resumo_custos["por_categoria"],
        )

    return api_system
