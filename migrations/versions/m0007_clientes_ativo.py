"""
Inativação de clientes (hotfix P1-3, KI-066) -- ver
docs/engineering/plans/PLAN-inativacao-clientes.md e BR-024
(docs/product/BUSINESS_RULES.md).

DDL puro e aditivo: uma coluna `ativo INTEGER NOT NULL DEFAULT 1` em `clientes`. O SQLite preenche o
default em toda linha existente -- todo cliente atual continua ativo; ids, contagens e vínculos
(`os`/`vendas`/`compras_aparelhos.cliente_id`) não mudam. Sem backfill, sem tocar outra tabela.

Rollback (só se necessário, com backup): `ALTER TABLE clientes DROP COLUMN ativo` (SQLite >= 3.35) e
`DELETE FROM schema_migrations WHERE id = '0007'`. O rollback só do código dispensa isso -- o código
anterior lista as colunas explicitamente e ignora `ativo`.
"""

import sqlite3

ID = "0007"
DESCRICAO = "Clientes: coluna ativo (inativação no lugar de exclusão física)"


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return any(row[1] == coluna for row in cursor.fetchall())


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    if not _coluna_existe(cursor, "clientes", "ativo"):
        cursor.execute("ALTER TABLE clientes ADD COLUMN ativo INTEGER NOT NULL DEFAULT 1")
