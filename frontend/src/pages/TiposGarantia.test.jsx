import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { toast } from "sonner";
import TiposGarantia from "./TiposGarantia";

const mockList = vi.fn();
const mockCreate = vi.fn();
const mockUpdate = vi.fn();
let mockPerfil = "admin";

vi.mock("@/api/client", () => ({
  tiposGarantia: {
    list: (...a) => mockList(...a),
    create: (...a) => mockCreate(...a),
    update: (...a) => mockUpdate(...a),
  },
}));
vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: mockPerfil } }),
}));
vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

const TERMO = { id: 3, nome: "Garantia 3 meses", duracao_meses: 3, texto: "Cobre o serviço por 3 meses.", ativo: true };

describe("Termos de Garantia (BR-055 + BR-105)", () => {
  beforeEach(() => {
    mockPerfil = "admin";
    mockList.mockReset();
    mockCreate.mockReset();
    mockUpdate.mockReset();
    toast.success.mockReset();
  });

  it("lista nome, prazo e texto", async () => {
    mockList.mockResolvedValue({ ok: true, items: [TERMO, { ...TERMO, id: 4, nome: "Sem texto", texto: "" }] });
    render(<TiposGarantia />);
    expect(await screen.findByText("Garantia 3 meses")).toBeInTheDocument();
    expect(screen.getByText("Cobre o serviço por 3 meses.")).toBeInTheDocument();
    expect(screen.getByText(/usa o texto padrão da loja/)).toBeInTheDocument();
  });

  it("admin cria termo com prazo e texto", async () => {
    mockList.mockResolvedValue({ ok: true, items: [] });
    mockCreate.mockResolvedValue({ ok: true, id: 9 });
    const { container } = render(<TiposGarantia />);
    fireEvent.click(await screen.findByRole("button", { name: /Novo Termo/ }));
    const [nome, meses] = container.ownerDocument.querySelectorAll("[role=dialog] input");
    fireEvent.change(nome, { target: { value: "Troca de tela" } });
    fireEvent.change(meses, { target: { value: "3" } });
    fireEvent.change(screen.getByLabelText("Texto do termo"), { target: { value: "Cobre a tela." } });
    fireEvent.click(screen.getByRole("button", { name: /Salvar/ }));

    await waitFor(() =>
      expect(mockCreate).toHaveBeenCalledWith({ nome: "Troca de tela", duracao_meses: 3, texto: "Cobre a tela.", ativo: true }),
    );
    expect(toast.success).toHaveBeenCalledWith("Termo de Garantia criado!");
  });

  it("não-admin não cria", async () => {
    mockPerfil = "tecnico";
    mockList.mockResolvedValue({ ok: true, items: [TERMO] });
    render(<TiposGarantia />);
    await screen.findByText("Garantia 3 meses");
    expect(screen.queryByRole("button", { name: /Novo Termo/ })).not.toBeInTheDocument();
  });
});
