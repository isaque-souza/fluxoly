import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import PendenciasHoje from "./PendenciasHoje";

const mockPendencias = vi.fn();
let mockPerfil = "admin";

vi.mock("@/api/client", () => ({ pendencias: { get: (...args) => mockPendencias(...args) } }));
vi.mock("@/contexts/AuthContext", () => ({ useAuth: () => ({ user: { perfil: mockPerfil } }) }));

const vazio = { quantidade: 0, total: 0 };

function renderComponente() {
  return render(
    <MemoryRouter>
      <PendenciasHoje />
    </MemoryRouter>,
  );
}

describe("PendenciasHoje (PLAN-pendencias-tela-inicial.md)", () => {
  beforeEach(() => {
    mockPendencias.mockReset();
    mockPerfil = "admin";
  });

  it("mostra contas vencidas e que vencem hoje, com link para o Financeiro", async () => {
    mockPendencias.mockResolvedValue({
      ok: true,
      contas_pagar: { vencidas: { quantidade: 2, total: 150 }, vencem_hoje: { quantidade: 1, total: 30 } },
      contas_receber: { vencidas: vazio, vencem_hoje: { quantidade: 1, total: 80 } },
    });
    renderComponente();

    await waitFor(() => expect(screen.getByTestId("pendencias-hoje")).toBeInTheDocument());
    expect(screen.getByTestId("pendencias-pagar")).toHaveTextContent("2 vencida(s) · R$ 150,00");
    expect(screen.getByTestId("pendencias-pagar")).toHaveTextContent("1 vence(m) hoje · R$ 30,00");
    expect(screen.getByTestId("pendencias-receber")).not.toHaveTextContent("vencida");
    expect(screen.getByRole("link", { name: "Abrir Financeiro" })).toHaveAttribute("href", "/financeiro");
  });

  it("sem pendência não renderiza", async () => {
    mockPendencias.mockResolvedValue({
      ok: true,
      contas_pagar: { vencidas: vazio, vencem_hoje: vazio },
      contas_receber: { vencidas: vazio, vencem_hoje: vazio },
    });
    renderComponente();

    await waitFor(() => expect(mockPendencias).toHaveBeenCalled());
    expect(screen.queryByTestId("pendencias-hoje")).not.toBeInTheDocument();
  });

  it("vendedor não consulta nem vê pendências financeiras", () => {
    mockPerfil = "vendedor";
    renderComponente();

    expect(mockPendencias).not.toHaveBeenCalled();
    expect(screen.queryByTestId("pendencias-hoje")).not.toBeInTheDocument();
  });
});
