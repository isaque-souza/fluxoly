"""
Termos de garantia cadastrados e escolhidos na OS -- ver
docs/engineering/plans/PLAN-termos-garantia-os.md e BR-105
(docs/product/BUSINESS_RULES.md).

DDL puro e aditivo, sem backfill: tabela nova `termos_garantia_modelos` e três
colunas nullable de snapshot em `os`. OS antigas ficam com as colunas NULL e o
comprovante de entrega segue usando `dados_loja.termos_garantia`.
"""

import sqlite3

ID = "0007"
DESCRICAO = "Termos de garantia: tabela termos_garantia_modelos e snapshot do termo na OS"

COLUNAS_OS = (
    ("termo_garantia_id", "INTEGER"),
    ("termo_garantia_nome", "TEXT"),
    ("termo_garantia_texto", "TEXT"),
)


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return any(row[1] == coluna for row in cursor.fetchall())


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS termos_garantia_modelos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            texto TEXT NOT NULL,
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL DEFAULT (datetime('now')),
            atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
        )
        """
    )
    for coluna, tipo in COLUNAS_OS:
        if not _coluna_existe(cursor, "os", coluna):
            cursor.execute(f"ALTER TABLE os ADD COLUMN {coluna} {tipo}")
