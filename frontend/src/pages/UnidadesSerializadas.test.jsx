import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import UnidadesSerializadas from "./UnidadesSerializadas";

const mockList = vi.fn();
const mockGet = vi.fn();
const mockHistorico = vi.fn().mockResolvedValue({ ok: true, historico: [] });
const mockVendaGet = vi.fn();

vi.mock("@/api/client", () => ({
  unidadesSerializadas: {
    list: (...args) => mockList(...args),
    get: (...args) => mockGet(...args),
    historico: (...args) => mockHistorico(...args),
  },
  vendas: { get: (...args) => mockVendaGet(...args) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

describe("UnidadesSerializadas — estados e status semântico", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<UnidadesSerializadas />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com o Badge de status semântico quando a API retorna unidades", async () => {
    mockList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{ id: 1, imei: "123456789012345", status: "disponivel", origem_tipo: "estoque" }],
    });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("123456789012345")).toBeInTheDocument());
    expect(screen.getByText("Disponível").className).toContain("bg-success/10");
    // ORIGEM_BADGE migrado para o Badge taxonômico variant="tag" no PR 5
    // (PLAN-design-system-fase2.md) -- cor neutra única, sem tom por valor.
    expect(screen.getByText("Estoque").className).toContain("bg-secondary/60");
  });

  it("mostra EmptyState quando não há unidades", async () => {
    mockList.mockResolvedValue({ ok: true, total: 0, items: [] });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("Nenhuma unidade serializada cadastrada ainda.")).toBeInTheDocument());
  });

  it("mostra ErrorState com retry quando a API falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar as unidades.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });

  it("KI-062: detalhe da unidade vendida mostra comprador e garantia da venda", async () => {
    mockList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{ id: 5, imei: "356000000000005", status: "vendido", origem_tipo: "estoque" }],
    });
    mockGet.mockResolvedValue({
      ok: true,
      unidade: { id: 5, imei: "356000000000005", status: "vendido", origem_tipo: "estoque", venda_id: 40, criado_em: "2026-10-01 09:00:00" },
    });
    mockVendaGet.mockResolvedValue({
      ok: true,
      venda: { id: 40, cliente_nome: "Carla Souza", criado_em: "2026-11-03 15:20:00" },
      itens: [{ unidade_serializada_id: 5, garantia_nome: "Seminovo 90 dias", garantia_data_fim: "2027-02-01" }],
    });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("356000000000005")).toBeInTheDocument());
    await userEvent.setup().click(screen.getByText("356000000000005"));

    await waitFor(() => expect(screen.getByTestId("unidade-comprador")).toHaveTextContent("Carla Souza"));
    expect(mockVendaGet).toHaveBeenCalledWith(40);
    expect(screen.getByTestId("unidade-comprador")).toHaveTextContent("Venda #40 · 03/11/2026");
    expect(screen.getByTestId("unidade-garantia")).toHaveTextContent("até 01/02/2027");
    expect(screen.queryByText(/módulo de Vendas em construção/)).not.toBeInTheDocument();
  });

  it("KI-062: unidade sem venda não consulta Vendas", async () => {
    mockVendaGet.mockReset();
    mockList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{ id: 6, imei: "356000000000006", status: "disponivel", origem_tipo: "estoque" }],
    });
    mockGet.mockResolvedValue({
      ok: true,
      unidade: { id: 6, imei: "356000000000006", status: "disponivel", origem_tipo: "estoque", venda_id: null },
    });
    render(<UnidadesSerializadas />);

    await waitFor(() => expect(screen.getByText("356000000000006")).toBeInTheDocument());
    await userEvent.setup().click(screen.getByText("356000000000006"));

    await waitFor(() => expect(screen.getByText("Sem venda registrada.")).toBeInTheDocument());
    expect(mockVendaGet).not.toHaveBeenCalled();
  });
});
