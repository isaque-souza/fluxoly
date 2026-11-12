import { useState } from "react";
import { toast } from "sonner";
import { Loader2, Search } from "lucide-react";
import { comprasAparelhos as comprasApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatCurrency } from "@/lib/constants";

// BR-093 -- relatório mensal de compra e revenda de aparelhos:
// quanto foi investido no mês (compras + peças das OS internas), o que foi
// vendido com o lucro de cada aparelho, e o capital parado no estoque hoje.

function mesAtual() {
  const hoje = new Date();
  return `${hoje.getFullYear()}-${String(hoje.getMonth() + 1).padStart(2, "0")}`;
}

function Metrica({ label, value, className = "text-card-foreground" }) {
  return (
    <div className="bg-card border border-border rounded-xl p-4">
      <p className={`text-xl font-bold ${className}`}>{value}</p>
      <p className="text-xs text-muted-foreground mt-0.5">{label}</p>
    </div>
  );
}

const STATUS_UNIDADE = { disponivel: "Disponível", em_reparo: "Em reparo" };

// Alertas de dados (docs/engineering/plans/PLAN-alertas-dados.md): protegem a margem.
// Sem alerta nenhum, o bloco não aparece.
function AlertasDados({ alertas }) {
  const abaixo = alertas?.vendas_abaixo_do_custo || [];
  const semCusto = alertas?.aparelhos_sem_custo || { total: 0, itens: [] };
  if (abaixo.length === 0 && semCusto.total === 0) return null;

  return (
    <div className="bg-card rounded-xl border border-warning/50 overflow-hidden" data-testid="alertas-dados">
      <div className="border-b border-border px-4 py-3">
        <h2 className="text-sm font-semibold text-card-foreground">Alertas de margem</h2>
        <p className="text-xs text-muted-foreground">
          Vendas do mês abaixo do custo e aparelhos em estoque sem custo conhecido (lucro não calculável).
        </p>
      </div>
      {abaixo.length > 0 && (
        <div className="px-4 py-3 space-y-2">
          <p className="text-xs font-medium text-destructive uppercase tracking-wider">
            Vendidos abaixo do custo ({abaixo.length})
          </p>
          <ul className="divide-y divide-border">
            {abaixo.map((a) => (
              <li key={`${a.venda_id}-${a.imei}`} data-testid="alerta-abaixo-custo" className="py-2 flex flex-wrap justify-between gap-2 text-sm">
                <span className="text-card-foreground">
                  Venda #{a.venda_id} · {a.produto_nome}
                  {a.imei && <span className="text-muted-foreground font-mono"> · {a.imei}</span>}
                </span>
                <span className="text-muted-foreground">
                  vendido {formatCurrency(a.valor_venda)} · custo {formatCurrency(a.custo)}
                  {a.base_custo === "catalogo" ? " (cadastro)" : " (compra)"} ·{" "}
                  <span className="text-destructive font-medium">−{formatCurrency(a.prejuizo)}</span>
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
      {semCusto.total > 0 && (
        <div className="px-4 py-3 space-y-2 border-t border-border">
          <p className="text-xs font-medium text-warning uppercase tracking-wider">
            Aparelhos em estoque sem custo ({semCusto.total})
          </p>
          <ul className="divide-y divide-border">
            {semCusto.itens.map((u) => (
              <li key={u.unidade_serializada_id} data-testid="alerta-sem-custo" className="py-2 flex justify-between gap-2 text-sm">
                <span className="text-card-foreground">
                  {u.produto_nome || "Aparelho"}
                  {u.imei && <span className="text-muted-foreground font-mono"> · {u.imei}</span>}
                </span>
                <span className="text-muted-foreground">{STATUS_UNIDADE[u.status] || u.status}</span>
              </li>
            ))}
          </ul>
          {semCusto.total > semCusto.itens.length && (
            <p className="text-xs text-muted-foreground">
              Mostrando {semCusto.itens.length} de {semCusto.total}. Cadastre o custo no produto ou registre a compra.
            </p>
          )}
        </div>
      )}
    </div>
  );
}

export default function CompraRevendaReport() {
  const [mes, setMes] = useState(mesAtual);
  const [loading, setLoading] = useState(false);
  const [relatorio, setRelatorio] = useState(null);

  const gerar = async () => {
    if (!mes) {
      toast.error("Escolha o mês do relatório.");
      return;
    }
    setLoading(true);
    setRelatorio(null);
    try {
      const res = await comprasApi.relatorio(mes);
      if (res?.ok) setRelatorio(res.relatorio);
      else toast.error(res?.erro || "Erro ao gerar relatório");
    } catch {
      toast.error("Erro ao gerar relatório");
    } finally {
      setLoading(false);
    }
  };

  const lucro = relatorio?.vendas?.lucro ?? 0;

  return (
    <div className="space-y-4">
      <div className="bg-card border border-border rounded-xl p-4 flex flex-wrap items-end gap-3">
        <div className="space-y-1.5">
          <label htmlFor="relatorio-compra-mes" className="text-xs text-muted-foreground">Mês</label>
          <Input id="relatorio-compra-mes" type="month" value={mes} onChange={(e) => setMes(e.target.value)} className="w-44" />
        </div>
        <Button onClick={gerar} disabled={loading}>
          {loading ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <Search className="h-4 w-4 mr-2" />}
          Gerar Relatório
        </Button>
      </div>

      {loading && (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      )}

      {relatorio && (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Metrica label={`Aparelhos comprados (${relatorio.compras.quantidade})`} value={formatCurrency(relatorio.compras.total_pago)} />
            <Metrica label="Peças das OS internas" value={formatCurrency(relatorio.pecas_os_internas)} />
            <Metrica label="Total investido no mês" value={formatCurrency(relatorio.total_investido)} className="text-destructive" />
            <Metrica
              label={`Lucro das vendas (${relatorio.vendas.quantidade})`}
              value={formatCurrency(lucro)}
              className={lucro < 0 ? "text-destructive" : "text-success"}
            />
          </div>

          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
            <Metrica label="Vendido no mês" value={formatCurrency(relatorio.vendas.total_vendido)} />
            <Metrica label="Custo do que foi vendido" value={formatCurrency(relatorio.vendas.custo_total)} />
            <Metrica
              label={`No estoque hoje (${relatorio.estoque_atual.em_reparo} em reparo · ${relatorio.estoque_atual.disponiveis} disponíveis)`}
              value={relatorio.estoque_atual.quantidade}
            />
            <Metrica label="Capital parado no estoque" value={formatCurrency(relatorio.estoque_atual.capital_parado)} />
          </div>

          <AlertasDados alertas={relatorio.alertas} />

          <div className="bg-card rounded-xl border border-border overflow-hidden">
            <div className="border-b border-border px-4 py-3">
              <h2 className="text-sm font-semibold text-card-foreground">Aparelhos comprados vendidos no mês</h2>
              <p className="text-xs text-muted-foreground">Custo = valor da compra + peças das OS internas.</p>
            </div>
            {relatorio.vendas.itens.length === 0 ? (
              <p className="px-4 py-6 text-sm text-muted-foreground">Nenhum aparelho comprado foi vendido neste mês.</p>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      {["Venda", "Data", "Aparelho", "IMEI", "Vendido por", "Compra", "Peças", "Custo", "Lucro"].map((h) => (
                        <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border">
                    {relatorio.vendas.itens.map((item) => (
                      <tr key={item.venda_id} className="hover:bg-accent/30">
                        <td className="px-4 py-3 text-muted-foreground">#{item.venda_id}</td>
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">
                          {item.vendido_em ? new Date(item.vendido_em).toLocaleDateString("pt-BR") : "—"}
                        </td>
                        <td className="px-4 py-3 font-medium text-card-foreground">{item.produto_nome}</td>
                        <td className="px-4 py-3 text-muted-foreground font-mono">{item.imei || "—"}</td>
                        <td className="px-4 py-3 text-card-foreground whitespace-nowrap">{formatCurrency(item.valor_venda)}</td>
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatCurrency(item.valor_compra)}</td>
                        <td className="px-4 py-3 text-muted-foreground whitespace-nowrap">{formatCurrency(item.custo_pecas)}</td>
                        <td className="px-4 py-3 text-destructive whitespace-nowrap">{formatCurrency(item.custo_total)}</td>
                        <td className={`px-4 py-3 font-medium whitespace-nowrap ${item.lucro < 0 ? "text-destructive" : "text-success"}`}>
                          {formatCurrency(item.lucro)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
