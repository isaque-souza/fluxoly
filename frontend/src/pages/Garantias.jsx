import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { toast } from "sonner";
import { Loader2 } from "lucide-react";
import { garantias as garantiasApi, vendas as vendasApi } from "@/api/client";
import { getOrderDisplayNumber } from "@/lib/constants";

function GarantiaBadge({ status, dias }) {
  const map = {
    vencida:   "bg-destructive/20 text-destructive border-destructive/30",
    vencendo:  "bg-warning/20 text-warning border-warning/30",
    ativa:     "bg-success/20 text-success border-success/30",
  };
  const label = status === "vencida" ? "Vencida" : status === "vencendo" ? `Vencendo (${dias}d)` : `${dias}d restantes`;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border ${map[status] || "bg-muted text-muted-foreground border-border"}`}>
      {label}
    </span>
  );
}

function formatData(value) {
  if (!value) return "—";
  const [ano, mes, dia] = String(value).slice(0, 10).split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : value;
}

function contar(lista) {
  return {
    ativa: lista.filter((g) => g.status_garantia === "ativa").length,
    vencendo: lista.filter((g) => g.status_garantia === "vencendo").length,
    vencida: lista.filter((g) => g.status_garantia === "vencida").length,
  };
}

// Painel de garantias unificado (PLAN-painel-garantias-unificado.md): aba Assistência (garantia de
// reparo, /api/garantias) + aba Vendas (garantia de venda, /api/vendas/garantias), mesma régua de
// status (vencendo = até 7 dias).
function GarantiasVendaTabela({ itens }) {
  if (itens.length === 0) {
    return (
      <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
        Nenhuma garantia de venda encontrada.
      </div>
    );
  }
  return (
    <div className="bg-card rounded-xl border border-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border">
              {["Venda", "Cliente", "Produto", "IMEI", "Garantia", "Vence em", "Status"].map((h) => (
                <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-border">
            {itens.map((g) => (
              <tr key={g.item_id} data-testid="garantia-venda" className="hover:bg-accent/30 transition-colors">
                <td className="px-4 py-3">
                  <Link to={`/vendas/${g.venda_id}`} className="font-mono text-xs text-primary hover:underline">#{g.venda_id}</Link>
                </td>
                <td className="px-4 py-3 font-medium text-card-foreground">{g.cliente_nome || "—"}</td>
                <td className="px-4 py-3 text-muted-foreground">{g.produto_nome || "—"}</td>
                <td className="px-4 py-3 font-mono text-xs text-muted-foreground">{g.imei || "—"}</td>
                <td className="px-4 py-3 text-muted-foreground text-xs">{g.garantia_nome || "—"}</td>
                <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatData(g.garantia_data_fim)}</td>
                <td className="px-4 py-3"><GarantiaBadge status={g.status_garantia} dias={g.dias_restantes} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function Garantias() {
  const [garantias, setGarantias] = useState([]);
  const [garantiasVenda, setGarantiasVenda] = useState([]);
  const [aba, setAba] = useState("assistencia");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([garantiasApi.list(), vendasApi.garantias()]).then(([res, vRes]) => {
      if (res?.ok) setGarantias(res.garantias || []);
      else toast.error("Erro ao carregar garantias");
      setGarantiasVenda(vRes?.ok ? (vRes.items || []) : []);
    }).catch(() => toast.error("Erro ao carregar garantias"))
      .finally(() => setLoading(false));
  }, []);

  const abas = [
    { id: "assistencia", label: "Assistência", lista: garantias },
    { id: "vendas", label: "Vendas", lista: garantiasVenda },
  ];
  const listaAtual = aba === "vendas" ? garantiasVenda : garantias;
  const resumo = contar(listaAtual);

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Garantias</h1>
        <p className="text-muted-foreground text-sm">Garantias de reparo e de venda, com os dias que faltam</p>
      </div>

      <div className="flex items-center gap-2 flex-wrap">
        {abas.map((a) => (
          <button
            key={a.id}
            type="button"
            onClick={() => setAba(a.id)}
            aria-pressed={aba === a.id}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-colors ${
              aba === a.id ? "bg-primary text-primary-foreground border-primary" : "bg-card text-muted-foreground border-border hover:text-foreground"
            }`}
          >
            {a.label} ({a.lista.length})
          </button>
        ))}
        {!loading && (
          <span className="text-xs text-muted-foreground ml-auto" data-testid="garantias-resumo">
            {resumo.ativa} ativas · {resumo.vencendo} vencendo · {resumo.vencida} vencidas
          </span>
        )}
      </div>

      {!loading && aba === "vendas" ? (
        <GarantiasVendaTabela itens={garantiasVenda} />
      ) : loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : garantias.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Nenhuma garantia encontrada.
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["OS", "Cliente", "Modelo", "Reparo", "Data Finalização", "Garantia"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {garantias.map((g, i) => {
                  // BR-062: uma linha por reparo -- mas ainda agrupável
                  // visualmente por OS (linhas consecutivas da mesma OS não
                  // repetem OS/Cliente/Modelo/Data, só o reparo e a garantia).
                  const mesmaOsDaAnterior = i > 0 && garantias[i - 1].id === g.id;
                  return (
                    <tr key={`${g.id}-${g.reparo_id}`} className="hover:bg-accent/30 transition-colors">
                      <td className="px-4 py-3">
                        {mesmaOsDaAnterior ? null : (
                          <Link to={`/ordens/editar/${g.id}`} className="font-mono text-xs text-primary hover:underline">
                            #{getOrderDisplayNumber(g)}
                          </Link>
                        )}
                      </td>
                      <td className="px-4 py-3 font-medium text-card-foreground">{mesmaOsDaAnterior ? "" : g.cliente}</td>
                      <td className="px-4 py-3 text-muted-foreground">{mesmaOsDaAnterior ? "" : g.modelo}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs max-w-[200px]">{g.reparos_texto || "—"}</td>
                      <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                        {mesmaOsDaAnterior ? "" : (g.data_finalizado ? new Date(g.data_finalizado).toLocaleDateString("pt-BR") : "—")}
                      </td>
                      <td className="px-4 py-3">
                        <GarantiaBadge status={g.status_garantia} dias={g.dias_restantes} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
