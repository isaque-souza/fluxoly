import { useState } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Loader2, Search, FileDown, Lock, HardDriveDownload } from "lucide-react";
import { relatorios as relatoriosApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/constants";

const TABS = [
  { key: "tecnicos", label: "Técnicos" },
  { key: "custos", label: "Custos Operacionais" },
];

function formatMonthLabel(key) {
  if (!key || typeof key !== "string") return "Período";
  const [year, month] = key.split("-");
  const months = {
    "01": "Jan",
    "02": "Fev",
    "03": "Mar",
    "04": "Abr",
    "05": "Mai",
    "06": "Jun",
    "07": "Jul",
    "08": "Ago",
    "09": "Set",
    "10": "Out",
    "11": "Nov",
    "12": "Dez",
  };
  return `${months[month] || month}/${year}`;
}

export default function Reports() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("tecnicos");
  const [startDate, setStartDate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const isAdmin = user?.perfil === "admin";
  const monthlyRows = Object.entries(results?.meses || {});
  const categoriasRows = Object.entries(results?.categorias || {});

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente administradores podem acessar relatórios.</p>
      </div>
    );
  }

  const handleSearch = async () => {
    setLoading(true);
    setResults(null);
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      const fn = activeTab === "tecnicos"
        ? relatoriosApi.tecnicos
        : relatoriosApi.custosOperacionais;
      const res = await fn(params);
      if (res?.ok) setResults(res);
      else toast.error(res?.erro || "Erro ao gerar relatório");
    } catch {
      toast.error("Erro ao gerar relatório");
    } finally {
      setLoading(false);
    }
  };

  const handleExportPdf = async () => {
    try {
      const params = {};
      if (startDate) params.start_date = startDate;
      if (endDate) params.end_date = endDate;
      
      const tipoMap = {
        tecnicos: "tecnicos",
        custos: "custos",
      };
      
      const fileName = `relatorio-${activeTab}-${startDate || "inicio"}-${endDate || "fim"}.pdf`;
      
      await relatoriosApi.downloadPdf(tipoMap[activeTab], params, fileName);
      toast.success("PDF exportado com sucesso!");
    } catch (error) {
      toast.error("Erro ao exportar PDF: " + (error.message || "Tente novamente"));
    }
  };

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Relatórios</h1>
        <p className="text-muted-foreground text-sm">Geração de relatórios e análises</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => { setActiveTab(tab.key); setResults(null); }}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key
                ? "bg-card text-card-foreground shadow"
                : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filters */}
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Data Inicial</label>
          <Input type="date" value={startDate} onChange={(e) => setStartDate(e.target.value)} className="w-36" />
        </div>
        <div className="space-y-1.5">
          <label className="text-xs text-muted-foreground">Data Final</label>
          <Input type="date" value={endDate} onChange={(e) => setEndDate(e.target.value)} className="w-36" />
        </div>
        <Button onClick={handleSearch} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
          Gerar Relatório
        </Button>
        <Link to="/backup">
          <Button variant="outline">
            <HardDriveDownload className="h-4 w-4 mr-2" />Backups
          </Button>
        </Link>
        {results && (
          <Button variant="outline" onClick={handleExportPdf}>
            <FileDown className="h-4 w-4 mr-2" />Exportar PDF
          </Button>
        )}
      </div>

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      )}

      {results && activeTab === "tecnicos" && (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Mês", "Técnico", "OS Finalizadas", "Faturamento", "Gasto Peças", "Lucro"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {monthlyRows.flatMap(([month, tecnicos]) =>
                  Object.entries(tecnicos || {}).map(([tecnico, summary]) => (
                    <tr key={`${month}-${tecnico}`} className="hover:bg-accent/30">
                      <td className="px-4 py-3 text-muted-foreground">{formatMonthLabel(month)}</td>
                      <td className="px-4 py-3 font-medium text-card-foreground">{tecnico}</td>
                      <td className="px-4 py-3 text-muted-foreground">{summary.total_os}</td>
                      <td className="px-4 py-3 text-card-foreground font-medium">{formatCurrency(summary.faturamento)}</td>
                      <td className="px-4 py-3 text-destructive">{formatCurrency(summary.gastos)}</td>
                      <td className="px-4 py-3 text-success font-medium">{formatCurrency(summary.lucro)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {results && activeTab === "custos" && (
        <div className="space-y-4">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            {[
              { label: "Lançamentos", value: results.total_lancamentos ?? 0 },
              { label: "Custo Total", value: formatCurrency(results.total_custos) },
              { label: "Meses", value: monthlyRows.length },
              { label: "Média por lançamento", value: results.total_lancamentos ? formatCurrency((results.total_custos || 0) / results.total_lancamentos) : formatCurrency(0) },
            ].map((s) => (
              <div key={s.label} className="bg-card border border-border rounded-xl p-4">
                <p className="text-xl font-bold text-card-foreground">{s.value}</p>
                <p className="text-xs text-muted-foreground mt-0.5">{s.label}</p>
              </div>
            ))}
          </div>

          <div className="grid gap-4 xl:grid-cols-[minmax(0,2fr)_minmax(260px,1fr)]">
            <div className="bg-card rounded-xl border border-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {["Mês", "Lançamentos", "Total", "Principais Categorias"].map((h) => (
                        <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {monthlyRows.map(([month, summary]) => (
                      <tr key={month} className="hover:bg-accent/30">
                        <td className="px-4 py-3 font-medium text-card-foreground">{formatMonthLabel(month)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{summary.total_itens}</td>
                        <td className="px-4 py-3 text-destructive font-medium">{formatCurrency(summary.total_valor)}</td>
                        <td className="px-4 py-3 text-muted-foreground">
                          {Object.entries(summary.categorias || {})
                            .slice(0, 3)
                            .map(([name, value]) => `${name} (${formatCurrency(value)})`)
                            .join(", ") || "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-4">
              <p className="text-sm font-semibold text-card-foreground">Categorias no período</p>
              <div className="mt-3 space-y-2">
                {categoriasRows.length === 0 ? (
                  <p className="text-sm text-muted-foreground">Nenhum custo no período.</p>
                ) : (
                  categoriasRows.map(([categoria, valor]) => (
                    <div key={categoria} className="flex items-center justify-between gap-3 rounded-lg bg-secondary/50 px-3 py-2">
                      <span className="text-sm text-card-foreground">{categoria}</span>
                      <span className="text-sm font-medium text-destructive">{formatCurrency(valor)}</span>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold text-card-foreground">Lançamentos Individuais</h2>
              <p className="text-xs text-muted-foreground">Todos os custos do período filtrado.</p>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    {["Data", "Mês", "Descrição", "Categoria", "Valor", "Observações"].map((h) => (
                      <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {monthlyRows.flatMap(([month, summary]) =>
                    (summary.itens || []).map((item) => (
                      <tr key={item.id} className="hover:bg-accent/30">
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{item.data ? new Date(item.data).toLocaleDateString("pt-BR") : "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatMonthLabel(month)}</td>
                        <td className="px-4 py-3 font-medium text-card-foreground">{item.descricao || "—"}</td>
                        <td className="px-4 py-3 text-muted-foreground">{item.categoria || "Outros"}</td>
                        <td className="px-4 py-3 text-destructive font-medium whitespace-nowrap">{formatCurrency(item.valor)}</td>
                        <td className="px-4 py-3 text-muted-foreground">{item.observacoes || "—"}</td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
