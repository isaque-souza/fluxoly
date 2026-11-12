/**
 * Recibo de venda para o cliente (BR-103, docs/engineering/plans/PLAN-recibo-venda.md), gerado no
 * navegador com jsPDF e as mesmas primitivas dos documentos da OS (`pdfDocumento.js`).
 *
 * O conteúdo vem pronto de GET /api/vendas/<id>/recibo — o backend já fecha o que pode sair para o
 * cliente (nunca custo, lucro, comissão ou preço de tabela). Este módulo só desenha.
 */
import { toast } from "sonner";
import { vendas as vendasApi } from "@/api/client";
import { formatCurrency } from "@/lib/constants";
import { criarDocumentoPdf, formatarData } from "@/lib/pdfDocumento";

function textoGarantia(garantia) {
  if (!garantia) return "Sem garantia";
  if (!garantia.duracao_meses) return `${garantia.nome} (sem garantia)`;
  const meses = garantia.duracao_meses === 1 ? "1 mês" : `${garantia.duracao_meses} meses`;
  return `${garantia.nome} (${meses})`;
}

/** Monta o PDF e devolve a instância jsPDF (sem salvar). `JsPDF` injetado para teste. */
export function montarPdfRecibo(JsPDF, recibo) {
  const { pdf, quadrosLadoALado, quadroDeTexto, tabela, termos, assinaturas, cabecalhoDocumento, linhaDeValor, rodape } =
    criarDocumentoPdf(JsPDF);
  const { loja, cliente, venda } = recibo;
  const numero = String(venda.id);

  cabecalhoDocumento(loja, "Recibo de venda", numero, formatarData(venda.data));

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
      titulo: "Dados da Venda",
      fracao: 0.42,
      campos: [
        ["Data", formatarData(venda.data)],
        ["Vendedor", venda.vendedor],
        ["Pagamento", venda.forma_pagamento],
      ],
    },
  ]);

  const itens = venda.itens || [];
  tabela(
    [
      { titulo: "Produto", fracao: 0.34 },
      { titulo: "IMEI", fracao: 0.22 },
      { titulo: "Garantia", fracao: 0.2 },
      { titulo: "Válida até", fracao: 0.12 },
      { titulo: "Valor", fracao: 0.12, alinhar: "right" },
    ],
    itens.length
      ? itens.map((i) => [
        i.produto,
        i.imei || "—",
        textoGarantia(i.garantia),
        formatarData(i.garantia?.data_fim) || "—",
        formatCurrency(i.valor),
      ])
      : [["—", "", "", "", ""]],
  );

  linhaDeValor("Valor total da venda:", venda.valor_total);

  if (venda.observacoes) quadroDeTexto("Observação", venda.observacoes);
  if (recibo.termos) termos("TERMOS DE GARANTIA", recibo.termos);

  assinaturas(cliente.nome, loja.nome_fantasia);
  rodape(`${loja.nome_fantasia} · Venda nº ${numero}`);
  return pdf;
}

export function nomeArquivoRecibo(recibo) {
  return `venda-${recibo.venda.id}-recibo.pdf`;
}

/**
 * Busca o recibo e baixa o PDF. Erros viram toast; quem chama só passa o id. `irParaDadosLoja`
 * (opcional) vira ação do toast quando faltam os Dados da Loja.
 */
export async function imprimirReciboVenda(vendaId, irParaDadosLoja) {
  try {
    const res = await vendasApi.recibo(vendaId);
    if (!res?.ok) {
      const erro = res?.erro || "Não foi possível gerar o recibo";
      if (irParaDadosLoja && erro.includes("Dados da Loja")) {
        toast.error(erro, { action: { label: "Cadastrar", onClick: irParaDadosLoja } });
      } else {
        toast.error(erro);
      }
      return false;
    }
    const { jsPDF } = await import("jspdf");
    montarPdfRecibo(jsPDF, res.recibo).save(nomeArquivoRecibo(res.recibo));
    return true;
  } catch {
    toast.error("Não foi possível gerar o recibo");
    return false;
  }
}
