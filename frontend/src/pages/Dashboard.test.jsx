import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Dashboard from "./Dashboard";

const mockGet = vi.fn();
const mockToastError = vi.fn();

vi.mock("@/api/client", () => ({
  dashboard: { get: (...args) => mockGet(...args) },
  constantes: { get: vi.fn().mockResolvedValue({ ok: true, tecnicos: [] }) },
}));

vi.mock("sonner", () => ({
  toast: { error: (...args) => mockToastError(...args), success: vi.fn() },
}));

// Graficos reais (Recharts) nao sao o alvo deste teste e nao se comportam bem
// em jsdom (ResizeObserver/layout ausentes) - mockados como stubs simples.
vi.mock("@/components/dashboard/RevenueChartCard", () => ({ default: () => <div>RevenueChart</div> }));
vi.mock("@/components/dashboard/TechnicianProfitChartCard", () => ({ default: () => <div>TechChart</div> }));
vi.mock("@/components/dashboard/ServicesChartCard", () => ({ default: () => <div>ServicesChart</div> }));
// Pendências têm teste próprio (PendenciasHoje.test.jsx) e dependem de AuthContext.
vi.mock("@/components/dashboard/PendenciasHoje", () => ({ default: () => null }));

const dadosComResultado = {
  ok: true,
  faturamento_total: 1000,
  lucro_total: 400,
  ordens_finalizadas: 5,
  ordens_abertas: 2,
  shopping_pendentes: 1,
  shopping_urgentes: 0,
  ticket_medio: 200,
  resultado_liquido: 300,
  faturamento_por_dia: [{ date: "2026-01-01", value: 100 }],
  lucro_por_tecnico: [],
  servicos_mais_feitos: [],
};

const dadosVazios = {
  ok: true,
  faturamento_total: 0,
  lucro_total: 0,
  ordens_finalizadas: 0,
  ordens_abertas: 0,
  shopping_pendentes: 0,
  shopping_urgentes: 0,
  ticket_medio: 0,
  resultado_liquido: 0,
  faturamento_por_dia: [],
  lucro_por_tecnico: [],
  servicos_mais_feitos: [],
};

describe("Dashboard — estados loading/success/empty/error", () => {
  beforeEach(() => {
    mockGet.mockReset();
    mockToastError.mockClear();
  });

  it("mostra skeleton na primeira carga, antes da API responder", () => {
    mockGet.mockReturnValue(new Promise(() => {})); // nunca resolve
    const { container } = render(<Dashboard />);

    expect(container.querySelectorAll(".animate-pulse").length).toBeGreaterThan(0);
    expect(screen.queryByText("Faturamento")).not.toBeInTheDocument();
  });

  it("mostra os KPIs quando a API retorna dados reais (success)", async () => {
    mockGet.mockResolvedValue(dadosComResultado);
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText("Ticket Médio")).toBeInTheDocument());
    expect(screen.getByText("Finalizadas")).toBeInTheDocument();
    expect(screen.queryByText("Nenhum dado no período selecionado")).not.toBeInTheDocument();
  });

  it("mostra estado vazio quando a API responde ok mas sem nenhum indicador", async () => {
    mockGet.mockResolvedValue(dadosVazios);
    render(<Dashboard />);

    await waitFor(() =>
      expect(screen.getByText("Nenhum dado no período selecionado")).toBeInTheDocument()
    );
    expect(screen.queryByText("Faturamento")).not.toBeInTheDocument();
  });

  it("mostra estado de erro em tela cheia quando a primeira carga falha", async () => {
    mockGet.mockResolvedValue({ ok: false });
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText("Erro ao carregar dashboard.")).toBeInTheDocument());
    expect(screen.getByRole("button", { name: /tentar novamente/i })).toBeInTheDocument();
    expect(mockToastError).toHaveBeenCalled();
  });

  it("mantém o dado anterior visível e mostra um banner ao falhar num refiltro", async () => {
    mockGet.mockResolvedValueOnce(dadosComResultado);
    render(<Dashboard />);
    await waitFor(() => expect(screen.getByText("Ticket Médio")).toBeInTheDocument());

    mockGet.mockResolvedValueOnce({ ok: false });
    const user = userEvent.setup();
    await user.click(screen.getByRole("button", { name: "Filtrar" }));

    await waitFor(() => expect(screen.getByText("Erro ao carregar dashboard.")).toBeInTheDocument());
    // dado antigo continua na tela — não é o estado de erro em tela cheia
    expect(screen.getByText("Ticket Médio")).toBeInTheDocument();
  });

  it("clique em Filtrar dispara uma nova busca", async () => {
    mockGet.mockResolvedValue(dadosComResultado);
    render(<Dashboard />);
    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(1));

    // KI-057: a chamada à API acontece antes de o botão existir na tela -- esperar o botão,
    // não só a chamada, senão o clique às vezes procura um elemento que ainda não renderizou.
    const filtrar = await screen.findByRole("button", { name: "Filtrar" });
    const user = userEvent.setup();
    await user.click(filtrar);

    await waitFor(() => expect(mockGet).toHaveBeenCalledTimes(2));
  });

  it("Faturamento aparece como métrica dominante (Panel), os outros KPIs como métricas soltas", async () => {
    mockGet.mockResolvedValue(dadosComResultado);
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText("Ticket Médio")).toBeInTheDocument());

    // Faturamento continua presente e com tratamento "hero" (texto maior que os outros números).
    // O mesmo valor formatado aparece 2x na tela (Panel hero + linha no Resumo Financeiro) —
    // colisão pré-existente (já existia no Dashboard antes desta Fase 3.2), então filtramos
    // pelo elemento que carrega a classe de texto "hero".
    const candidates = screen.getAllByText("R$ 1.000,00");
    const faturamentoValor = candidates.find((el) => /text-(4|5)xl/.test(el.className));
    expect(faturamentoValor).toBeInTheDocument();
    expect(faturamentoValor.className).toMatch(/text-(4|5)xl/);
  });
});

describe("Dashboard — vendas somadas às OS (PLAN-dashboard-vendas-os.md)", () => {
  it("hero mostra o consolidado, composição e top vendedores", async () => {
    mockGet.mockResolvedValue({
      ...dadosComResultado,
      vendas: {
        quantidade: 2,
        faturamento: 5000,
        ticket_medio: 2500,
        por_vendedor: [{ vendedor: "Bia", quantidade: 2, faturamento: 5000 }],
        lucro_aparelhos: { aparelhos_com_custo: 1, valor_vendido: 3000, custo_total: 2000, lucro: 1000 },
      },
      consolidado: { faturamento: 6000, faturamento_os: 1000, faturamento_vendas: 5000, ticket_medio: 2000 },
    });
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByTestId("dashboard-vendas")).toBeInTheDocument());
    const hero = screen.getAllByText("R$ 6.000,00").find((el) => /text-(4|5)xl/.test(el.className));
    expect(hero).toBeInTheDocument();
    expect(screen.getByTestId("faturamento-composicao")).toHaveTextContent("Vendas R$ 5.000,00");
    expect(screen.getByTestId("top-vendedor")).toHaveTextContent("Bia · 2 venda(s)");
    expect(screen.getByText("Lucro Aparelhos")).toBeInTheDocument();
  });

  it("sem lucro_aparelhos (vendedor) não mostra lucro de aparelho", async () => {
    mockGet.mockResolvedValue({
      ...dadosComResultado,
      vendas: { quantidade: 1, faturamento: 900, ticket_medio: 900, por_vendedor: [] },
      consolidado: { faturamento: 1900 },
    });
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByTestId("dashboard-vendas")).toBeInTheDocument());
    expect(screen.queryByText("Lucro Aparelhos")).not.toBeInTheDocument();
  });
});

describe("Dashboard — vendedor sem custo/lucro (PLAN-esconder-lucro-vendedor.md)", () => {
  it("sem as chaves de custo/lucro, esconde Lucro Bruto, Resultado, gráfico de lucro e Resumo Financeiro", async () => {
    const semCusto = { ...dadosComResultado };
    ["lucro_total", "custo_consumido_periodo", "custos_operacionais_periodo", "resultado_liquido",
      "gasto_total_estoque", "lucro_por_tecnico", "custos_por_categoria"].forEach((k) => delete semCusto[k]);
    mockGet.mockResolvedValue(semCusto);
    render(<Dashboard />);

    await waitFor(() => expect(screen.getByText("Ticket Médio")).toBeInTheDocument());
    expect(screen.queryByText("Lucro Bruto")).not.toBeInTheDocument();
    expect(screen.queryByText("Resultado Líq.")).not.toBeInTheDocument();
    expect(screen.queryByText("TechChart")).not.toBeInTheDocument();
    expect(screen.queryByText("Resumo Financeiro")).not.toBeInTheDocument();
  });
});
