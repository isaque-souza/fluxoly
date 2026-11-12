import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Orders from "./Orders";

const mockList = vi.fn();
const mockConstGet = vi.fn().mockResolvedValue({ ok: true });

vi.mock("@/api/client", () => ({
  ordens: { list: (...args) => mockList(...args), delete: vi.fn() },
  constantes: { get: (...args) => mockConstGet(...args) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

function renderOrders() {
  return render(
    <MemoryRouter>
      <Orders />
    </MemoryRouter>
  );
}

describe("Orders — estados loading/success/empty/error", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = renderOrders();

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela quando a API retorna ordens", async () => {
    mockList.mockResolvedValue({ ok: true, ordens: [{ id: 1, cliente: "Maria", status: "Em andamento" }] });
    renderOrders();

    await waitFor(() => expect(screen.getByText("Maria")).toBeInTheDocument());
    expect(screen.getByText("Em andamento")).toBeInTheDocument();
  });

  it("BR-101: OS atrasada ganha selo e entra na métrica Atrasadas", async () => {
    mockList.mockResolvedValue({
      ok: true,
      ordens: [
        { id: 1, cliente: "Maria", status: "Em andamento", atrasada: true, data_previsao: "2026-11-01" },
        { id: 2, cliente: "João", status: "Em andamento", atrasada: false, data_previsao: "2099-01-01" },
      ],
    });
    renderOrders();

    await waitFor(() => expect(screen.getByText("Maria")).toBeInTheDocument());
    expect(screen.getAllByTestId("os-atrasada").length).toBeGreaterThan(0);
    expect(screen.getByText("Atrasadas")).toBeInTheDocument();
  });

  it("mostra EmptyState quando não há ordens", async () => {
    mockList.mockResolvedValue({ ok: true, ordens: [] });
    renderOrders();

    await waitFor(() => expect(screen.getByText("Nenhuma ordem encontrada")).toBeInTheDocument());
  });

  it("mostra ErrorState em tela cheia quando a carga inicial falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    renderOrders();

    await waitFor(() => expect(screen.getByText("Não foi possível carregar as ordens.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });
});
