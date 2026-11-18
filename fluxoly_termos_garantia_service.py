"""
fluxoly_termos_garantia_service.py

Regra de negócio do cadastro Termos de Garantia (BR-105,
docs/engineering/plans/PLAN-termos-garantia-os.md). Consumido pela OS
(`api_os.py`) via `obter_termo_garantia` -- ninguém fora daqui acessa
`fluxoly_termos_garantia_repository.py` (ENGINEERING_GUIDE.md §3.1).

O termo não tem prazo: o prazo continua no Tipo de Garantia de cada reparo
(BR-061). Sem exclusão, só inativação, como Tipos de Garantia (BR-055).
"""

import fluxoly_termos_garantia_repository as repo
from fluxoly_dados_loja_service import LIMITES as LIMITES_DADOS_LOJA

# Mesmo limite do texto padrão em Dados da Loja: os dois saem no mesmo bloco do PDF.
LIMITE_TEXTO = LIMITES_DADOS_LOJA["termos_garantia"]
LIMITE_NOME = 120

TERMO_NAO_ENCONTRADO = "Termo de Garantia não encontrado."


def _termo_para_dict(row):
    return {"id": row[0], "nome": row[1], "texto": row[2], "ativo": bool(row[3])}


def _validar(nome, texto):
    """Retorna (nome, texto, erro) já normalizados."""
    nome = (nome or "").strip() if isinstance(nome, str) else ""
    texto = (texto or "").strip() if isinstance(texto, str) else ""
    if not nome:
        return None, None, "Nome é obrigatório."
    if len(nome) > LIMITE_NOME:
        return None, None, f"Nome deve ter no máximo {LIMITE_NOME} caracteres."
    if not texto:
        return None, None, "Texto do termo é obrigatório."
    if len(texto) > LIMITE_TEXTO:
        return None, None, f"Texto do termo deve ter no máximo {LIMITE_TEXTO} caracteres."
    return nome, texto, None


def criar_termo_garantia(conectar, nome, texto):
    """Retorna (id, erro)."""
    nome, texto, erro = _validar(nome, texto)
    if erro:
        return None, erro
    conn = conectar()
    try:
        cursor = conn.cursor()
        termo_id = repo.inserir(cursor, nome, texto)
        conn.commit()
    finally:
        conn.close()
    return termo_id, None


def atualizar_termo_garantia(conectar, termo_id, nome, texto, ativo=True):
    """Retorna (sucesso, erro). Editar o termo nunca altera OS já finalizadas --
    elas guardam snapshot em `os.termo_garantia_*`."""
    nome, texto, erro = _validar(nome, texto)
    if erro:
        return False, erro
    conn = conectar()
    try:
        cursor = conn.cursor()
        if repo.atualizar(cursor, termo_id, nome, texto, ativo) == 0:
            conn.rollback()
            return False, TERMO_NAO_ENCONTRADO
        conn.commit()
    finally:
        conn.close()
    return True, None


def obter_termo_garantia(conectar, termo_id):
    """None se não existir -- o chamador decide a mensagem."""
    conn = conectar()
    try:
        row = repo.buscar_por_id(conn.cursor(), termo_id)
    finally:
        conn.close()
    return _termo_para_dict(row) if row else None


def listar_termos_garantia(conectar, incluir_inativos=False):
    conn = conectar()
    try:
        rows = repo.listar(conn.cursor(), incluir_inativos)
    finally:
        conn.close()
    return [_termo_para_dict(r) for r in rows]
