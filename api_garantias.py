"""
Fluxoly - API Blueprint (Garantias)
Rota /api/garantias (listagem agregada) -- consumida pelo frontend React (Garantias.jsx).
Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 2º domínio extraído).
"""

from datetime import datetime, timedelta

from flask import Blueprint, request

from fluxoly_api_helpers import err, ok, usuario_logado


def create_api_garantias_blueprint(deps):
    api_garantias = Blueprint("api_garantias", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    garantia_reparo_dias_padrao = deps["garantia_reparo_dias_padrao"]
    parse_data_ymd = deps["parse_data_ymd"]

    def _classificar_garantia(dias_restantes):
        if dias_restantes is None:
            return "Sem data", "gray"
        if dias_restantes < 0:
            return "Vencida", "red"
        if dias_restantes <= 7:
            return f"Vence em {dias_restantes}d", "amber"
        return f"{dias_restantes} dias", "green"

    @api_garantias.route("/garantias")
    def listar_garantias():
        """V1.5 -- Garantia de Reparo (BR-062/BR-063): uma entrada por linha
        de `os_reparos`, não mais uma por OS -- uma OS com 3 reparos gera até
        3 entradas, cada uma com seu próprio prazo. Chave da resposta
        continua `ordens` por compatibilidade com os consumidores existentes
        (`Garantias.jsx`, `Clientes.jsx`), mesmo a granularidade tendo mudado.
        Linhas com `tipo_garantia_id` gravado (concedidas a partir da V1.5)
        usam o snapshot (`garantia_data_fim`) direto; linhas sem isso (dado
        histórico, anterior à V1.5, ou isentas por BR-061 como sync do
        Mercado Phone) caem no fallback do prazo fixo
        (`GARANTIA_REPARO_DIAS_PADRAO`) a partir de `data_finalizado` -- nunca
        inventa uma garantia que não foi de fato concedida."""
        if not usuario_logado():
            return err("Não autenticado.", 401)

        q = (request.args.get("q") or "").strip().lower()
        hoje = datetime.now().date()
        garantia_dias = garantia_reparo_dias_padrao

        conn = conectar()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT os.id, os.cliente, os.modelo, os.tecnico,
                   COALESCE(os.data_finalizado,''), COALESCE(os.data,''), COALESCE(os.imei,''),
                   COALESCE(os.origem_integracao,''), COALESCE(os.id_externo_integracao,''),
                   os_reparos.reparo_id, COALESCE(reparos.nome,''),
                   os_reparos.tipo_garantia_id, COALESCE(os_reparos.garantia_data_fim,'')
            FROM os
            JOIN os_reparos ON os_reparos.os_id = os.id
            JOIN reparos ON reparos.id = os_reparos.reparo_id
            WHERE os.status='Finalizado'
            ORDER BY os.id DESC, reparos.nome ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()

        result = []
        for r in rows:
            (
                os_id,
                cliente,
                modelo,
                tecnico,
                data_fin,
                data_os,
                imei,
                origem_integracao,
                id_externo_integracao,
                reparo_id,
                reparo_nome,
                tipo_garantia_id,
                garantia_data_fim_raw,
            ) = r
            if q and q not in f"{cliente} {modelo} {imei} {reparo_nome}".lower():
                continue

            if tipo_garantia_id is not None:
                fim_dt = parse_data_ymd(garantia_data_fim_raw)
                fim = fim_dt.date() if fim_dt else None
            else:
                base = parse_data_ymd(data_fin) or parse_data_ymd(data_os)
                fim = (base + timedelta(days=garantia_dias)).date() if base else None

            dias_restantes = (fim - hoje).days if fim else None
            label, color = _classificar_garantia(dias_restantes)

            result.append(
                {
                    "id": os_id,
                    "reparo_id": reparo_id,
                    "reparo_nome": reparo_nome or "",
                    "cliente": cliente or "",
                    "modelo": modelo or "",
                    "tecnico": tecnico or "",
                    "imei": imei or "",
                    "data_finalizado": data_fin or data_os,
                    "origem_integracao": origem_integracao or "",
                    "id_externo_integracao": id_externo_integracao or "",
                    "garantia": {"dias_restantes": dias_restantes, "label": label, "color": color},
                }
            )

        total = len(result)
        ativas = len([r for r in result if r["garantia"]["color"] == "green"])
        vencendo = len([r for r in result if r["garantia"]["color"] == "amber"])
        vencidas = len([r for r in result if r["garantia"]["color"] == "red"])

        return ok(
            ordens=result,
            total=total,
            ativas=ativas,
            vencendo=vencendo,
            vencidas=vencidas,
        )

    return api_garantias
