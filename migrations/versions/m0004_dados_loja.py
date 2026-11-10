"""
Dados da Loja (cabeçalho dos documentos da OS para o cliente) -- ver
docs/engineering/plans/PLAN-documentos-os-cliente.md e BR-094
(docs/product/BUSINESS_RULES.md).

DDL puro e aditivo, sem backfill: tabela nova `dados_loja` de linha única
(`id = 1`, garantido pelo CHECK). A linha nasce no primeiro salvamento.
"""

import sqlite3

ID = "0004"
DESCRICAO = "Dados da Loja: tabela dados_loja (linha única)"


def apply(cursor: sqlite3.Cursor, conn: sqlite3.Connection) -> None:
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS dados_loja (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        nome_fantasia TEXT NOT NULL DEFAULT '',
        razao_social TEXT NOT NULL DEFAULT '',
        cnpj TEXT NOT NULL DEFAULT '',
        telefone TEXT NOT NULL DEFAULT '',
        email TEXT NOT NULL DEFAULT '',
        endereco TEXT NOT NULL DEFAULT '',
        termos_entrada TEXT NOT NULL DEFAULT '',
        termos_garantia TEXT NOT NULL DEFAULT '',
        atualizado_por INTEGER,
        atualizado_em TEXT NOT NULL DEFAULT (datetime('now'))
    )
    """
    )
