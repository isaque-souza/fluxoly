"""
Fluxoly - API Blueprint (Relatórios)
Rotas /api/relatorios/* (JSON agregado + PDF) -- consumidas pelo frontend
React (Relatorios.jsx). Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2
-- 8º domínio extraído).
"""

from flask import Blueprint, request

from fluxoly_api_helpers import err, ok, usuario_logado


def create_api_reports_blueprint(deps):
    api_reports = Blueprint("api_reports", __name__, url_prefix="/api")
    agrupar_relatorio_tecnicos = deps["agrupar_relatorio_tecnicos"]
    agrupar_relatorio_custos_operacionais = deps["agrupar_relatorio_custos_operacionais"]
    montar_linhas_relatorio_tecnicos = deps["montar_linhas_relatorio_tecnicos"]
    montar_linhas_relatorio_custos_operacionais = deps["montar_linhas_relatorio_custos_operacionais"]
    formatar_periodo_relatorio = deps["formatar_periodo_relatorio"]
    montar_pdf_texto = deps["montar_pdf_texto"]

    @api_reports.route("/relatorios/tecnicos")
    def relatorio_tecnicos():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_tecnicos(start_date, end_date)
        return ok(meses=resumo)

    @api_reports.route("/relatorios/custos-operacionais")
    def relatorio_custos_operacionais():
        if not usuario_logado():
            return err("Não autenticado.", 401)

        start_date = (request.args.get("start_date") or "").strip()
        end_date = (request.args.get("end_date") or "").strip()
        resumo = agrupar_relatorio_custos_operacionais(start_date, end_date)
        total_lancamentos = sum(v["total_itens"] for v in resumo.values())
        total_custos = sum(v["total_valor"] for v in resumo.values())

        categorias = {}
        for mes in resumo.values():
            for categoria, valor in (mes.get("categorias") or {}).items():
                categorias[categoria] = categorias.get(categoria, 0) + valor

        categorias_ordenadas = dict(sorted(categorias.items(), key=lambda item: (-item[1], item[0])))
        return ok(
            meses=resumo,
            total_lancamentos=total_lancamentos,
            total_custos=round(total_custos, 2),
            categorias=categorias_ordenadas,
        )

    @api_reports.route("/relatorios/pdf/tecnicos")
    def pdf_tecnicos():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_tecnicos(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Tecnicos",
            f"Servicos finalizados por tecnico com gastos e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-tecnicos.pdf",
        )

    @api_reports.route("/relatorios/pdf/custos-operacionais")
    def pdf_custos_operacionais():
        if not usuario_logado():
            return err("Não autenticado.", 401)
        data_inicio = (request.args.get("start_date") or "").strip()
        data_fim = (request.args.get("end_date") or "").strip()
        linhas = montar_linhas_relatorio_custos_operacionais(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Custos Operacionais",
            f"Custos operacionais agregados por mes e categoria. Periodo: {periodo}",
            linhas,
            "relatorio-custos-operacionais.pdf",
        )

    return api_reports
