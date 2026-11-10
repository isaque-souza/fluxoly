/**
 * Documentos da OS para o cliente (BR-095 a BR-098): comprovante de entrada e
 * comprovante de entrega, gerados no navegador com jsPDF.
 *
 * O conteúdo vem pronto de GET /api/ordens/<id>/documento — o backend já fecha
 * o que pode sair para o cliente (BR-097). Este módulo só desenha.
 */
import { formatCurrency } from "@/lib/constants";

const MARGEM = 15;
const LARGURA_A4 = 210;
const ALTURA_A4 = 297;
const LARGURA_UTIL = LARGURA_A4 - MARGEM * 2;
const ALTURA_LINHA = 5;

export const TITULOS_DOCUMENTO = {
  entrada: "Comprovante de Entrada",
  entrega: "Comprovante de Entrega",
};

export function formatarData(valor) {
  const texto = String(valor || "").trim();
  const m = texto.match(/^(\d{4})-(\d{2})-(\d{2})/);
  return m ? `${m[3]}/${m[2]}/${m[1]}` : texto;
}

function textoGarantia(garantia) {
  if (!garantia) return "Sem garantia registrada";
  if (!garantia.duracao_meses) return `${garantia.nome} (sem garantia)`;
  const meses = garantia.duracao_meses === 1 ? "1 mês" : `${garantia.duracao_meses} meses`;
  const fim = garantia.data_fim ? ` — válida até ${formatarData(garantia.data_fim)}` : "";
  return `${garantia.nome} (${meses})${fim}`;
}

/**
 * Monta o PDF e devolve a instância jsPDF (sem salvar). `JsPDF` é injetado para
 * permitir teste sem depender do import dinâmico.
 */
export function montarPdfOs(JsPDF, documento, numero) {
  const pdf = new JsPDF({ unit: "mm", format: "a4" });
  const { loja, cliente, ordem } = documento;
  const entrega = documento.tipo === "entrega";
  let y = MARGEM;

  const garantirEspaco = (altura) => {
    if (y + altura > ALTURA_A4 - MARGEM) {
      pdf.addPage();
      y = MARGEM;
    }
  };

  const escrever = (texto, { tamanho = 10, negrito = false, recuo = 0, alinhar } = {}) => {
    pdf.setFont("helvetica", negrito ? "bold" : "normal");
    pdf.setFontSize(tamanho);
    const linhas = pdf.splitTextToSize(String(texto ?? ""), LARGURA_UTIL - recuo);
    for (const linha of linhas) {
      garantirEspaco(ALTURA_LINHA);
      if (alinhar === "direita") pdf.text(linha, LARGURA_A4 - MARGEM, y, { align: "right" });
      else pdf.text(linha, MARGEM + recuo, y);
      y += tamanho >= 12 ? ALTURA_LINHA + 1 : ALTURA_LINHA;
    }
  };

  const campo = (rotulo, valor) => {
    if (!valor) return;
    escrever(`${rotulo}: ${valor}`);
  };

  const separador = () => {
    garantirEspaco(4);
    pdf.setDrawColor(180);
    pdf.line(MARGEM, y - 2, LARGURA_A4 - MARGEM, y - 2);
    y += 3;
  };

  const secao = (titulo) => {
    y += 2;
    escrever(titulo, { tamanho: 11, negrito: true });
  };

  // Cabeçalho da loja
  escrever(loja.nome_fantasia, { tamanho: 16, negrito: true });
  const identificacao = [loja.razao_social, loja.cnpj && `CNPJ ${loja.cnpj}`].filter(Boolean).join(" — ");
  if (identificacao) escrever(identificacao, { tamanho: 9 });
  if (loja.endereco) escrever(loja.endereco, { tamanho: 9 });
  const contato = [loja.telefone, loja.email].filter(Boolean).join(" — ");
  if (contato) escrever(contato, { tamanho: 9 });
  y += 2;
  separador();

  // Título
  escrever(`${TITULOS_DOCUMENTO[documento.tipo]} — OS nº ${numero || ordem.id}`, { tamanho: 13, negrito: true });
  campo("Data de entrada", formatarData(ordem.data));
  if (entrega) campo("Data de conclusão", formatarData(ordem.data_finalizado));
  campo("Técnico responsável", ordem.tecnico);

  secao("Cliente");
  campo("Nome", cliente.nome);
  campo("Telefone", cliente.telefone);
  campo("CPF/CNPJ", cliente.cpf_cnpj);

  secao("Aparelho");
  campo("Aparelho", ordem.aparelho);
  campo("Modelo", ordem.modelo);
  campo("Cor", ordem.cor);
  campo("IMEI", ordem.imei);

  secao(entrega ? "Serviços realizados e garantia" : "Serviços solicitados");
  if (!ordem.servicos?.length) escrever("—", { recuo: 3 });
  for (const servico of ordem.servicos || []) {
    escrever(`• ${servico.nome}`, { recuo: 3 });
    if (entrega) escrever(`Garantia: ${textoGarantia(servico.garantia)}`, { recuo: 7, tamanho: 9 });
  }

  if (ordem.observacoes) {
    secao("Observações");
    escrever(ordem.observacoes);
  }

  y += 2;
  escrever(`${entrega ? "Valor total" : "Valor previsto"}: ${formatCurrency(ordem.valor_total)}`, {
    tamanho: 12,
    negrito: true,
    alinhar: "direita",
  });

  if (documento.termos) {
    secao(entrega ? "Termos de garantia" : "Termos de entrada");
    escrever(documento.termos, { tamanho: 9 });
  }

  // Assinaturas
  garantirEspaco(30);
  y += 20;
  const larguraAssinatura = (LARGURA_UTIL - 20) / 2;
  pdf.setDrawColor(0);
  pdf.line(MARGEM, y, MARGEM + larguraAssinatura, y);
  pdf.line(LARGURA_A4 - MARGEM - larguraAssinatura, y, LARGURA_A4 - MARGEM, y);
  pdf.setFont("helvetica", "normal");
  pdf.setFontSize(9);
  pdf.text(entrega ? "Cliente (retirada)" : "Cliente", MARGEM, y + 5);
  pdf.text(loja.nome_fantasia, LARGURA_A4 - MARGEM - larguraAssinatura, y + 5);

  return pdf;
}

export function nomeArquivoPdfOs(documento, numero) {
  return `os-${numero || documento.ordem.id}-${documento.tipo}.pdf`;
}

/** Carrega o jsPDF sob demanda (fora do bundle inicial) e baixa o PDF. */
export async function baixarPdfOs(documento, numero) {
  const { jsPDF } = await import("jspdf");
  const pdf = montarPdfOs(jsPDF, documento, numero);
  pdf.save(nomeArquivoPdfOs(documento, numero));
}
