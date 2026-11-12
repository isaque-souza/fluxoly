"""
fluxoly_contas_receber_service.py

Regra de negócio pura do domínio Contas a Receber (Financeiro Mínimo,
docs/engineering/plans/PLAN-financeiro-minimo.md) -- não conhece Flask,
`request` nem `jsonify` (ENGINEERING_GUIDE.md §3.1). Espelho de
`fluxoly_contas_pagar_service.py`.

BR-068 -- Contas a Receber representa só compromissos financeiros gerais,
sem FK ou qualquer relação com o domínio Vendas: nenhuma função aqui recebe
ou consulta `venda_id`/dado de Vendas.

A baixa (`receber_conta`) transiciona `status: pendente -> recebido` e chama
`fluxoly_caixa_service.registrar_entrada_de_conta_receber` na mesma
transação (cursor compartilhado).

Depende de: `fluxoly_contas_receber_repository.py` (SQL), `fluxoly_caixa_service.py`,
`fluxoly_audit.py`.
"""

import fluxoly_caixa_service as caixa_service
import fluxoly_contas_receber_repository as repo
from fluxoly_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20


def _conta_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "descricao": row[1],
        "categoria": row[2] or "",
        "valor": row[3],
        "data_vencimento": row[4],
        "status": row[5],
        "movimentacao_caixa_id": row[6],
        "criado_em": row[7],
        "atualizado_em": row[8],
    }


def _validar_campos(descricao, valor):
    descricao = (descricao or "").strip()
    if not descricao:
        return None, "Descrição é obrigatória."
    if not isinstance(valor, int | float) or valor <= 0:
        return None, "Valor deve ser maior que zero."
    return descricao, None


def listar_contas_receber(conectar, status=None, page=None, per_page=None):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, status)
        rows = repo.buscar_paginado(cursor, status, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_conta_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def obter_conta_receber(conectar, conta_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, conta_id)
    finally:
        conn.close()
    return _conta_para_dict(row)


def criar_conta_receber(conectar, usuario_id, descricao, categoria="", valor=None, data_vencimento=None):
    """Retorna (conta_id, erro)."""
    descricao, erro = _validar_campos(descricao, valor)
    if erro:
        return None, erro
    categoria = (categoria or "").strip()

    conn = conectar()
    try:
        cursor = conn.cursor()
        conta_id = repo.inserir(cursor, descricao, categoria, valor, data_vencimento)
        registrar_log_auditoria(
            cursor,
            "conta_receber",
            conta_id,
            usuario_id,
            "create",
            depois={"descricao": descricao, "categoria": categoria, "valor": valor, "data_vencimento": data_vencimento},
        )
        conn.commit()
    finally:
        conn.close()

    return conta_id, None


def atualizar_conta_receber(conectar, usuario_id, conta_id, descricao, categoria="", valor=None, data_vencimento=None):
    """Retorna (sucesso, erro). Só permitido enquanto `status='pendente'`."""
    descricao, erro = _validar_campos(descricao, valor)
    if erro:
        return False, erro
    categoria = (categoria or "").strip()

    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, conta_id)
        if not antes:
            return False, "Conta a receber não encontrada."

        linhas = repo.atualizar(cursor, conta_id, descricao, categoria, valor, data_vencimento)
        if linhas == 0:
            conn.rollback()
            return False, "Conta a receber não pode ser editada (já recebida ou cancelada)."

        registrar_log_auditoria(
            cursor,
            "conta_receber",
            conta_id,
            usuario_id,
            "update",
            antes=_conta_para_dict(antes),
            depois={"descricao": descricao, "categoria": categoria, "valor": valor, "data_vencimento": data_vencimento},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def excluir_conta_receber(conectar, usuario_id, conta_id):
    """Retorna (sucesso, erro). Só permitido enquanto `status='pendente'`."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        antes = repo.buscar_por_id(cursor, conta_id)
        if not antes:
            return False, "Conta a receber não encontrada."

        linhas = repo.deletar(cursor, conta_id)
        if linhas == 0:
            conn.rollback()
            return False, "Conta a receber não pode ser excluída (já recebida ou cancelada)."

        registrar_log_auditoria(cursor, "conta_receber", conta_id, usuario_id, "delete", antes=_conta_para_dict(antes))
        conn.commit()
    finally:
        conn.close()

    return True, None


def receber_conta(conectar, usuario_id, conta_id):
    """Retorna (sucesso, erro). Baixa: `pendente -> recebido`, lança a
    entrada de caixa correspondente na mesma transação (compare-and-swap:
    só baixa se ainda estiver `pendente` no momento da escrita)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        conta = repo.buscar_por_id(cursor, conta_id)
        if not conta:
            return False, "Conta a receber não encontrada."
        if conta[5] != "pendente":
            return False, "Conta a receber não pode ser recebida (já recebida ou cancelada)."

        movimentacao_id = caixa_service.registrar_entrada_de_conta_receber(
            cursor, conta_id, conta[3], f"Recebimento: {conta[1]}", usuario_id
        )

        linhas = repo.marcar_como_recebido(cursor, conta_id, movimentacao_id)
        if linhas == 0:
            conn.rollback()
            return False, "Conta a receber não pode ser recebida (estado mudou)."

        registrar_log_auditoria(
            cursor,
            "conta_receber",
            conta_id,
            usuario_id,
            "status_change",
            antes={"status": "pendente"},
            depois={"status": "recebido", "movimentacao_caixa_id": movimentacao_id},
        )
        conn.commit()
    except Exception as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()

    return True, None


def cancelar_conta_receber(conectar, usuario_id, conta_id):
    """Retorna (sucesso, erro). Só permitido enquanto `status='pendente'` --
    sem efeito de caixa (nunca foi recebida)."""
    conn = conectar()
    try:
        cursor = conn.cursor()
        conta = repo.buscar_por_id(cursor, conta_id)
        if not conta:
            return False, "Conta a receber não encontrada."

        linhas = repo.cancelar(cursor, conta_id)
        if linhas == 0:
            conn.rollback()
            return False, "Conta a receber não pode ser cancelada (já recebida ou já cancelada)."

        registrar_log_auditoria(
            cursor,
            "conta_receber",
            conta_id,
            usuario_id,
            "status_change",
            antes={"status": "pendente"},
            depois={"status": "cancelado"},
        )
        conn.commit()
    finally:
        conn.close()

    return True, None


def resumir_pendencias(conectar, hoje):
    """Pendências da tela inicial (PLAN-pendencias-tela-inicial.md): contas pendentes vencidas e que
    vencem em `hoje` (`YYYY-MM-DD`), com quantidade e total de cada grupo."""
    conn = conectar()
    try:
        qtd_vencidas, total_vencidas, qtd_hoje, total_hoje = repo.resumir_pendentes_por_vencimento(conn.cursor(), hoje)
    finally:
        conn.close()
    return {
        "vencidas": {"quantidade": qtd_vencidas, "total": round(total_vencidas or 0.0, 2)},
        "vencem_hoje": {"quantidade": qtd_hoje, "total": round(total_hoje or 0.0, 2)},
    }
