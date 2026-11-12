import { describe, it, expect, vi, beforeEach } from "vitest";
import { jsPDF } from "jspdf";

const mockRecibo = vi.fn();
const mockToastError = vi.fn();
vi.mock("@/api/client", () => ({ vendas: { recibo: (...args) => mockRecibo(...args) } }));
vi.mock("sonner", () => ({ toast: { error: (...args) => mockToastError(...args) } }));

import { montarPdfRecibo, nomeArquivoRecibo, imprimirReciboVenda } from "@/lib/vendaPdf";

const recibo = {
  loja: { nome_fantasia: "Loja Teste", razao_social: "", cnpj: "", telefone: "", email: "", endereco: "" },
  termos: "Garantia nao cobre mau uso.",
  cliente: { nome: "Carla Lima", telefone: "(11) 97777-6666", email: "", cpf_cnpj: "" },
  venda: {
    id: 40,
    data: "2026-11-11 14:00:00",
    vendedor: "Bia",
    forma_pagamento: "Pix",
    valor_total: 4200,
    observacoes: "",
    itens: [
      { produto: "iPhone 13 128GB", imei: "356000000000040", valor: 4200, garantia: { nome: "Garantia Loja", duracao_meses: 3, data_fim: "2027-02-11" } },
    ],
  },
};

const conteudo = (pdf) => pdf.output();

describe("vendaPdf (BR-103)", () => {
  beforeEach(() => {
    mockRecibo.mockReset();
    mockToastError.mockReset();
  });

  it("desenha cliente, item com IMEI e garantia, total e termos", () => {
    const texto = conteudo(montarPdfRecibo(jsPDF, recibo));
    expect(texto).toContain("Recibo de venda");
    expect(texto).toContain("Carla Lima");
    expect(texto).toContain("356000000000040");
    expect(texto).toContain("Garantia Loja");
    expect(texto).toContain("11/02/2027");
    expect(texto).toContain("Garantia nao cobre mau uso.");
    expect(texto).not.toContain("E-mail:");
  });

  it("nomeia o arquivo pelo número da venda", () => {
    expect(nomeArquivoRecibo(recibo)).toBe("venda-40-recibo.pdf");
  });

  it("erro do backend vira toast, com atalho para Dados da Loja quando faltam", async () => {
    mockRecibo.mockResolvedValue({ ok: false, erro: "Cadastre os Dados da Loja antes de gerar documentos." });
    const irParaDadosLoja = vi.fn();

    expect(await imprimirReciboVenda(40, irParaDadosLoja)).toBe(false);
    expect(mockToastError).toHaveBeenCalledWith(
      "Cadastre os Dados da Loja antes de gerar documentos.",
      expect.objectContaining({ action: expect.objectContaining({ label: "Cadastrar" }) }),
    );
  });

  it("venda cancelada: toast simples", async () => {
    mockRecibo.mockResolvedValue({ ok: false, erro: "Venda cancelada não gera recibo." });
    expect(await imprimirReciboVenda(41)).toBe(false);
    expect(mockToastError).toHaveBeenCalledWith("Venda cancelada não gera recibo.");
  });
});
