from flask import Blueprint, request, send_from_directory

from fluxoly_web import redirecionar_com_query_string


def create_main_blueprint(deps):
    bp = Blueprint("main_views", __name__)
    formatar_periodo_relatorio = deps["formatar_periodo_relatorio"]
    montar_linhas_relatorio_tecnicos = deps["montar_linhas_relatorio_tecnicos"]
    montar_pdf_texto = deps["montar_pdf_texto"]
    backup_dir = deps["backup_dir"]

    @bp.route("/")
    @bp.route("/dashboard")
    @bp.route("/dashboard/")
    @bp.route("/dashboard.html")
    @bp.route("/index")
    @bp.route("/index.html")
    def index():
        return redirecionar_com_query_string(request, "/app")

    @bp.route("/relatorios")
    def relatorios():
        return redirecionar_com_query_string(request, "/app/relatorios")

    @bp.route("/relatorios/pdf/tecnicos")
    def relatorio_pdf_tecnicos():
        data_inicio = (request.args.get("start_date") or request.args.get("data_ini") or "").strip()
        data_fim = (request.args.get("end_date") or request.args.get("data_fim") or "").strip()
        linhas = montar_linhas_relatorio_tecnicos(data_inicio, data_fim)
        periodo = formatar_periodo_relatorio(data_inicio, data_fim)
        return montar_pdf_texto(
            "Relatorio Mensal - Tecnicos",
            f"Servicos finalizados por tecnico com gastos e lucro. Periodo: {periodo}",
            linhas,
            "relatorio-tecnicos.pdf",
        )

    @bp.route("/kanban")
    def kanban():
        return redirecionar_com_query_string(request, "/app/kanban")

    @bp.route("/garantias")
    def garantias():
        return redirecionar_com_query_string(request, "/app/garantias")

    @bp.route("/backup")
    def backup():
        return redirecionar_com_query_string(request, "/app/backup")

    @bp.route("/backup/download/<path:nome>")
    def backup_download(nome):
        return send_from_directory(backup_dir, nome, as_attachment=True)

    return bp
