"""
fluxoly_auditoria_repository.py

Único ponto de acesso SQL de leitura da tabela `audit_log` para a tela de
Auditoria (benchmark Mercado Phone, Etapa 2 -- `docs/engineering/plans/
PLAN-tela-auditoria.md`). Só SELECT: a escrita continua exclusiva de
`fluxoly_audit.py::registrar_log_auditoria`; nenhuma rota edita ou apaga log.
"""

_COLUNAS = (
    "a.id, a.entidade, a.entidade_id, a.usuario_id, u.nome AS usuario_nome, "
    "a.acao, a.valor_anterior, a.valor_novo, a.criado_em"
)
_FROM = "FROM audit_log a LEFT JOIN usuarios u ON a.usuario_id = u.id"


def _montar_filtros(entidade, entidade_id, usuario_id, acao, data_inicio, data_fim):
    condicoes, params = [], []
    if entidade:
        condicoes.append("a.entidade = ?")
        params.append(entidade)
    if entidade_id is not None:
        condicoes.append("a.entidade_id = ?")
        params.append(entidade_id)
    if usuario_id is not None:
        condicoes.append("a.usuario_id = ?")
        params.append(usuario_id)
    if acao:
        condicoes.append("a.acao = ?")
        params.append(acao)
    if data_inicio:
        condicoes.append("a.criado_em >= ?")
        params.append(data_inicio)
    if data_fim:
        condicoes.append("a.criado_em <= ?")
        params.append(data_fim)
    where = ("WHERE " + " AND ".join(condicoes)) if condicoes else ""
    return where, params


def contar(cursor, entidade=None, entidade_id=None, usuario_id=None, acao=None, data_inicio=None, data_fim=None):
    where, params = _montar_filtros(entidade, entidade_id, usuario_id, acao, data_inicio, data_fim)
    cursor.execute(f"SELECT COUNT(*) {_FROM} {where}", params)
    return cursor.fetchone()[0]


def buscar_paginado(cursor, entidade=None, entidade_id=None, usuario_id=None, acao=None,
                    data_inicio=None, data_fim=None, limite=50, offset=0):
    where, params = _montar_filtros(entidade, entidade_id, usuario_id, acao, data_inicio, data_fim)
    cursor.execute(
        f"SELECT {_COLUNAS} {_FROM} {where} ORDER BY a.criado_em DESC, a.id DESC LIMIT ? OFFSET ?",
        params + [limite, offset],
    )
    return cursor.fetchall()


def listar_entidades(cursor):
    cursor.execute("SELECT DISTINCT entidade FROM audit_log ORDER BY entidade")
    return [row[0] for row in cursor.fetchall()]
