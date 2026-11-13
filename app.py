"""
Fluxoly - Sistema de Gestão de Assistência Técnica
Application main module - Flask app bootstrap, configuration, and core functionality
"""

# ============================================================================
# IMPORTS PADRÃO DA BIBLIOTECA
# ============================================================================
import functools
import os
import re
import sqlite3
import sys
import threading
import time
import traceback
import uuid
import weakref
import webbrowser
from datetime import UTC, datetime, timedelta

from dotenv import load_dotenv

# Carrega .env em dev local antes de qualquer leitura de os.environ abaixo.
# Não sobrescreve variáveis já definidas no processo. Pulado quando os mesmos
# sinais de IS_SERVER_RUNTIME (definida adiante) já estão presentes: produção
# nunca tem .env de qualquer forma (Dockerfile não copia, .gitignore exclui),
# mas testes que simulam runtime de servidor num subprocesso isolado, rodando
# com cwd na raiz do repo, encontrariam o .env real do desenvolvedor e
# mascarariam a checagem obrigatória de FLASK_SECRET_KEY (ver
# tests/test_security_flask_secret_key_fallback.py).
if not any(
    os.environ.get(var)
    for var in ("IR_FLOW_DATA_DIR", "FLY_DATA_DIR", "RENDER_DISK_PATH", "RENDER", "RENDER_SERVICE_ID")
):
    load_dotenv()

# ============================================================================
# IMPORTS FLASK
# ============================================================================
from flask import Flask, flash, g, jsonify, redirect, request, send_from_directory, session, url_for

# ============================================================================
# IMPORTS DE OBSERVABILIDADE (Sprint Observabilidade)
# ============================================================================
from prometheus_client import CONTENT_TYPE_LATEST, CollectorRegistry, Counter, Histogram, generate_latest, multiprocess
from werkzeug.security import generate_password_hash

from fluxoly_app_security import configurar_seguranca

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - REGISTRY DE BLUEPRINTS (TD-02 Fatia 3)
# ============================================================================
from fluxoly_blueprint_registry import RuntimeDeps, registrar_blueprints

# ============================================================================
# CONFIGURAÇÃO DE AMBIENTE, PATHS E FEATURE-FLAGS
# ============================================================================
# TD-02 Fatia 1 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- extraído para
# fluxoly_config.py. app.py só importa os nomes; MERCADO_PHONE_SYNC_ENABLED/
# _INTERVAL_SECONDS/_START_DATE continuam sendo reatribuídos mais abaixo (seção "CONFIGURAÇÃO
# MERCADO PHONE") ao mesclar com integrations.json -- mesmo comportamento de antes.
import fluxoly_config  # noqa: E402
from fluxoly_config import (  # noqa: E402
    APP_HOST,
    APP_PORT,
    AUDIT_LOG_EXPURGO_APOS_DIAS,
    AUDIT_LOG_PII_MASK_APOS_DIAS,
    BACKGROUND_JOBS_ENABLED,
    BACKUP_DIR,
    DB_PATH,
    INTEGRATIONS_CONFIG_PATH,
    IS_DEMO_ENVIRONMENT,
    IS_PULL_REQUEST,
    IS_SERVER_RUNTIME,
    MERCADO_PHONE_API_BASE,
    MERCADO_PHONE_DEFAULT_TECNICO,
    MERCADO_PHONE_SYNC_ENABLED,
    MERCADO_PHONE_SYNC_INTERVAL_SECONDS,
    MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT,
    MERCADO_PHONE_SYNC_START_DATE,
    MERCADO_PHONE_SYNC_TIMEOUT_SECONDS,
    PRICE_TABLES_PATH,
    RESOURCE_DIR,
    VERCEL_URL,
)

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - CORE
# ============================================================================
from fluxoly_core import (
    STATUS_AGUARDANDO_PECA,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    normalizar_busca_texto,
    normalizar_status_os,
    sessao_ainda_ativa,
    texto_limpo,
)
from fluxoly_logging import configurar_logging, get_logger
from fluxoly_mercadophone import loop_sincronizacao_mercado_phone

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - OS, STORAGE, MERCADOPHONE
# ============================================================================
from fluxoly_os import obter_ou_criar_reparo, salvar_reparos_os
from fluxoly_price_tables import carregar_tabelas_preco as carregar_tabelas_preco_arquivo
from fluxoly_price_tables import salvar_tabelas_preco as salvar_tabelas_preco_arquivo
from fluxoly_reference_data import (
    REPAROS_PADRAO,
    TECNICOS,
    VENDEDORES,
    canonicalizar_para_lista,
    extrair_cor_da_descricao_aparelho,
    extrair_modelo_da_descricao_aparelho,
    modelo_para_os,
    nome_reparo_importavel,
    normalizar_imei,
)
from fluxoly_audit import iniciar_thread_manutencao_audit_log
from fluxoly_storage import carregar_configuracoes_integracoes, iniciar_thread_backup_automatico
from fluxoly_web import anexar_query_string

# ============================================================================
# IMPORTS DE MÓDULOS INTERNOS - MIGRATIONS (TD-03 Fatia 2)
# ============================================================================
from migrations.runner import run_migrations

# ============================================================================
# BOOTSTRAP FLASK
# ============================================================================
# Configurado antes de qualquer outra coisa poder logar durante o boot.
configurar_logging()
logger = get_logger("app")

# INC-003: visibilidade explícita em vez de silêncio -- se IS_PULL_REQUEST for
# detectado (Render PR Preview), background jobs (sync MercadoPhone, backup
# automático) já ficam desligados via BACKGROUND_JOBS_ENABLED (fluxoly_config.py),
# mas isso precisa aparecer no log de boot para não parecer um bug caso alguém
# no futuro não conheça esta decisão.
if IS_PULL_REQUEST:
    logger.warning(
        "preview_background_jobs_desativados",
        extra={"motivo": "IS_PULL_REQUEST=true", "referencia": "INC-003/KI-035/KI-036"},
    )

# ADR-012: mesma visibilidade explícita de boot, agora para o ambiente Demo --
# IS_DEMO_ENVIRONMENT já desliga BACKGROUND_JOBS_ENABLED (fluxoly_config.py),
# este log só evita que a ausência de sync/backup pareça um bug no Demo.
if IS_DEMO_ENVIRONMENT:
    logger.warning(
        "demo_background_jobs_desativados",
        extra={"motivo": "IR_FLOW_ENVIRONMENT=demo", "referencia": "ADR-012"},
    )

# Sentry (Sprint Observabilidade) -- só inicializa com SENTRY_DSN definida.
# Vazia por padrão: usuário ainda não tem conta Sentry, vai criar depois e
# só colar o DSN no Render (mesmo padrão de integração opcional já usado
# pelo Mercado Phone). send_default_pii=False é deliberado -- o sistema
# lida com dado real de cliente (nome, IMEI), não pode vazar em
# breadcrumb/payload de erro. traces_sample_rate=0 -- só captura de erro,
# sem tracing de performance (evita overhead/custo sem necessidade
# confirmada; pode ser revisto depois se fizer sentido). environment checa
# IS_PULL_REQUEST antes de IS_SERVER_RUNTIME (KI-036) -- um Render PR Preview
# também seta IS_SERVER_RUNTIME=True (mesmos sinais de RENDER/RENDER_SERVICE_ID
# de produção), então sem essa checagem erros de um preview seriam reportados
# como "production" e poluiriam o monitoramento real. release lê
# RENDER_GIT_COMMIT, injetada automaticamente pelo Render em todo deploy, sem
# exigir nenhuma configuração manual de versionamento.
_sentry_dsn = os.environ.get("SENTRY_DSN", "").strip()
if _sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    if IS_PULL_REQUEST:
        _sentry_environment = "preview"
    elif IS_DEMO_ENVIRONMENT:
        _sentry_environment = "demo"
    elif IS_SERVER_RUNTIME:
        _sentry_environment = "production"
    else:
        _sentry_environment = "development"

    sentry_sdk.init(
        dsn=_sentry_dsn,
        integrations=[FlaskIntegration()],
        send_default_pii=False,
        traces_sample_rate=0,
        environment=_sentry_environment,
        release=os.environ.get("RENDER_GIT_COMMIT", "dev"),
    )
    logger.info("sentry_inicializado", extra={"environment": _sentry_environment})

app = Flask(__name__, template_folder=os.path.join(RESOURCE_DIR, "templates"))

# SECURITY_AUDIT_2026-07.md item 3: antes, um deploy sem FLASK_SECRET_KEY configurada
# iniciava silenciosamente com um valor hardcoded e publico ("ir-flow-dev-key"),
# permitindo forjar cookies de sessao. Falha no boot fora de dev local em vez de
# usar esse fallback -- em dev local (sem IR_FLOW_DATA_DIR/RENDER/FLY), o fallback
# continua liberado por conveniencia, documentado em .env.example.
_flask_secret_key_env = os.environ.get("FLASK_SECRET_KEY")
if not _flask_secret_key_env and IS_SERVER_RUNTIME:
    raise RuntimeError(
        "FLASK_SECRET_KEY obrigatoria fora de desenvolvimento local. "
        'Gere uma com: python -c "import secrets; print(secrets.token_hex(32))"'
    )
app.secret_key = _flask_secret_key_env or "ir-flow-dev-key"

# Cookies de sessão: em produção cross-site (Vercel -> Render), o navegador
# exige SameSite=None + Secure para enviar cookie com credentials: include.
if IS_SERVER_RUNTIME:
    app.config["SESSION_COOKIE_SAMESITE"] = "None"
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_PARTITIONED"] = True
else:
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = False
    app.config["SESSION_COOKIE_PARTITIONED"] = False
app.config["SESSION_COOKIE_HTTPONLY"] = True

# Configuração de CORS para aceitar requisições do frontend.
# Pode ser definido como lista separada por vírgula em IR_FLOW_CORS_ORIGINS.
cors_origins_env = (os.environ.get("IR_FLOW_CORS_ORIGINS") or "").strip()


def _normalizar_origem_cors(valor):
    texto = (valor or "").strip()
    if not texto:
        return ""
    if texto.startswith("http://") or texto.startswith("https://"):
        return texto
    # Em alguns ambientes o VERCEL_URL pode vir sem esquema.
    return f"https://{texto}"


if cors_origins_env:
    cors_origins = [_normalizar_origem_cors(item) for item in cors_origins_env.split(",") if item.strip()]
elif VERCEL_URL:
    cors_origins = [_normalizar_origem_cors(VERCEL_URL)]
else:
    cors_origins = [
        r"https://.*\.vercel\.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

# TD-02 Fatia 2 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- CORS, headers de
# segurança (CSP/X-Frame-Options/etc.) e os respectivos @app.after_request extraídos para
# fluxoly_app_security.py. cors_origins continua calculado aqui (fonte de verdade única).
configurar_seguranca(app, cors_origins)

# ============================================================================
# CORRELATION ID + LOG DE ACESSO POR REQUEST (Sprint Observabilidade)
# ============================================================================
# Alfanumérico + hífen, até 64 chars — aceita o formato usual de UUID/ULID.
# Um X-Request-Id de cliente fora desse formato é descartado (gera um novo),
# nunca repassado como veio: evita que um valor hostil (ex. com quebra de
# linha) vaze para dentro da linha de log JSON.
_REQUEST_ID_VALIDO = re.compile(r"^[A-Za-z0-9-]{1,64}$")

# Labels usam request.url_rule.rule (ex. "/api/ordens/<int:os_id>"), nunca
# request.path -- caso contrário cada OS/id vira uma série temporal nova
# (cardinalidade sem limite). Em modo multiprocess (PROMETHEUS_MULTIPROC_DIR
# setada, só acontece dentro do container -- ver Dockerfile/gunicorn.conf.py)
# o prometheus_client detecta a env var por conta própria e faz cada Counter/
# Histogram gravar num arquivo mmap compartilhado por worker; a agregação
# entre workers só acontece na leitura, em /metrics (ver metrics_endpoint).
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total de requisições HTTP recebidas",
    ["method", "route", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "Duração das requisições HTTP em segundos",
    ["method", "route"],
)


@app.before_request
def _iniciar_request_id():
    recebido = (request.headers.get("X-Request-Id") or "").strip()
    g.request_id = recebido if _REQUEST_ID_VALIDO.match(recebido) else str(uuid.uuid4())
    g._inicio_request = time.monotonic()


@app.after_request
def _logar_acesso(response):
    response.headers["X-Request-Id"] = getattr(g, "request_id", "") or str(uuid.uuid4())

    duracao_ms = None
    inicio = getattr(g, "_inicio_request", None)
    if inicio is not None:
        duracao_ms = round((time.monotonic() - inicio) * 1000, 2)

    rota = request.url_rule.rule if request.url_rule else request.path
    logger.info(
        "request",
        extra={
            "http_method": request.method,
            "http_route": rota,
            "http_status": response.status_code,
            "duration_ms": duracao_ms,
            "usuario_id": session.get("usuario_id"),
        },
    )

    HTTP_REQUESTS_TOTAL.labels(method=request.method, route=rota, status=response.status_code).inc()
    if duracao_ms is not None:
        HTTP_REQUEST_DURATION_SECONDS.labels(method=request.method, route=rota).observe(duracao_ms / 1000)

    return response


# FUNÇÕES AUXILIARES - CARREGAMENTO DE DADOS
# ============================================================================
carregar_tabelas_preco = functools.partial(carregar_tabelas_preco_arquivo, PRICE_TABLES_PATH)
salvar_tabelas_preco = functools.partial(salvar_tabelas_preco_arquivo, PRICE_TABLES_PATH)


def parse_data_ymd(valor):
    """Converte string de data YYYY-MM-DD para objeto datetime."""
    texto = texto_limpo(valor)
    if not texto:
        return None
    try:
        return datetime.strptime(texto[:10], "%Y-%m-%d")
    except ValueError:
        return None


# ============================================================================
# LOCKS E FLAGS DE INICIALIZAÇÃO
# ============================================================================
SQLITE_TIMEOUT_SECONDS = max(5, int(os.environ.get("IR_FLOW_SQLITE_TIMEOUT_SECONDS", "30")))
SQLITE_BUSY_TIMEOUT_MS = SQLITE_TIMEOUT_SECONDS * 1000


def _configurar_conexao_sqlite(conn, habilitar_wal=False):
    conn.execute(f"PRAGMA busy_timeout = {SQLITE_BUSY_TIMEOUT_MS}")
    conn.execute("PRAGMA synchronous = NORMAL")
    if habilitar_wal:
        try:
            conn.execute("PRAGMA journal_mode = WAL")
        except sqlite3.OperationalError as exc:
            if "locked" not in str(exc).lower():
                raise


# ============================================================================
# FUNÇÕES DE DATABASE
# ============================================================================

# INC-001 (docs/operations/INCIDENTS/INC-001-database-is-locked.md) — instrumentação
# temporária, estritamente observacional (ver critérios C-1 a C-9 no documento do
# incidente), para reproduzir "database is locked" com evidência de runtime, não só
# leitura de código. Desligada por padrão (IR_FLOW_DEBUG_CONN_TRACE=1 para ligar);
# desligada, conectar() se comporta exatamente como antes, sem overhead algum. Vive
# inteiramente dentro de conectar() (C-9) — nenhuma rota precisa saber que ela existe,
# e removê-la não exige tocar em nenhuma rota. Remover assim que a causa raiz for
# confirmada.
_CONN_TRACE_ATIVO = os.environ.get("IR_FLOW_DEBUG_CONN_TRACE") == "1"
_conn_trace_lock = threading.Lock()
_conn_trace_contador = 0


def _proximo_conn_trace_id():
    global _conn_trace_contador
    with _conn_trace_lock:
        _conn_trace_contador += 1
        return _conn_trace_contador


def _conn_trace_rota_atual():
    try:
        if request:
            return f"{request.method} {request.path}"
    except RuntimeError:
        pass
    return threading.current_thread().name


class _ConexaoRastreada:
    """Envolve uma sqlite3.Connection real e loga OPEN/COMMIT/ROLLBACK/CLOSE (INC-001)
    via o logger estruturado já existente (fluxoly_logging.py, extra={...} -- nunca
    print() nem um pipeline de log paralelo).

    Transparente por requisito (C-2/C-9): qualquer atributo ou método não
    explicitamente instrumentado aqui (cursor(), execute(), row_factory, etc.) é
    delegado à conexão real via __getattr__/__setattr__ -- este objeto deve se
    comportar de forma indistinguível de um sqlite3.Connection normal para quem o
    usa, inclusive para código futuro ainda não escrito hoje.
    """

    def __init__(self, conn_real):
        self._conn = conn_real
        self._id = _proximo_conn_trace_id()
        self._rota = _conn_trace_rota_atual()
        self._thread_name = threading.current_thread().name
        self._thread_ident = threading.get_ident()
        self._abertura_monotonic = time.monotonic()
        self._aberta_em = datetime.now(UTC).isoformat()

        # Últimos 5 frames antes desta chamada -- suficiente para identificar quem
        # abriu a conexão sem despejar a stack inteira do processo no log.
        stack_resumida = "".join(traceback.format_stack()[:-1][-5:])
        conn_id, rota, thread_name, thread_ident = self._id, self._rota, self._thread_name, self._thread_ident

        def _ao_coletar(
            _ref, conn_id=conn_id, rota=rota, thread_name=thread_name, thread_ident=thread_ident, stack=stack_resumida
        ):
            logger.warning(
                "INC-001: conexão coletada pelo GC sem close() explícito",
                extra={
                    "inc001_connection_id": conn_id,
                    "inc001_route": rota,
                    "inc001_thread_name": thread_name,
                    "inc001_thread_ident": thread_ident,
                    "inc001_close_called": False,
                    "inc001_stack": stack,
                },
            )

        self._finalizer = weakref.finalize(self, _ao_coletar, None)

        logger.info(
            "INC-001: conexão aberta",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
                "inc001_thread_ident": self._thread_ident,
                "inc001_opened_at": self._aberta_em,
            },
        )

    def commit(self):
        self._conn.commit()
        logger.info(
            "INC-001: conexão commit",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
            },
        )

    def rollback(self):
        self._conn.rollback()
        logger.info(
            "INC-001: conexão rollback",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
            },
        )

    def close(self):
        # Cancela o finalizer antes de fechar -- close() explícito não deve gerar o
        # aviso de vazamento reservado para a coleta pelo GC.
        self._finalizer.detach()
        self._conn.close()
        elapsed_ms = (time.monotonic() - self._abertura_monotonic) * 1000
        logger.info(
            "INC-001: conexão fechada",
            extra={
                "inc001_connection_id": self._id,
                "inc001_route": self._rota,
                "inc001_thread_name": self._thread_name,
                "inc001_thread_ident": self._thread_ident,
                "inc001_opened_at": self._aberta_em,
                "inc001_closed_at": datetime.now(UTC).isoformat(),
                "inc001_elapsed_ms": round(elapsed_ms, 3),
                "inc001_close_called": True,
            },
        )

    def __getattr__(self, nome):
        # Só chamado quando o atributo não existe nesta classe (isto é, não é um
        # dos métodos instrumentados acima) -- delega à conexão real.
        return getattr(self._conn, nome)

    def __setattr__(self, nome, valor):
        if nome in (
            "_conn",
            "_id",
            "_rota",
            "_thread_name",
            "_thread_ident",
            "_abertura_monotonic",
            "_aberta_em",
            "_finalizer",
        ):
            object.__setattr__(self, nome, valor)
        else:
            setattr(self._conn, nome, valor)


def conectar():
    """Cria conexão com banco de dados. Schema é garantido pelo bootstrap
    (run_migrations(), ver seção FUNÇÕES DE DATABASE abaixo) -- conectar()
    não decide mais schema (TD-03 Fatia 2)."""
    conn = sqlite3.connect(DB_PATH, timeout=SQLITE_TIMEOUT_SECONDS)
    _configurar_conexao_sqlite(conn)
    if _CONN_TRACE_ATIVO:
        return _ConexaoRastreada(conn)
    return conn


def forcar_migracao_schema():
    """Reexecuta migrations pendentes no banco atual (útil após restore de
    arquivo legado ou atrasado)."""
    run_migrations()


run_migrations()
if BACKGROUND_JOBS_ENABLED:
    iniciar_thread_backup_automatico(BACKUP_DIR, conectar)
    # Decisão 6 (PLAN-LGPD-Compliance.md): só inicia se pelo menos um prazo estiver configurado --
    # sem AUDIT_LOG_PII_MASK_APOS_DIAS/AUDIT_LOG_EXPURGO_APOS_DIAS, a rotina nunca é chamada (fail-safe
    # por ausência de invocação, não por uma checagem interna que poderia ser esquecida).
    if AUDIT_LOG_PII_MASK_APOS_DIAS or AUDIT_LOG_EXPURGO_APOS_DIAS:
        iniciar_thread_manutencao_audit_log(
            conectar, AUDIT_LOG_PII_MASK_APOS_DIAS, AUDIT_LOG_EXPURGO_APOS_DIAS
        )


def criar_admin_padrao():
    """Cria usuário admin padrão se não existir nenhum usuário admin.

    KI-038/KI-039: a senha vem de IR_FLOW_ADMIN_PASSWORD fora de dev local
    -- ausente nesse caso, o boot falha (RuntimeError propaga, não é
    capturado pelo try/except abaixo, que protege só a inserção em si).
    Em dev local (IS_SERVER_RUNTIME=False) mantém o fallback histórico,
    documentado em .env.example.
    """
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM usuarios WHERE usuario = ?", ("admin",))
        precisa_criar = cursor.fetchone() is None
    finally:
        conn.close()

    if not precisa_criar:
        return

    admin_senha = os.environ.get("IR_FLOW_ADMIN_PASSWORD")
    if not admin_senha:
        if IS_SERVER_RUNTIME:
            raise RuntimeError(
                "IR_FLOW_ADMIN_PASSWORD obrigatória para criar o admin inicial fora de " "desenvolvimento local."
            )
        admin_senha = "irflow@2024"

    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?, ?, ?, ?)",
            ("Administrador", "admin", generate_password_hash(admin_senha), "admin"),
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        # Loga o erro mas não interrompe o boot -- erro de banco na inserção,
        # não de configuração ausente (esse já propagou acima).
        logger.warning("criar_admin_padrao_falhou", extra={"erro": str(exc)})
    finally:
        conn.close()


criar_admin_padrao()

# ============================================================================
# CONFIGURAÇÃO MERCADO PHONE
# ============================================================================

INTEGRATIONS_CONFIG = carregar_configuracoes_integracoes(INTEGRATIONS_CONFIG_PATH)
MERCADO_PHONE_CONFIG = INTEGRATIONS_CONFIG.get("mercado_phone", {}) if isinstance(INTEGRATIONS_CONFIG, dict) else {}
MERCADO_PHONE_API_TOKEN = os.environ.get("MERCADO_PHONE_API_TOKEN", "") or texto_limpo(
    MERCADO_PHONE_CONFIG.get("api_token")
)
MERCADO_PHONE_SYNC_ENABLED = (
    (
        texto_limpo(str(MERCADO_PHONE_CONFIG.get("sync_enabled", MERCADO_PHONE_SYNC_ENABLED))).lower()
        not in {"0", "false", "nao", "off"}
    )
    if MERCADO_PHONE_API_TOKEN
    else False
)
MERCADO_PHONE_SYNC_INTERVAL_SECONDS = int(
    MERCADO_PHONE_CONFIG.get("sync_interval_seconds", MERCADO_PHONE_SYNC_INTERVAL_SECONDS)
    or MERCADO_PHONE_SYNC_INTERVAL_SECONDS
)
MERCADO_PHONE_SYNC_START_DATE = (
    texto_limpo(MERCADO_PHONE_CONFIG.get("sync_start_date", MERCADO_PHONE_SYNC_START_DATE)) or "2026-04-01"
)

MERCADO_PHONE_RUNTIME_CONFIG = {
    "api_token": MERCADO_PHONE_API_TOKEN,
    "api_base": MERCADO_PHONE_API_BASE,
    "default_tecnico": MERCADO_PHONE_DEFAULT_TECNICO,
    "sync_enabled": MERCADO_PHONE_SYNC_ENABLED,
    "sync_interval_seconds": MERCADO_PHONE_SYNC_INTERVAL_SECONDS,
    "sync_timeout_seconds": MERCADO_PHONE_SYNC_TIMEOUT_SECONDS,
    "sync_only_after_boot": MERCADO_PHONE_SYNC_ONLY_AFTER_BOOT,
    "sync_start_date": MERCADO_PHONE_SYNC_START_DATE,
}

MERCADO_PHONE_HELPERS = {
    "texto_limpo": texto_limpo,
    "modelo_para_os": modelo_para_os,
    "extrair_modelo_da_descricao_aparelho": extrair_modelo_da_descricao_aparelho,
    "extrair_cor_da_descricao_aparelho": extrair_cor_da_descricao_aparelho,
    "normalizar_imei": normalizar_imei,
    "nome_reparo_importavel": nome_reparo_importavel,
    "obter_ou_criar_reparo": obter_ou_criar_reparo,
    "salvar_reparos_os": salvar_reparos_os,
    "normalizar_busca_texto": normalizar_busca_texto,
    "normalizar_status_os": normalizar_status_os,
    "canonicalizar_para_lista": canonicalizar_para_lista,
    "tecnicos": TECNICOS,
    "vendedores": VENDEDORES,
}

# ============================================================================
# FUNÇÕES DE NEGÓCIO
# ============================================================================


def sincronizar_reparos_padrao():
    """Sincroniza lista de reparos padrão para o banco."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute("SELECT lower(nome) FROM reparos")
    existentes = {row[0] for row in cursor.fetchall() if row[0]}

    for reparo in REPAROS_PADRAO:
        if reparo.lower() in existentes:
            continue
        cursor.execute("INSERT INTO reparos (nome) VALUES (?)", (reparo,))

    conn.commit()
    conn.close()


def obter_alertas_sistema(limit=8):
    """
    Coleta alertas de sistema:
    - Estoque baixo
    - OS em aberto há muito tempo
    - Garantia perto de vencer
    """
    conn = conectar()
    cursor = conn.cursor()
    alerts = []
    hoje = datetime.now().date()

    # Alerta: Estoque Baixo
    cursor.execute(
        """
        SELECT id, descricao, quantidade
        FROM estoque
        WHERE COALESCE(quantidade, 0) <= 2
        ORDER BY quantidade ASC, descricao ASC
        LIMIT 10
        """
    )
    for _item_id, descricao, quantidade in cursor.fetchall():
        qtd = quantidade or 0
        status_txt = "sem estoque" if qtd == 0 else f"{qtd} unid."
        alerts.append(
            {
                "nivel": "critico" if qtd == 0 else "atencao",
                "titulo": "Estoque baixo",
                "mensagem": f"{descricao or 'Peca'} ({status_txt})",
                "link": "/app/estoque",
            }
        )

    # Alerta: OS em Aberto há Muito Tempo
    cursor.execute(
        """
        SELECT id, cliente, modelo, status, data
        FROM os
        WHERE status IN ('Em andamento', 'Aguardando peca', 'Aguardando peça')
        ORDER BY id DESC
        """
    )
    for os_id, cliente, _modelo, status, data_os in cursor.fetchall():
        if normalizar_status_os(status) not in {STATUS_EM_ANDAMENTO, STATUS_AGUARDANDO_PECA}:
            continue
        dt = parse_data_ymd(data_os)
        if not dt:
            continue
        dias = (hoje - dt.date()).days
        if dias >= 10:
            alerts.append(
                {
                    "nivel": "info",
                    "titulo": "OS em aberto ha muito tempo",
                    "mensagem": f"OS #{os_id} - {cliente or 'Sem cliente'} ({dias} dias)",
                    "link": "/app/ordens",
                }
            )

    # Alerta: Garantia Perto de Vencer
    cursor.execute(
        """
        SELECT id, cliente, modelo, data_finalizado, data, status
        FROM os
        WHERE status='Finalizado' AND COALESCE(tipo, '') != 'Interna'
        ORDER BY id DESC
        """
    )
    for os_id, cliente, _modelo, data_finalizado, data_os, status in cursor.fetchall():
        if normalizar_status_os(status) != STATUS_FINALIZADO:
            continue
        inicio = parse_data_ymd(data_finalizado) or parse_data_ymd(data_os)
        if not inicio:
            continue
        fim = (inicio + timedelta(days=90)).date()
        dias_restantes = (fim - hoje).days
        if 0 <= dias_restantes <= 7:
            alerts.append(
                {
                    "nivel": "atencao",
                    "titulo": "Garantia perto do vencimento",
                    "mensagem": f"OS #{os_id} - {cliente or 'Sem cliente'} (vence em {dias_restantes} dia(s))",
                    "link": url_for("main_views.garantias"),
                }
            )

    conn.close()

    # Ordena por prioridade
    prioridade = {"critico": 0, "atencao": 1, "info": 2}
    alerts.sort(key=lambda a: prioridade.get(a["nivel"], 3))
    return alerts[:limit]


def listar_custos_operacionais(data_inicio="", data_fim=""):
    """Lista custos operacionais com filtros de período e agregação por categoria."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            COALESCE(descricao, ''),
            COALESCE(categoria, 'Outros'),
            COALESCE(valor, 0),
            COALESCE(data, ''),
            COALESCE(observacoes, '')
        FROM custos_operacionais
        ORDER BY data DESC, id DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    itens = []
    total_periodo = 0
    por_categoria = {}

    for custo_id, descricao, categoria, valor, data, observacoes in rows:
        if (data_inicio or data_fim) and not data:
            continue
        if data_inicio and data and data < data_inicio:
            continue
        if data_fim and data and data > data_fim:
            continue

        item = {
            "id": custo_id,
            "descricao": descricao,
            "categoria": categoria or "Outros",
            "valor": round(valor or 0, 2),
            "data": data,
            "observacoes": observacoes,
        }
        itens.append(item)
        total_periodo += valor or 0
        por_categoria[item["categoria"]] = por_categoria.get(item["categoria"], 0) + (valor or 0)

    por_categoria_ordenado = sorted(por_categoria.items(), key=lambda item: item[1], reverse=True)
    return {
        "itens": itens,
        "total_periodo": round(total_periodo, 2),
        "por_categoria": por_categoria_ordenado,
        "labels_categoria": [item[0] for item in por_categoria_ordenado],
        "values_categoria": [round(item[1], 2) for item in por_categoria_ordenado],
    }


# ============================================================================
# CONTEXT PROCESSORS
# ============================================================================


@app.context_processor
def inject_system_alerts():
    """Injeta alertas de sistema em todos os templates."""
    try:
        alerts = obter_alertas_sistema(limit=10)
    except Exception:
        alerts = []
    return {
        "system_alerts": alerts,
        "system_alert_count": len(alerts),
    }


# ============================================================================
# REGISTRO DE BLUEPRINTS COM DEPENDÊNCIAS
# ============================================================================

sincronizar_reparos_padrao()

# ============================================================================
# AUTENTICAÇÃO — PERMISSÕES E BEFORE_REQUEST
# ============================================================================

# Perfis disponíveis: admin, tecnico, vendedor
# None = qualquer perfil logado
# Sentinel usado só para distinguir "endpoint não cadastrado aqui" (nega por
# padrão) de "cadastrado com valor None" (qualquer perfil logado) — ver uso em
# verificar_autenticacao().
_ENDPOINT_SEM_ENTRADA = object()

ROUTE_PERMISSIONS: dict[str, list[str] | None] = {
    # Acesso livre (não requer login)
    "auth_views.login": [],
    "auth_views.logout": [],
    "static": [],
    # Qualquer usuário logado
    "main_views.index": None,
    "main_views.kanban": None,
    "main_views.garantias": None,
    # Somente admin
    "main_views.relatorios": ["admin"],
    "main_views.backup": ["admin"],
    "main_views.backup_download": ["admin"],
    "main_views.relatorio_pdf_tecnicos": ["admin"],
}


LEGACY_REACT_REDIRECTS = {
    "/": "/app",
    "/dashboard": "/app",
    "/dashboard/": "/app",
    "/dashboard.html": "/app",
    "/index": "/app",
    "/index.html": "/app",
    "/login": "/app/login",
    "/ordens": "/app/ordens",
    "/nova": "/app/ordens/nova",
    "/kanban": "/app/kanban",
    "/garantias": "/app/garantias",
    "/estoque": "/app/estoque",
    "/estoque/cadastro": "/app/estoque",
    "/reparos": "/app/reparos",
    "/tabelas-preco": "/app/precos",
    "/custos-operacionais": "/app/custos",
    "/relatorios": "/app/relatorios",
    "/backup": "/app/backup",
    "/usuarios": "/app/usuarios",
}


def destino_react_legado(path: str) -> str | None:
    if path in LEGACY_REACT_REDIRECTS:
        return LEGACY_REACT_REDIRECTS[path]

    if path.startswith("/editar/"):
        os_id = path.removeprefix("/editar/").strip("/")
        if os_id.isdigit():
            return f"/app/ordens/editar/{os_id}"

    return None


def revalidar_usuario_da_sessao():
    """Derruba a sessão de usuário excluído ou inativo e atualiza perfil e nome com o banco."""
    conn = conectar()
    try:
        row = conn.execute(
            "SELECT nome, perfil, ativo FROM usuarios WHERE id = ?",
            (session["usuario_id"],),
        ).fetchone()
    finally:
        conn.close()

    if not row or row[2] != 1:
        session.clear()
        return
    if session.get("usuario_perfil") != row[1]:
        session["usuario_perfil"] = row[1]
    if session.get("usuario_nome") != row[0]:
        session["usuario_nome"] = row[0]


@app.before_request
def verificar_autenticacao():
    endpoint = request.endpoint
    if request.method in ("GET", "HEAD"):
        destino_react = destino_react_legado(request.path)
        if destino_react:
            return redirect(anexar_query_string(destino_react, request.query_string))

    if not endpoint:
        return

    # Rotas estáticas e API — autenticação gerenciada pela própria API
    # "health_check"/"ready_check"/"metrics_endpoint": probes de infraestrutura
    # (Render, Prometheus) não autenticam — Sprint Observabilidade.
    if endpoint in (
        "static",
        "serve_react",
        "serve_react_assets",
        "health_check",
        "ready_check",
        "metrics_endpoint",
    ):
        return

    # Expiração de sessão por inatividade — roda para TODA rota autenticada,
    # inclusive /api/*, já que este before_request dispara antes do bypass
    # abaixo. Limpar a sessão aqui é suficiente para /api/* também: o
    # usuario_logado() de fluxoly_blueprints_api.py checa session["usuario_id"],
    # que já estará vazio quando a view rodar.
    if session.get("usuario_id") and not sessao_ainda_ativa(session):
        session.clear()

    # P1-2 (QA 2026-11-12): o cookie guarda perfil e id desde o login. Relê o usuário a cada
    # requisição autenticada para que desativar, excluir ou trocar o perfil valha na hora,
    # inclusive nas rotas que leem session["usuario_perfil"] direto.
    if session.get("usuario_id"):
        revalidar_usuario_da_sessao()

    # Bypass por path (não só pelo blueprint "api.") — cobre também blueprints
    # de domínio novos sob /api/* (ex.: clientes_api, unidades_serializadas_api),
    # que autenticam via usuario_logado() dentro de si mesmos, igual à API
    # principal. Checar o path em vez do nome do blueprint evita ter que
    # atualizar esta lista a cada novo domínio adicionado sob /api/*.
    if endpoint and endpoint.startswith("api."):
        return
    if request.path.startswith("/api/"):
        return

    perms = ROUTE_PERMISSIONS.get(endpoint, _ENDPOINT_SEM_ENTRADA)
    if perms is _ENDPOINT_SEM_ENTRADA:
        # Endpoint legado sem entrada em ROUTE_PERMISSIONS — nega por padrão
        # (fail secure) em vez de liberar para qualquer usuário logado, que é
        # o que `None` (chave presente) significa nesta tabela.
        flash("Você não tem permissão para acessar esta página.", "danger")
        return redirect("/app")
    if perms == []:
        # Acesso livre
        return

    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return redirect("/app/login")

    perfil = session.get("usuario_perfil", "")
    if perms is not None and perfil not in perms:
        flash("Você não tem permissão para acessar esta página.", "danger")
        return redirect("/app")


# ============================================================================
# REGISTRO DE BLUEPRINTS (TD-02 Fatia 3 — fluxoly_blueprint_registry.py)
# ============================================================================
# As 20 chamadas app.register_blueprint(...) que antes viviam inline aqui
# (auth + 12 domínios TD-01 + fluxoly_blueprints_api.py vazio + 5 domínios
# controller/service/repository) foram movidas para
# fluxoly_blueprint_registry.py::registrar_blueprints() -- mesma ordem, mesmos
# dicts de deps, nenhuma factory create_*_blueprint mudou. runtime carrega só
# os valores construídos em runtime dentro deste arquivo, que o registry não
# consegue importar direto sem criar import circular (ver docstring de
# RuntimeDeps em fluxoly_blueprint_registry.py).
runtime = RuntimeDeps(
    conectar=conectar,
    carregar_tabelas_preco=carregar_tabelas_preco,
    salvar_tabelas_preco=salvar_tabelas_preco,
    forcar_migracao_schema=forcar_migracao_schema,
    mercado_phone_runtime_config=MERCADO_PHONE_RUNTIME_CONFIG,
    mercado_phone_helpers=MERCADO_PHONE_HELPERS,
    listar_custos_operacionais=listar_custos_operacionais,
    obter_alertas_sistema=obter_alertas_sistema,
    parse_data_ymd=parse_data_ymd,
)
registrar_blueprints(app, runtime)

# ============================================================================
# HEALTH CHECKS (Sprint Observabilidade) — sem autenticação, usados por
# probes de infraestrutura (Render, load balancer). Não usam a convenção
# ok()/err() das blueprints de domínio de propósito — são infraestrutura,
# não API de negócio.
# ============================================================================


@app.route("/health")
def health_check():
    """Liveness — processo está de pé. Não checa nenhuma dependência externa."""
    return jsonify({"status": "ok"}), 200


@app.route("/ready")
def ready_check():
    """Readiness — banco de dados está acessível."""
    try:
        conn = conectar()
        try:
            conn.execute("SELECT 1")
        finally:
            conn.close()
    except Exception as exc:
        logger.error("readiness_check_failed", extra={"erro": str(exc)})
        return jsonify({"status": "unavailable"}), 503
    return jsonify({"status": "ok"}), 200


def _metrics_autorizado():
    # Fora de IS_SERVER_RUNTIME (dev local, testes) libera sem token, pra
    # facilitar curl local. Em produção, exige METRICS_TOKEN configurada e
    # correspondente -- se a variável não estiver setada, nega por padrão
    # (mais seguro do que deixar aberto por omissão de configuração).
    if not IS_SERVER_RUNTIME:
        return True
    token_esperado = os.environ.get("METRICS_TOKEN", "")
    if not token_esperado:
        return False
    return request.headers.get("X-Metrics-Token", "") == token_esperado


@app.route("/metrics")
def metrics_endpoint():
    """Métricas Prometheus. Em modo multiprocess (container com --workers 2,
    ver Dockerfile/gunicorn.conf.py), agrega os dados de todos os workers a
    partir dos arquivos em PROMETHEUS_MULTIPROC_DIR -- sem isso, cada worker
    reportaria só a própria fatia do tráfego."""
    if not _metrics_autorizado():
        return jsonify({"erro": "Não autorizado."}), 401

    multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if multiproc_dir:
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
        payload = generate_latest(registry)
    else:
        payload = generate_latest()

    return payload, 200, {"Content-Type": CONTENT_TYPE_LATEST}


# ============================================================================
# SERVE REACT SPA — catch-all para todas as rotas não-API
# ============================================================================

REACT_DIST = os.path.join(RESOURCE_DIR, "frontend", "dist")


@app.route("/app", defaults={"path": ""})
@app.route("/app/<path:path>")
def serve_react(path):
    """Serve o frontend React. O React Router cuida da navegação interna."""
    if path and os.path.exists(os.path.join(REACT_DIST, path)):
        return send_from_directory(REACT_DIST, path)
    index_path = os.path.join(REACT_DIST, "index.html")
    if os.path.exists(index_path):
        return send_from_directory(REACT_DIST, "index.html")
    return "Frontend não encontrado. Execute: cd frontend && npm run build", 404


@app.route("/app/assets/<path:filename>")
def serve_react_assets(filename):
    return send_from_directory(os.path.join(REACT_DIST, "assets"), filename)


_MERCADO_PHONE_SYNC_THREAD_STARTED = False


def iniciar_sync_mercadophone_se_habilitado():
    """Inicia thread de sincronização automática no processo atual, quando configurado."""
    global _MERCADO_PHONE_SYNC_THREAD_STARTED

    if _MERCADO_PHONE_SYNC_THREAD_STARTED:
        return

    if not BACKGROUND_JOBS_ENABLED:
        return

    # ADR-014: integração MercadoPhone desligada por padrão, independente de token/config.
    if not fluxoly_config.integracao_mercadophone_habilitada():
        return

    if not (MERCADO_PHONE_SYNC_ENABLED and MERCADO_PHONE_API_TOKEN):
        return

    sync_thread = threading.Thread(
        target=loop_sincronizacao_mercado_phone,
        args=(conectar, MERCADO_PHONE_RUNTIME_CONFIG, MERCADO_PHONE_HELPERS),
        daemon=True,
        # INC-001: nome explícito (era "Thread-N" genérico) -- identifica esta
        # thread nos logs da instrumentação de conexões sem ambiguidade. Puramente
        # cosmético, não altera nenhum comportamento de sincronização.
        name="mercadophone-sync",
    )
    sync_thread.start()
    _MERCADO_PHONE_SYNC_THREAD_STARTED = True


# Em produção (Render/Gunicorn), o módulo é importado sem passar por __main__.
# Por isso iniciamos a sincronização aqui também.
iniciar_sync_mercadophone_se_habilitado()

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    is_frozen = getattr(sys, "frozen", False)
    is_server = IS_SERVER_RUNTIME
    debug_mode = not is_frozen and not is_server

    # Inicia thread de sincronização Mercado Phone se habilitada
    iniciar_sync_mercadophone_se_habilitado()

    # Abre navegador automaticamente apenas no modo desktop (não no servidor)
    if not is_server and not os.environ.get("IR_FLOW_NO_BROWSER"):
        threading.Timer(1.2, lambda: webbrowser.open(f"http://{APP_HOST}:{APP_PORT}")).start()

    # Inicia servidor Flask
    app.run(host=APP_HOST, debug=debug_mode, use_reloader=False, port=APP_PORT)
