import calendar
import os
import unicodedata
from datetime import datetime, timedelta


STATUS_EM_ANDAMENTO = "Em andamento"
STATUS_AGUARDANDO_PECA = "Aguardando peca"
STATUS_FINALIZADO = "Finalizado"
STATUS_CANCELADO = "Cancelado"
STATUS_OS_VALIDOS = {
    STATUS_EM_ANDAMENTO,
    STATUS_AGUARDANDO_PECA,
    STATUS_FINALIZADO,
    STATUS_CANCELADO,
}
STATUS_OS_OPCOES = [
    STATUS_EM_ANDAMENTO,
    STATUS_AGUARDANDO_PECA,
    STATUS_FINALIZADO,
    STATUS_CANCELADO,
]

# Tipo de OS não é validado contra lista fechada no backend hoje (aceita
# qualquer texto, só usa "Assistencia" como default) — esta lista é a fonte
# única de exibição (GET /api/constantes), não uma whitelist de gravação.
# BR-090 -- OS interna: conserto de aparelho comprado pela loja (Compra de Aparelhos).
TIPO_OS_INTERNA = "Interna"
OS_TIPOS_OPCOES = ["Assistencia", "Garantia", TIPO_OS_INTERNA]
CLIENTE_OS_INTERNA = "Estoque próprio"

# Prazo padrão de garantia de reparo (dias) — distinto da futura garantia de
# venda (docs/product/PRODUCT_GLOSSARY.md), que terá prazo próprio por tipo
# de aparelho quando o Épico Vendas existir.
GARANTIA_REPARO_DIAS_PADRAO = 90

# Perfis de usuário válidos — sem hierarquia entre eles (BR-003). "estoque"
# adicionado em 2026-07-25 (Sprint Segurança 1.0, docs/security/SECURITY_AUDIT_2026-07.md)
# junto da restrição de perfil nas rotas de mutação de Estoque. "financeiro"
# adicionado em 2026-07-29 (V1.4 -- Comissão, BR-044) -- acompanhamento
# financeiro das vendas, não substitui admin. Fonte única — usada tanto para
# validar o campo `perfil` na criação/edição de usuário quanto como cinto de
# segurança para rotas que checam perfil por lista explícita.
PERFIS_OPCOES = ["admin", "tecnico", "vendedor", "estoque", "financeiro"]


def texto_limpo(valor):
    return str(valor or "").strip()


def normalizar_busca_texto(valor):
    texto = unicodedata.normalize("NFKD", str(valor or "")).encode("ascii", "ignore").decode("ascii")
    texto = texto.lower().replace("-", " ").replace("/", " ")
    return " ".join(texto.split())


def normalizar_status_os(valor, status_padrao=STATUS_EM_ANDAMENTO):
    texto = normalizar_busca_texto(valor)
    if not texto:
        return status_padrao
    if "cancel" in texto:
        return STATUS_CANCELADO
    if "final" in texto or "entreg" in texto or "conclu" in texto:
        return STATUS_FINALIZADO
    if "aguard" in texto:
        return STATUS_AGUARDANDO_PECA
    if "andamento" in texto or "andando" in texto:
        return STATUS_EM_ANDAMENTO
    return status_padrao


def status_aguardando_peca(valor):
    return normalizar_status_os(valor) == STATUS_AGUARDANDO_PECA


def status_finalizado(valor):
    return normalizar_status_os(valor) == STATUS_FINALIZADO


def status_cancelado(valor):
    return normalizar_status_os(valor) == STATUS_CANCELADO


def status_aberto(valor):
    status_norm = normalizar_status_os(valor)
    return status_norm not in {STATUS_FINALIZADO, STATUS_CANCELADO}


def normalizar_data_previsao(valor):
    """BR-101 -- previsão de entrega da OS: `YYYY-MM-DD` ou vazio (sem previsão).
    Retorna (data_ou_None, erro)."""
    texto = (valor or "").strip() if isinstance(valor, str) else ("" if valor is None else str(valor))
    if not texto:
        return None, None
    try:
        return datetime.strptime(texto, "%Y-%m-%d").strftime("%Y-%m-%d"), None
    except ValueError:
        return None, "Data de previsão inválida (use AAAA-MM-DD)."


# BR-102 -- textos livres da OS além de `observacoes`. Os dois primeiros saem no documento do
# cliente; `observacao_interna` nunca sai da loja.
CAMPOS_TEXTO_OS = ("relato_cliente", "laudo_tecnico", "observacao_interna")
CAMPOS_TEXTO_OS_DOCUMENTO = ("relato_cliente", "laudo_tecnico")


def os_atrasada(status, data_previsao, hoje=None):
    """BR-101 -- atrasada = ainda aberta (nem finalizada nem cancelada) e previsão já passou.
    Vence no fim do dia da previsão: no próprio dia ainda não está atrasada."""
    if not data_previsao or not status_aberto(status):
        return False
    hoje_txt = (hoje or datetime.now().date()).strftime("%Y-%m-%d")
    return data_previsao < hoje_txt


def coletar_status_opcoes(rows, status_index):
    return sorted({normalizar_status_os(row[status_index]) for row in rows if row[status_index]})


def calcular_faturamento_os(valor_cobrado, valor_descontado):
    """Valor da OS. `valor_descontado` é o preço final com desconto (campo "Valor com
    Desconto"), não o valor do desconto: quando preenchido, é ele que vale; sem ele, vale
    o Valor Cobrado (KI-059, decisão do CTO em 2026-11-10)."""
    valor_cobrado = valor_cobrado or 0
    valor_descontado = valor_descontado or 0
    return valor_descontado if valor_descontado > 0 else valor_cobrado


def calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo):
    if tipo in {"Assistencia", "Assistência", "Upgrade"}:
        return calcular_faturamento_os(valor_cobrado, valor_descontado) - (custo or 0)
    return -(custo or 0)


def calcular_data_fim_garantia(data_inicio, duracao_meses):
    """V1.5 -- Garantia (BR-057/BR-062, docs/engineering/plans/PLAN-V1.5-Garantia.md). Soma meses
    de calendário a partir de `data_inicio` (um `date`), tratando o caso do dia de origem não
    existir no mês de destino (ex.: 31/01 + 1 mês -> 28/02 ou 29/02, nunca "03/03"). Função pura,
    única em todo o projeto -- compartilhada entre Vendas e Assistência para nunca divergir entre
    os dois domínios."""
    mes_total = data_inicio.month - 1 + duracao_meses
    ano = data_inicio.year + mes_total // 12
    mes = mes_total % 12 + 1
    ultimo_dia_do_mes = calendar.monthrange(ano, mes)[1]
    dia = min(data_inicio.day, ultimo_dia_do_mes)
    return data_inicio.replace(year=ano, month=mes, day=dia)


def to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _limite_inatividade_minutos():
    try:
        return int(os.environ.get("IR_FLOW_SESSION_INACTIVITY_MINUTES", "30"))
    except (TypeError, ValueError):
        return 30


def sessao_ainda_ativa(session, agora=None):
    """
    Janela deslizante de inatividade de sessão. Retorna False se a sessão está
    inativa há mais tempo que IR_FLOW_SESSION_INACTIVITY_MINUTES (default 30).

    Em toda checagem que não expira, atualiza `session["_ultima_atividade"]`
    para o instante atual — cada request autenticado reseta o timer.

    Sessões sem "_ultima_atividade" (criadas antes desta funcionalidade
    existir, ou logo após o login) são tratadas como ativas agora, não
    expiradas de imediato — evita derrubar sessões em andamento no momento
    do deploy.

    Quem chama é responsável por checar `usuario_id` antes — esta função não
    avalia se a sessão está autenticada, só há quanto tempo está inativa.
    """
    agora = agora or datetime.now()
    ultima_atividade_str = session.get("_ultima_atividade")

    if ultima_atividade_str:
        try:
            ultima_atividade = datetime.fromisoformat(ultima_atividade_str)
        except (TypeError, ValueError):
            ultima_atividade = agora
        if agora - ultima_atividade > timedelta(minutes=_limite_inatividade_minutos()):
            return False

    session["_ultima_atividade"] = agora.isoformat()
    return True
