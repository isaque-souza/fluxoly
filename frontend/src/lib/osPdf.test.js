import { describe, it, expect } from "vitest";
import { jsPDF } from "jspdf";
import { montarPdfOs, formatarData, nomeArquivoPdfOs } from "@/lib/osPdf";

const LOJA = {
  nome_fantasia: "Loja Teste",
  razao_social: "Loja Teste Ltda",
  cnpj: "12.345.678/0001-90",
  telefone: "(11) 4000-0000",
  email: "contato@loja.teste",
  endereco: "Rua A, 100",
};

function documento(tipo, ordemExtra = {}) {
  return {
    tipo,
    loja: LOJA,
    termos: tipo === "entrega" ? "Garantia nao cobre mau uso." : "Loja nao se responsabiliza por dados.",
    cliente: { nome: "Maria Souza", telefone: "(11) 98888-7777", cpf_cnpj: "" },
    ordem: {
      id: 42,
      data: "2026-11-01",
      data_finalizado: tipo === "entrega" ? "2026-11-05 10:00:00" : "",
      status: tipo === "entrega" ? "Finalizado" : "Em andamento",
      aparelho: "iPhone 13",
      modelo: "iPhone 13",
      cor: "Azul",
      imei: "356789012345678",
      tecnico: "ISAQUE SOUZA",
      observacoes: "Tela trincada",
      valor_total: 350,
      servicos: [
        tipo === "entrega"
          ? { nome: "Troca de tela", garantia: { nome: "Garantia Padrao", duracao_meses: 3, data_fim: "2027-02-05" } }
          : { nome: "Troca de tela" },
      ],
      ...ordemExtra,
    },
  };
}

// jsPDF grava o texto sem compressão por padrão: dá para conferir o conteúdo no stream.
const conteudo = (pdf) => pdf.output();

describe("osPdf", () => {
  it("formata datas ISO para dd/mm/aaaa", () => {
    expect(formatarData("2026-11-05 10:00:00")).toBe("05/11/2026");
    expect(formatarData("")).toBe("");
  });

  it("gera o comprovante de entrada com os dados principais", () => {
    const texto = conteudo(montarPdfOs(jsPDF, documento("entrada"), "42"));
    expect(texto).toContain("Comprovante de Entrada");
    expect(texto).toContain("Loja Teste");
    expect(texto).toContain("Maria Souza");
    expect(texto).toContain("356789012345678");
    expect(texto).toContain("ISAQUE SOUZA");
    expect(texto).toContain("Valor previsto");
    expect(texto).toContain("Loja nao se responsabiliza por dados.");
    expect(texto).not.toContain("Garantia Padrao");
  });

  it("gera o comprovante de entrega com garantia por serviço e valor total", () => {
    const texto = conteudo(montarPdfOs(jsPDF, documento("entrega"), "42"));
    expect(texto).toContain("Comprovante de Entrega");
    expect(texto).toContain("Garantia Padrao");
    expect(texto).toContain("05/02/2027");
    expect(texto).toContain("Valor total");
    expect(texto).toContain("Garantia nao cobre mau uso.");
  });

  it("quebra em mais de uma página quando o texto é longo", () => {
    const longo = documento("entrada", { observacoes: "linha de observacao ".repeat(600) });
    const pdf = montarPdfOs(jsPDF, longo, "42");
    expect(pdf.getNumberOfPages()).toBeGreaterThan(1);
  });

  it("nomeia o arquivo pelo número da OS e tipo", () => {
    expect(nomeArquivoPdfOs(documento("entrega"), "77")).toBe("os-77-entrega.pdf");
  });
});
