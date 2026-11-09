"""
fluxoly_compras_aparelhos_service.py

Regra de negócio pura do domínio Compra de Aparelhos (BR-083 a BR-089,
docs/engineering/plans/PLAN-compra-aparelhos.md) -- não conhece Flask,
`request` nem `jsonify` (ENGINEERING_GUIDE.md §3.1).

Registrar uma compra cria, numa única transação (um cursor, um commit): a
linha em `compras_aparelhos`, a unidade serializada do aparelho (BR-084, via
`fluxoly_unidades_serializadas_service.criar_unidade_de_compra`) e a saída de
caixa (BR-086, via `fluxoly_caixa_service.registrar_saida_de_compra_aparelho`).
Cancelar faz o caminho inverso na mesma transação (BR-087).

Depende de: `fluxoly_compras_aparelhos_repository.py` (SQL),
`fluxoly_unidades_serializadas_service.py`, `fluxoly_caixa_service.py`,
`fluxoly_clientes_service.py`, `fluxoly_vendas_service.py` (leitura),
`fluxoly_audit.py`.
"""

import sqlite3

import fluxoly_caixa_service as caixa_service
import fluxoly_clientes_service as clientes_service
import fluxoly_compras_aparelhos_repository as repo
import fluxoly_unidades_serializadas_service as unidades_service
import fluxoly_vendas_service as vendas_service
from fluxoly_audit import registrar_log_auditoria

PAGINA_PADRAO = 1
POR_PAGINA_PADRAO = 20

ORIGENS_VALIDAS = {"marketplace", "troca", "outro"}
FORMAS_PAGAMENTO_VALIDAS = {"pix", "dinheiro", "transferencia", "cartao", "abatido_na_venda"}
STATUS_VALIDOS = {"ativa", "cancelada"}

TAMANHO_MAXIMO_TEXTO = 500
TAMANHO_MAXIMO_CURTO = 120


class _CompraConflitoError(Exception):
    """Falha de regra no meio da transação -- força rollback de tudo."""


def _compra_para_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "unidade_serializada_id": row[1],
        "produto_id": row[2],
        "origem": row[3],
        "cliente_id": row[4],
        "venda_id": row[5],
        "vendedor_nome": row[6] or "",
        "vendedor_telefone": row[7] or "",
        "valor_pago": row[8],
        "forma_pagamento": row[9],
        "estado": row[10] or "",
        "defeito": row[11] or "",
        "status": row[12],
        "motivo_cancelamento": row[13] or "",
        "cancelado_por": row[14],
        "cancelado_em": row[15],
        "usuario_id": row[16],
        "criado_em": row[17],
        "imei": row[18] or "",
        "unidade_status": row[19],
        "produto_label": row[20] or "",
        "produto_cor": row[21] or "",
        "produto_capacidade": row[22] or "",
        "cliente_nome": row[23] or "",
        "usuario_nome": row[24] or "",
    }


def _texto(valor, limite):
    return (valor or "").strip()[:limite] if isinstance(valor, str) or valor is None else None


def registrar_compra(
    conectar,
    usuario_id,
    produto_id,
    imei,
    origem,
    valor_pago,
    forma_pagamento,
    estado,
    defeito="",
    cliente_id=None,
    venda_id=None,
    vendedor_nome="",
    vendedor_telefone="",
):
    """Retorna (compra_id, erro). `erro` é None em caso de sucesso."""
    origem = (origem or "").strip().lower()
    forma_pagamento = (forma_pagamento or "").strip().lower()
    estado = _texto(estado, TAMANHO_MAXIMO_TEXTO)
    defeito = _texto(defeito, TAMANHO_MAXIMO_TEXTO)
    vendedor_nome = _texto(vendedor_nome, TAMANHO_MAXIMO_CURTO)
    vendedor_telefone = _texto(vendedor_telefone, TAMANHO_MAXIMO_CURTO)
    if None in (estado, defeito, vendedor_nome, vendedor_telefone):
        return None, "Campos de texto inválidos."

    # BR-083
    if not produto_id:
        return None, "Selecione o modelo do aparelho."
    if not (imei or "").strip():
        return None, "IMEI é obrigatório."
    if origem not in ORIGENS_VALIDAS:
        return None, "Origem inválida."
    if not isinstance(valor_pago, int | float) or valor_pago <= 0:
        return None, "Valor pago deve ser maior que zero."
    if forma_pagamento not in FORMAS_PAGAMENTO_VALIDAS:
        return None, "Forma de pagamento inválida."
    if not estado:
        return None, "Informe o estado do aparelho."

    # BR-085
    if origem == "troca":
        if not cliente_id:
            return None, "Na troca, informe o cliente que entregou o aparelho."
        if not clientes_service.obter_cliente(conectar, cliente_id):
            return None, "Cliente não encontrado."
        if venda_id:
            venda, _itens = vendas_service.obter_venda_com_itens(conectar, venda_id)
            if not venda:
                return None, "Venda não encontrada."
            if venda["status"] != "concluida":
                return None, "A venda informada não está concluída."
            if venda["cliente_id"] != cliente_id:
                return None, "A venda informada é de outro cliente."
    else:
        if forma_pagamento == "abatido_na_venda":
            return None, "'Abatido na venda' só vale para compra por troca."
        if venda_id:
            return None, "Só a compra por troca pode ser ligada a uma venda."
        cliente_id = None
        venda_id = None

    valor_pago = round(float(valor_pago), 2)

    conn = conectar()
    try:
        cursor = conn.cursor()
        unidade_id, erro = unidades_service.criar_unidade_de_compra(
            cursor, usuario_id, produto_id, imei, com_defeito=bool(defeito)
        )
        if erro:
            raise _CompraConflitoError(erro)

        compra_id = repo.inserir(
            cursor,
            unidade_id,
            produto_id,
            origem,
            cliente_id,
            venda_id,
            vendedor_nome,
            vendedor_telefone,
            valor_pago,
            forma_pagamento,
            estado,
            defeito,
            usuario_id,
        )
        registrar_log_auditoria(
            cursor,
            "compra_aparelho",
            compra_id,
            usuario_id,
            "create",
            depois={
                "unidade_serializada_id": unidade_id,
                "produto_id": produto_id,
                "origem": origem,
                "cliente_id": cliente_id,
                "venda_id": venda_id,
                "valor_pago": valor_pago,
                "forma_pagamento": forma_pagamento,
            },
        )
        # BR-086 -- saída de caixa na mesma transação.
        caixa_service.registrar_saida_de_compra_aparelho(cursor, compra_id, valor_pago, usuario_id)
        conn.commit()
    except _CompraConflitoError as exc:
        conn.rollback()
        return None, str(exc)
    except sqlite3.IntegrityError:
        conn.rollback()
        return None, "Não foi possível registrar a compra (conflito de dados)."
    finally:
        conn.close()

    return compra_id, None


def obter_compra(conectar, compra_id):
    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, compra_id)
    finally:
        conn.close()
    return _compra_para_dict(row)


def listar_compras(
    conectar, origem=None, status=None, data_inicio=None, data_fim=None, termo="", page=None, per_page=None
):
    page = page or PAGINA_PADRAO
    per_page = per_page or POR_PAGINA_PADRAO
    offset = (max(1, page) - 1) * per_page
    origem = origem if origem in ORIGENS_VALIDAS else None
    status = status if status in STATUS_VALIDOS else None

    conn = conectar()
    try:
        cursor = conn.cursor()
        total = repo.contar(cursor, origem, status, data_inicio, data_fim, termo)
        rows = repo.buscar_paginado(cursor, origem, status, data_inicio, data_fim, termo, per_page, offset)
    finally:
        conn.close()

    return {
        "items": [_compra_para_dict(r) for r in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


def cancelar_compra(conectar, compra_id, usuario_id, motivo):
    """BR-087 -- retorna (sucesso, erro). Só cancela compra ativa cujo aparelho ainda não
    foi vendido; estorna a saída de caixa e devolve a unidade (`devolvido`)."""
    motivo = (motivo or "").strip()[:TAMANHO_MAXIMO_TEXTO]
    if not motivo:
        return False, "Informe o motivo do cancelamento."

    conn = conectar()
    try:
        cursor = conn.cursor()
        row = repo.buscar_por_id(cursor, compra_id)
        if not row:
            return False, "Compra não encontrada."
        compra = _compra_para_dict(row)
        if compra["status"] != "ativa":
            return False, "Compra já cancelada."

        if repo.cancelar(cursor, compra_id, motivo, usuario_id) == 0:
            raise _CompraConflitoError("Compra já cancelada.")

        sucesso, erro = unidades_service.devolver_unidade_de_compra(
            cursor, compra["unidade_serializada_id"], usuario_id
        )
        if not sucesso:
            raise _CompraConflitoError(erro)

        caixa_service.estornar_saida_de_compra_aparelho(cursor, compra_id, usuario_id)
        registrar_log_auditoria(
            cursor,
            "compra_aparelho",
            compra_id,
            usuario_id,
            "cancelamento",
            antes={"status": "ativa"},
            depois={"status": "cancelada", "motivo": motivo},
        )
        conn.commit()
    except _CompraConflitoError as exc:
        conn.rollback()
        return False, str(exc)
    finally:
        conn.close()

    return True, None
