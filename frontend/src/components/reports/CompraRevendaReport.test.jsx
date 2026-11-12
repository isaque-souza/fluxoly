import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import CompraRevendaReport from "./CompraRevendaReport";

const mockRelatorio = vi.fn();

vi.mock("@/api/client", () => ({
  comprasAparelhos: { relatorio: (...args) => mockRelatorio(...args) },
}));

vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

const relatorio = {
  mes: "2026-11",
  compras: { quantidade: 2, total_pago: 1800 },
  pecas_os_internas: 500,
  total_investido: 2300,
  vendas: {
    quantidade: 1,
    total_vendido: 3500,
    custo_total: 1300,
    lucro: 2200,
    itens: [{
      venda_id: 9, vendido_em: "2026-11-05 10:00:00", unidade_serializada_id: 3, produto_nome: "iPhone 13",
      imei: "350000000000001", valor_venda: 3500, valor_compra: 1000, custo_pecas: 300, custo_total: 1300, lucro: 2200,
    }],
  },
  estoque_atual: { quantidade: 1, em_reparo: 0, disponiveis: 1, capital_parado: 1000 },
};

describe("CompraRevendaReport (BR-093)", () => {
  beforeEach(() => mockRelatorio.mockReset());

  it("pede o relatório do mês escolhido e mostra investimento, lucro e aparelhos vendidos", async () => {
    mockRelatorio.mockResolvedValue({ ok: true, relatorio });
    render(<CompraRevendaReport />);

    fireEvent.change(screen.getByLabelText("Mês"), { target: { value: "2026-11" } });
    fireEvent.click(screen.getByRole("button", { name: /Gerar Relatório/ }));

    expect(await screen.findByText("Total investido no mês")).toBeInTheDocument();
    expect(mockRelatorio).toHaveBeenCalledWith("2026-11");
    expect(screen.getByText("#9")).toBeInTheDocument();
    expect(screen.getAllByText(/2\.200,00/).length).toBeGreaterThan(0);
  });

  it("avisa quando nenhum aparelho comprado foi vendido no mês", async () => {
    mockRelatorio.mockResolvedValue({ ok: true, relatorio: { ...relatorio, vendas: { quantidade: 0, total_vendido: 0, custo_total: 0, lucro: 0, itens: [] } } });
    render(<CompraRevendaReport />);

    fireEvent.click(screen.getByRole("button", { name: /Gerar Relatório/ }));

    expect(await screen.findByText("Nenhum aparelho comprado foi vendido neste mês.")).toBeInTheDocument();
  });

  it("mostra alertas de venda abaixo do custo e de aparelho sem custo", async () => {
    mockRelatorio.mockResolvedValue({
      ok: true,
      relatorio: {
        ...relatorio,
        alertas: {
          vendas_abaixo_do_custo: [
            { venda_id: 12, vendido_em: "2026-11-06 10:00:00", produto_nome: "iPhone 14", imei: "", valor_venda: 1500, custo: 2000, prejuizo: 500, base_custo: "catalogo" },
          ],
          aparelhos_sem_custo: { total: 3, itens: [{ unidade_serializada_id: 4, produto_nome: "iPhone 12 128GB", imei: "350000000000004", status: "disponivel" }] },
        },
      },
    });
    render(<CompraRevendaReport />);

    fireEvent.click(screen.getByRole("button", { name: /Gerar Relatório/ }));

    expect(await screen.findByTestId("alertas-dados")).toBeInTheDocument();
    expect(screen.getByTestId("alerta-abaixo-custo")).toHaveTextContent("Venda #12 · iPhone 14");
    expect(screen.getByTestId("alerta-abaixo-custo")).toHaveTextContent("(cadastro)");
    expect(screen.getAllByTestId("alerta-sem-custo")).toHaveLength(1);
    expect(screen.getByText("Mostrando 1 de 3. Cadastre o custo no produto ou registre a compra.")).toBeInTheDocument();
  });

  it("sem alertas, o bloco não aparece", async () => {
    mockRelatorio.mockResolvedValue({
      ok: true,
      relatorio: { ...relatorio, alertas: { vendas_abaixo_do_custo: [], aparelhos_sem_custo: { total: 0, itens: [] } } },
    });
    render(<CompraRevendaReport />);

    fireEvent.click(screen.getByRole("button", { name: /Gerar Relatório/ }));

    expect(await screen.findByText("Total investido no mês")).toBeInTheDocument();
    expect(screen.queryByTestId("alertas-dados")).not.toBeInTheDocument();
  });
});
