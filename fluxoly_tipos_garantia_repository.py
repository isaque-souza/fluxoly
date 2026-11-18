"""
fluxoly_tipos_garantia_repository.py

Único ponto de acesso SQL do cadastro Tipos de Garantia
(docs/product/features/VENDAS.md "V1.5 -- Garantia", BR-055). Módulo
compartilhado entre Vendas (Garantia de Venda) e Assistência (Garantia de
Reparo) -- não pertence a nenhum dos dois, por isso nasce como domínio
próprio (ADR-008, prefixo `fluxoly_`), seguindo a mesma convenção de camadas
de `docs/engineering/ENGINEERING_GUIDE.md` §3.1.

`tipos_garantia` é o cadastro de política (nome + duração), nunca a garantia
concedida em si -- a instância concreta vive como snapshot em
`vendas_itens`/`os_reparos` (ver `fluxoly_vendas_repository.py`/`fluxoly_os.py`),
nunca lida ao vivo daqui depois de concedida.
"""


def inserir(cursor, nome, duracao_meses, texto=""):
    cursor.execute(
        "INSERT INTO tipos_garantia (nome, duracao_meses, texto) VALUES (?, ?, ?)",
        (nome, duracao_meses, texto),
    )
    return cursor.lastrowid


def atualizar(cursor, tipo_garantia_id, nome, duracao_meses, ativo, texto=None):
    """`texto=None` mantém o texto atual (cliente antigo que não envia o campo)."""
    cursor.execute(
        """
        UPDATE tipos_garantia
        SET nome = ?, duracao_meses = ?, ativo = ?, texto = COALESCE(?, texto),
            atualizado_em = datetime('now')
        WHERE id = ?
        """,
        (nome, duracao_meses, 1 if ativo else 0, texto, tipo_garantia_id),
    )
    return cursor.rowcount


def buscar_por_id(cursor, tipo_garantia_id):
    """Usado pelos services de Vendas/Assistência para resolver o tipo
    escolhido no momento da concessão -- nunca depois (a garantia já
    concedida é snapshot, não lê mais daqui)."""
    cursor.execute(
        "SELECT id, nome, duracao_meses, ativo, texto FROM tipos_garantia WHERE id = ?",
        (tipo_garantia_id,),
    )
    return cursor.fetchone()


def listar(cursor, incluir_inativos=False):
    if incluir_inativos:
        cursor.execute("SELECT id, nome, duracao_meses, ativo, texto FROM tipos_garantia ORDER BY nome")
    else:
        cursor.execute("SELECT id, nome, duracao_meses, ativo, texto FROM tipos_garantia WHERE ativo = 1 ORDER BY nome")
    return cursor.fetchall()
