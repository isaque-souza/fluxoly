"""
Configuração de ambiente, paths e feature-flags do Fluxoly.

TD-02 Fatia 1 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- extraído do bloco B de
app.py (linhas 158-256 antes desta extração). Só leitura de os.environ e derivação de constantes --
zero dependência de Flask, zero I/O além da criação/cópia de arquivos de dados que já existia no
bloco original (idempotente, mesmo comportamento de antes).
"""

import os
import shutil
import sys

# ============================================================================
# CONFIGURAÇÃO DE AMBIENTE E CAMINHOS
# ============================================================================
if getattr(sys, "frozen", False):
    # Executável PyInstaller (desktop)
    APP_DIR = os.path.dirname(sys.executable)
    RESOURCE_DIR = getattr(sys, "_MEIPASS", APP_DIR)
    USER_BASE = os.environ.get("LOCALAPPDATA") or APP_DIR
    DATA_DIR = os.path.join(USER_BASE, "IR Flow")
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))
    RESOURCE_DIR = APP_DIR
    # Em produção (Fly/Render), usa diretório persistente quando configurado.
    # Em desenvolvimento local, usa o próprio diretório da app.
    SERVER_DATA_DIR = (
        os.environ.get("IR_FLOW_DATA_DIR") or os.environ.get("FLY_DATA_DIR") or os.environ.get("RENDER_DISK_PATH")
    )
    if not SERVER_DATA_DIR and os.path.isdir("/data"):
        SERVER_DATA_DIR = "/data"
    DATA_DIR = SERVER_DATA_DIR or APP_DIR

os.makedirs(DATA_DIR, exist_ok=True)

# ============================================================================
# CONFIGURAÇÃO DE BANCO DE DADOS
# ============================================================================
DB_PATH = os.path.join(DATA_DIR, "database.db")
SEED_DB_PATH = os.path.join(APP_DIR, "database.db")
INTEGRATIONS_CONFIG_PATH = os.path.join(DATA_DIR, "integrations.json")

if getattr(sys, "frozen", False) and not os.path.exists(DB_PATH) and os.path.exists(SEED_DB_PATH):
    shutil.copy2(SEED_DB_PATH, DB_PATH)

# ============================================================================
# CONFIGURAÇÃO DE BACKUP E ARMAZENAMENTO
# ============================================================================
BACKUP_DIR = os.path.join(DATA_DIR, "backups")
IS_SERVER_RUNTIME = bool(
    os.environ.get("IR_FLOW_DATA_DIR")
    or os.environ.get("FLY_DATA_DIR")
    or os.environ.get("RENDER_DISK_PATH")
    or os.environ.get("RENDER")
    or os.environ.get("RENDER_SERVICE_ID")
)
# IS_PULL_REQUEST: variável setada automaticamente pelo Render em todo PR Preview
# (confirmada presente e "true" no shell de um preview real -- ver INC-003). Não
# existe em produção nem em desenvolvimento local. IS_SERVER_RUNTIME sozinha não
# basta para identificar um preview -- ela é verdadeira tanto em produção quanto
# em preview (ambos setam RENDER/RENDER_SERVICE_ID).
IS_PULL_REQUEST = os.environ.get("IS_PULL_REQUEST", "").strip().lower() == "true"

# IR_FLOW_ENVIRONMENT=demo: sinal manual de ambiente (ADR-012), distinto de
# IS_PULL_REQUEST (que o Render seta sozinho em todo PR Preview). Os dois
# coexistem -- nenhum substitui o outro. Só o valor "demo" tem efeito; qualquer
# outro valor (incluindo ausente/vazio) é tratado como produção/desenvolvimento.
IR_FLOW_ENVIRONMENT = os.environ.get("IR_FLOW_ENVIRONMENT", "").strip().lower()
IS_DEMO_ENVIRONMENT = IR_FLOW_ENVIRONMENT == "demo"

BACKGROUND_JOBS_ENABLED = (
    os.environ.get("IR_FLOW_ENABLE_BACKGROUND_JOBS", "1").strip().lower()
    not in {
        "0",
        "false",
        "nao",
        "off",
    }
    and not IS_PULL_REQUEST
    and not IS_DEMO_ENVIRONMENT
)
# ^ INC-003: um Render PR Preview herda todas as variáveis de ambiente do
# serviço-base, inclusive IR_FLOW_ENABLE_BACKGROUND_JOBS=1 e as credenciais de
# integrações externas. IS_PULL_REQUEST desliga background jobs (sync MercadoPhone,
# backup automático) incondicionalmente em qualquer preview, mesmo que o valor
# herdado de IR_FLOW_ENABLE_BACKGROUND_JOBS diga o contrário -- não é possível
# confiar em alguém lembrar de sobrescrever essa variável manualmente a cada
# preview novo (ver docs/engineering/plans/PLAN-preview-seguro-inc003-ki035.md).
# IS_DEMO_ENVIRONMENT segue a mesma lógica (ADR-012) para o ambiente Demo.


def integracao_externa_bloqueada_neste_ambiente():
    """Ponto único de verdade para o guard do KI-037 (Preview ou Demo).

    Evita duplicar `IS_PULL_REQUEST or IS_DEMO_ENVIRONMENT` nos 4 endpoints de
    escrita/ação de `api_mercadophone.py` -- ver ADR-012 e
    docs/engineering/plans/PLAN-ambiente-demo-homologacao.md.
    """
    return IS_PULL_REQUEST or IS_DEMO_ENVIRONMENT


# ADR-014: a integração MercadoPhone fica desligada por padrão (desvínculo com a IR Phones). Com a flag
# desligada, as rotas /api/integracoes/mercadophone/* respondem 404 e o sync em background não inicia,
# mesmo com token configurado no ambiente ou em integrations.json. Religar: MERCADO_PHONE_INTEGRATION_ENABLED=1.
MERCADO_PHONE_INTEGRATION_ENABLED = os.environ.get("MERCADO_PHONE_INTEGRATION_ENABLED", "0") == "1"


def integracao_mercadophone_habilitada():
    """Ponto único de verdade da flag ADR-014. Lê o atributo do módulo a cada chamada (não uma cópia
    importada), para que testes possam alternar a flag via monkeypatch -- mesmo padrão do KI-037."""
    return MERCADO_PHONE_INTEGRATION_ENABLED


APP_HOST = os.environ.get("IR_FLOW_HOST", "0.0.0.0" if IS_SERVER_RUNTIME else "127.0.0.1")
APP_PORT = int(os.environ.get("IR_FLOW_PORT", "5080"))
VERCEL_URL = (os.environ.get("VERCEL_URL") or "").strip()  # Ex: https://assistencia-system.vercel.app


def _normalizar_url_publica(valor):
    texto = (valor or "").strip().rstrip("/")
    if not texto:
        return ""
    if texto.startswith("http://") or texto.startswith("https://"):
        return texto
    return f"https://{texto}"


PUBLIC_BASE_URL = _normalizar_url_publica(os.environ.get("IR_FLOW_PUBLIC_BASE_URL")) or _normalizar_url_publica(
    VERCEL_URL
)
# KI-043: os destinos externos de backup (Google Drive, e-mail) foram removidos em 2026-11-06 -- o backup
# fica só no disco local (BACKUP_DIR). IR_FLOW_GOOGLE_DRIVE_BACKUP_DIR / IR_FLOW_BACKUP_EMAIL* não são
# mais lidas.


def _parse_dias_retencao(valor):
    """KI-044 decisão 6 (PLAN-LGPD-Compliance.md): sem valor configurado (ou valor inválido/não
    positivo), retorna None -- ausência de prazo real desliga a rotina de manutenção do audit_log por
    completo, nunca um número inventado pela engenharia."""
    valor = (valor or "").strip()
    if not valor:
        return None
    try:
        dias = int(valor)
    except ValueError:
        return None
    return dias if dias > 0 else None


# Prazos de mascaramento/expurgo de PII em audit_log -- deliberadamente sem default. Aguardam decisão
# jurídica/operacional (não de engenharia); até lá, iniciar_thread_manutencao_audit_log() nunca é
# chamada em app.py.
AUDIT_LOG_PII_MASK_APOS_DIAS = _parse_dias_retencao(os.environ.get("AUDIT_LOG_PII_MASK_APOS_DIAS"))
AUDIT_LOG_EXPURGO_APOS_DIAS = _parse_dias_retencao(os.environ.get("AUDIT_LOG_EXPURGO_APOS_DIAS"))

# Tabelas de preço ficam no volume persistente; na primeira execução, copia o
# arquivo de referência embutido no código para o diretório de dados.
_PRICE_TABLES_SEED = os.path.join(RESOURCE_DIR, "data", "price_tables.json")
PRICE_TABLES_PATH = os.path.join(DATA_DIR, "data", "price_tables.json")
os.makedirs(os.path.dirname(PRICE_TABLES_PATH), exist_ok=True)
if not os.path.exists(PRICE_TABLES_PATH) and os.path.exists(_PRICE_TABLES_SEED):
    shutil.copy2(_PRICE_TABLES_SEED, PRICE_TABLES_PATH)

# ============================================================================
# CONFIGURAÇÃO MERCADOPHONE
# ============================================================================
MERCADO_PHONE_WEBHOOK_TOKEN = os.environ.get("MERCADO_PHONE_WEBHOOK_TOKEN", "")
MERCADO_PHONE_DEFAULT_TECNICO = os.environ.get("MERCADO_PHONE_DEFAULT_TECNICO", "Aguardando definicao")
MERCADO_PHONE_API_BASE = os.environ.get(
    "MERCADO_PHONE_API_BASE",
    "https://app.mercadophone.tech/api.php?class=OrdemServicoApiController&method=",
)
MERCADO_PHONE_SYNC_ENABLED = os.environ.get("MERCADO_PHONE_SYNC_ENABLED", "1") == "1"
MERCADO_PHONE_SYNC_INTERVAL_SECONDS = int(os.environ.get("MERCADO_PHONE_SYNC_INTERVAL_SECONDS", "30"))
MERCADO_PHONE_SYNC_TIMEOUT_SECONDS = int(os.environ.get("MERCADO_PHONE_SYNC_TIMEOUT_SECONDS", "20"))
MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT = os.environ.get("MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT", "0") == "1"
MERCADO_PHONE_SYNC_START_DATE = os.environ.get("MERCADO_PHONE_SYNC_START_DATE", "2026-04-01")
