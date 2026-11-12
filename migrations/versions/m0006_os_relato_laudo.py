"""
Relato do cliente, laudo técnico e observação interna da OS -- ver
docs/engineering/plans/PLAN-os-relato-laudo.md e BR-102
(docs/product/BUSINESS_RULES.md).

DDL puro e aditivo, sem backfill: três colunas TEXT nullable em `os`.
`observacoes` (já existente, sai no documento do cliente) não muda.
"""

import sqlite3

ID = "0006"
DESCRICAO = "OS: colunas relato_cliente, laudo_tecnico e observacao_interna"

COLUNAS = ("relato_cliente", "laudo_tecnico", "observacao_interna")


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return any(row[1] == coluna for row in cursor.fetchall())


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    for coluna in COLUNAS:
        if not _coluna_existe(cursor, "os", coluna):
            cursor.execute(f"ALTER TABLE os ADD COLUMN {coluna} TEXT")
