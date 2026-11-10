import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { toast } from "sonner";
import DadosLoja from "./DadosLoja";

const mockGet = vi.fn();
const mockSave = vi.fn();
let mockPerfil = "admin";

vi.mock("@/api/client", () => ({
  dadosLoja: { get: (...a) => mockGet(...a), save: (...a) => mockSave(...a) },
}));
vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { perfil: mockPerfil } }),
}));
vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

const DADOS = {
  nome_fantasia: "Loja Teste",
  razao_social: "",
  cnpj: "12.345.678/0001-90",
  telefone: "",
  email: "",
  endereco: "",
  termos_entrada: "",
  termos_garantia: "Garantia não cobre mau uso.",
};

describe("DadosLoja (BR-094)", () => {
  beforeEach(() => {
    mockPerfil = "admin";
    mockGet.mockReset();
    mockSave.mockReset();
    toast.error.mockReset();
    toast.success.mockReset();
  });

  it("carrega os dados salvos no formulário", async () => {
    mockGet.mockResolvedValue({ ok: true, dados_loja: DADOS });
    render(<DadosLoja />);
    expect(await screen.findByDisplayValue("Loja Teste")).toBeInTheDocument();
    expect(screen.getByDisplayValue("Garantia não cobre mau uso.")).toBeInTheDocument();
  });

  it("admin salva os dados", async () => {
    mockGet.mockResolvedValue({ ok: true, dados_loja: DADOS });
    mockSave.mockResolvedValue({ ok: true, dados_loja: DADOS });
    render(<DadosLoja />);
    const nome = await screen.findByLabelText(/Nome fantasia/);
    fireEvent.change(nome, { target: { value: "Loja Nova" } });
    fireEvent.click(screen.getByRole("button", { name: /Salvar/ }));

    await waitFor(() => expect(mockSave).toHaveBeenCalledWith({ ...DADOS, nome_fantasia: "Loja Nova" }));
    expect(toast.success).toHaveBeenCalled();
  });

  it("não envia sem nome fantasia", async () => {
    mockGet.mockResolvedValue({ ok: true, dados_loja: { ...DADOS, nome_fantasia: "" } });
    render(<DadosLoja />);
    await screen.findByLabelText(/Nome fantasia/);
    fireEvent.submit(screen.getByRole("button", { name: /Salvar/ }).closest("form"));

    expect(toast.error).toHaveBeenCalledWith("Nome fantasia é obrigatório.");
    expect(mockSave).not.toHaveBeenCalled();
  });

  it("não-admin vê os campos bloqueados e sem botão de salvar", async () => {
    mockPerfil = "tecnico";
    mockGet.mockResolvedValue({ ok: true, dados_loja: DADOS });
    render(<DadosLoja />);
    expect(await screen.findByLabelText(/Nome fantasia/)).toBeDisabled();
    expect(screen.queryByRole("button", { name: /Salvar/ })).not.toBeInTheDocument();
    expect(screen.getByText(/Somente administradores/)).toBeInTheDocument();
  });
});
