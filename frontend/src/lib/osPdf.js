/**
 * Documentos da OS para o cliente (BR-095 a BR-098): comprovante de entrada e
 * comprovante de entrega, gerados no navegador com jsPDF.
 *
 * O conteúdo vem pronto de GET /api/ordens/<id>/documento — o backend já fecha
 * o que pode sair para o cliente (BR-097). Este módulo só desenha: cabeçalho da
 * loja, quadros com faixa de título cinza e tabelas, no formato de ordem de
 * serviço que a loja já entrega ao cliente.
 */
import { criarDocumentoPdf, formatarData } from "@/lib/pdfDocumento";

export { formatarData };

export const TITULOS_DOCUMENTO = {
  entrada: "Comprovante de Entrada",
  entrega: "Comprovante de Entrega",
};

function textoGarantia(garantia) {
  if (!garantia) return "Sem garantia registrada";
  if (!garantia.duracao_meses) return `${garantia.nome} (sem garantia)`;
  const meses = garantia.duracao_meses === 1 ? "1 mês" : `${garantia.duracao_meses} meses`;
  return `${garantia.nome} (${meses})`;
}

/**
 * Monta o PDF e devolve a instância jsPDF (sem salvar). `JsPDF` é injetado para
 * permitir teste sem depender do import dinâmico.
 */
export function montarPdfOs(JsPDF, documento, numero) {
  const { pdf, quadrosLadoALado, quadroDeTexto, tabela, termos, assinaturas, cabecalhoDocumento, linhaDeValor, rodape } =
    criarDocumentoPdf(JsPDF);
  const { loja, cliente, ordem } = documento;
  const entrega = documento.tipo === "entrega";
  const numeroOs = String(numero || ordem.id);

  cabecalhoDocumento(loja, "Ordem de serviço", numeroOs, TITULOS_DOCUMENTO[documento.tipo]);

  // ── Cliente e OS ────────────────────────────────────────────────────────────
  quadrosLadoALado([
    {
      titulo: "Dados do Cliente",
      fracao: 0.58,
      campos: [
        ["Nome", cliente.nome],
        ["CPF/CNPJ", cliente.cpf_cnpj],
        ["Telefone", cliente.telefone],
        ["E-mail", cliente.email],
      ],
    },
    {
      titulo: "Dados da OS",
      fracao: 0.42,
      campos: [
        ["Situação", ordem.status],
        ["Técnico", ordem.tecnico],
        ["Data de entrada", formatarData(ordem.data)],
        ["Data de finalização", entrega ? formatarData(ordem.data_finalizado) : ""],
      ],
    },
  ]);

  // ── Aparelho ────────────────────────────────────────────────────────────────
  tabela(
    [
      { titulo: "Aparelho", fracao: 0.32 },
      { titulo: "Modelo", fracao: 0.26 },
      { titulo: "IMEI", fracao: 0.24 },
      { titulo: "Cor", fracao: 0.18 },
    ],
    [[ordem.aparelho || "—", ordem.modelo, ordem.imei, ordem.cor]],
  );

  // ── Serviços ────────────────────────────────────────────────────────────────
  const servicos = ordem.servicos || [];
  if (entrega) {
    tabela(
      [
        { titulo: "Serviço realizado", fracao: 0.46 },
        { titulo: "Garantia", fracao: 0.34 },
        { titulo: "Válida até", fracao: 0.2, alinhar: "right" },
      ],
      servicos.length
        ? servicos.map((s) => [s.nome, textoGarantia(s.garantia), formatarData(s.garantia?.data_fim) || "—"])
        : [["—", "", ""]],
    );
  } else {
    tabela([{ titulo: "Serviço solicitado", fracao: 1 }], servicos.length ? servicos.map((s) => [s.nome]) : [["—"]]);
  }

  linhaDeValor(entrega ? "Valor total da OS:" : "Valor previsto da OS:", ordem.valor_total);

  // BR-102 -- relato e laudo vêm do backend só quando preenchidos; observação interna nunca vem.
  if (ordem.relato_cliente) quadroDeTexto("Relato do cliente", ordem.relato_cliente);
  if (ordem.laudo_tecnico) quadroDeTexto("Laudo técnico", ordem.laudo_tecnico);
  if (ordem.observacoes) quadroDeTexto("Observação", ordem.observacoes);

  if (documento.termos) termos(entrega ? "TERMOS DE GARANTIA" : "TERMOS DE ENTRADA", documento.termos);

  assinaturas(cliente.nome, loja.nome_fantasia, entrega ? "Cliente (retirada)" : "Cliente");

  rodape(`${loja.nome_fantasia} · OS nº ${numeroOs}`);

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
