import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { toast } from "sonner";
import TermosGarantia from "./TermosGarantia";

const mockList = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();
let mockPerfil = "admin";

vi.mock("@/api/client", () => ({
  termosGarantia: {
    list: (...a) => mockList(...a),
    create: (...a) => mockCreate(...a),
    update: (...a) => mockUpdate(...a),
  },
}));
vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: mockPerfil } }),
}));
vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

const TERMO = { id: 3, nome: "Assistência 90 dias", texto: "Cobre o serviço por 90 dias.", ativo: true };

describe("TermosGarantia (BR-105)", () => {
  beforeEach(() => {
    mockPerfil = "admin";
    mockList.mockReset();
    mockCreate.mockReset();
    mockUpdate.mockReset();
    toast.error.mockReset();
    toast.success.mockReset();
  });

  it("admin lista incluindo inativos", async () => {
    mockList.mockResolvedValue({ ok: true, items: [TERMO, { ...TERMO, id: 4, nome: "Antigo", ativo: false }] });
    render(<TermosGarantia />);
    expect(await screen.findByText("Assistência 90 dias")).toBeInTheDocument();
    expect(screen.getByText("Inativo")).toBeInTheDocument();
    expect(mockList).toHaveBeenCalledWith({ incluir_inativos: 1 });
  });

  it("estado vazio explica o texto padrão da loja", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    render(<TermosGarantia />);
    expect(await screen.findByText(/texto padrão de Dados da Loja/)).toBeInTheDocument();
  });

  it("admin cria um termo", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    mockCreate.mockResolvedValue({ ok: true, id: 9 });
    render(<TermosGarantia />);
    fireEvent.click(await screen.findByRole("button", { name: /Novo Termo/ }));
    fireEvent.change(screen.getByLabelText(/Nome/), { target: { value: "Troca de tela" } });
    fireEvent.change(screen.getByLabelText(/Texto do termo/), { target: { value: "Cobre a tela." } });
    fireEvent.click(screen.getByRole("button", { name: /Salvar/ }));

    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith({ nome: "Troca de tela", texto: "Cobre a tela.", ativo: true }),
    );
    expect(toast.success).toHaveBeenCalled();
  });

  it("não-admin só lê: sem criar nem editar", async () => {
    mockPerfil = "tecnico";
    mockList.mockResolvedValue({ ok: true, items: [TERMO] });
    render(<TermosGarantia />);
    await screen.findByText("Assistência 90 dias");
    expect(screen.queryByRole("button", { name: /Novo Termo/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /Editar/ })).not.toBeInTheDocument();
    expect(mockList).toHaveBeenCalledWith({});
  });
});
