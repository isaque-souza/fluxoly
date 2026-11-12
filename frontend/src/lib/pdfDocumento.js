/**
 * Primitivas de desenho dos documentos para o cliente em PDF (jsPDF): cabeçalho da loja,
 * quadros com faixa de título cinza, tabelas, termos, assinaturas e rodapé. Extraído de
 * `osPdf.js` para ser reaproveitado por outros documentos. Só desenha — o conteúdo que pode
 * sair para o cliente é decidido no backend.
 */
import { formatCurrency } from "@/lib/constants";

const MARGEM = 12;
const LARGURA_A4 = 210;
const ALTURA_A4 = 297;
const LARGURA_UTIL = LARGURA_A4 - MARGEM * 2;
const LIMITE_INFERIOR = ALTURA_A4 - MARGEM - 6; // espaço do rodapé
const ESPACO_ENTRE_BLOCOS = 4;
const PADDING = 1.8;
const ALTURA_FAIXA = 6;
const LINHA_PADRAO = 4.3;

const COR_FAIXA = [233, 236, 239];
const COR_BORDA = [190, 194, 199];
const COR_TEXTO = [33, 37, 41];
const COR_SUAVE = [108, 117, 125];

export function formatarData(valor) {
  const texto = String(valor || "").trim();
  const m = texto.match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : texto;
}

/** Linha de termos que vira subtítulo: curta e toda em maiúsculas (ex.: "DA GARANTIA DO PRODUTO"). */
function ehTituloDeTermos(linha) {
  const texto = linha.trim();
  return texto.length > 0 && texto.length <= 70 && /[A-ZÀ-Ý]/.test(texto) && texto === texto.toLocaleUpperCase("pt-BR");
}

/** Cria a folha A4 e devolve as primitivas de desenho, que compartilham o cursor vertical. */
export function criarDocumentoPdf(JsPDF) {
  const pdf = new JsPDF({ unit: "mm", format: "a4" });
  let y = MARGEM;

  const fonte = (tamanho, negrito = false, cor = COR_TEXTO) => {
    pdf.setFont("helvetica", negrito ? "bold" : "normal");
    pdf.setFontSize(tamanho);
    pdf.setTextColor(...cor);
  };

  const novaPagina = () => {
    pdf.addPage();
    y = MARGEM;
  };

  const garantirEspaco = (altura) => {
    if (y + altura > LIMITE_INFERIOR) {
      novaPagina();
      return true;
    }
    return false;
  };

  const faixa = (x, largura, titulo, alinhar = "left") => {
    pdf.setFillColor(...COR_FAIXA);
    pdf.setDrawColor(...COR_BORDA);
    pdf.rect(x, y, largura, ALTURA_FAIXA, "FD");
    fonte(8.5, true);
    if (alinhar === "right") pdf.text(titulo, x + largura - PADDING, y + 4.2, { align: "right" });
    else pdf.text(titulo, x + PADDING, y + 4.2);
  };

  /** "Rótulo: valor" com rótulo em negrito, quebrando o valor na largura do quadro. */
  const linhasDeCampos = (campos, largura) => {
    fonte(8.5);
    const linhas = [];
    for (const [rotulo, valor] of campos) {
      if (!valor) continue;
      fonte(8.5, true);
      const prefixo = `${rotulo}: `;
      const larguraPrefixo = pdf.getTextWidth(prefixo);
      fonte(8.5);
      const partes = pdf.splitTextToSize(String(valor), largura - larguraPrefixo);
      linhas.push({ prefixo, larguraPrefixo, texto: partes[0] });
      for (const resto of partes.slice(1)) linhas.push({ prefixo: "", larguraPrefixo, texto: resto });
    }
    return linhas;
  };

  const desenharLinhasDeCampos = (linhas, x, topo) => {
    linhas.forEach((linha, i) => {
      const base = topo + PADDING + 3 + i * LINHA_PADRAO;
      if (linha.prefixo) {
        fonte(8.5, true);
        pdf.text(linha.prefixo, x + PADDING, base);
      }
      fonte(8.5);
      pdf.text(linha.texto, x + PADDING + linha.larguraPrefixo, base);
    });
  };

  /** Quadros lado a lado, cada um com faixa de título e campos; a altura é a do maior. */
  const quadrosLadoALado = (quadros) => {
    const vao = 3;
    const larguraTotal = LARGURA_UTIL - vao * (quadros.length - 1);
    const preparados = quadros.map((q) => {
      const largura = larguraTotal * q.fracao;
      return { ...q, largura, linhas: linhasDeCampos(q.campos, largura - PADDING * 2) };
    });
    const maiorQtd = Math.max(1, ...preparados.map((q) => q.linhas.length));
    const alturaCorpo = maiorQtd * LINHA_PADRAO + PADDING * 2;
    garantirEspaco(ALTURA_FAIXA + alturaCorpo);
    let x = MARGEM;
    for (const q of preparados) {
      faixa(x, q.largura, q.titulo);
      pdf.setDrawColor(...COR_BORDA);
      pdf.rect(x, y + ALTURA_FAIXA, q.largura, alturaCorpo);
      desenharLinhasDeCampos(q.linhas, x, y + ALTURA_FAIXA);
      x += q.largura + vao;
    }
    y += ALTURA_FAIXA + alturaCorpo + ESPACO_ENTRE_BLOCOS;
  };

  /** Quadro de largura total com texto livre; continua na página seguinte se for longo. */
  const quadroDeTexto = (titulo, texto) => {
    fonte(8.5);
    const linhas = pdf.splitTextToSize(String(texto), LARGURA_UTIL - PADDING * 2);
    garantirEspaco(ALTURA_FAIXA + LINHA_PADRAO + PADDING * 2);
    faixa(MARGEM, LARGURA_UTIL, titulo);
    y += ALTURA_FAIXA;
    let inicio = y;
    y += PADDING;
    const fecharBorda = () => {
      pdf.setDrawColor(...COR_BORDA);
      pdf.rect(MARGEM, inicio, LARGURA_UTIL, y + PADDING - inicio);
    };
    for (const linha of linhas) {
      if (y + LINHA_PADRAO + PADDING > LIMITE_INFERIOR) {
        fecharBorda();
        novaPagina();
        faixa(MARGEM, LARGURA_UTIL, `${titulo} (continuação)`);
        y += ALTURA_FAIXA;
        inicio = y;
        y += PADDING;
      }
      fonte(8.5);
      pdf.text(linha, MARGEM + PADDING, y + 3);
      y += LINHA_PADRAO;
    }
    fecharBorda();
    y += PADDING + ESPACO_ENTRE_BLOCOS;
  };

  /** Tabela com cabeçalho cinza; repete o cabeçalho quando quebra de página. */
  const tabela = (colunas, linhas) => {
    const larguras = colunas.map((c) => LARGURA_UTIL * c.fracao);
    const xs = larguras.reduce((acc, _l, i) => [...acc, i === 0 ? MARGEM : acc[i - 1] + larguras[i - 1]], []);

    const cabecalho = () => {
      colunas.forEach((c, i) => faixa(xs[i], larguras[i], c.titulo, c.alinhar));
      y += ALTURA_FAIXA;
    };

    garantirEspaco(ALTURA_FAIXA + LINHA_PADRAO + PADDING * 2);
    cabecalho();
    for (const linha of linhas) {
      fonte(8.5);
      const celulas = linha.map((valor, i) => pdf.splitTextToSize(String(valor ?? ""), larguras[i] - PADDING * 2));
      const altura = Math.max(1, ...celulas.map((c) => c.length)) * LINHA_PADRAO + PADDING * 2;
      if (garantirEspaco(altura)) cabecalho();
      celulas.forEach((texto, i) => {
        pdf.setDrawColor(...COR_BORDA);
        pdf.rect(xs[i], y, larguras[i], altura);
        fonte(8.5);
        texto.forEach((parte, j) => {
          const base = y + PADDING + 3 + j * LINHA_PADRAO;
          if (colunas[i].alinhar === "right") pdf.text(parte, xs[i] + larguras[i] - PADDING, base, { align: "right" });
          else pdf.text(parte, xs[i] + PADDING, base);
        });
      });
      y += altura;
    }
    y += ESPACO_ENTRE_BLOCOS;
  };

  const termos = (titulo, texto) => {
    garantirEspaco(14);
    pdf.setDrawColor(...COR_TEXTO);
    pdf.setLineWidth(0.4);
    pdf.line(MARGEM, y, LARGURA_A4 - MARGEM, y);
    pdf.setLineWidth(0.2);
    y += 6;
    fonte(11, true);
    pdf.text(titulo, LARGURA_A4 / 2, y, { align: "center" });
    y += 5;

    for (const paragrafo of String(texto).split(/\r?\n/)) {
      if (!paragrafo.trim()) {
        y += 2;
        continue;
      }
      if (ehTituloDeTermos(paragrafo)) {
        garantirEspaco(10);
        y += 2;
        fonte(10, true);
        pdf.text(paragrafo.trim(), LARGURA_A4 / 2, y, { align: "center" });
        y += 5;
        continue;
      }
      // "Cláusula 1ª:" (ou qualquer "Rótulo:" curto no começo) sai em negrito.
      const m = paragrafo.match(/^(\s*[^:]{1,25}:)\s*(.*)$/);
      const prefixo = m && /cl[áa]usula|par[áa]grafo|§/i.test(m[1]) ? `${m[1].trim()} ` : "";
      const resto = prefixo ? m[2] : paragrafo.trim();
      fonte(8, true);
      const larguraPrefixo = prefixo ? pdf.getTextWidth(prefixo) : 0;
      fonte(8);
      const primeira = pdf.splitTextToSize(resto, LARGURA_UTIL - larguraPrefixo);
      const linhaInicial = primeira[0] || "";
      const demais = pdf.splitTextToSize(resto.slice(linhaInicial.length).trim(), LARGURA_UTIL);
      garantirEspaco(LINHA_PADRAO);
      if (prefixo) {
        fonte(8, true);
        pdf.text(prefixo, MARGEM, y);
      }
      fonte(8);
      pdf.text(linhaInicial, MARGEM + larguraPrefixo, y);
      y += 3.8;
      for (const linha of demais) {
        if (!linha) continue;
        garantirEspaco(3.8);
        pdf.text(linha, MARGEM, y);
        y += 3.8;
      }
    }
    y += ESPACO_ENTRE_BLOCOS;
  };

  const assinaturas = (nomeCliente, nomeLoja, rotuloCliente = "Cliente") => {
    garantirEspaco(26);
    y += 18;
    const largura = (LARGURA_UTIL - 14) / 2;
    const xCliente = MARGEM;
    const xLoja = LARGURA_A4 - MARGEM - largura;
    pdf.setDrawColor(...COR_TEXTO);
    pdf.setLineWidth(0.4);
    pdf.line(xCliente, y, xCliente + largura, y);
    pdf.line(xLoja, y, xLoja + largura, y);
    pdf.setLineWidth(0.2);
    fonte(8.5, true);
    pdf.text(nomeCliente || "Cliente", xCliente + largura / 2, y + 4.5, { align: "center" });
    pdf.text(nomeLoja, xLoja + largura / 2, y + 4.5, { align: "center" });
    fonte(7.5, false, COR_SUAVE);
    pdf.text(rotuloCliente, xCliente + largura / 2, y + 8.5, { align: "center" });
    pdf.text("Loja", xLoja + largura / 2, y + 8.5, { align: "center" });
    y += 12;
  };

  /** Cabeçalho: nome da loja | dados da loja | título, número e subtítulo. */
  const cabecalhoDocumento = (loja, titulo, numero, subtitulo) => {
    const larguraLateral = 52;
    const centro = LARGURA_A4 / 2;
    fonte(15, true);
    const nomeLinhas = pdf.splitTextToSize(loja.nome_fantasia, larguraLateral);
    nomeLinhas.forEach((linha, i) => pdf.text(linha, MARGEM, y + 6 + i * 6));

    const linhasLoja = [
      loja.razao_social && { texto: loja.razao_social, negrito: true },
      loja.endereco && { texto: loja.endereco },
      loja.cnpj && { texto: `CNPJ: ${loja.cnpj}` },
      [loja.telefone && `Telefone: ${loja.telefone}`, loja.email].filter(Boolean).join(" · ") && {
        texto: [loja.telefone && `Telefone: ${loja.telefone}`, loja.email].filter(Boolean).join(" · "),
      },
    ].filter(Boolean);
    let yLoja = y + 3;
    for (const item of linhasLoja) {
      fonte(8, Boolean(item.negrito));
      for (const parte of pdf.splitTextToSize(item.texto, LARGURA_UTIL - larguraLateral * 2)) {
        pdf.text(parte, centro, yLoja, { align: "center" });
        yLoja += 3.8;
      }
    }

    fonte(13, true);
    pdf.text(titulo, LARGURA_A4 - MARGEM, y + 5, { align: "right" });
    fonte(11, true);
    pdf.text(`Nº ${numero}`, LARGURA_A4 - MARGEM, y + 10.5, { align: "right" });
    fonte(8, false, COR_SUAVE);
    pdf.text(subtitulo, LARGURA_A4 - MARGEM, y + 15, { align: "right" });

    y = Math.max(y + 18, yLoja + 1, y + 6 + nomeLinhas.length * 6);
    pdf.setDrawColor(...COR_TEXTO);
    pdf.setLineWidth(0.4);
    pdf.line(MARGEM, y, LARGURA_A4 - MARGEM, y);
    pdf.setLineWidth(0.2);
    y += 4;
  };

  /** Linha de total com régua embaixo. */
  const linhaDeValor = (rotulo, valor) => {
    garantirEspaco(10);
    fonte(10, true);
    pdf.text(rotulo, MARGEM, y + 3);
    pdf.text(formatCurrency(valor), LARGURA_A4 - MARGEM, y + 3, { align: "right" });
    y += 5;
    pdf.setDrawColor(...COR_TEXTO);
    pdf.setLineWidth(0.4);
    pdf.line(MARGEM, y, LARGURA_A4 - MARGEM, y);
    pdf.setLineWidth(0.2);
    y += ESPACO_ENTRE_BLOCOS + 1;
  };

  /** Rodapé em todas as páginas: texto à esquerda e paginação à direita. */
  const rodape = (textoEsquerda) => {
    const totalPaginas = pdf.getNumberOfPages();
    for (let pagina = 1; pagina <= totalPaginas; pagina += 1) {
      pdf.setPage(pagina);
      fonte(7.5, false, COR_SUAVE);
      pdf.text(textoEsquerda, MARGEM, ALTURA_A4 - MARGEM + 2);
      pdf.text(`Página ${pagina} de ${totalPaginas}`, LARGURA_A4 - MARGEM, ALTURA_A4 - MARGEM + 2, { align: "right" });
    }
  };

  return { pdf, fonte, quadrosLadoALado, quadroDeTexto, tabela, termos, assinaturas, cabecalhoDocumento, linhaDeValor, rodape };
}
