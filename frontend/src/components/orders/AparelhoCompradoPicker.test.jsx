import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import AparelhoCompradoPicker, { aparelhoLabel } from "./AparelhoCompradoPicker";

const mockList = vi.fn();

vi.mock("@/api/client", () => ({
  unidadesSerializadas: { list: (...args) => mockList(...args) },
}));

const emReparo = { id: 1, imei: "350000000000001", status: "em_reparo", origem_label: "iPhone 13", produto_capacidade: "128GB", produto_cor: "Azul" };
const vendido = { id: 2, imei: "350000000000002", status: "vendido", origem_label: "iPhone 12" };

describe("AparelhoCompradoPicker (BR-090)", () => {
  beforeEach(() => mockList.mockReset());

  it("busca só aparelhos de compra e lista apenas os que ainda estão no estoque", async () => {
    mockList.mockResolvedValue({ ok: true, items: [emReparo, vendido] });
    render(<AparelhoCompradoPicker selecionado={null} onSelecionar={vi.fn()} />);

    await waitFor(() => expect(screen.getByText("iPhone 13 · 128GB · Azul")).toBeInTheDocument());
    expect(mockList).toHaveBeenCalledWith(expect.objectContaining({ origem: "compra" }));
    expect(screen.queryByText("iPhone 12")).not.toBeInTheDocument();
  });

  it("chama onSelecionar com a unidade clicada", async () => {
    mockList.mockResolvedValue({ ok: true, items: [emReparo] });
    const onSelecionar = vi.fn();
    render(<AparelhoCompradoPicker selecionado={null} onSelecionar={onSelecionar} />);

    fireEvent.click(await screen.findByText("iPhone 13 · 128GB · Azul"));
    expect(onSelecionar).toHaveBeenCalledWith(emReparo);
  });

  it("mostra o aparelho escolhido sem buscar de novo", () => {
    render(<AparelhoCompradoPicker selecionado={emReparo} onSelecionar={vi.fn()} onTrocar={vi.fn()} />);

    expect(screen.getByText(`IMEI ${emReparo.imei}`)).toBeInTheDocument();
    expect(mockList).not.toHaveBeenCalled();
    expect(aparelhoLabel(emReparo)).toBe("iPhone 13 · 128GB · Azul");
  });
});
