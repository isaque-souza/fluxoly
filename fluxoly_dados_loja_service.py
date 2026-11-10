"""
fluxoly_dados_loja_service.py

Regra de negócio do domínio Dados da Loja (BR-094) — não conhece Flask
(`docs/engineering/ENGINEERING_GUIDE.md` §3.1).

Responsabilidade: o cadastro único com os dados da loja que vão no cabeçalho
dos documentos da OS para o cliente (BR-095 a BR-098). Nome fantasia é
obrigatório; os demais campos são opcionais, com limite de tamanho.

Depende de: `fluxoly_dados_loja_repository.py` (SQL), `fluxoly_audit.py`
(auditoria de cada salvamento).
"""

import fluxoly_dados_loja_repository as repo
from fluxoly_audit import registrar_log_auditoria

CAMPOS = repo.CAMPOS

LIMITES = {
    "nome_fantasia": 120,
    "razao_social": 160,
    "cnpj": 30,
    "telefone": 40,
    "email": 120,
    "endereco": 300,
    "termos_entrada": 4000,
    "termos_garantia": 4000,
}

ROTULOS = {
    "nome_fantasia": "Nome fantasia",
    "razao_social": "Razão social",
    "cnpj": "CNPJ",
    "telefone": "Telefone",
    "email": "E-mail",
    "endereco": "Endereço",
    "termos_entrada": "Termos de entrada",
    "termos_garantia": "Termos de garantia",
}


def _vazio():
    dados = dict.fromkeys(CAMPOS, "")
    dados["atualizado_em"] = None
    return dados


def _para_dict(row):
    if not row:
        return _vazio()
    dados = {campo: row[i] or "" for i, campo in enumerate(CAMPOS)}
    dados["atualizado_em"] = row[len(CAMPOS)]
    return dados


def obter_dados_loja_com_cursor(cursor):
    """Para quem já tem uma conexão aberta (ex.: documento da OS). Sempre devolve
    um dict com todas as chaves — vazio enquanto a loja não foi cadastrada."""
    return _para_dict(repo.buscar(cursor))


def obter_dados_loja(conectar):
    conn = conectar()
    try:
        return obter_dados_loja_com_cursor(conn.cursor())
    finally:
        conn.close()


def salvar_dados_loja(conectar, usuario_id, payload):
    """Retorna (dados_salvos, erro). `erro` é None em caso de sucesso."""
    valores = {}
    for campo in CAMPOS:
        valor = payload.get(campo)
        if valor is not None and not isinstance(valor, str):
            return None, f"{ROTULOS[campo]} inválido."
        valor = (valor or "").strip()
        if len(valor) > LIMITES[campo]:
            return None, f"{ROTULOS[campo]} deve ter no máximo {LIMITES[campo]} caracteres."
        valores[campo] = valor

    if not valores["nome_fantasia"]:
        return None, "Nome fantasia é obrigatório."

    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = _para_dict(repo.buscar(cursor))
        repo.salvar(cursor, valores, usuario_id)
        registrar_log_auditoria(
            cursor,
            "dados_loja",
            1,
            usuario_id,
            "update",
            antes={c: antes[c] for c in CAMPOS},
            depois=valores,
        )
        conn.commit()
        return _para_dict(repo.buscar(cursor)), None
    finally:
        conn.close()
