"""
Termo de Garantia único: o cadastro `tipos_garantia` (nome + prazo) ganha o
texto do termo -- ver docs/engineering/plans/PLAN-termo-unico-garantia.md e
BR-105 (docs/product/BUSINESS_RULES.md).

DDL puro e aditivo: uma coluna TEXT com default ''. Tipos existentes ficam sem
texto (o comprovante usa o texto padrão de Dados da Loja). A tabela
`termos_garantia_modelos` (m0007) deixa de ser usada e não é removida aqui.
"""

import sqlite3

ID = "0008"
DESCRICAO = "Tipos de garantia: coluna texto (termo de garantia único)"


def _coluna_existe(cursor, tabela, coluna):
    cursor.execute(f"PRAGMA table_info({tabela})")
    return any(row[1] == coluna for row in cursor.fetchall())


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    if not _coluna_existe(cursor, "tipos_garantia", "texto"):
        cursor.execute("ALTER TABLE tipos_garantia ADD COLUMN texto TEXT NOT NULL DEFAULT ''")
