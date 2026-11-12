import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import Garantias from "./Garantias";

const mockGarantiasList = vi.fn();
const mockVendasGarantias = vi.fn();

vi.mock("@/api/client", () => ({
  garantias: { list: (...args) => mockGarantiasList(...args) },
  vendas: { garantias: (...args) => mockVendasGarantias(...args) },
}));

vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

function renderPage() {
  return render(
    <MemoryRouter>
      <Garantias />
    </MemoryRouter>,
  );
}

describe("Garantias — painel unificado (assistência + vendas)", () => {
  beforeEach(() => {
    mockGarantiasList.mockReset();
    mockVendasGarantias.mockReset();
    mockGarantiasList.mockResolvedValue({
      ok: true,
      garantias: [{ id: 3, reparo_id: 1, cliente: "Ana", modelo: "iPhone 12", status_garantia: "vencida", dias_restantes: -2 }],
    });
    mockVendasGarantias.mockResolvedValue({
      ok: true,
      items: [
        { item_id: 9, venda_id: 40, cliente_nome: "Carla", produto_nome: "iPhone 13", imei: "356000000000009", garantia_nome: "12 meses", garantia_data_fim: "2027-11-01", dias_restantes: 355, status_garantia: "ativa" },
        { item_id: 10, venda_id: 41, cliente_nome: "Bruno", produto_nome: "iPhone 11", imei: "", garantia_nome: "90 dias", garantia_data_fim: "2026-11-15", dias_restantes: 4, status_garantia: "vencendo" },
      ],
    });
  });

  it("abre na aba Assistência com as contagens das duas abas", async () => {
    renderPage();

    await waitFor(() => expect(screen.getByText("Ana")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: "Assistência (1)" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Vendas (2)" })).toBeInTheDocument();
    expect(screen.getByTestId("garantias-resumo")).toHaveTextContent("0 ativas · 0 vencendo · 1 vencidas");
  });

  it("aba Vendas lista as garantias de venda com vencimento e status", async () => {
    renderPage();
    await waitFor(() => expect(screen.getByText("Ana")).toBeInTheDocument());

    await userEvent.setup().click(screen.getByRole("button", { name: "Vendas (2)" }));

    expect(screen.getAllByTestId("garantia-venda")).toHaveLength(2);
    expect(screen.getByText("Carla")).toBeInTheDocument();
    expect(screen.getByText("01/11/2027")).toBeInTheDocument();
    expect(screen.getByText("Vencendo (4d)")).toBeInTheDocument();
    expect(screen.getByTestId("garantias-resumo")).toHaveTextContent("1 ativas · 1 vencendo · 0 vencidas");
  });
});
