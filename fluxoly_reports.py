"""
Modulo de utilitarios para relatorios e PDF.
Centraliza funcoes de formatacao, geracao de PDF e agregacao de dados para relatorios.
"""

from flask import Response
from datetime import datetime
import unicodedata
from collections import defaultdict

from fluxoly_core import (
    STATUS_FINALIZADO,
    calcular_faturamento_os,
    calcular_lucro_os,
    normalizar_status_os,
)
from fluxoly_os import obter_reparos_por_os

MESES_PT = {
    "01": "Janeiro",
    "02": "Fevereiro",
    "03": "Marco",
    "04": "Abril",
    "05": "Maio",
    "06": "Junho",
    "07": "Julho",
    "08": "Agosto",
    "09": "Setembro",
    "10": "Outubro",
    "11": "Novembro",
    "12": "Dezembro",
}


def normalizar_texto_pdf(valor):
    """Normaliza texto removendo acentos e caracteres especiais para PDF."""
    texto = str(valor or "")
    texto = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto.replace("\r", " ").replace("\n", " ").strip()


def normalizar_chave_preco(valor):
    """Normaliza chave de preco para busca em tabelas."""
    texto = normalizar_texto_pdf(valor).lower()
    texto = texto.replace("iphone ", "")
    return "".join(ch for ch in texto if ch.isalnum())


def formatar_mes_referencia(chave_mes):
    """Formata chave de mes (YYYY-MM) para exibicao legivel."""
    if not chave_mes or len(chave_mes) != 7 or "-" not in chave_mes:
        return chave_mes or "-"
    ano, mes = chave_mes.split("-", 1)
    return f"{MESES_PT.get(mes, mes)}/{ano}"


def formatar_periodo_relatorio(data_inicio, data_fim):
    """Formata periodo de fechamento de relatorio."""
    if data_inicio and data_fim:
        return f"{data_inicio} a {data_fim}"
    if data_inicio:
        return f"A partir de {data_inicio}"
    if data_fim:
        return f"Ate {data_fim}"
    return "Todo o periodo"


def obter_data_referencia_os(data_finalizado, data_os):
    """Obtem data de referencia prioritariamente finalizacao, depois criacao."""
    return (data_finalizado or data_os or "").strip()


def texto_reparos_os(reparos_info, fallback="Servico nao informado"):
    """Monta texto de reparos realizados em uma OS."""
    nomes = reparos_info.get("nomes", []) if reparos_info else []
    if nomes:
        return ", ".join(nomes)
    return fallback


def linha_tabela(colunas):
    """Monta linha formatada de tabela para PDF."""
    return " | ".join(colunas)


def limitar_texto(valor, tamanho):
    """Limita texto a um tamanho maximo para exibicao em tabela."""
    texto = normalizar_texto_pdf(valor)
    if len(texto) <= tamanho:
        return texto.ljust(tamanho)
    if tamanho <= 3:
        return texto[:tamanho]
    return (texto[: tamanho - 3] + "...").ljust(tamanho)


def moeda_pdf(valor):
    """Formata valor em formato monetario R$."""
    return f"R$ {float(valor or 0):.2f}"


def montar_pdf_texto(titulo, subtitulo, linhas, nome_arquivo):
    """
    Gera PDF com texto simples atraves de stream PDF manual.
    Suporta multiplas paginas, fontes diferentes e paginacao.
    """
    largura = 595
    altura = 842
    margem_x = 40
    topo = 802
    rodape = 40
    leading = 14
    max_linhas = int((topo - rodape) / leading) - 2

    paginas = []
    pagina_atual = []

    def nova_pagina():
        nonlocal pagina_atual
        if pagina_atual:
            paginas.append(pagina_atual)
        pagina_atual = []

    data_geracao = datetime.now().strftime("%Y-%m-%d %H:%M")
    cabecalho_base = [
        ("bold", 14, normalizar_texto_pdf(titulo)),
        ("regular", 10, normalizar_texto_pdf(subtitulo)),
        ("regular", 9, f"Gerado em {data_geracao}"),
        ("regular", 9, ""),
    ]

    pagina_atual.extend(cabecalho_base)
    for linha in linhas:
        if len(pagina_atual) >= max_linhas:
            nova_pagina()
            pagina_atual.extend(cabecalho_base)
        pagina_atual.append(("mono", 9, normalizar_texto_pdf(linha)))
    if pagina_atual:
        paginas.append(pagina_atual)

    objetos = []

    def escapar_pdf(texto):
        return texto.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    def adicionar_objeto(conteudo):
        objetos.append(conteudo)
        return len(objetos)

    font_regular_id = adicionar_objeto(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font_bold_id = adicionar_objeto(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font_mono_id = adicionar_objeto(b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids = []
    content_ids = []

    for indice, pagina in enumerate(paginas, start=1):
        linhas_stream = ["BT"]
        y = topo
        for fonte, tamanho, texto in pagina:
            font_name = {"regular": "F1", "bold": "F2", "mono": "F3"}[fonte]
            linhas_stream.append(f"/{font_name} {tamanho} Tf")
            linhas_stream.append(f"1 0 0 1 {margem_x} {y} Tm")
            linhas_stream.append(f"({escapar_pdf(texto)}) Tj")
            y -= leading
        linhas_stream.append("/F1 9 Tf")
        linhas_stream.append(f"1 0 0 1 {margem_x} 24 Tm")
        linhas_stream.append(f"(Pagina {indice} de {len(paginas)}) Tj")
        linhas_stream.append("ET")
        stream = "\n".join(linhas_stream).encode("latin-1", "replace")
        content_id = adicionar_objeto(b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream")
        content_ids.append(content_id)
        page_ids.append(None)

    pages_id = adicionar_objeto(b"<< /Type /Pages /Kids [] /Count 0 >>")
    kids_refs = []
    for idx, content_id in enumerate(content_ids):
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {largura} {altura}] "
            f"/Resources << /Font << /F1 {font_regular_id} 0 R /F2 {font_bold_id} 0 R /F3 {font_mono_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        ).encode("ascii")
        page_ids[idx] = adicionar_objeto(page_obj)
        kids_refs.append(f"{page_ids[idx]} 0 R")

    objetos[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(kids_refs)}] /Count {len(page_ids)} >>".encode("ascii")
    )
    catalog_id = adicionar_objeto(f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("ascii"))

    pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for obj_id, conteudo in enumerate(objetos, start=1):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_id} 0 obj\n".encode("ascii"))
        pdf.extend(conteudo)
        pdf.extend(b"\nendobj\n")

    xref_pos = len(pdf)
    pdf.extend(f"xref\n0 {len(objetos) + 1}\n".encode("ascii"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    pdf.extend(
        (
            f"trailer\n<< /Size {len(objetos) + 1} /Root {catalog_id} 0 R >>\n"
            f"startxref\n{xref_pos}\n%%EOF"
        ).encode("ascii")
    )

    headers = {
        "Content-Type": "application/pdf",
        "Content-Disposition": f'attachment; filename="{nome_arquivo}"',
    }
    return Response(bytes(pdf), headers=headers)


def buscar_dados_relatorios(conectar):
    """Busca dados de OS finalizadas para montagem de relatorios."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            os.id,
            COALESCE(os.cliente, ''),
            COALESCE(os.tecnico, ''),
            COALESCE(os.tipo, ''),
            COALESCE(os.status, ''),
            COALESCE(os.valor_cobrado, 0),
            COALESCE(os.valor_descontado, 0),
            COALESCE(os.data, ''),
            COALESCE(os.data_finalizado, ''),
            COALESCE(os.modelo, '')
        FROM os
        ORDER BY COALESCE(os.data_finalizado, os.data, '') ASC, os.id ASC
        """
    )
    ordens = cursor.fetchall()
    reparos_por_os = obter_reparos_por_os(cursor)

    cursor.execute(
        """
        SELECT os_id, COALESCE(SUM(valor), 0)
        FROM os_pecas
        GROUP BY os_id
        """
    )
    custos = {row[0]: row[1] or 0 for row in cursor.fetchall()}
    conn.close()

    return ordens, custos, reparos_por_os


def agrupar_relatorio_tecnicos(data_inicio="", data_fim="", conectar=None):
    """Agrega dados de relatorio por tecnico e mes."""
    ordens, custos, reparos_por_os = buscar_dados_relatorios(conectar)
    meses = defaultdict(lambda: defaultdict(lambda: {
        "total_os": 0,
        "faturamento": 0.0,
        "gastos": 0.0,
        "lucro": 0.0,
        "servicos": defaultdict(int),
    }))

    for row in ordens:
        os_id, cliente, tecnico, tipo, status, valor_cobrado, valor_descontado, data_os, data_finalizado, modelo = row
        if normalizar_status_os(status) != STATUS_FINALIZADO:
            continue
        if not (tecnico or "").strip():
            tecnico = "Tecnico nao informado"

        data_ref = obter_data_referencia_os(data_finalizado, data_os)
        if not data_ref:
            continue
        if data_inicio and data_ref < data_inicio:
            continue
        if data_fim and data_ref > data_fim:
            continue

        chave_mes = data_ref[:7]
        custo = custos.get(os_id, 0)
        faturamento = calcular_faturamento_os(valor_cobrado, valor_descontado)
        lucro = calcular_lucro_os(tipo, valor_cobrado, valor_descontado, custo)
        servicos = reparos_por_os.get(os_id, {}).get("nomes", []) or [tipo or "Servico nao informado"]

        bucket = meses[chave_mes][tecnico]
        bucket["total_os"] += 1
        bucket["faturamento"] += faturamento
        bucket["gastos"] += custo
        bucket["lucro"] += lucro
        for servico in servicos:
            bucket["servicos"][servico] += 1

    return {mes: dict(sorted(tecnicos.items())) for mes, tecnicos in sorted(meses.items())}


def agrupar_relatorio_custos_operacionais(data_inicio="", data_fim="", conectar=None):
    """Agrega custos operacionais por mes e categoria."""
    conn = conectar()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            COALESCE(id, 0),
            COALESCE(descricao, ''),
            COALESCE(categoria, 'Outros'),
            COALESCE(valor, 0),
            COALESCE(data, ''),
            COALESCE(observacoes, '')
        FROM custos_operacionais
        ORDER BY COALESCE(data, '') ASC, id ASC
        """
    )
    rows = cursor.fetchall()
    conn.close()

    meses = defaultdict(lambda: {
        "total_itens": 0,
        "total_valor": 0.0,
        "categorias": defaultdict(float),
        "itens": [],
    })

    for custo_id, descricao, categoria, valor, data, observacoes in rows:
        if not data:
            continue
        if data_inicio and data < data_inicio:
            continue
        if data_fim and data > data_fim:
            continue

        chave_mes = data[:7]
        bucket = meses[chave_mes]
        bucket["total_itens"] += 1
        bucket["total_valor"] += float(valor or 0)
        bucket["categorias"][categoria or "Outros"] += float(valor or 0)
        bucket["itens"].append(
            {
                "id": custo_id,
                "descricao": descricao,
                "categoria": categoria or "Outros",
                "valor": round(float(valor or 0), 2),
                "data": data,
                "observacoes": observacoes,
            }
        )

    resultado = {}
    for chave_mes, resumo in sorted(meses.items()):
        categorias_ordenadas = dict(
            sorted(resumo["categorias"].items(), key=lambda item: (-item[1], item[0]))
        )
        resultado[chave_mes] = {
            "total_itens": resumo["total_itens"],
            "total_valor": round(resumo["total_valor"], 2),
            "categorias": {categoria: round(valor, 2) for categoria, valor in categorias_ordenadas.items()},
            "itens": resumo["itens"],
        }
    return resultado


def montar_linhas_relatorio_tecnicos(data_inicio="", data_fim="", conectar=None):
    """Monta linhas de relatorio formatadas por tecnico."""
    agrupado = agrupar_relatorio_tecnicos(data_inicio, data_fim, conectar)
    linhas = []

    if not agrupado:
        linhas.append("Nenhuma OS finalizada com tecnico encontrada para o periodo informado.")
        return linhas

    for chave_mes, tecnicos in agrupado.items():
        linhas.append(f"TECNICOS - {formatar_mes_referencia(chave_mes)}")
        linhas.append("=" * 92)
        for tecnico, resumo in tecnicos.items():
            linhas.append(normalizar_texto_pdf(tecnico).upper())
            linhas.append(
                linha_tabela(
                    [
                        limitar_texto(f"OS: {resumo['total_os']}", 14),
                        limitar_texto(f"Faturamento: {moeda_pdf(resumo['faturamento'])}", 24),
                        limitar_texto(f"Gastos: {moeda_pdf(resumo['gastos'])}", 20),
                        limitar_texto(f"Lucro: {moeda_pdf(resumo['lucro'])}", 20),
                    ]
                )
            )
            linhas.append(linha_tabela([limitar_texto("Servico", 56), limitar_texto("Quantidade", 12)]))
            for servico, quantidade in sorted(resumo["servicos"].items(), key=lambda item: (-item[1], item[0])):
                linhas.append(linha_tabela([limitar_texto(servico, 56), limitar_texto(str(quantidade), 12)]))
            linhas.append("-" * 92)
        linhas.append("")

    return linhas


def montar_linhas_relatorio_custos_operacionais(data_inicio="", data_fim="", conectar=None):
    """Monta linhas do relatorio de custos operacionais."""
    agrupado = agrupar_relatorio_custos_operacionais(data_inicio, data_fim, conectar)
    linhas = []
    total_geral_itens = 0
    total_geral_valor = 0.0

    if not agrupado:
        linhas.append("Nenhum custo operacional encontrado para o periodo informado.")
        return linhas

    for chave_mes, resumo in agrupado.items():
        total_geral_itens += resumo["total_itens"]
        total_geral_valor += resumo["total_valor"]

        linhas.append(f"CUSTOS OPERACIONAIS - {formatar_mes_referencia(chave_mes)}")
        linhas.append("-" * 92)
        ticket_medio = resumo["total_valor"] / resumo["total_itens"] if resumo["total_itens"] else 0
        linhas.append(
            linha_tabela(
                [
                    limitar_texto(f"Lancamentos: {resumo['total_itens']}", 24),
                    limitar_texto(f"Total: {moeda_pdf(resumo['total_valor'])}", 24),
                    limitar_texto(f"Media: {moeda_pdf(ticket_medio)}", 24),
                ]
            )
        )
        linhas.append("")
        linhas.append("Categorias do mes")
        linhas.append(linha_tabela([limitar_texto("Categoria", 56), limitar_texto("Valor", 18)]))
        for categoria, valor in resumo["categorias"].items():
            linhas.append(linha_tabela([limitar_texto(categoria, 56), limitar_texto(moeda_pdf(valor), 18)]))
        linhas.append("")
        linhas.append("Lancamentos do mes")
        linhas.append(
            linha_tabela(
                [
                    limitar_texto("Data", 12),
                    limitar_texto("Categoria", 22),
                    limitar_texto("Descricao", 34),
                    limitar_texto("Valor", 14),
                ]
            )
        )
        for item in resumo.get("itens", []):
            linhas.append(
                linha_tabela(
                    [
                        limitar_texto(item.get("data") or "-", 12),
                        limitar_texto(item.get("categoria") or "Outros", 22),
                        limitar_texto(item.get("descricao") or "Sem descricao", 34),
                        limitar_texto(moeda_pdf(item.get("valor")), 14),
                    ]
                )
            )
        linhas.append("")

    linhas.append("=" * 92)
    linhas.append("RESUMO GERAL DO PERIODO")
    linhas.append(
        linha_tabela(
            [
                limitar_texto(f"Lancamentos: {total_geral_itens}", 24),
                limitar_texto(f"Total: {moeda_pdf(total_geral_valor)}", 24),
            ]
        )
    )
    return linhas
