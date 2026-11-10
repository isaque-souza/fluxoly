import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { toast } from "sonner";
import EditOrder from "./EditOrder";

const mockOrdensGet = vi.fn();
const mockConstGet = vi.fn();
const mockReparosList = vi.fn();
const mockEstoqueList = vi.fn();
const mockTiposGarantiaList = vi.fn();
const mockChecklistGetByOrder = vi.fn().mockResolvedValue({ ok: true, checklist: null });
const mockDocumento = vi.fn();
const mockBaixarPdfOs = vi.fn();

vi.mock("@/api/client", () => ({
  ordens: {
    get: (...args) => mockOrdensGet(...args),
    update: vi.fn(),
    patchStatus: vi.fn(),
    documento: (...args) => mockDocumento(...args),
  },
  constantes: { get: (...args) => mockConstGet(...args) },
  reparos: { list: (...args) => mockReparosList(...args) },
  estoque: { list: (...args) => mockEstoqueList(...args) },
  checklist: {
    getByOrder: (...args) => mockChecklistGetByOrder(...args),
    generateToken: vi.fn(),
    qrImageUrl: vi.fn(),
  },
  precos: { sugerir: vi.fn() },
  tiposGarantia: { list: (...args) => mockTiposGarantiaList(...args) },
}));

vi.mock("@/lib/osPdf", () => ({
  baixarPdfOs: (...args) => mockBaixarPdfOs(...args),
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn() },
}));

const ordemValida = {
  id: 1,
  cliente: "João",
  modelo: "iPhone 13",
  cor: "Preto",
  status: "Em andamento",
  reparo_ids: [],
  pecas_usadas: [],
};

function renderEditOrder() {
  return render(
    <MemoryRouter initialEntries={["/ordens/1/editar"]}>
      <Routes>
        <Route path="/ordens/:id/editar" element={<EditOrder />} />
        <Route path="/ordens" element={<div>Lista de Ordens</div>} />
      </Routes>
    </MemoryRouter>
  );
}

describe("EditOrder — carga inicial", () => {
  beforeEach(() => {
    mockOrdensGet.mockReset();
    mockConstGet.mockReset();
    mockReparosList.mockReset();
    mockEstoqueList.mockReset();
    mockTiposGarantiaList.mockReset();
    toast.error.mockReset();
  });

  it("mostra o formulário (Panel de Cliente) quando a API responde", async () => {
    mockOrdensGet.mockResolvedValue({ ok: true, ordem: ordemValida });
    mockConstGet.mockResolvedValue({ ok: true, os_tipos: [], iphone_models: [] });
    mockReparosList.mockResolvedValue({ ok: true, reparos: [] });
    mockEstoqueList.mockResolvedValue({ ok: true, items: [] });
    mockTiposGarantiaList.mockResolvedValue({ ok: true, items: [] });
    renderEditOrder();

    await waitFor(() => expect(screen.getByText("Cliente")).toBeInTheDocument());
  });

  it("mostra toast.error e navega para longe (sem travar no spinner nem quebrar) quando a promise da carga inicial rejeita (KI-048)", async () => {
    mockOrdensGet.mockRejectedValue(new Error("network error"));
    mockConstGet.mockResolvedValue({ ok: true, os_tipos: [], iphone_models: [] });
    mockReparosList.mockResolvedValue({ ok: true, reparos: [] });
    mockEstoqueList.mockResolvedValue({ ok: true, items: [] });
    mockTiposGarantiaList.mockResolvedValue({ ok: true, items: [] });
    const { container } = renderEditOrder();

    expect(container.querySelector(".animate-spin")).toBeInTheDocument();

    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Erro ao carregar dados da ordem"));
    // `form` só é preenchido no branch de sucesso -- sem navegar para longe daqui, o restante do
    // componente tentaria ler `form.cliente` contra `null` e quebraria (ver comentário no catch em
    // EditOrder.jsx). Confirmar a navegação prova tanto "saiu do spinner" quanto "não quebrou".
    await waitFor(() => expect(screen.getByText("Lista de Ordens")).toBeInTheDocument());
  });
});

describe("EditOrder — PDF para o cliente (BR-095 a BR-098)", () => {
  const carregar = (ordem) => {
    mockOrdensGet.mockResolvedValue({ ok: true, ordem: { ...ordemValida, ...ordem } });
    mockConstGet.mockResolvedValue({ ok: true, os_tipos: [], iphone_models: [] });
    mockReparosList.mockResolvedValue({ ok: true, reparos: [] });
    mockEstoqueList.mockResolvedValue({ ok: true, items: [] });
    mockTiposGarantiaList.mockResolvedValue({ ok: true, items: [] });
    renderEditOrder();
  };

  beforeEach(() => {
    mockDocumento.mockReset();
    mockBaixarPdfOs.mockReset();
    toast.error.mockReset();
  });

  it("OS em andamento: entrada habilitada, entrega desabilitada", async () => {
    carregar({ status: "Em andamento" });
    const entrada = await screen.findByRole("button", { name: /PDF de entrada/ });
    expect(entrada).toBeEnabled();
    expect(screen.getByRole("button", { name: /PDF de entrega/ })).toBeDisabled();
  });

  it("OS finalizada: gera o PDF de entrega com o documento do backend", async () => {
    const documento = { tipo: "entrega", loja: {}, cliente: {}, ordem: { id: 1 } };
    mockDocumento.mockResolvedValue({ ok: true, documento });
    carregar({ status: "Finalizado" });

    fireEvent.click(await screen.findByRole("button", { name: /PDF de entrega/ }));

    await waitFor(() => expect(mockBaixarPdfOs).toHaveBeenCalledWith(documento, "1"));
    expect(mockDocumento).toHaveBeenCalledWith("1", "entrega");
  });

  it("mostra o erro do backend (ex.: loja sem cadastro) sem gerar PDF", async () => {
    mockDocumento.mockResolvedValue({ ok: false, erro: "Cadastre os Dados da Loja antes de gerar documentos." });
    carregar({ status: "Em andamento" });

    fireEvent.click(await screen.findByRole("button", { name: /PDF de entrada/ }));

    await waitFor(() =>
      expect(toast.error).toHaveBeenCalledWith("Cadastre os Dados da Loja antes de gerar documentos."),
    );
    expect(mockBaixarPdfOs).not.toHaveBeenCalled();
  });

  it.each([
    ["OS cancelada", { status: "Cancelado" }],
    ["OS interna", { tipo: "Interna" }],
  ])("%s não mostra os botões de PDF", async (_, ordem) => {
    carregar(ordem);
    await screen.findByRole("button", { name: /Finalizar OS/ });
    expect(screen.queryByRole("button", { name: /PDF de entrada/ })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /PDF de entrega/ })).not.toBeInTheDocument();
  });
});
