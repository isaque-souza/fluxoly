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

import re
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


def _custo_para_dict(valor_pago, custo_pecas):
    valor_pago = round(valor_pago or 0.0, 2)
    custo_pecas = round(custo_pecas or 0.0, 2)
    return {"valor_compra": valor_pago, "custo_pecas": custo_pecas, "custo_total": round(valor_pago + custo_pecas, 2)}


def obter_custo_aparelho(conectar, unidade_id):
    """BR-092 -- custo = valor pago na compra ativa + peças das OS internas (não canceladas).
    Calculado na hora, nunca gravado. `None` se o aparelho não veio de uma compra.
    A visibilidade (só admin/financeiro) é decidida no controller, não aqui."""
    conn = conectar()
    try:
        row = repo.buscar_custo_da_unidade(conn.cursor(), unidade_id)
    finally:
        conn.close()
    if not row:
        return None
    return _custo_para_dict(row[0], row[1])


def calcular_lucro(valor_venda, custo):
    """BR-092 -- lucro = valor da venda − custo do aparelho. `None` se não há custo (não veio de compra)."""
    if not custo or valor_venda is None:
        return None
    return round(valor_venda - custo["custo_total"], 2)


_MES_RE = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")


def obter_relatorio_mensal(conectar, mes):
    """BR-093 -- relatório de compra e revenda do mês (`AAAA-MM`). Retorna (relatorio, erro).

    - compras: aparelhos comprados no mês (compras ativas) e quanto foi pago;
    - pecas_os_internas: peças das OS internas do mês;
    - vendas: aparelhos comprados que foram vendidos no mês, com custo total e lucro de cada um
      (o custo inclui compra e peças de qualquer mês -- é o custo do aparelho, não do período);
    - estoque_atual: retrato de hoje dos aparelhos comprados ainda não vendidos.
    """
    m = _MES_RE.match(mes or "")
    if not m:
        return None, "Informe o mês no formato AAAA-MM."
    ano, mes_num = int(m.group(1)), int(m.group(2))
    inicio = f"{ano:04d}-{mes_num:02d}-01 00:00:00"
    prox_ano, prox_mes = (ano + 1, 1) if mes_num == 12 else (ano, mes_num + 1)
    fim = f"{prox_ano:04d}-{prox_mes:02d}-01 00:00:00"

    conn = conectar()
    try:
        cursor = conn.cursor()
        qtd_compras, total_pago = repo.resumir_compras_do_periodo(cursor, inicio, fim)
        pecas_mes = repo.somar_pecas_os_internas_do_periodo(cursor, inicio, fim)
        vendas_rows = repo.buscar_vendas_de_aparelhos_comprados(cursor, inicio, fim)
        estoque_rows = repo.buscar_aparelhos_comprados_em_estoque(cursor)
    finally:
        conn.close()

    itens_vendidos = []
    for venda_id, vendido_em, unidade_id, produto_nome, imei, valor_venda, valor_pago, custo_pecas in vendas_rows:
        custo = _custo_para_dict(valor_pago, custo_pecas)
        itens_vendidos.append(
            {
                "venda_id": venda_id,
                "vendido_em": vendido_em,
                "unidade_serializada_id": unidade_id,
                "produto_nome": produto_nome or "",
                "imei": imei,
                "valor_venda": round(valor_venda or 0.0, 2),
                **custo,
                "lucro": calcular_lucro(valor_venda or 0.0, custo),
            }
        )

    total_vendido = round(sum(i["valor_venda"] for i in itens_vendidos), 2)
    custo_vendidos = round(sum(i["custo_total"] for i in itens_vendidos), 2)
    em_reparo = sum(1 for r in estoque_rows if r[0] == "em_reparo")
    capital_parado = round(sum((r[1] or 0.0) + (r[2] or 0.0) for r in estoque_rows), 2)

    return {
        "mes": f"{ano:04d}-{mes_num:02d}",
        "compras": {"quantidade": qtd_compras, "total_pago": round(total_pago or 0.0, 2)},
        "pecas_os_internas": round(pecas_mes, 2),
        "total_investido": round((total_pago or 0.0) + pecas_mes, 2),
        "vendas": {
            "quantidade": len(itens_vendidos),
            "total_vendido": total_vendido,
            "custo_total": custo_vendidos,
            "lucro": round(total_vendido - custo_vendidos, 2),
            "itens": itens_vendidos,
        },
        "estoque_atual": {
            "quantidade": len(estoque_rows),
            "em_reparo": em_reparo,
            "disponiveis": len(estoque_rows) - em_reparo,
            "capital_parado": capital_parado,
        },
    }, None


def abrir_reparo_interno(cursor, unidade_id, usuario_id):
    """BR-090 -- chamada de dentro da criação/reabertura de uma OS interna (api_os.py), na
    mesma transação. Só aparelho com compra ativa pode ter OS interna. Retorna (imei, erro)."""
    if not unidade_id:
        return None, "Selecione o aparelho comprado que vai para o conserto."
    if not repo.existe_compra_ativa_da_unidade(cursor, unidade_id):
        return None, "Este aparelho não tem compra ativa registrada."
    return unidades_service.iniciar_reparo_interno(cursor, unidade_id, usuario_id)


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
