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
