import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";
import { toast } from "sonner";
import VendaDetalhe from "./VendaDetalhe";

const mockVendasGet = vi.fn();
const mockHistoricoDesconto = vi.fn().mockResolvedValue({ ok: true, historico: [] });
const mockHistoricoComissao = vi.fn().mockResolvedValue({ ok: true, historico: [] });
const mockHistoricoGarantia = vi.fn().mockResolvedValue({ ok: true, historico: [] });
const mockTiposGarantiaList = vi.fn();

vi.mock("@/api/client", () => ({
  vendas: {
    get: (...args) => mockVendasGet(...args),
    historicoDescontoItem: (...args) => mockHistoricoDesconto(...args),
    historicoComissaoItem: (...args) => mockHistoricoComissao(...args),
    historicoGarantiaItem: (...args) => mockHistoricoGarantia(...args),
    ajustarDescontoItem: vi.fn(),
    atribuirComissaoItem: vi.fn(),
    corrigirGarantiaItem: vi.fn(),
    cancelar: vi.fn(),
  },
  tiposGarantia: { list: (...args) => mockTiposGarantiaList(...args) },
}));

vi.mock("sonner", () => ({
  toast: { error: vi.fn(), success: vi.fn(), info: vi.fn() },
}));

vi.mock("@/contexts/AuthContext", () => ({
  useAuth: () => ({ user: { id: 1, perfil: "admin" } }),
}));

const vendaConcluida = {
  id: 42,
  status: "concluida",
  cliente_nome: "Maria",
  vendedor_nome: "João",
  vendedor_id: 1,
  forma_pagamento: "pix",
  valor_total: 1500,
  criado_em: "2026-08-20 10:00",
};

const itensConcluida = [
  {
    id: 7,
    produto_nome: "iPhone 13",
    imei: "123456789012345",
    produto_sku: "IP13-128",
    valor_tabela: 1600,
    valor_unitario: 1500,
    desconto: 100,
    subtotal: 1500,
    tipo_garantia_id: null,
    garantia_nome: null,
  },
];

function renderVendaDetalhe() {
  return render(
    <MemoryRouter initialEntries={["/vendas/42"]}>
      <Routes>
        <Route path="/vendas/:id" element={<VendaDetalhe />} />
      </Routes>
    </MemoryRouter>
  );
}

describe("VendaDetalhe — tipos de garantia (KI-048)", () => {
  beforeEach(() => {
    mockVendasGet.mockReset();
    mockHistoricoDesconto.mockClear();
    mockHistoricoComissao.mockClear();
    mockHistoricoGarantia.mockClear();
    mockTiposGarantiaList.mockReset();
    toast.error.mockReset();
  });

  it("mostra a venda normalmente quando a busca de tipos de garantia funciona", async () => {
    mockVendasGet.mockResolvedValue({ ok: true, venda: vendaConcluida, itens: itensConcluida });
    mockTiposGarantiaList.mockResolvedValue({ ok: true, items: [] });
    renderVendaDetalhe();

    await waitFor(() => expect(screen.getAllByText("Venda #42").length).toBeGreaterThan(0));
    expect(toast.error).not.toHaveBeenCalled();
  });

  it("mostra toast.error quando a busca de tipos de garantia rejeita, sem travar a tela (KI-048)", async () => {
    mockVendasGet.mockResolvedValue({ ok: true, venda: vendaConcluida, itens: itensConcluida });
    mockTiposGarantiaList.mockRejectedValue(new Error("network error"));
    renderVendaDetalhe();

    // podeCorrigirGarantia exige admin + venda concluida + itemPrincipal -- todos verdadeiros aqui,
    // entao o useEffect de tiposGarantiaApi.list() dispara e deve cair no catch.
    await waitFor(() => expect(toast.error).toHaveBeenCalledWith("Erro ao carregar tipos de garantia"));
    // A tela continua funcional -- nao trava no spinner nem quebra o restante da renderizacao.
    expect(screen.getAllByText("Venda #42").length).toBeGreaterThan(0);
  });
});

describe("VendaDetalhe — custo e lucro do aparelho comprado (BR-092)", () => {
  beforeEach(() => {
    mockVendasGet.mockReset();
    mockTiposGarantiaList.mockReset();
    mockTiposGarantiaList.mockResolvedValue({ ok: true, items: [] });
  });

  it("mostra custo total e lucro quando o item veio de compra", async () => {
    const itens = [{ ...itensConcluida[0], custo_aparelho: { valor_compra: 1000, custo_pecas: 300, custo_total: 1300 }, lucro: 200 }];
    mockVendasGet.mockResolvedValue({ ok: true, venda: vendaConcluida, itens });
    renderVendaDetalhe();

    await waitFor(() => expect(screen.getByText("Custo e lucro do aparelho")).toBeInTheDocument());
    expect(screen.getByTestId("venda-lucro")).toHaveTextContent("200,00");
  });

  it("não mostra o painel quando o backend não manda custo (aparelho sem compra ou perfil sem acesso)", async () => {
    mockVendasGet.mockResolvedValue({ ok: true, venda: vendaConcluida, itens: itensConcluida });
    renderVendaDetalhe();

    await waitFor(() => expect(screen.getAllByText("Venda #42").length).toBeGreaterThan(0));
    expect(screen.queryByText("Custo e lucro do aparelho")).not.toBeInTheDocument();
  });
});
