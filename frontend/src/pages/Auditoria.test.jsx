import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Auditoria from "./Auditoria";

const mockList = vi.fn();

vi.mock("@/api/client", () => ({
  auditoria: { list: (...args) => mockList(...args) },
}));

const registro = {
  id: 1,
  entidade: "venda",
  entidade_id: 40,
  usuario_nome: "Admin Teste",
  acao: "update",
  criado_em: "2026-11-11 18:06:00",
  alteracoes: [{ campo: "valor_total", antes: 0, depois: 15520 }],
};

describe("Auditoria", () => {
  beforeEach(() => {
    mockList.mockReset();
  });

  it("lista os registros e abre o detalhe com antes e depois", async () => {
    mockList.mockResolvedValue({ ok: true, items: [registro], total: 1, entidades: ["venda"] });
    render(<Auditoria />);

    await waitFor(() => expect(screen.getAllByTestId("auditoria-linha")).toHaveLength(1));
    expect(screen.getByText("Admin Teste")).toBeInTheDocument();
    expect(screen.getByText("11/11/2026 18:06")).toBeInTheDocument();
    expect(mockList).toHaveBeenCalledWith({ page: 1, per_page: 50 });

    await userEvent.setup().click(screen.getByTestId("auditoria-linha"));

    const diff = await screen.findByTestId("auditoria-diff");
    expect(diff).toHaveTextContent("valor_total");
    expect(diff).toHaveTextContent("15520");
  });

  it("filtra pelo número do registro", async () => {
    mockList.mockResolvedValue({ ok: true, items: [], total: 0, entidades: [] });
    render(<Auditoria />);

    await waitFor(() => expect(screen.getByText("Nenhum registro de auditoria encontrado.")).toBeInTheDocument());
    await userEvent.setup().type(screen.getByPlaceholderText("Nº do registro"), "40");

    await waitFor(() => expect(mockList).toHaveBeenLastCalledWith({ page: 1, per_page: 50, entidade_id: "40" }));
  });

  it("mostra ErrorState quando a API falha", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<Auditoria />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar a auditoria.")).toBeInTheDocument());
  });
});
