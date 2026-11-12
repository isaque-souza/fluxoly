"""
fluxoly_auditoria_service.py

Regra de leitura da tela de Auditoria (`docs/engineering/plans/
PLAN-tela-auditoria.md`). Só consulta -- nunca remonta dado pessoal: os
snapshots são devolvidos exatamente como gravados (já mascarados por
`fluxoly_audit.py::mascarar_audit_log_pii_expirado` após o prazo de retenção).
"""

import json

import fluxoly_auditoria_repository as repo

ACOES_VALIDAS = ("create", "update", "delete", "status_change")
POR_PAGINA_MAX = 100


def _parse_json(valor):
    if valor in (None, ""):
        return None
    try:
        return json.loads(valor)
    except (TypeError, ValueError):
        return valor


def _diff(antes, depois):
    """Lista campo a campo do que mudou -- só quando ao menos um lado é dict.
    Para create/delete (um lado vazio) devolve cada campo do lado presente."""
    if not isinstance(antes, dict) and not isinstance(depois, dict):
        return []
    antes = antes if isinstance(antes, dict) else {}
    depois = depois if isinstance(depois, dict) else {}
    campos = []
    for chave in sorted(set(antes) | set(depois)):
        valor_antes, valor_depois = antes.get(chave), depois.get(chave)
        if valor_antes != valor_depois:
            campos.append({"campo": chave, "antes": valor_antes, "depois": valor_depois})
    return campos


def _linha_para_dict(row):
    antes = _parse_json(row[6])
    depois = _parse_json(row[7])
    return {
        "id": row[0],
        "entidade": row[1],
        "entidade_id": row[2],
        "usuario_id": row[3],
        "usuario_nome": row[4],
        "acao": row[5],
        "antes": antes,
        "depois": depois,
        "alteracoes": _diff(antes, depois),
        "criado_em": row[8],
    }


def listar_auditoria(conectar, entidade=None, entidade_id=None, usuario_id=None, acao=None,
                     data_inicio=None, data_fim=None, page=1, per_page=50):
    """Retorna (resultado, erro)."""
    if acao and acao not in ACOES_VALIDAS:
        return None, "Ação inválida."
    if page < 1 or per_page < 1:
        return None, "Parâmetros page/per_page inválidos."
    per_page = min(per_page, POR_PAGINA_MAX)
    if data_fim and len(data_fim) == 10:
        data_fim = f"{data_fim} 23:59:59"

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, entidade, entidade_id, usuario_id, acao, data_inicio, data_fim)
        linhas = repo.buscar_paginado(
            cursor, entidade, entidade_id, usuario_id, acao, data_inicio, data_fim,
            limite=per_page, offset=(page - 1) * per_page,
        )
        entidades = repo.listar_entidades(cursor)
    finally:
        conn.close()
    return {
        "items": [_linha_para_dict(r) for r in linhas],
        "total": total,
        "page": page,
        "per_page": per_page,
        "entidades": entidades,
    }, None
