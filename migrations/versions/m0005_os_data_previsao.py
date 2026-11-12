"""
Data de previsão de entrega da OS -- ver
docs/engineering/plans/PLAN-os-data-previsao.md e BR-101
(docs/product/BUSINESS_RULES.md).

DDL puro e aditivo, sem backfill: coluna nullable `os.data_previsao`
(`YYYY-MM-DD`). OS antigas ficam sem previsão e nunca aparecem como
atrasadas.
"""

import sqlite3

ID = "0005"
DESCRICAO = "OS: coluna data_previsao (previsão de entrega)"


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return any(row[1] == coluna for row in cursor.fetchall())


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    if not _coluna_existe(cursor, "os", "data_previsao"):
        cursor.execute("ALTER TABLE os ADD COLUMN data_previsao TEXT")
