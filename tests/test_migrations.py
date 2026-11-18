"""
Testes do sistema de migrations (TD-03, Fase 2 Fatia 1).

Escopo desta fatia: só o mecanismo novo (migrations/), isolado -- app.py não
foi alterado, então nenhum teste aqui usa a fixture `app`/`client` de
conftest.py. Ver docs/operations/SPRINTS/SPRINT_TD03_MIGRATIONS_FORMAIS.md
seção 12 para a lista de testes obrigatórios desta fatia.
"""

import sqlite3

import pytest

from migrations.registry import MIGRATIONS
from migrations.runner import run_migrations

TABELAS_ESPERADAS = {
    "reparos",
    "os",
    "estoque",
    "estoque_lotes",
    "os_pecas",
    "os_reparos",
    "movimentacoes",
    "custos_operacionais",
    "integracao_sync_estado",
    "integracao_os_vistas",
    "compras",
    "usuarios",
    "os_checklists",
    "login_attempts",
    "audit_log",
    "password_reset_tokens",
    "clientes",
    "dados_loja",
    "unidades_serializadas",
    "produtos",
    "vendas",
    "vendas_itens",
    "tipos_garantia",
    "shopping_list",
    "shopping_list_logs",
    "movimentacoes_caixa",
    "contas_pagar",
    "contas_receber",
}

INDICES_ESPERADOS = {
    "idx_login_attempts_identificador_criado_em",
    "idx_audit_log_entidade",
    "idx_password_reset_tokens_usuario_id",
    "idx_clientes_telefone",
    "idx_clientes_cpf_cnpj",
    "idx_clientes_nome",
    "idx_unidades_serializadas_estoque_id",
    "idx_unidades_serializadas_produto_id",
    "idx_unidades_serializadas_status",
    "idx_unidades_serializadas_imei",
    "idx_produtos_categoria",
    "idx_produtos_sku",
    "idx_produtos_ativo",
    "idx_vendas_cliente_id",
    "idx_vendas_vendedor_id",
    "idx_vendas_itens_venda_id",
    "idx_vendas_itens_unidade_ativa",
    "idx_os_origem_id_externo",
    "idx_estoque_sku",
    "idx_estoque_tripla",
    "idx_lotes_estoque_id",
    "idx_shopping_list_os_produto",
    "idx_movimentacoes_caixa_origem",
    "idx_movimentacoes_caixa_tipo_estornada",
    "idx_movimentacoes_caixa_venda_ativa",
}


@pytest.fixture
def conn():
    conexao = sqlite3.connect(":memory:")
    yield conexao
    conexao.close()


class TestBaselineEmBancoVazio:
    def test_cria_as_24_tabelas_esperadas(self, conn):
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tabelas = {row[0] for row in cursor.fetchall()}
        assert tabelas >= TABELAS_ESPERADAS

    def test_cria_os_22_indices_esperados(self, conn):
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indices = {row[0] for row in cursor.fetchall()}
        assert indices >= INDICES_ESPERADOS

    def test_retorna_id_da_migration_aplicada(self, conn):
        executadas = run_migrations(conn)
        assert executadas == ["0001", "0002", "0003", "0004", "0005", "0006", "0007"]


class TestIdempotencia:
    def test_rodar_duas_vezes_nao_reaplica_nem_falha(self, conn):
        primeira = run_migrations(conn)
        segunda = run_migrations(conn)
        assert primeira == ["0001", "0002", "0003", "0004", "0005", "0006", "0007"]
        assert segunda == []

    def test_schema_migrations_fica_com_exatamente_0001(self, conn):
        run_migrations(conn)
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM schema_migrations")
        assert cursor.fetchall() == [("0001",), ("0002",), ("0003",), ("0004",), ("0005",), ("0006",), ("0007",)]

    def test_reaplicar_a_migration_direto_nao_duplica_backfill(self, conn):
        # Backfill de estoque_lotes é condicional (WHERE NOT EXISTS) -- roda
        # sem duplicar mesmo se a migration em si fosse chamada de novo (o
        # que run_migrations() nunca faz, mas o backfill é seguro por
        # conteúdo, não só por schema_migrations).
        run_migrations(conn)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO estoque (descricao, quantidade) VALUES ('Tela iPhone', 5)")
        conn.commit()
        MIGRATIONS[0].apply(cursor, conn)
        MIGRATIONS[0].apply(cursor, conn)
        cursor.execute("SELECT id FROM estoque WHERE descricao = 'Tela iPhone'")
        estoque_id = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM estoque_lotes WHERE estoque_id = ?", (estoque_id,))
        assert cursor.fetchone()[0] == 1


class TestBancoAtrasado:
    def test_baseline_completa_banco_sem_colunas_recentes(self, conn):
        """Simula um banco 'atrasado' -- schema mínimo original, sem os 37
        ALTER TABLE aditivos -- e confirma que run_migrations() completa
        corretamente (prova direta da decisão da Phase 1 seção 6: a baseline
        não pode assumir que as colunas aditivas já existem)."""
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE os (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT,
                cliente TEXT,
                aparelho TEXT,
                tecnico TEXT,
                reparo_id INTEGER,
                status TEXT,
                valor_cobrado REAL,
                valor_descontado REAL,
                custo_pecas REAL,
                data TEXT
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE estoque (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descricao TEXT,
                valor REAL,
                fornecedor TEXT,
                quantidade INTEGER,
                data_compra TEXT,
                sku TEXT,
                modelo TEXT,
                tipo TEXT,
                qualidade TEXT
            )
            """
        )
        cursor.execute(
            "CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nome TEXT NOT NULL, "
            "usuario TEXT UNIQUE NOT NULL, senha_hash TEXT NOT NULL, "
            "perfil TEXT NOT NULL DEFAULT 'tecnico', ativo INTEGER NOT NULL DEFAULT 1)"
        )
        conn.commit()

        run_migrations(conn)

        cursor.execute("PRAGMA table_info(os)")
        colunas_os = {row[1] for row in cursor.fetchall()}
        assert {"data_finalizado", "modelo", "cliente_id", "id_externo_integracao"} <= colunas_os

        cursor.execute("PRAGMA table_info(estoque)")
        colunas_estoque = {row[1] for row in cursor.fetchall()}
        assert {"requer_imei"} <= colunas_estoque

        cursor.execute("PRAGMA table_info(usuarios)")
        colunas_usuarios = {row[1] for row in cursor.fetchall()}
        assert "limite_desconto_livre" in colunas_usuarios


class TestOrdemDeExecucao:
    def test_registry_nao_esta_vazio_e_comeca_pela_0001(self):
        assert len(MIGRATIONS) >= 1
        assert MIGRATIONS[0].ID == "0001"

    def test_ids_sao_unicos_e_crescentes(self):
        ids = [m.ID for m in MIGRATIONS]
        assert len(ids) == len(set(ids))
        assert ids == sorted(ids)


class TestProtecaoContraLocked:
    def test_operational_error_locked_retorna_lista_vazia_sem_propagar(self, conn, monkeypatch):
        class _MigracaoQueTrava:
            ID = "9999"

            @staticmethod
            def apply(cursor, conn):
                raise sqlite3.OperationalError("database is locked")

        monkeypatch.setattr("migrations.runner.MIGRATIONS", [_MigracaoQueTrava])
        resultado = run_migrations(conn)
        assert resultado == []

    def test_operational_error_sem_locked_propaga(self, conn, monkeypatch):
        class _MigracaoComErroReal:
            ID = "9999"

            @staticmethod
            def apply(cursor, conn):
                raise sqlite3.OperationalError("syntax error near FOO")

        monkeypatch.setattr("migrations.runner.MIGRATIONS", [_MigracaoComErroReal])
        with pytest.raises(sqlite3.OperationalError):
            run_migrations(conn)


class TestProtecaoContraCorridaDeMigrations:
    """KI-035: com múltiplos workers Gunicorn, dois processos podem ler
    schema_migrations antes de qualquer commit do outro e concluir que a
    mesma migration ainda falta -- o segundo INSERT perde a corrida e recebe
    sqlite3.IntegrityError (não OperationalError), que TestProtecaoContraLocked
    acima não cobre. Reproduzido em produção (deploy do commit d7ef012,
    2026-08-10, "Worker failed to boot") e de novo no primeiro boot do preview
    do INC-003."""

    def test_corrida_em_schema_migrations_id_nao_propaga_e_segue_para_a_proxima(self, conn, monkeypatch):
        class _MigracaoQuePerdeuACorrida:
            ID = "9999"

            @staticmethod
            def apply(cursor, conn):
                # Simula outro worker que já inseriu e commitou este ID um
                # instante antes -- o INSERT que run_migrations() tenta a
                # seguir (linha correspondente em migrations/runner.py) vai
                # colidir com a UNIQUE constraint de schema_migrations.id.
                cursor.execute("INSERT INTO schema_migrations (id) VALUES (?)", ("9999",))
                conn.commit()

        class _MigracaoSeguinteSemConflito:
            ID = "9999b"

            @staticmethod
            def apply(cursor, conn):
                cursor.execute("CREATE TABLE _prova_migration_seguinte (id INTEGER)")

        monkeypatch.setattr(
            "migrations.runner.MIGRATIONS",
            [_MigracaoQuePerdeuACorrida, _MigracaoSeguinteSemConflito],
        )

        resultado = run_migrations(conn)

        # A migration que perdeu a corrida não aparece como "aplicada por
        # esta chamada" (outro worker já a aplicou) -- mas o boot não cai, e
        # a migration seguinte pendente, sem conflito, continua sendo
        # aplicada no mesmo boot (não aborta o loop inteiro).
        assert resultado == ["9999b"]
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='_prova_migration_seguinte'")
        assert cursor.fetchone() is not None

    def test_integrity_error_que_nao_e_schema_migrations_propaga(self, conn, monkeypatch):
        """Guarda contra falso-negativo: um IntegrityError de origem
        diferente (ex.: violação de UNIQUE de dado real dentro do apply() de
        uma migration) NUNCA pode ser mascarado como "outro worker já
        aplicou" -- precisa propagar, senão uma falha real de schema/dado
        ficaria escondida."""

        class _MigracaoComErroDeDadoReal:
            ID = "9999"

            @staticmethod
            def apply(cursor, conn):
                cursor.execute("CREATE TABLE _t_dado_real (id INTEGER PRIMARY KEY)")
                cursor.execute("INSERT INTO _t_dado_real (id) VALUES (1)")
                cursor.execute("INSERT INTO _t_dado_real (id) VALUES (1)")  # UNIQUE constraint failed: _t_dado_real.id

        monkeypatch.setattr("migrations.runner.MIGRATIONS", [_MigracaoComErroDeDadoReal])
        with pytest.raises(sqlite3.IntegrityError):
            run_migrations(conn)


class TestBootstrapDeAppUsaRunMigrations:
    def test_conectar_nao_expoe_mais_criar_tabelas(self):
        """TD-03 Fatia 2: criar_tabelas()/SCHEMA_READY/SCHEMA_LOCK foram
        removidos de app.py -- run_migrations() (testado no resto deste
        arquivo) é o único mecanismo de schema. Este teste substitui
        TestEquivalenciaComOMecanismoAntigo (Fatia 1), cuja premissa -- comparar
        contra o mecanismo antigo -- deixou de existir nesta fatia."""
        import app as appmod

        assert not hasattr(appmod, "criar_tabelas")
        assert not hasattr(appmod, "SCHEMA_READY")
        assert not hasattr(appmod, "SCHEMA_LOCK")

    def test_schema_migrations_registrado_apos_bootstrap_real(self):
        """A conexão real da aplicação (via app.conectar(), depois do
        bootstrap de import) já deve ter schema_migrations = ['0001', '0002', '0003', '0004', '0005', '0006', '0007']."""
        import app as appmod

        conn = appmod.conectar()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM schema_migrations")
            assert cursor.fetchall() == [("0001",), ("0002",), ("0003",), ("0004",), ("0005",), ("0006",), ("0007",)]
        finally:
            conn.close()


class TestM0003CorridaEntreWorkers:
    """KI-058: no boot os 2 workers do Gunicorn aplicam a m0003 juntos; o outro
    worker pode criar `os.unidade_serializada_id` entre a checagem e o ALTER
    (produção, 2026-11-09, `duplicate column name` derrubou o boot)."""

    def _banco_ate_0002(self, conn, monkeypatch):
        monkeypatch.setattr("migrations.runner.MIGRATIONS", [m for m in MIGRATIONS if m.ID != "0003"])
        run_migrations(conn)
        monkeypatch.undo()

    def test_coluna_criada_pelo_outro_worker_no_meio_nao_derruba(self, conn, monkeypatch):
        from migrations.versions import m0003_compras_aparelhos as m0003

        self._banco_ate_0002(conn, monkeypatch)
        conn.execute("ALTER TABLE os ADD COLUMN unidade_serializada_id INTEGER")  # o "outro worker"
        monkeypatch.setattr(m0003, "_coluna_existe", lambda *_: False)  # checagem feita antes dele

        m0003.apply(conn.cursor(), conn)

        colunas = [r[1] for r in conn.execute("PRAGMA table_info(os)")]
        assert colunas.count("unidade_serializada_id") == 1

    def test_outro_operational_error_no_alter_propaga(self, conn, monkeypatch):
        from migrations.versions import m0003_compras_aparelhos as m0003

        self._banco_ate_0002(conn, monkeypatch)
        conn.execute("DROP TABLE os")
        conn.execute("CREATE VIEW os AS SELECT 1 AS id")  # ALTER em view falha com outro erro
        monkeypatch.setattr(m0003, "_coluna_existe", lambda *_: False)

        with pytest.raises(sqlite3.OperationalError):
            m0003.apply(conn.cursor(), conn)


class TestTravaEntreWorkers:
    """KI-060: com a trava, dois workers rodando o bootstrap ao mesmo tempo nunca
    aplicam migrations em paralelo. Threads com conexões próprias disputam a trava
    de arquivo do SQLite do mesmo jeito que processos separados."""

    @pytest.fixture
    def banco_em_tmp(self, tmp_path, monkeypatch):
        caminho = str(tmp_path / "database.db")
        monkeypatch.setattr("migrations.runner.DB_PATH", caminho)
        return caminho

    def test_dois_workers_simultaneos_nunca_aplicam_em_paralelo(self, banco_em_tmp, monkeypatch):
        import threading
        import time

        estado = {"rodando": 0, "maximo": 0, "aplicacoes": 0}
        guarda = threading.Lock()

        class _MigracaoLenta:
            ID = "9001"

            @staticmethod
            def apply(cursor, conn):
                with guarda:
                    estado["rodando"] += 1
                    estado["maximo"] = max(estado["maximo"], estado["rodando"])
                    estado["aplicacoes"] += 1
                time.sleep(0.3)
                with guarda:
                    estado["rodando"] -= 1

        monkeypatch.setattr("migrations.runner.MIGRATIONS", [_MigracaoLenta])
        largada = threading.Barrier(2)
        resultados, erros = [], []

        def worker():
            largada.wait()
            try:
                resultados.append(run_migrations())
            except Exception as exc:  # pragma: no cover - só aparece se a trava falhar
                erros.append(exc)

        threads = [threading.Thread(target=worker) for _ in range(2)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=30)

        assert erros == []
        assert estado["maximo"] == 1
        assert estado["aplicacoes"] == 1
        assert sorted(resultados, key=len) == [[], ["9001"]]

    def test_espera_a_trava_do_outro_worker_e_depois_aplica(self, banco_em_tmp):
        import threading
        import time

        outro_worker = sqlite3.connect(banco_em_tmp + ".migrations-lock", isolation_level=None, check_same_thread=False)
        outro_worker.execute("BEGIN EXCLUSIVE")
        threading.Timer(0.5, outro_worker.close).start()

        inicio = time.monotonic()
        aplicadas = run_migrations()

        assert time.monotonic() - inicio >= 0.4
        assert aplicadas == [m.ID for m in MIGRATIONS]

    def test_trava_presa_alem_do_timeout_retorna_lista_vazia(self, banco_em_tmp, monkeypatch):
        monkeypatch.setattr("migrations.runner._SQLITE_TIMEOUT_SECONDS", 0.2)
        outro_worker = sqlite3.connect(banco_em_tmp + ".migrations-lock", isolation_level=None)
        outro_worker.execute("BEGIN EXCLUSIVE")
        try:
            assert run_migrations() == []
        finally:
            outro_worker.close()

    def test_trava_e_solta_depois_de_rodar(self, banco_em_tmp):
        run_migrations()

        outro = sqlite3.connect(banco_em_tmp + ".migrations-lock", timeout=0, isolation_level=None)
        try:
            outro.execute("BEGIN EXCLUSIVE")  # não levanta "locked"
        finally:
            outro.close()
