"""
fluxoly_dados_loja_repository.py

Único ponto de acesso SQL do domínio Dados da Loja (BR-094) — convenção
controller → service → repository de `docs/engineering/ENGINEERING_GUIDE.md`
§3.1. Nenhuma regra de negócio aqui, só queries parametrizadas.

Tabela: `dados_loja` (linha única, `id = 1` — migration `m0004`).

Depende de: nenhum outro módulo de domínio.
"""

CAMPOS = (
    "nome_fantasia",
    "razao_social",
    "cnpj",
    "telefone",
    "email",
    "endereco",
    "termos_entrada",
    "termos_garantia",
)

_COLUNAS = ", ".join(CAMPOS + ("atualizado_em",))


def buscar(cursor):
    cursor.execute(f"SELECT {_COLUNAS} FROM dados_loja WHERE id = 1")
    return cursor.fetchone()


def salvar(cursor, valores, usuario_id):
    """Upsert da linha única. `valores` é um dict com exatamente as chaves de CAMPOS."""
    colunas = ", ".join(CAMPOS)
    marcadores = ", ".join("?" for _ in CAMPOS)
    atualizacoes = ", ".join(f"{c} = excluded.{c}" for c in CAMPOS)
    cursor.execute(
        f"""
        INSERT INTO dados_loja (id, {colunas}, atualizado_por, atualizado_em)
        VALUES (1, {marcadores}, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET {atualizacoes},
            atualizado_por = excluded.atualizado_por,
            atualizado_em = excluded.atualizado_em
        """,
        tuple(valores[c] for c in CAMPOS) + (usuario_id,),
    )
