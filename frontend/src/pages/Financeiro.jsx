import { useState, useEffect, useCallback } from "react";
import { toast } from "sonner";
import {
  CircleNotch, Lock, Plus, ArrowCounterClockwise, XCircle, Pencil, Trash,
  CaretLeft, CaretRight, ArrowCircleDown, ArrowCircleUp,
} from "@phosphor-icons/react";
import { caixa as caixaApi, contasPagar as contasPagarApi, contasReceber as contasReceberApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle } from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Reveal } from "@/components/ui/reveal";
import { FilterBar, FilterSelect, FilterInput } from "@/components/ui/filter-bar";
import { DataTable } from "@/components/ui/data-table";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { formatCurrency } from "@/lib/constants";

const PER_PAGE = 20;

// TIPO_BADGE/STATUS_CONTA_BADGE -- status genuíno (não categórico), migrado
// para o Badge semântico da Foundation no PR 5. Vocábulo local a este
// arquivo (mesmo critério de Stock.jsx/UnidadesSerializadas.jsx).
const TIPO_LABEL = { entrada: "Entrada", saida: "Saída" };

function tipoVariant(tipo) {
  return tipo === "entrada" ? "success" : "error";
}

const ORIGEM_LABEL = {
  manual: "Manual",
  venda: "Venda",
  conta_pagar: "Conta a Pagar",
  conta_receber: "Conta a Receber",
  compra_aparelho: "Compra de aparelho",
};

const STATUS_CONTA_LABEL = {
  pendente: "Pendente",
  pago: "Pago",
  recebido: "Recebido",
  cancelado: "Cancelado",
};

function statusContaVariant(status) {
  if (status === "pendente") return "warning";
  if (status === "pago" || status === "recebido") return "success";
  return "neutral";
}

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

function formatData(value) {
  if (!value) return "—";
  const [ano, mes, dia] = value.split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : value;
}

const EMPTY_MOVIMENTACAO = { tipo: "entrada", valor: "", descricao: "" };

function Movimentacoes({ onMutate }) {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [tipoFilter, setTipoFilter] = useState("");
  const [origemFilter, setOrigemFilter] = useState("");
  const [dataInicio, setDataInicio] = useState("");
  const [dataFim, setDataFim] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_MOVIMENTACAO);
  const [submitting, setSubmitting] = useState(false);
  const [estornarId, setEstornarId] = useState(null);
  const [estornando, setEstornando] = useState(false);

  const buscar = useCallback(() => {
    setLoading(true);
    setErro(false);
    const params = { page, per_page: PER_PAGE };
    if (tipoFilter) params.tipo = tipoFilter;
    if (origemFilter) params.origem = origemFilter;
    if (dataInicio) params.data_inicio = dataInicio;
    if (dataFim) params.data_fim = dataFim;

    caixaApi.list(params)
      .then((res) => {
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          setErro(true);
          toast.error(res?.erro || "Erro ao carregar movimentações");
        }
      })
      .catch(() => {
        setErro(true);
        toast.error("Erro ao carregar movimentações");
      })
      .finally(() => setLoading(false));
  }, [page, tipoFilter, origemFilter, dataInicio, dataFim]);

  useEffect(() => { buscar(); }, [buscar]);

  const handleFiltro = (setter) => (v) => { setter(v === "all" ? "" : v); setPage(1); };

  const openCreate = () => {
    setForm(EMPTY_MOVIMENTACAO);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valor);
    if (!valor || valor <= 0) {
      toast.error("Informe um valor válido.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await caixaApi.create({ tipo: form.tipo, valor, descricao: form.descricao });
      if (res?.ok) {
        toast.success("Movimentação lançada!");
        setDialogOpen(false);
        buscar();
        onMutate();
      } else {
        toast.error(res?.erro || "Erro ao lançar movimentação");
      }
    } catch {
      toast.error("Erro ao lançar movimentação");
    } finally {
      setSubmitting(false);
    }
  };

  const handleEstornar = async () => {
    setEstornando(true);
    try {
      const res = await caixaApi.estornar(estornarId);
      if (res?.ok) {
        toast.success("Movimentação estornada");
        buscar();
        onMutate();
      } else {
        toast.error(res?.erro || "Erro ao estornar");
      }
    } catch {
      toast.error("Erro ao estornar");
    } finally {
      setEstornando(false);
      setEstornarId(null);
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));

  return (
    <div className="space-y-4">
      {loading ? (
        <ListSkeleton rows={6} />
      ) : erro ? (
        <ErrorState title="Não foi possível carregar as movimentações." onRetry={buscar} />
      ) : (
        <Reveal className="space-y-4">
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <FilterSelect
              value={tipoFilter || "all"}
              onValueChange={handleFiltro(setTipoFilter)}
              placeholder="Tipo"
              options={[{ value: "all", label: "Todos os tipos" }, { value: "entrada", label: "Entrada" }, { value: "saida", label: "Saída" }]}
            />
            <FilterSelect
              value={origemFilter || "all"}
              onValueChange={handleFiltro(setOrigemFilter)}
              placeholder="Origem"
              className="w-44"
              options={[{ value: "all", label: "Todas as origens" }, ...Object.entries(ORIGEM_LABEL).map(([v, label]) => ({ value: v, label }))]}
            />
            <FilterInput type="date" value={dataInicio} onChange={(e) => { setDataInicio(e.target.value); setPage(1); }} className="w-40" aria-label="Data inicial" />
            <FilterInput type="date" value={dataFim} onChange={(e) => { setDataFim(e.target.value); setPage(1); }} className="w-40" aria-label="Data final" />
            <Button className="ml-auto" onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Lançar</Button>
          </FilterBar>

          {items.length === 0 ? (
            <EmptyState title="Nenhuma movimentação encontrada." />
          ) : (
            <>
              <DataTable
                columns={[
                  {
                    key: "criado_em",
                    header: "Data",
                    className: "text-muted-foreground whitespace-nowrap",
                    render: (m) => formatDateTime(m.criado_em),
                  },
                  {
                    key: "tipo",
                    header: "Tipo",
                    render: (m) => <Badge variant={tipoVariant(m.tipo)}>{TIPO_LABEL[m.tipo] || m.tipo}</Badge>,
                  },
                  {
                    key: "valor",
                    header: "Valor",
                    className: "font-medium text-card-foreground whitespace-nowrap",
                    render: (m) => formatCurrency(m.valor),
                  },
                  { key: "descricao", header: "Descrição", className: "text-muted-foreground", render: (m) => m.descricao || "—" },
                  {
                    key: "origem",
                    header: "Origem",
                    className: "text-muted-foreground",
                    render: (m) => ORIGEM_LABEL[m.origem] || m.origem,
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (m) => m.estornada ? (
                      <span className="text-xs text-muted-foreground">Estornada</span>
                    ) : (
                      <span className="text-xs text-success">Ativa</span>
                    ),
                  },
                  {
                    key: "acoes",
                    header: "",
                    render: (m) => !m.estornada && m.origem === "manual" && (
                      <Button variant="ghost" size="icon" className="h-7 w-7" title="Estornar" onClick={() => setEstornarId(m.id)}>
                        <ArrowCounterClockwise className="h-3.5 w-3.5" />
                      </Button>
                    ),
                  },
                ]}
                rows={items}
                getRowKey={(m) => m.id}
              />

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "movimentação" : "movimentações"}</span>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                    <CaretLeft className="h-4 w-4 mr-1" /> Anterior
                  </Button>
                  <Button variant="outline" size="sm" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)}>
                    Próxima <CaretRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </Reveal>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>Nova Movimentação</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Tipo *</Label>
              <Select value={form.tipo} onValueChange={(v) => setForm((p) => ({ ...p, tipo: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="entrada">Entrada</SelectItem>
                  <SelectItem value="saida">Saída</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>Valor (R$) *</Label>
              <Input type="number" step="0.01" min="0.01" value={form.valor} onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} required />
            </div>
            <div className="space-y-1.5">
              <Label>Descrição</Label>
              <Textarea value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} />
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>{submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}Lançar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!estornarId} onOpenChange={(open) => !open && setEstornarId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Estornar movimentação?</AlertDialogTitle>
            <AlertDialogDescription>
              A movimentação permanece no histórico, mas deixa de contar no saldo. Esta ação não pode ser desfeita.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleEstornar} disabled={estornando} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {estornando && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}Estornar
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

const EMPTY_CONTA = { descricao: "", categoria: "", valor: "", data_vencimento: "" };

const CONTAS_CONFIG = {
  pagar: {
    api: contasPagarApi,
    titulo: "Conta a Pagar",
    statusQuitado: "pago",
    acaoLabel: "Pagar",
    acaoIcon: ArrowCircleUp,
    acaoFn: (api, id) => api.pagar(id),
    vazio: "Nenhuma conta a pagar cadastrada.",
  },
  receber: {
    api: contasReceberApi,
    titulo: "Conta a Receber",
    statusQuitado: "recebido",
    acaoLabel: "Receber",
    acaoIcon: ArrowCircleDown,
    acaoFn: (api, id) => api.receber(id),
    vazio: "Nenhuma conta a receber cadastrada.",
  },
};

function ContasTab({ dominio, onMutate }) {
  const cfg = CONTAS_CONFIG[dominio];
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [statusFilter, setStatusFilter] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_CONTA);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [acaoId, setAcaoId] = useState(null);
  const [cancelarId, setCancelarId] = useState(null);
  const [processando, setProcessando] = useState(false);

  const buscar = useCallback(() => {
    setLoading(true);
    setErro(false);
    const params = { page, per_page: PER_PAGE };
    if (statusFilter) params.status = statusFilter;

    cfg.api.list(params)
      .then((res) => {
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          setErro(true);
          toast.error(res?.erro || `Erro ao carregar ${cfg.titulo.toLowerCase()}s`);
        }
      })
      .catch(() => {
        setErro(true);
        toast.error(`Erro ao carregar ${cfg.titulo.toLowerCase()}s`);
      })
      .finally(() => setLoading(false));
  }, [cfg, page, statusFilter]);

  useEffect(() => { buscar(); }, [buscar]);

  const openCreate = () => {
    setForm(EMPTY_CONTA);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (c) => {
    setForm({
      descricao: c.descricao || "",
      categoria: c.categoria || "",
      valor: c.valor ?? "",
      data_vencimento: c.data_vencimento || "",
    });
    setEditId(c.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valor);
    if (!form.descricao.trim()) {
      toast.error("Informe a descrição.");
      return;
    }
    if (!valor || valor <= 0) {
      toast.error("Informe um valor válido.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = { ...form, valor };
      const res = editId ? await cfg.api.update(editId, payload) : await cfg.api.create(payload);
      if (res?.ok) {
        toast.success(editId ? `${cfg.titulo} atualizada!` : `${cfg.titulo} criada!`);
        setDialogOpen(false);
        buscar();
      } else {
        toast.error(res?.erro || "Erro ao salvar");
      }
    } catch {
      toast.error("Erro ao salvar");
    } finally {
      setSubmitting(false);
    }
  };

  const handleAcao = async () => {
    setProcessando(true);
    try {
      const res = await cfg.acaoFn(cfg.api, acaoId);
      if (res?.ok) {
        toast.success(`${cfg.titulo} marcada como ${cfg.statusQuitado}!`);
        buscar();
        onMutate();
      } else {
        toast.error(res?.erro || "Erro ao processar");
      }
    } catch {
      toast.error("Erro ao processar");
    } finally {
      setProcessando(false);
      setAcaoId(null);
    }
  };

  const handleCancelar = async () => {
    setProcessando(true);
    try {
      const res = await cfg.api.cancelar(cancelarId);
      if (res?.ok) {
        toast.success(`${cfg.titulo} cancelada`);
        buscar();
      } else {
        toast.error(res?.erro || "Erro ao cancelar");
      }
    } catch {
      toast.error("Erro ao cancelar");
    } finally {
      setProcessando(false);
      setCancelarId(null);
    }
  };

  const handleDelete = async () => {
    try {
      const res = await cfg.api.delete(deleteId);
      if (res?.ok) {
        toast.success(`${cfg.titulo} excluída`);
        buscar();
      } else {
        toast.error(res?.erro || "Erro ao excluir");
      }
    } catch {
      toast.error("Erro ao excluir");
    } finally {
      setDeleteId(null);
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));
  const AcaoIcon = cfg.acaoIcon;

  return (
    <div className="space-y-4">
      {loading ? (
        <ListSkeleton rows={6} />
      ) : erro ? (
        <ErrorState title={`Não foi possível carregar ${cfg.titulo.toLowerCase()}s.`} onRetry={buscar} />
      ) : (
        <Reveal className="space-y-4">
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <FilterSelect
              value={statusFilter || "all"}
              onValueChange={(v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); }}
              placeholder="Status"
              className="w-44"
              options={[
                { value: "all", label: "Todos os status" },
                { value: "pendente", label: "Pendente" },
                { value: cfg.statusQuitado, label: STATUS_CONTA_LABEL[cfg.statusQuitado] },
                { value: "cancelado", label: "Cancelado" },
              ]}
            />
            <Button className="ml-auto" onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Nova {cfg.titulo}</Button>
          </FilterBar>

          {items.length === 0 ? (
            <EmptyState title={cfg.vazio} />
          ) : (
            <>
              <DataTable
                columns={[
                  { key: "descricao", header: "Descrição", className: "font-medium text-card-foreground" },
                  { key: "categoria", header: "Categoria", className: "text-muted-foreground", render: (c) => c.categoria || "—" },
                  {
                    key: "valor",
                    header: "Valor",
                    className: "font-medium text-card-foreground whitespace-nowrap",
                    render: (c) => formatCurrency(c.valor),
                  },
                  {
                    key: "data_vencimento",
                    header: "Vencimento",
                    className: "text-muted-foreground whitespace-nowrap",
                    render: (c) => formatData(c.data_vencimento),
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (c) => <Badge variant={statusContaVariant(c.status)}>{STATUS_CONTA_LABEL[c.status] || c.status}</Badge>,
                  },
                  {
                    key: "acoes",
                    header: "",
                    render: (c) => c.status === "pendente" && (
                      <div className="flex items-center gap-1 justify-end">
                        <Button variant="ghost" size="icon" className="h-7 w-7" title={cfg.acaoLabel} onClick={() => setAcaoId(c.id)}>
                          <AcaoIcon className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7" title="Editar" onClick={() => openEdit(c)}>
                          <Pencil className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7" title="Cancelar" onClick={() => setCancelarId(c.id)}>
                          <XCircle className="h-3.5 w-3.5" />
                        </Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" title="Excluir" onClick={() => setDeleteId(c.id)}>
                          <Trash className="h-3.5 w-3.5" />
                        </Button>
                      </div>
                    ),
                  },
                ]}
                rows={items}
                getRowKey={(c) => c.id}
              />

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "conta" : "contas"}</span>
                <div className="flex items-center gap-2">
                  <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                    <CaretLeft className="h-4 w-4 mr-1" /> Anterior
                  </Button>
                  <Button variant="outline" size="sm" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)}>
                    Próxima <CaretRight className="h-4 w-4 ml-1" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </Reveal>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader><DialogTitle>{editId ? `Editar ${cfg.titulo}` : `Nova ${cfg.titulo}`}</DialogTitle></DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Descrição *</Label>
              <Input value={form.descricao} onChange={(e) => setForm((p) => ({ ...p, descricao: e.target.value }))} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Categoria</Label>
                <Input value={form.categoria} onChange={(e) => setForm((p) => ({ ...p, categoria: e.target.value }))} />
              </div>
              <div className="space-y-1.5">
                <Label>Valor (R$) *</Label>
                <Input type="number" step="0.01" min="0.01" value={form.valor} onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} required />
              </div>
              <div className="space-y-1.5 col-span-2">
                <Label>Vencimento</Label>
                <Input type="date" value={form.data_vencimento} onChange={(e) => setForm((p) => ({ ...p, data_vencimento: e.target.value }))} />
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>{submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}Salvar</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      <AlertDialog open={!!acaoId} onOpenChange={(open) => !open && setAcaoId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>{cfg.acaoLabel} esta conta?</AlertDialogTitle>
            <AlertDialogDescription>
              Isso gera uma {cfg.statusQuitado === "pago" ? "saída" : "entrada"} de caixa correspondente e não pode ser desfeito.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction onClick={handleAcao} disabled={processando}>
              {processando && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}{cfg.acaoLabel}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!cancelarId} onOpenChange={(open) => !open && setCancelarId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar esta conta?</AlertDialogTitle>
            <AlertDialogDescription>A conta fica marcada como cancelada e não pode mais ser paga/recebida.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction onClick={handleCancelar} disabled={processando} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              {processando && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}Cancelar conta
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Excluir {cfg.titulo}?</AlertDialogTitle>
            <AlertDialogDescription>Esta ação não pode ser desfeita.</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">Excluir</AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}

const TABS = [
  { key: "movimentacoes", label: "Movimentações" },
  { key: "contas-pagar", label: "Contas a Pagar" },
  { key: "contas-receber", label: "Contas a Receber" },
];

export default function Financeiro() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState("movimentacoes");
  const [saldo, setSaldo] = useState(null);
  const [saldoLoading, setSaldoLoading] = useState(true);
  const [saldoRefreshKey, setSaldoRefreshKey] = useState(0);

  const podeAcessar = user?.perfil === "admin" || user?.perfil === "financeiro";
  const carregarSaldo = () => setSaldoRefreshKey((k) => k + 1);

  useEffect(() => {
    if (!podeAcessar) return;
    let ativo = true;

    async function buscar() {
      setSaldoLoading(true);
      try {
        const res = await caixaApi.saldo();
        if (ativo && res?.ok) setSaldo(res.saldo);
      } catch {
        if (ativo) toast.error("Erro ao carregar saldo em caixa");
      } finally {
        if (ativo) setSaldoLoading(false);
      }
    }

    buscar();
    return () => { ativo = false; };
  }, [podeAcessar, saldoRefreshKey]);

  if (!podeAcessar) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente perfis administrador ou financeiro podem acessar o Financeiro.</p>
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Financeiro</h1>
        <p className="text-muted-foreground text-sm">Caixa, contas a pagar e contas a receber</p>
      </div>

      {/* Métrica dominante */}
      <Panel>
        <PanelHeader>
          <PanelTitle>Saldo em caixa</PanelTitle>
        </PanelHeader>
        <PanelContent className="pt-0">
          {saldoLoading ? (
            <CircleNotch className="h-8 w-8 animate-spin text-muted-foreground" />
          ) : (
            <p className={`text-4xl sm:text-5xl font-bold tracking-tight ${saldo < 0 ? "text-destructive" : "text-card-foreground"}`}>
              {formatCurrency(saldo)}
            </p>
          )}
        </PanelContent>
      </Panel>

      <div className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
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

      {activeTab === "movimentacoes" && <Movimentacoes onMutate={carregarSaldo} />}
      {activeTab === "contas-pagar" && <ContasTab dominio="pagar" onMutate={carregarSaldo} />}
      {activeTab === "contas-receber" && <ContasTab dominio="receber" onMutate={carregarSaldo} />}
    </div>
  );
}
