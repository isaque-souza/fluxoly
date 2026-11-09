"""
fluxoly_caixa_service.py

Regra de negócio pura do domínio Caixa (Financeiro Mínimo, BR-067 a BR-069,
docs/engineering/plans/PLAN-financeiro-minimo.md) -- não conhece Flask,
`request` nem `jsonify` (ENGINEERING_GUIDE.md §3.1).

`registrar_entrada_de_venda`/`estornar_entrada_de_venda` recebem `cursor` já
aberto por `fluxoly_vendas_service.py` (iniciar_venda/cancelar_venda) --
nunca abrem conexão própria, para que a criação/estorno da venda e a
movimentação de caixa sejam sempre a mesma transação atômica (achado da
revisão final do plano, 2026-08-08). A idempotência real é garantida pelo
índice único `idx_movimentacoes_caixa_venda_ativa` (banco), não só pela
checagem em código.

`registrar_saida_de_conta_pagar`/`registrar_entrada_de_conta_receber` seguem
o mesmo padrão cursor-based, chamadas de dentro da baixa de Contas a
Pagar/Receber (mesma transação).

O resto (CRUD de movimentação manual, saldo, relatório) abre conexão
própria via `conectar`, mesmo padrão do resto dos domínios controller/
service/repository.

Depende de: `fluxoly_caixa_repository.py` (SQL), `fluxoly_audit.py`.
"""

import sqlite3

import fluxoly_caixa_repository as repo
from fluxoly_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20


def _movimentacao_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "tipo": row[1],
        "valor": row[2],
        "descricao": row[3] or "",
        "origem": row[4],
        "origem_id": row[5],
        "estornada": bool(row[6]),
        "usuario_id": row[7],
        "criado_em": row[8],
    }


def registrar_entrada_de_venda(cursor, venda_id, valor, usuario_id):
    """BR-069 -- chamada de dentro de `iniciar_venda()`, antes do
    `conn.commit()`. Idempotente: se já existe uma entrada ativa para esta
    venda (dupla chamada, retry), não duplica -- o guardião real é o índice
    único `idx_movimentacoes_caixa_venda_ativa`, esta checagem prévia só
    evita uma IntegrityError desnecessária no caminho feliz."""
    existente = repo.buscar_ativa_por_origem(cursor, "venda", venda_id)
    if existente:
        return existente[0]

    try:
        movimentacao_id = repo.inserir(cursor, "entrada", valor, f"Venda #{venda_id}", "venda", venda_id, usuario_id)
    except sqlite3.IntegrityError:
        # Corrida: outra chamada venceu entre a checagem acima e este INSERT --
        # o índice único é quem decide, aqui só devolvemos a que já existe.
        existente = repo.buscar_ativa_por_origem(cursor, "venda", venda_id)
        return existente[0] if existente else None

    registrar_log_auditoria(
        cursor,
        "movimentacao_caixa",
        movimentacao_id,
        usuario_id,
        "create",
        depois={"tipo": "entrada", "valor": valor, "origem": "venda", "origem_id": venda_id},
    )
    return movimentacao_id


def estornar_entrada_de_venda(cursor, venda_id, usuario_id):
    """BR-069 -- chamada de dentro de `cancelar_venda()`, antes do
    `conn.commit()`. Idempotente: se não há entrada ativa para a venda (já
    estornada, ou nunca existiu), não faz nada -- nunca apaga a linha,
    preserva auditoria."""
    existente = repo.buscar_ativa_por_origem(cursor, "venda", venda_id)
    if not existente:
        return

    movimentacao_id = existente[0]
    repo.estornar(cursor, movimentacao_id)
    registrar_log_auditoria(
        cursor,
        "movimentacao_caixa",
        movimentacao_id,
        usuario_id,
        "estorno",
        antes={"estornada": False},
        depois={"estornada": True},
    )


def registrar_saida_de_compra_aparelho(cursor, compra_id, valor, usuario_id):
    """BR-086 -- chamada de dentro de `registrar_compra()` (domínio Compra de Aparelhos),
    antes do `conn.commit()`. Mesmo desenho de `registrar_entrada_de_venda`: idempotente,
    com o índice único `idx_movimentacoes_caixa_compra_ativa` como guardião real."""
    existente = repo.buscar_ativa_por_origem(cursor, "compra_aparelho", compra_id)
    if existente:
        return existente[0]

    try:
        movimentacao_id = repo.inserir(
            cursor, "saida", valor, f"Compra de aparelho #{compra_id}", "compra_aparelho", compra_id, usuario_id
        )
    except sqlite3.IntegrityError:
        existente = repo.buscar_ativa_por_origem(cursor, "compra_aparelho", compra_id)
        return existente[0] if existente else None

    registrar_log_auditoria(
        cursor,
        "movimentacao_caixa",
        movimentacao_id,
        usuario_id,
        "create",
        depois={"tipo": "saida", "valor": valor, "origem": "compra_aparelho", "origem_id": compra_id},
    )
    return movimentacao_id


def estornar_saida_de_compra_aparelho(cursor, compra_id, usuario_id):
    """BR-086/BR-087 -- chamada de dentro de `cancelar_compra()`, antes do
    `conn.commit()`. Idempotente; nunca apaga a linha."""
    existente = repo.buscar_ativa_por_origem(cursor, "compra_aparelho", compra_id)
    if not existente:
        return

    movimentacao_id = existente[0]
    repo.estornar(cursor, movimentacao_id)
    registrar_log_auditoria(
        cursor,
        "movimentacao_caixa",
        movimentacao_id,
        usuario_id,
        "estorno",
        antes={"estornada": False},
        depois={"estornada": True},
    )


def registrar_saida_de_conta_pagar(cursor, conta_pagar_id, valor, descricao, usuario_id):
    """Chamada de dentro da baixa de Contas a Pagar (mesma transação),
    nunca abre conexão própria. Retorna o id da movimentação criada."""
    movimentacao_id = repo.inserir(cursor, "saida", valor, descricao, "conta_pagar", conta_pagar_id, usuario_id)
    registrar_log_auditoria(
        cursor,
        "movimentacao_caixa",
        movimentacao_id,
        usuario_id,
        "create",
        depois={"tipo": "saida", "valor": valor, "origem": "conta_pagar", "origem_id": conta_pagar_id},
    )
    return movimentacao_id


def registrar_entrada_de_conta_receber(cursor, conta_receber_id, valor, descricao, usuario_id):
    """Chamada de dentro da baixa de Contas a Receber (mesma transação),
    nunca abre conexão própria. Retorna o id da movimentação criada."""
    movimentacao_id = repo.inserir(cursor, "entrada", valor, descricao, "conta_receber", conta_receber_id, usuario_id)
    registrar_log_auditoria(
        cursor,
        "movimentacao_caixa",
        movimentacao_id,
        usuario_id,
        "create",
        depois={"tipo": "entrada", "valor": valor, "origem": "conta_receber", "origem_id": conta_receber_id},
    )
    return movimentacao_id


def criar_movimentacao_manual(conectar, usuario_id, tipo, valor, descricao=""):
    """Retorna (movimentacao_id, erro). `erro` é None em caso de sucesso."""
    tipo = (tipo or "").strip().lower()
    if tipo not in ("entrada", "saida"):
        return None, "Tipo deve ser 'entrada' ou 'saida'."
    if not isinstance(valor, int | float) or valor <= 0:
        return None, "Valor deve ser maior que zero."
    descricao = (descricao or "").strip()

    conn = conectar()
    try:
        cursor = conn.cursor()
        movimentacao_id = repo.inserir(cursor, tipo, valor, descricao, "manual", None, usuario_id)
        registrar_log_auditoria(
            cursor,
            "movimentacao_caixa",
            movimentacao_id,
            usuario_id,
            "create",
            depois={"tipo": tipo, "valor": valor, "origem": "manual", "descricao": descricao},
        )
        conn.commit()
    finally:
        conn.close()

    return movimentacao_id, None


def estornar_movimentacao_manual(conectar, usuario_id, movimentacao_id):
    """Retorna (sucesso, erro). Só estorna movimentação de origem 'manual' --
    entradas/saídas automáticas (venda, conta a pagar/receber) são estornadas
    pelo fluxo de origem (cancelamento de venda, etc.), nunca diretamente
    aqui, para não desalinhar `movimentacao_caixa_id` da conta de origem."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, movimentacao_id)
        if not row:
            return False, "Movimentação não encontrada."
        if row[4] != "manual":
            return False, "Só é possível estornar movimentações manuais diretamente."
        if row[6]:
            return False, "Movimentação já está estornada."

        repo.estornar(cursor, movimentacao_id)
        registrar_log_auditoria(
            cursor,
            "movimentacao_caixa",
            movimentacao_id,
            usuario_id,
            "estorno",
            antes={"estornada": False},
            depois={"estornada": True},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def listar_movimentacoes(conectar, tipo=None, origem=None, data_inicio=None, data_fim=None, page=None, per_page=None):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, tipo, origem, data_inicio, data_fim)
        rows = repo.buscar_paginado(cursor, tipo, origem, data_inicio, data_fim, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_movimentacao_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_saldo(conectar):
    conn = conectar()
    try:
        cursor = conn.cursor()
        saldo = repo.calcular_saldo(cursor)
    finally:
        conn.close()
    return saldo


def obter_relatorio_fluxo_caixa(conectar, data_inicio=None, data_fim=None):
    conn = conectar()
    try:
        cursor = conn.cursor()
        linhas = repo.agrupar_por_periodo(cursor, data_inicio, data_fim)
    finally:
        conn.close()

    return [
        {"dia": dia, "entradas": entradas, "saidas": saidas, "saldo_periodo": round(entradas - saidas, 2)}
        for dia, entradas, saidas in linhas
    ]
