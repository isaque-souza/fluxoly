import os
import tempfile
import uuid
from datetime import datetime

# Must be set before importing app — DB_PATH is resolved at module load time
_tmp_dir = tempfile.mkdtemp()
os.environ["IR_FLOW_DATA_DIR"] = _tmp_dir
os.environ["IR_FLOW_ENABLE_BACKGROUND_JOBS"] = "0"
os.environ["MERCADO_PHONE_SYNC_ENABLED"] = "0"
# ADR-014: a integração MercadoPhone é desligada por padrão; a suíte liga a flag para continuar cobrindo
# as rotas existentes. O estado desligado é coberto em test_mercadophone_integracao_desligada.py.
os.environ["MERCADO_PHONE_INTEGRATION_ENABLED"] = "1"
# IR_FLOW_DATA_DIR acima liga IS_SERVER_RUNTIME em app.py, que agora exige
# FLASK_SECRET_KEY (SECURITY_AUDIT_2026-07.md item 3) -- valor fixo só para teste,
# nunca usado fora deste processo.
os.environ.setdefault("FLASK_SECRET_KEY", "chave-de-teste-nao-usar-em-producao")
# KI-038: mesma razão do FLASK_SECRET_KEY acima -- IR_FLOW_DATA_DIR liga
# IS_SERVER_RUNTIME, e criar_admin_padrao() agora exige a variável nesse caso.
os.environ.setdefault("IR_FLOW_ADMIN_PASSWORD", "senha-admin-teste-nao-usar-em-producao")

import pytest  # noqa: E402
from werkzeug.security import generate_password_hash  # noqa: E402

import app as _app  # noqa: E402

SENHA_PADRAO = "senha_teste_123"


@pytest.fixture(scope="session")
def app():
    _app.app.config["TESTING"] = True
    _app.app.config["WTF_CSRF_ENABLED"] = False
    yield _app.app


@pytest.fixture
def client(app):
    """Cliente HTTP isolado por teste — nao reutiliza sessao de outros testes."""
    return app.test_client()


@pytest.fixture(autouse=True)
def _limpar_login_attempts():
    """
    O cliente de teste do Flask usa sempre o mesmo IP (127.0.0.1) e nao envia
    header Fly-Client-IP, entao todo teste que faz login compartilharia o
    mesmo identificador de rate limit. Sem isolamento, um teste que exercita
    varias tentativas de login (validas ou invalidas) esgotaria o limite
    para todos os testes seguintes na mesma sessao pytest.
    """
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM login_attempts")
        conn.commit()
    finally:
        conn.close()
    yield


def _criar_usuario(nome, perfil="tecnico", ativo=1):
    login = f"user_{uuid.uuid4().hex[:10]}"
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO usuarios (nome, usuario, senha_hash, perfil, ativo) VALUES (?, ?, ?, ?, ?)",
            (nome, login, generate_password_hash(SENHA_PADRAO), perfil, ativo),
        )
        conn.commit()
        user_id = cursor.lastrowid
    finally:
        conn.close()
    return {"id": user_id, "nome": nome, "usuario": login, "senha": SENHA_PADRAO}


def _remover_usuario(user_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM usuarios WHERE id = ?", (user_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def usuario_tecnico():
    dados = _criar_usuario("Tecnico Teste", perfil="tecnico", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_admin():
    dados = _criar_usuario("Admin Teste", perfil="admin", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_vendedor():
    dados = _criar_usuario("Vendedor Teste", perfil="vendedor", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_estoque():
    dados = _criar_usuario("Estoque Teste", perfil="estoque", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_financeiro():
    dados = _criar_usuario("Financeiro Teste", perfil="financeiro", ativo=1)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def usuario_inativo():
    dados = _criar_usuario("Usuario Inativo", perfil="tecnico", ativo=0)
    yield dados
    _remover_usuario(dados["id"])


@pytest.fixture
def login_como():
    """Factory: autentica um cliente via /api/auth/login com os dados de um fixture de usuario."""

    def _login(client, usuario):
        return client.post(
            "/api/auth/login",
            json={"usuario": usuario["usuario"], "senha": usuario["senha"]},
        )

    return _login


@pytest.fixture(scope="session")
def auth_client(app):
    client = app.test_client()
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        from werkzeug.security import generate_password_hash

        cursor.execute(
            "INSERT OR IGNORE INTO usuarios (nome, usuario, senha_hash, perfil) VALUES (?, ?, ?, ?)",
            ("Admin Teste", "admin_test", generate_password_hash("test_senha_123"), "admin"),
        )
        conn.commit()
    finally:
        conn.close()

    client.post("/login", data={"usuario": "admin_test", "senha": "test_senha_123"}, follow_redirects=True)
    return client


# ============================================================================
# Fixtures de Ordens de Serviço (Sprint 2.4)
# ============================================================================


def _reparo_ids_existentes(n=1):
    """Le reparos ja semeados por sincronizar_reparos_padrao() na inicializacao do app."""
    conn = _app.conectar()
    try:
        rows = conn.execute("SELECT id FROM reparos ORDER BY id LIMIT ?", (n,)).fetchall()
        return [r[0] for r in rows]
    finally:
        conn.close()


@pytest.fixture
def reparo_padrao_id():
    """Le um reparo ja semeado por sincronizar_reparos_padrao() na inicializacao do app."""
    return _reparo_ids_existentes(1)[0]


@pytest.fixture
def dois_reparos_ids():
    return _reparo_ids_existentes(2)


@pytest.fixture
def tipo_garantia_padrao_id():
    """V1.5 -- Garantia de Reparo (BR-061): concluir uma OS (PATCH .../status
    ou PUT .../ordens/<id> levando o status a Finalizado) passa a exigir um
    Tipo de Garantia por linha de reparo. Fixture de apoio para qualquer
    teste que finalize uma OS -- não é o objeto sob teste (isso é
    tests/test_tipos_garantia.py e o service de Garantia de Reparo)."""
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_garantia (nome, duracao_meses) VALUES (?, ?)",
            ("Garantia Teste Padrão (Reparo)", 12),
        )
        conn.commit()
        tipo_garantia_id = cursor.lastrowid
    finally:
        conn.close()
    yield tipo_garantia_id
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (tipo_garantia_id,))
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def payload_os_valido(reparo_padrao_id, tipo_garantia_padrao_id):
    """Factory: payload minimo valido para POST/PUT /api/ordens, com overrides pontuais.

    `garantias` é derivado automaticamente dos `reparo_ids` finais (depois de
    aplicar overrides) -- só tem efeito real quando o status vira Finalizado
    (BR-061), mas é sempre incluído por simplicidade (ignorado nos demais
    casos). Um teste que precise provar a rejeição por garantia ausente deve
    sobrescrever `garantias` explicitamente."""

    def _payload(**overrides):
        base = {
            "tipo": "Assistencia",
            "cliente": f"Cliente {uuid.uuid4().hex[:6]}",
            "modelo": "iPhone 13",
            "tecnico": "ISAQUE SOUZA",
            "vendedor": "Camila",
            "reparo_ids": [reparo_padrao_id],
        }
        base.update(overrides)
        if "garantias" not in base:
            base["garantias"] = {str(rid): tipo_garantia_padrao_id for rid in base.get("reparo_ids") or []}
        return base

    return _payload


@pytest.fixture
def criar_os(reparo_padrao_id):
    """Factory: cria uma OS direto no banco (sem passar pela API), devolve o id. Limpa ao final do teste."""
    ids_criados = []

    def _criar(
        tipo="Assistencia",
        cliente=None,
        modelo="iPhone 13",
        tecnico="ISAQUE SOUZA",
        vendedor="Camila",
        status="Em andamento",
        reparo_ids=None,
        valor_cobrado=0.0,
        valor_descontado=0.0,
        data=None,
    ):
        reparos = reparo_ids or [reparo_padrao_id]
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO os (tipo, cliente, aparelho, tecnico, reparo_id, status,
                    valor_cobrado, valor_descontado, custo_pecas, data, vendedor, modelo)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)
                """,
                (
                    tipo,
                    cliente or f"Cliente {uuid.uuid4().hex[:6]}",
                    modelo,
                    tecnico,
                    reparos[0],
                    status,
                    valor_cobrado,
                    valor_descontado,
                    0,
                    data or datetime.now().strftime("%Y-%m-%d"),
                    vendedor,
                    modelo,
                ),
            )
            os_id = cursor.lastrowid
            for reparo_id in reparos:
                cursor.execute("INSERT INTO os_reparos (os_id, reparo_id) VALUES (?, ?)", (os_id, reparo_id))
            conn.commit()
        finally:
            conn.close()
        ids_criados.append(os_id)
        return os_id

    yield _criar

    conn = _app.conectar()
    try:
        for os_id in ids_criados:
            conn.execute("DELETE FROM os_pecas WHERE os_id=?", (os_id,))
            conn.execute("DELETE FROM os_reparos WHERE os_id=?", (os_id,))
            conn.execute("DELETE FROM os_checklists WHERE os_id=?", (os_id,))
            conn.execute("DELETE FROM os WHERE id=?", (os_id,))
        conn.commit()
    finally:
        conn.close()


# ============================================================================
# Fixtures de Estoque (Sprint 2.5)
# ============================================================================


@pytest.fixture
def criar_item_estoque():
    """Factory: cria um item de estoque, devolve o id. Limpa (lotes, movimentacoes, item) ao final do teste."""
    ids_criados = []

    def _criar(modelo="iPhone 13", quantidade=5, valor=50.0, descricao="Peca Teste", tipo="Tela", qualidade="Padrao"):
        conn = _app.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO estoque (descricao, valor, fornecedor, quantidade, modelo, sku, tipo, qualidade)
                VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    descricao,
                    valor,
                    "Fornecedor Teste",
                    quantidade,
                    modelo,
                    f"SKU-{uuid.uuid4().hex[:8]}",
                    tipo,
                    qualidade,
                ),
            )
            conn.commit()
            item_id = cursor.lastrowid
        finally:
            conn.close()
        ids_criados.append(item_id)
        return item_id

    yield _criar

    conn = _app.conectar()
    try:
        for item_id in ids_criados:
            conn.execute("DELETE FROM estoque_lotes WHERE estoque_id=?", (item_id,))
            conn.execute("DELETE FROM movimentacoes WHERE estoque_id=?", (item_id,))
            conn.execute("DELETE FROM os_pecas WHERE estoque_id=?", (item_id,))
            conn.execute("DELETE FROM estoque WHERE id=?", (item_id,))
        conn.commit()
    finally:
        conn.close()
