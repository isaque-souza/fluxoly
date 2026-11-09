import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { toast } from "sonner";
import ComprasAparelhos from "./ComprasAparelhos";

const mockProdutosList = vi.fn();
const mockComprasList = vi.fn();
const mockComprasCreate = vi.fn();

vi.mock("@/api/client", () => ({
  produtos: { list: (...args) => mockProdutosList(...args) },
  clientes: { list: vi.fn().mockResolvedValue({ ok: true, items: [] }) },
  comprasAparelhos: {
    list: (...args) => mockComprasList(...args),
    create: (...args) => mockComprasCreate(...args),
    cancelar: vi.fn(),
  },
}));

vi.mock("sonner", () => ({ toast: { error: vi.fn(), success: vi.fn() } }));

describe("ComprasAparelhos", () => {
  beforeEach(() => {
    mockProdutosList.mockReset();
    mockComprasList.mockReset();
    mockComprasCreate.mockReset();
    toast.error.mockReset();
    mockProdutosList.mockResolvedValue({ ok: true, items: [] });
  });

  it("não envia a compra sem o modelo do aparelho", async () => {
    render(<ComprasAparelhos />);
    await waitFor(() => expect(mockProdutosList).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Registrar compra" }));

    expect(toast.error).toHaveBeenCalledWith("Selecione o modelo do aparelho.");
    expect(mockComprasCreate).not.toHaveBeenCalled();
  });

  it("lista o histórico de compras", async () => {
    mockComprasList.mockResolvedValue({
      ok: true,
      total: 1,
      items: [{
        id: 5, criado_em: "2026-11-05 10:00:00", produto_label: "iPhone 13", imei: "350000000000001",
        origem: "marketplace", forma_pagamento: "pix", valor_pago: 1000, status: "ativa", unidade_status: "em_reparo",
      }],
    });
    render(<ComprasAparelhos />);

    fireEvent.click(screen.getByRole("button", { name: "Histórico" }));

    expect(await screen.findByText("350000000000001")).toBeInTheDocument();
    expect(mockComprasList).toHaveBeenCalledWith(expect.objectContaining({ page: 1 }));
  });
});
