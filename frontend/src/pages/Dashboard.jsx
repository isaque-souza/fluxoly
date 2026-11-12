import { lazy, Suspense, useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, WarningCircle, Tray, ArrowClockwise } from "@phosphor-icons/react";
import { dashboard as dashboardApi, constantes } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { ListBlock, ListBlockItem } from "@/components/ui/list-block";
import { LooseMetric } from "@/components/ui/loose-metric";
import { formatCurrency } from "@/lib/constants";

import PendenciasHoje from "@/components/dashboard/PendenciasHoje";

const RevenueChartCard = lazy(() => import("@/components/dashboard/RevenueChartCard"));
const TechnicianProfitChartCard = lazy(() => import("@/components/dashboard/TechnicianProfitChartCard"));
const ServicesChartCard = lazy(() => import("@/components/dashboard/ServicesChartCard"));

function ChartFallback() {
  return (
    <div className="bg-card rounded-xl border border-border p-5 flex items-center justify-center h-48 text-muted-foreground text-sm">
      <CircleNotch className="h-5 w-5 animate-spin" />
    </div>
  );
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* Métrica dominante */}
      <div className="rounded-xl border border-border bg-card shadow-sm p-6 space-y-3">
        <Skeleton className="h-4 w-40" />
        <Skeleton className="h-10 w-56" />
      </div>

      {/* Métricas soltas */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4">
        {Array.from({ length: 7 }).map((_, i) => (
          <div key={i} className="space-y-1.5">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-5 w-24" />
          </div>
        ))}
      </div>

      {/* Charts -- 1 principal (2/3) + 2 de apoio (1/3 cada) */}
      <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="h-48 rounded-xl" />
      </div>
      <div className="grid lg:grid-cols-3 gap-4">
        <Skeleton className="h-48 rounded-xl" />
        <Skeleton className="lg:col-span-2 h-48 rounded-xl" />
      </div>
    </div>
  );
}

function DashboardEmpty() {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <Tray className="h-10 w-10 text-muted-foreground" />
        <div>
          <p className="text-card-foreground font-medium">Nenhum dado no período selecionado</p>
          <p className="text-muted-foreground text-sm mt-1">
            Ajuste os filtros de data ou técnico para ver o resultado da operação.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

function DashboardError({ message, onRetry }) {
  return (
    <Card className="border-destructive/40">
      <CardContent className="flex flex-col items-center justify-center gap-3 py-16 text-center">
        <WarningCircle className="h-10 w-10 text-destructive" />
        <div>
          <p className="text-card-foreground font-medium">{message}</p>
          <p className="text-muted-foreground text-sm mt-1">Verifique sua conexão e tente novamente.</p>
        </div>
        <Button variant="outline" onClick={onRetry}>
          <ArrowClockwise className="h-4 w-4" />
          Tentar novamente
        </Button>
      </CardContent>
    </Card>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tecnicos, setTecnicos] = useState([]);
  const [filters, setFilters] = useState({ startDate: "", endDate: "", tecnico: "" });

  const fetchData = async (params = {}) => {
    setLoading(true);
    try {
      const res = await dashboardApi.get(Object.fromEntries(Object.entries(params).filter(([, v]) => v)));
      if (res?.ok) {
        setData(res);
        setError(null);
      } else {
        setError("Erro ao carregar dashboard.");
        toast.error("Erro ao carregar dashboard");
      }
    } catch {
      setError("Erro ao carregar dashboard.");
      toast.error("Erro ao carregar dashboard");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    constantes.get().then((res) => {
      if (res?.ok) setTecnicos(res.tecnicos || []);
    });
  }, []);

  const handleSearch = () => fetchData(filters);

  const revenueData = data?.faturamento_por_dia?.map((item) => ({
    data: item.date,
    total: item.value,
  })) || [];

  const techData = data?.lucro_por_tecnico?.map((item) => ({
    tecnico: item.name,
    lucro: item.value,
  })) || [];

  const servicesData = data?.servicos_mais_feitos || [];

  const hasAnyData =
    revenueData.length > 0 ||
    techData.length > 0 ||
    servicesData.length > 0 ||
    Boolean(data?.faturamento_total) ||
    Boolean(data?.ordens_finalizadas) ||
    Boolean(data?.ordens_abertas) ||
    Boolean(data?.vendas?.quantidade);
  const isEmpty = Boolean(data) && !hasAnyData;

  // Dashboard somando vendas e OS (PLAN-dashboard-vendas-os.md). Backend antigo sem `vendas`
  // cai no faturamento só de OS, como antes.
  const vendas = data?.vendas;
  const faturamentoHero = data?.consolidado?.faturamento ?? data?.faturamento_total;
  const lucroAparelhos = vendas?.lucro_aparelhos;
  // Vendedor não recebe custo/lucro/resultado (PLAN-esconder-lucro-vendedor.md): sem a chave, o bloco some.
  const veCustoLucro = data?.lucro_total !== undefined;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground text-sm">Visão geral do negócio</p>
        </div>
        <div className="flex items-center gap-2 flex-wrap">
          <Input
            type="date"
            value={filters.startDate}
            onChange={(e) => setFilters((p) => ({ ...p, startDate: e.target.value }))}
            className="w-36"
          />
          <Input
            type="date"
            value={filters.endDate}
            onChange={(e) => setFilters((p) => ({ ...p, endDate: e.target.value }))}
            className="w-36"
          />
          <Select value={filters.tecnico || ""} onValueChange={(v) => setFilters((p) => ({ ...p, tecnico: v === "all" ? "" : v }))}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Técnico" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">Todos</SelectItem>
              {tecnicos.map((t) => <SelectItem key={t} value={t}>{t}</SelectItem>)}
            </SelectContent>
          </Select>
          <Button onClick={handleSearch} disabled={loading}>
            {loading ? <CircleNotch className="h-4 w-4 animate-spin" /> : "Filtrar"}
          </Button>
        </div>
      </div>

      <PendenciasHoje />

      {loading && !data ? (
        <DashboardSkeleton />
      ) : error && !data ? (
        <DashboardError message={error} onRetry={handleSearch} />
      ) : (
        <>
          {error && (
            <Card className="border-destructive/40 bg-destructive/10">
              <CardContent className="flex items-center justify-between gap-3 py-3 flex-wrap">
                <div className="flex items-center gap-2 text-sm text-card-foreground">
                  <WarningCircle className="h-4 w-4 text-destructive shrink-0" />
                  {error}
                </div>
                <Button variant="outline" size="sm" onClick={handleSearch}>
                  <ArrowClockwise className="h-4 w-4" />
                  Tentar novamente
                </Button>
              </CardContent>
            </Card>
          )}

          {isEmpty ? (
            <DashboardEmpty />
          ) : (
            <>
              {/* Métrica dominante */}
              <Panel>
                <PanelHeader>
                  <PanelTitle>Faturamento do período</PanelTitle>
                </PanelHeader>
                <PanelContent className="pt-0">
                  <p className="text-4xl sm:text-5xl font-bold text-card-foreground tracking-tight">
                    {formatCurrency(faturamentoHero)}
                  </p>
                  {vendas && (
                    <p className="text-sm text-muted-foreground mt-1" data-testid="faturamento-composicao">
                      Assistência {formatCurrency(data?.faturamento_total)} · Vendas {formatCurrency(vendas.faturamento)}
                    </p>
                  )}
                </PanelContent>
              </Panel>

              {/* Métricas soltas -- peso secundário, sem moldura */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4">
                {veCustoLucro && <LooseMetric label="Lucro Bruto" value={formatCurrency(data?.lucro_total)} />}
                <LooseMetric label="Finalizadas" value={data?.ordens_finalizadas ?? "—"} />
                <LooseMetric label="Em Aberto" value={data?.ordens_abertas ?? "—"} valueClassName="text-warning" />
                {data?.ordens_atrasadas > 0 && (
                  <LooseMetric label="OS Atrasadas" value={data.ordens_atrasadas} valueClassName="text-destructive" />
                )}
                <LooseMetric label="Peças Pendentes" value={data?.shopping_pendentes ?? "—"} />
                <LooseMetric label="Urgentes" value={data?.shopping_urgentes ?? "—"} valueClassName="text-destructive" />
                <LooseMetric label="Ticket Médio" value={formatCurrency(data?.ticket_medio)} />
                {veCustoLucro && (
                  <LooseMetric
                    label="Resultado Líq."
                    value={formatCurrency(data?.resultado_liquido)}
                    valueClassName={data?.resultado_liquido >= 0 ? "text-success" : "text-destructive"}
                  />
                )}
              </div>

              {vendas && (
                <div className="space-y-3" data-testid="dashboard-vendas">
                  <h3 className="text-sm font-medium text-card-foreground">Vendas de aparelhos</h3>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-x-6 gap-y-4">
                    <LooseMetric label="Vendas Realizadas" value={vendas.quantidade ?? "—"} />
                    <LooseMetric label="Faturamento Vendas" value={formatCurrency(vendas.faturamento)} />
                    <LooseMetric label="Ticket Médio Vendas" value={formatCurrency(vendas.ticket_medio)} />
                    {lucroAparelhos && (
                      <LooseMetric
                        label="Lucro Aparelhos"
                        value={formatCurrency(lucroAparelhos.lucro)}
                        valueClassName={lucroAparelhos.lucro >= 0 ? "text-success" : "text-destructive"}
                      />
                    )}
                  </div>
                  {vendas.por_vendedor?.length > 0 && (
                    <ListBlock>
                      {vendas.por_vendedor.slice(0, 5).map((v) => (
                        <ListBlockItem key={v.vendedor} data-testid="top-vendedor">
                          <span className="text-sm text-muted-foreground">
                            {v.vendedor} · {v.quantidade} venda(s)
                          </span>
                          <span className="text-sm font-semibold text-success">{formatCurrency(v.faturamento)}</span>
                        </ListBlockItem>
                      ))}
                    </ListBlock>
                  )}
                  {lucroAparelhos && (
                    <p className="text-xs text-muted-foreground">
                      Lucro calculado sobre {lucroAparelhos.aparelhos_com_custo} aparelho(s) com compra registrada;
                      aparelho sem custo conhecido fica fora do lucro.
                    </p>
                  )}
                </div>
              )}

              {/* Charts -- 1 principal (2/3) + 2 de apoio (1/3 cada) */}
              <Suspense fallback={<div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4"><ChartFallback /><ChartFallback /></div>}>
                <div className="grid grid-cols-1 lg:grid-cols-[2fr_1fr] gap-4">
                  <RevenueChartCard data={revenueData} />
                  {veCustoLucro && <TechnicianProfitChartCard data={techData} />}
                </div>
              </Suspense>
              <div className="grid lg:grid-cols-3 gap-4">
                <Suspense fallback={<ChartFallback />}>
                  <ServicesChartCard data={servicesData} />
                </Suspense>

                {/* Resumo Financeiro -- bloco de lista, peso secundário */}
                {veCustoLucro && <div className="lg:col-span-2">
                  <h3 className="text-sm font-medium text-card-foreground mb-2">Resumo Financeiro</h3>
                  <ListBlock>
                    {[
                      { label: "Custo de Peças", value: data?.custo_consumido_periodo, color: "text-destructive" },
                      { label: "Custos Operacionais", value: data?.custos_operacionais_periodo, color: "text-warning" },
                      { label: "Faturamento", value: data?.faturamento_total, color: "text-success" },
                      { label: "Lucro Bruto", value: data?.lucro_total, color: "text-info" },
                    ].map((item) => (
                      <ListBlockItem key={item.label}>
                        <span className="text-sm text-muted-foreground">{item.label}</span>
                        <span className={`text-sm font-semibold ${item.color}`}>{formatCurrency(item.value)}</span>
                      </ListBlockItem>
                    ))}
                  </ListBlock>
                </div>}
              </div>
            </>
          )}
        </>
      )}
    </div>
  );
}
