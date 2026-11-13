import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Clientes from "./Clientes";

const mockList = vi.fn();
const mockGarantiasList = vi.fn();
const mockClienteHistory = vi.fn().mockResolvedValue({ ok: true, ordens: [] });
const mockVendasList = vi.fn().mockResolvedValue({ ok: true, items: [] });
const mockInativar = vi.fn();
const mockReativar = vi.fn();
const mockDelete = vi.fn();

vi.mock("@/api/client", () => ({
  clientes: {
    list: (...args) => mockList(...args),
    inativar: (...args) => mockInativar(...args),
    reativar: (...args) => mockReativar(...args),
    delete: (...args) => mockDelete(...args),
  },
  ordens: { clienteHistory: (...args) => mockClienteHistory(...args) },
  garantias: { list: (...args) => mockGarantiasList(...args) },
  vendas: { list: (...args) => mockVendasList(...args) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: "admin" } }),
}));

describe("Clientes — estados e status semântico (PR 5)", () => {
  beforeEach(() => {
    mockList.mockReset();
    mockGarantiasList.mockReset();
    mockGarantiasList.mockResolvedValue({ ok: true, garantias: [] });
  });

  it("mostra o skeleton de lista antes da API responder", () => {
    mockList.mockReturnValue(new Promise(() => {}));
    const { container } = render(<Clientes />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
  });

  it("mostra a tabela com os clientes quando a API responde", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, nome: "Carla Souza", telefone: "11999990000", email: "carla@example.com" }],
    });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
  });

  it("mostra EmptyState quando não há clientes", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Nenhum cliente cadastrado ainda.")).toBeInTheDocument());
  });

  it("mostra os filtros e KPIs da listagem após carregar", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByPlaceholderText("Buscar por nome, telefone, e-mail, CPF/CNPJ...")).toBeInTheDocument());
    expect(screen.getByText("Com telefone")).toBeInTheDocument();
  });

  it("mostra o Badge de garantia com a variante semântica correta no perfil do cliente", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, nome: "Carla Souza", telefone: "11999990000", email: "carla@example.com" }],
    });
    mockGarantiasList.mockResolvedValue({
      ok: true,
      garantias: [{ id: 1, reparo_id: 1, modelo: "iPhone 13", status_garantia: "vencida", dias_restantes: 0 }],
    });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByText("Carla Souza"));

    await waitFor(() => expect(screen.getByText("Vencida")).toBeInTheDocument());
    expect(screen.getByText("Vencida").className).toContain("bg-destructive/10");
  });

  it("mostra ErrorState com retry quando a API de clientes falha (KI-049)", async () => {
    mockList.mockResolvedValue({ ok: false });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar os clientes.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
  });

  it("mostra ErrorState quando a promise da API de clientes rejeita (KI-049)", async () => {
    mockList.mockRejectedValue(new Error("network error"));
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Não foi possível carregar os clientes.")).toBeInTheDocument());
  });

  it("perfil do cliente não fica preso no loading quando a busca de histórico/garantias rejeita (KI-048)", async () => {
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 1, nome: "Carla Souza", telefone: "11999990000", email: "carla@example.com" }],
    });
    mockClienteHistory.mockRejectedValue(new Error("network error"));
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByText("Carla Souza"));

    await waitFor(() => expect(screen.getByText("Nenhuma OS encontrada para este cliente.")).toBeInTheDocument());
  });

  it("KI-062: perfil do cliente lista as compras buscadas por cliente_id", async () => {
    // o teste KI-048 acima deixa clienteHistory rejeitando -- restaura o caminho feliz
    mockClienteHistory.mockResolvedValue({ ok: true, ordens: [] });
    mockList.mockResolvedValue({
      ok: true,
      items: [{ id: 7, nome: "Carla Souza", telefone: "11999990000" }],
    });
    mockVendasList.mockResolvedValueOnce({
      ok: true,
      items: [
        { id: 31, status: "concluida", valor_total: 3500, criado_em: "2026-11-01 10:00:00", itens_resumo: [{ produto_nome: "iPhone 13 128GB" }] },
        { id: 32, status: "cancelada", valor_total: 900, criado_em: "2026-11-02 11:00:00", itens_resumo: [{ produto_nome: "iPhone 11" }] },
      ],
    });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Carla Souza")).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByText("Carla Souza"));

    await waitFor(() => expect(screen.getAllByTestId("compra-cliente")).toHaveLength(2));
    expect(mockVendasList).toHaveBeenCalledWith({ cliente_id: 7, per_page: 50 });
    expect(screen.getByText("iPhone 13 128GB")).toBeInTheDocument();
    expect(screen.getByText("Cancelada")).toBeInTheDocument();
    expect(screen.queryByText(/módulo de Vendas em construção/)).not.toBeInTheDocument();
  });

  it("KI-062: perfil sem compras mostra mensagem sem placeholder de módulo em construção", async () => {
    // o teste KI-048 acima deixa clienteHistory rejeitando -- restaura o caminho feliz
    mockClienteHistory.mockResolvedValue({ ok: true, ordens: [] });
    mockList.mockResolvedValue({ ok: true, items: [{ id: 8, nome: "Bruno Lima" }] });
    mockVendasList.mockResolvedValueOnce({ ok: true, items: [] });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Bruno Lima")).toBeInTheDocument());
    const user = userEvent.setup();
    await user.click(screen.getByText("Bruno Lima"));

    await waitFor(() => expect(screen.getByText("Nenhuma compra registrada para este cliente.")).toBeInTheDocument());
  });
});

describe("Clientes — inativação no lugar da exclusão (KI-066, BR-024)", () => {
  beforeEach(() => {
    mockList.mockReset();
    mockInativar.mockReset();
    mockReativar.mockReset();
    mockDelete.mockReset();
    mockGarantiasList.mockResolvedValue({ ok: true, garantias: [] });
    mockClienteHistory.mockResolvedValue({ ok: true, ordens: [] });
  });

  it("pede só clientes ativos por padrão", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<Clientes />);

    await waitFor(() => expect(mockList).toHaveBeenCalledWith({ per_page: 500, status: "ativos" }));
  });

  it("não oferece Excluir: Inativar pede confirmação e chama a API de inativação", async () => {
    mockList.mockResolvedValue({ ok: true, items: [{ id: 5, nome: "Ana Ativa", ativo: true }] });
    mockInativar.mockResolvedValue({ ok: true, alterado: true, ativo: false });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Ana Ativa")).toBeInTheDocument());
    expect(screen.queryByLabelText("Excluir cliente 5")).not.toBeInTheDocument();
    expect(screen.queryByTestId("cliente-badge-inativo")).not.toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByLabelText("Inativar cliente 5"));
    expect(await screen.findByText("Inativar Cliente?")).toBeInTheDocument();
    expect(screen.getByText(/Nada é apagado/)).toBeInTheDocument();
    expect(mockInativar).not.toHaveBeenCalled();

    await user.click(screen.getByTestId("clientes-confirmar-situacao"));
    await waitFor(() => expect(mockInativar).toHaveBeenCalledWith(5));
    expect(mockDelete).not.toHaveBeenCalled();
  });

  it("cliente inativo mostra o badge e a ação Reativar", async () => {
    mockList.mockResolvedValue({ ok: true, items: [{ id: 6, nome: "Ivo Inativo", ativo: false }] });
    mockReativar.mockResolvedValue({ ok: true, alterado: true, ativo: true });
    render(<Clientes />);

    await waitFor(() => expect(screen.getByText("Ivo Inativo")).toBeInTheDocument());
    expect(screen.getByTestId("cliente-badge-inativo")).toHaveTextContent("Inativo");
    expect(screen.queryByLabelText("Inativar cliente 6")).not.toBeInTheDocument();

    const user = userEvent.setup();
    await user.click(screen.getByLabelText("Reativar cliente 6"));
    expect(await screen.findByText("Reativar Cliente?")).toBeInTheDocument();
    await user.click(screen.getByTestId("clientes-confirmar-situacao"));
    await waitFor(() => expect(mockReativar).toHaveBeenCalledWith(6));
  });
});
