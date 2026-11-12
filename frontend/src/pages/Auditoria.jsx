import { useState, useEffect } from "react";
import { CaretLeft, CaretRight } from "@phosphor-icons/react";
import { auditoria as auditoriaApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { FilterBar, FilterSelect, FilterInput, DateRangeFilter, ClearFiltersButton } from "@/components/ui/filter-bar";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";

// Tela de Auditoria -- leitura do audit_log (docs/engineering/plans/PLAN-tela-auditoria.md).
// Só consulta: não existe ação de editar/apagar. Acesso admin/financeiro (gate no backend e no menu).

const ACAO_LABEL = { create: "Criou", update: "Alterou", delete: "Excluiu", status_change: "Mudou status" };
const ACAO_VARIANT = { create: "success", update: "info", delete: "error", status_change: "warning" };

const ENTIDADE_LABEL = {
  cliente: "Cliente",
  compra_aparelho: "Compra de aparelho",
  conta_pagar: "Conta a pagar",
  conta_receber: "Conta a receber",
  dados_loja: "Dados da loja",
  estoque_unidade: "Unidade (legado)",
  movimentacao_caixa: "Caixa",
  os_reparo: "Reparo da OS",
  produto: "Produto",
  unidade_serializada: "Unidade / IMEI",
  venda: "Venda",
  venda_item: "Item de venda",
};

const POR_PAGINA = 50;

export function entidadeLabel(entidade) {
  return ENTIDADE_LABEL[entidade] || entidade;
}

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${(hora || "").slice(0, 5)}`.trim() : value;
}

function formatValor(valor) {
  if (valor === null || valor === undefined || valor === "") return "—";
  if (typeof valor === "object") return JSON.stringify(valor);
  return String(valor);
}

function DetalheRegistro({ registro, onClose }) {
  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {ACAO_LABEL[registro.acao] || registro.acao} · {entidadeLabel(registro.entidade)} #{registro.entidade_id ?? "—"}
          </DialogTitle>
          <DialogDescription>
            {formatDateTime(registro.criado_em)} · {registro.usuario_nome || "Sistema"}
          </DialogDescription>
        </DialogHeader>

        {registro.alteracoes.length === 0 ? (
          <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">
            Nenhuma diferença campo a campo registrada.
          </p>
        ) : (
          <table className="w-full text-sm" data-testid="auditoria-diff">
            <thead>
              <tr className="border-b border-border">
                {["Campo", "Antes", "Depois"].map((h) => (
                  <th key={h} className="text-left px-3 py-2 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {registro.alteracoes.map((a) => (
                <tr key={a.campo}>
                  <td className="px-3 py-2 font-mono text-xs text-card-foreground">{a.campo}</td>
                  <td className="px-3 py-2 text-destructive break-all">{formatValor(a.antes)}</td>
                  <td className="px-3 py-2 text-success break-all">{formatValor(a.depois)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        <DialogFooter className="mt-4">
          <Button type="button" variant="outline" onClick={onClose}>Fechar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Auditoria() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [entidades, setEntidades] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [page, setPage] = useState(1);
  const [filtros, setFiltros] = useState({ entidade: "", acao: "", entidade_id: "", data_inicio: "", data_fim: "" });
  const [selecionado, setSelecionado] = useState(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let ativo = true;

    async function buscar() {
      setLoading(true);
      setLoadError(false);
      const params = { page, per_page: POR_PAGINA };
      Object.entries(filtros).forEach(([k, v]) => { if (v) params[k] = v; });
      try {
        const res = await auditoriaApi.list(params);
        if (!ativo) return;
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
          setEntidades(res.entidades || []);
        } else {
          setLoadError(true);
        }
      } catch {
        if (ativo) setLoadError(true);
      } finally {
        if (ativo) setLoading(false);
      }
    }

    buscar();
    return () => { ativo = false; };
  }, [page, filtros, reload]);

  const setFiltro = (campo, valor) => {
    setPage(1);
    setFiltros((f) => ({ ...f, [campo]: valor }));
  };
  const limpar = () => {
    setPage(1);
    setFiltros({ entidade: "", acao: "", entidade_id: "", data_inicio: "", data_fim: "" });
  };
  const totalPaginas = Math.max(1, Math.ceil(total / POR_PAGINA));

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Auditoria</h1>
        <p className="text-muted-foreground text-sm">Quem criou, alterou ou excluiu cada registro — com o antes e o depois</p>
      </div>

      <FilterBar>
        <FilterSelect
          value={filtros.entidade || "all"}
          onValueChange={(v) => setFiltro("entidade", v === "all" ? "" : v)}
          placeholder="Módulo"
          options={[{ value: "all", label: "Todos os módulos" }, ...entidades.map((e) => ({ value: e, label: entidadeLabel(e) }))]}
        />
        <FilterSelect
          value={filtros.acao || "all"}
          onValueChange={(v) => setFiltro("acao", v === "all" ? "" : v)}
          placeholder="Ação"
          options={[{ value: "all", label: "Todas as ações" }, ...Object.entries(ACAO_LABEL).map(([value, label]) => ({ value, label }))]}
        />
        <FilterInput
          placeholder="Nº do registro"
          inputMode="numeric"
          value={filtros.entidade_id}
          onChange={(e) => setFiltro("entidade_id", e.target.value.replace(/\D/g, ""))}
          className="w-36"
        />
        <DateRangeFilter
          startValue={filtros.data_inicio}
          endValue={filtros.data_fim}
          onStartChange={(v) => setFiltro("data_inicio", v)}
          onEndChange={(v) => setFiltro("data_fim", v)}
        />
        <ClearFiltersButton onClear={limpar} />
      </FilterBar>

      {loading ? (
        <ListSkeleton />
      ) : loadError ? (
        <ErrorState title="Não foi possível carregar a auditoria." onRetry={() => setReload((r) => r + 1)} />
      ) : items.length === 0 ? (
        <EmptyState title="Nenhum registro de auditoria encontrado." />
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Data", "Usuário", "Ação", "Módulo", "Registro", "Campos"].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {items.map((r) => (
                  <tr
                    key={r.id}
                    data-testid="auditoria-linha"
                    className="hover:bg-accent/30 transition-colors cursor-pointer"
                    onClick={() => setSelecionado(r)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">{formatDateTime(r.criado_em)}</td>
                    <td className="px-4 py-3 text-card-foreground">{r.usuario_nome || "Sistema"}</td>
                    <td className="px-4 py-3"><Badge variant={ACAO_VARIANT[r.acao] || "neutral"}>{ACAO_LABEL[r.acao] || r.acao}</Badge></td>
                    <td className="px-4 py-3 text-card-foreground">{entidadeLabel(r.entidade)}</td>
                    <td className="px-4 py-3 font-mono text-xs">#{r.entidade_id ?? "—"}</td>
                    <td className="px-4 py-3 text-muted-foreground text-xs">
                      {r.alteracoes.map((a) => a.campo).slice(0, 4).join(", ") || "—"}
                      {r.alteracoes.length > 4 && ` +${r.alteracoes.length - 4}`}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="flex items-center justify-between px-4 py-3 border-t border-border text-sm text-muted-foreground">
            <span>{total} registro(s)</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)} aria-label="Página anterior">
                <CaretLeft className="h-4 w-4" />
              </Button>
              <span>{page} / {totalPaginas}</span>
              <Button variant="outline" size="sm" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)} aria-label="Próxima página">
                <CaretRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      )}

      {selecionado && <DetalheRegistro registro={selecionado} onClose={() => setSelecionado(null)} />}
    </div>
  );
}
