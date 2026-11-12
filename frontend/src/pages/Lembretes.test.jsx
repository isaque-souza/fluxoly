import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import Lembretes, { numeroWhatsapp, linkWhatsapp } from "./Lembretes";

const mockLembretes = vi.fn();
vi.mock("@/api/client", () => ({ vendas: { lembretes: (...args) => mockLembretes(...args) } }));

function renderPage() {
  return render(
    <MemoryRouter>
      <Lembretes />
    </MemoryRouter>,
  );
}

describe("Lembretes de pós-venda (BR-104)", () => {
  beforeEach(() => mockLembretes.mockReset());

  it("normaliza telefone brasileiro para wa.me", () => {
    expect(numeroWhatsapp("(11) 99999-8888")).toBe("5511999998888");
    expect(numeroWhatsapp("11 3333-4444")).toBe("551133334444");
    expect(numeroWhatsapp("+55 11 99999-8888")).toBe("5511999998888");
    expect(numeroWhatsapp("9999")).toBeNull();
    expect(numeroWhatsapp("")).toBeNull();
  });

  it("monta o link com primeiro nome e produto na mensagem", () => {
    const link = linkWhatsapp({ telefone: "11999998888", cliente_nome: "Carla Lima", produtos: "iPhone 13" }, "upgrade");
    expect(link.startsWith("https://wa.me/5511999998888?text=")).toBe(true);
    const texto = decodeURIComponent(link.split("text=")[1]);
    expect(texto).toContain("Olá, Carla!");
    expect(texto).toContain("iPhone 13");
  });

  it("lista por marco, com botão de WhatsApp só para telefone válido", async () => {
    mockLembretes.mockResolvedValue({
      ok: true,
      data: "2026-11-11",
      grupos: [
        { dias: 7, tipo: "pos_venda", itens: [{ venda_id: 1, data_venda: "2026-11-04", cliente_nome: "Ana", telefone: "11988887777", produtos: "iPhone 14" }] },
        { dias: 30, tipo: "satisfacao", itens: [] },
        { dias: 365, tipo: "upgrade", itens: [{ venda_id: 2, data_venda: "2025-11-11", cliente_nome: "Bruno", telefone: "", produtos: "iPhone 11" }] },
      ],
    });
    renderPage();

    await waitFor(() => expect(screen.getAllByTestId("lembrete")).toHaveLength(2));
    expect(screen.getByTestId("lembretes-pos_venda")).toBeInTheDocument();
    expect(screen.queryByTestId("lembretes-satisfacao")).not.toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: /Abrir WhatsApp/ })).toHaveLength(1);
    expect(screen.getByText("Sem telefone válido")).toBeInTheDocument();
  });

  it("dia sem lembretes mostra estado vazio", async () => {
    mockLembretes.mockResolvedValue({ ok: true, grupos: [{ dias: 7, tipo: "pos_venda", itens: [] }] });
    renderPage();
    expect(await screen.findByText("Nenhum cliente para procurar neste dia.")).toBeInTheDocument();
  });
});
