"""
fluxoly_termos_garantia_repository.py

Único ponto de acesso SQL do cadastro Termos de Garantia (BR-105,
docs/engineering/plans/PLAN-termos-garantia-os.md). Mesma convenção de camadas
de `docs/engineering/ENGINEERING_GUIDE.md` §3.1 e mesmo formato de
`fluxoly_tipos_garantia_repository.py`.

`termos_garantia_modelos` é o cadastro (nome + texto). O termo escolhido numa OS
vive como snapshot em `os.termo_garantia_*` (ver `fluxoly_os.py`) e nunca é lido
ao vivo daqui depois de gravado. O nome da tabela evita confusão com a coluna
`dados_loja.termos_garantia`, que segue como texto padrão da loja.
"""

_COLUNAS = "id, nome, texto, ativo"


def inserir(cursor, nome, texto):
    cursor.execute(
        "INSERT INTO termos_garantia_modelos (nome, texto) VALUES (?, ?)",
        (nome, texto),
    )
    return cursor.lastrowid


def atualizar(cursor, termo_id, nome, texto, ativo):
    cursor.execute(
        """
        UPDATE termos_garantia_modelos
        SET nome = ?, texto = ?, ativo = ?, atualizado_em = datetime('now')
        WHERE id = ?
        """,
        (nome, texto, 1 if ativo else 0, termo_id),
    )
    return cursor.rowcount


def buscar_por_id(cursor, termo_id):
    cursor.execute(f"SELECT {_COLUNAS} FROM termos_garantia_modelos WHERE id = ?", (termo_id,))
    return cursor.fetchone()


def listar(cursor, incluir_inativos=False):
    if incluir_inativos:
        cursor.execute(f"SELECT {_COLUNAS} FROM termos_garantia_modelos ORDER BY nome")
    else:
        cursor.execute(f"SELECT {_COLUNAS} FROM termos_garantia_modelos WHERE ativo = 1 ORDER BY nome")
    return cursor.fetchall()
