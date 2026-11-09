import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, MagnifyingGlass, UserCircle, Check, Plus, CaretLeft, CaretRight } from "@phosphor-icons/react";
import { clientes as clientesApi, produtos as produtosApi, comprasAparelhos as comprasApi } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription, DialogFooter } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Reveal } from "@/components/ui/reveal";
import { FilterBar, FilterSelect, FilterInput } from "@/components/ui/filter-bar";
import { DataTable } from "@/components/ui/data-table";
import { Panel, PanelContent } from "@/components/ui/panel";
import { formatCurrency } from "@/lib/constants";

// Compra de Aparelhos (BR-083 a BR-089, docs/engineering/plans/PLAN-compra-aparelhos.md).

export const ORIGENS_COMPRA = [
  { value: "marketplace", label: "Marketplace" },
  { value: "troca", label: "Troca" },
  { value: "outro", label: "Outro" },
];

export const FORMAS_PAGAMENTO_COMPRA = [
  { value: "pix", label: "Pix" },
  { value: "dinheiro", label: "Dinheiro" },
  { value: "transferencia", label: "Transferência" },
  { value: "cartao", label: "Cartão" },
  { value: "abatido_na_venda", label: "Abatido na venda" },
];

const STATUS_APARELHO_LABEL = {
  em_reparo: "Em reparo",
  disponivel: "Disponível",
  vendido: "Vendido",
  devolvido: "Devolvido",
};

function statusAparelhoVariant(status) {
  if (status === "disponivel") return "success";
  if (status === "em_reparo") return "warning";
  if (status === "devolvido") return "info";
  return "neutral";
}

const labelDe = (lista, valor) => lista.find((i) => i.value === valor)?.label || valor || "—";

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${(hora || "").slice(0, 5)}`.trim() : value;
}

function produtoLabel(p) {
  return [p.modelo || p.descricao, p.capacidade, p.cor, p.condicao].filter(Boolean).join(" · ");
}

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

const EMPTY_FORM = {
  produtoId: "",
  imei: "",
  origem: "marketplace",
  valorPago: "",
  formaPagamento: "",
  estado: "",
  defeito: "",
  vendedorNome: "",
  vendedorTelefone: "",
  clienteQuery: "",
  clienteSelecionado: null,
  vendaId: "",
};

function NovaCompra() {
  const [form, setForm] = useState(EMPTY_FORM);
  const [produtos, setProdutos] = useState([]);
  const [clienteResultados, setClienteResultados] = useState([]);
  const [buscandoCliente, setBuscandoCliente] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [concluida, setConcluida] = useState(null);

  const setField = (key, value) => setForm((p) => ({ ...p, [key]: value }));
  const troca = form.origem === "troca";

  // Só produtos com rastreio por unidade podem virar aparelho no estoque (BR-084).
  useEffect(() => {
    produtosApi.list({ ativo: "1", per_page: 100 }).then((res) => {
      if (res?.ok) setProdutos((res.items || []).filter((p) => p.requer_rastreio_unidade));
    }).catch(() => toast.error("Erro ao carregar o catálogo de produtos"));
  }, []);

  const clienteQueryDebounced = useDebounced(form.clienteQuery);
  useEffect(() => {
    if (!troca || form.clienteSelecionado || clienteQueryDebounced.trim().length < 2) {
      setClienteResultados([]);
      return;
    }
    let ativo = true;
    setBuscandoCliente(true);
    clientesApi.list({ q: clienteQueryDebounced }).then((res) => {
      if (ativo) setClienteResultados(res?.ok ? res.items || [] : []);
    }).catch(() => {
      if (ativo) setClienteResultados([]);
    }).finally(() => { if (ativo) setBuscandoCliente(false); });
    return () => { ativo = false; };
  }, [clienteQueryDebounced, form.clienteSelecionado, troca]);

  const mudarOrigem = (origem) => {
    setForm((p) => ({
      ...p,
      origem,
      // "Abatido na venda" só existe na troca (BR-085).
      formaPagamento: origem !== "troca" && p.formaPagamento === "abatido_na_venda" ? "" : p.formaPagamento,
      clienteSelecionado: origem === "troca" ? p.clienteSelecionado : null,
      clienteQuery: origem === "troca" ? p.clienteQuery : "",
      vendaId: origem === "troca" ? p.vendaId : "",
    }));
  };

  const formasDisponiveis = troca ? FORMAS_PAGAMENTO_COMPRA : FORMAS_PAGAMENTO_COMPRA.filter((f) => f.value !== "abatido_na_venda");

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valorPago);
    if (!form.produtoId) return toast.error("Selecione o modelo do aparelho.");
    if (!form.imei.trim()) return toast.error("Informe o IMEI.");
    if (!valor || valor <= 0) return toast.error("Informe o valor pago.");
    if (!form.formaPagamento) return toast.error("Selecione a forma de pagamento.");
    if (!form.estado.trim()) return toast.error("Descreva o estado do aparelho.");
    if (troca && !form.clienteSelecionado) return toast.error("Na troca, selecione o cliente que entregou o aparelho.");

    setSubmitting(true);
    try {
      const res = await comprasApi.create({
        produto_id: parseInt(form.produtoId, 10),
        imei: form.imei.trim(),
        origem: form.origem,
        valor_pago: valor,
        forma_pagamento: form.formaPagamento,
        estado: form.estado,
        defeito: form.defeito,
        vendedor_nome: troca ? "" : form.vendedorNome,
        vendedor_telefone: troca ? "" : form.vendedorTelefone,
        cliente_id: troca ? form.clienteSelecionado.id : undefined,
        venda_id: troca && form.vendaId ? parseInt(form.vendaId, 10) : undefined,
      });
      if (res?.ok) {
        toast.success("Compra registrada!");
        setConcluida({ id: res.id, valor, comDefeito: Boolean(form.defeito.trim()) });
      } else {
        toast.error(res?.erro || "Erro ao registrar a compra");
      }
    } catch {
      toast.error("Erro ao registrar a compra");
    } finally {
      setSubmitting(false);
    }
  };

  if (concluida) {
    return (
      <div className="space-y-5 max-w-xl">
        <Panel>
          <PanelContent className="text-center space-y-4 pt-6">
            <div className="mx-auto h-12 w-12 rounded-full bg-success/10 flex items-center justify-center">
              <Check className="h-6 w-6 text-success" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Compra registrada</h1>
              <p className="text-muted-foreground text-sm">Compra #{concluida.id} — {formatCurrency(concluida.valor)} lançado como saída no caixa</p>
            </div>
            <p className="text-sm text-muted-foreground">
              {concluida.comDefeito
                ? "O aparelho entrou no estoque como Em reparo. Abra uma OS do tipo Interna para o conserto."
                : "O aparelho entrou no estoque como Disponível para venda."}
            </p>
            <Button onClick={() => { setForm(EMPTY_FORM); setConcluida(null); }}>
              <Plus className="h-4 w-4 mr-2" />Nova compra
            </Button>
          </PanelContent>
        </Panel>
      </div>
    );
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Nova Compra</h1>
        <p className="text-muted-foreground text-sm">Aparelho comprado para consertar e revender</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="bg-card border border-border rounded-xl p-4 grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="compra-produto">Modelo do aparelho *</Label>
            <Select value={form.produtoId} onValueChange={(v) => setField("produtoId", v)}>
              <SelectTrigger id="compra-produto" className="w-full"><SelectValue placeholder="Selecione do catálogo" /></SelectTrigger>
              <SelectContent>
                {produtos.map((p) => <SelectItem key={p.id} value={String(p.id)}>{produtoLabel(p)}</SelectItem>)}
              </SelectContent>
            </Select>
            {produtos.length === 0 && (
              <p className="text-xs text-muted-foreground">
                Nenhum produto com rastreio por unidade — cadastre o modelo em Produtos marcando “rastrear por unidade”.
              </p>
            )}
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="compra-imei">IMEI *</Label>
            <Input id="compra-imei" value={form.imei} onChange={(e) => setField("imei", e.target.value)} maxLength={20} />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="compra-origem">Origem *</Label>
            <Select value={form.origem} onValueChange={mudarOrigem}>
              <SelectTrigger id="compra-origem" className="w-full"><SelectValue /></SelectTrigger>
              <SelectContent>
                {ORIGENS_COMPRA.map((o) => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="compra-estado">Estado do aparelho *</Label>
            <Input id="compra-estado" placeholder="Ex.: tela trincada, carcaça boa, bateria 82%" value={form.estado} onChange={(e) => setField("estado", e.target.value)} />
          </div>
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="compra-defeito">Defeito</Label>
            <Textarea id="compra-defeito" rows={2} placeholder="Deixe vazio se o aparelho não tem defeito" value={form.defeito} onChange={(e) => setField("defeito", e.target.value)} />
            <p className="text-xs text-muted-foreground">Com defeito, o aparelho entra no estoque como Em reparo; sem defeito, já entra Disponível.</p>
          </div>
        </div>

        {troca ? (
          <div className="bg-card border border-border rounded-xl p-4 space-y-3">
            <Label className="flex items-center gap-2"><UserCircle className="h-4 w-4" />Cliente que entregou o aparelho *</Label>
            {form.clienteSelecionado ? (
              <div className="flex items-center justify-between bg-secondary/40 rounded-lg px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-card-foreground">{form.clienteSelecionado.nome}</p>
                  <p className="text-xs text-muted-foreground">{form.clienteSelecionado.telefone || form.clienteSelecionado.email || "—"}</p>
                </div>
                <Button type="button" variant="ghost" size="sm" onClick={() => setForm((p) => ({ ...p, clienteSelecionado: null, clienteQuery: "" }))}>Trocar</Button>
              </div>
            ) : (
              <div className="relative">
                <MagnifyingGlass className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar cliente por nome, telefone ou e-mail..."
                  className="pl-8"
                  value={form.clienteQuery}
                  onChange={(e) => setField("clienteQuery", e.target.value)}
                />
                {buscandoCliente && <CircleNotch className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />}
                {clienteResultados.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-popover border border-border rounded-lg shadow-lg max-h-56 overflow-y-auto">
                    {clienteResultados.map((c) => (
                      <button
                        type="button"
                        key={c.id}
                        onClick={() => { setForm((p) => ({ ...p, clienteSelecionado: c, clienteQuery: c.nome })); setClienteResultados([]); }}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
                      >
                        <p className="font-medium text-card-foreground">{c.nome}</p>
                        <p className="text-xs text-muted-foreground">{c.telefone || c.email || "—"}</p>
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
            <div className="space-y-1.5">
              <Label htmlFor="compra-venda">Nº da venda em que entrou na troca (opcional)</Label>
              <Input id="compra-venda" type="number" min="1" value={form.vendaId} onChange={(e) => setField("vendaId", e.target.value)} className="w-40" />
            </div>
          </div>
        ) : (
          <div className="bg-card border border-border rounded-xl p-4 space-y-3">
            <div>
              <Label>Quem vendeu o aparelho (opcional)</Label>
              <p className="text-xs text-muted-foreground mt-0.5">Guarde para comprovar a procedência se o aparelho aparecer como roubado.</p>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <Input aria-label="Nome de quem vendeu" placeholder="Nome" value={form.vendedorNome} onChange={(e) => setField("vendedorNome", e.target.value)} maxLength={120} />
              <Input aria-label="Telefone de quem vendeu" placeholder="Telefone" value={form.vendedorTelefone} onChange={(e) => setField("vendedorTelefone", e.target.value)} maxLength={120} />
            </div>
          </div>
        )}

        <Panel>
          <PanelContent className="space-y-4 pt-6">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="compra-valor">Valor pago *</Label>
                <Input id="compra-valor" type="number" step="0.01" min="0" value={form.valorPago} onChange={(e) => setField("valorPago", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="compra-pagamento">Forma de pagamento *</Label>
                <Select value={form.formaPagamento} onValueChange={(v) => setField("formaPagamento", v)}>
                  <SelectTrigger id="compra-pagamento" className="w-full"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {formasDisponiveis.map((f) => <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <p className="text-xs text-muted-foreground">
              O valor sai do caixa automaticamente — inclusive quando abatido na venda, porque a venda entra no caixa pelo valor cheio.
            </p>
            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
              {submitting ? "Registrando..." : "Registrar compra"}
            </Button>
          </PanelContent>
        </Panel>
      </form>
    </div>
  );
}

const PER_PAGE = 20;

function Historico() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [origemFilter, setOrigemFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [cancelando, setCancelando] = useState(null);
  const [motivo, setMotivo] = useState("");
  const [enviandoCancelamento, setEnviandoCancelamento] = useState(false);

  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    let ativo = true;
    setLoading(true);
    setErro(false);
    const params = { page, per_page: PER_PAGE };
    if (search) params.q = search;
    if (origemFilter) params.origem = origemFilter;
    if (statusFilter) params.status = statusFilter;
    comprasApi.list(params).then((res) => {
      if (!ativo) return;
      if (res?.ok) {
        setItems(res.items || []);
        setTotal(res.total || 0);
      } else {
        setErro(true);
      }
    }).catch(() => {
      if (ativo) setErro(true);
    }).finally(() => { if (ativo) setLoading(false); });
    return () => { ativo = false; };
  }, [page, search, origemFilter, statusFilter, reloadToken]);

  const confirmarCancelamento = async () => {
    if (!motivo.trim()) {
      toast.error("Informe o motivo do cancelamento.");
      return;
    }
    setEnviandoCancelamento(true);
    try {
      const res = await comprasApi.cancelar(cancelando.id, { motivo });
      if (res?.ok) {
        toast.success("Compra cancelada — saída de caixa estornada.");
        setCancelando(null);
        setMotivo("");
        setReloadToken((t) => t + 1);
      } else {
        toast.error(res?.erro || "Erro ao cancelar a compra");
      }
    } catch {
      toast.error("Erro ao cancelar a compra");
    } finally {
      setEnviandoCancelamento(false);
    }
  };

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));
  const filtrosAtivos = Boolean(search || origemFilter || statusFilter);

  return (
    <div className="space-y-5">
      <FilterBar className="bg-card border border-border rounded-xl p-4">
        <div className="relative flex-1 min-w-[200px]">
          <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
          <FilterInput
            placeholder="Buscar por IMEI, modelo, cliente ou vendedor..."
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            className="w-full pl-8"
          />
        </div>
        <FilterSelect
          value={origemFilter || "all"}
          onValueChange={(v) => { setOrigemFilter(v === "all" ? "" : v); setPage(1); }}
          placeholder="Origem"
          className="w-40"
          options={[{ value: "all", label: "Todas as origens" }, ...ORIGENS_COMPRA]}
        />
        <FilterSelect
          value={statusFilter || "all"}
          onValueChange={(v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); }}
          placeholder="Status"
          className="w-40"
          options={[{ value: "all", label: "Todas" }, { value: "ativa", label: "Ativas" }, { value: "cancelada", label: "Canceladas" }]}
        />
      </FilterBar>

      {loading ? (
        <ListSkeleton rows={6} />
      ) : erro ? (
        <ErrorState title="Não foi possível carregar as compras." onRetry={() => setReloadToken((t) => t + 1)} />
      ) : items.length === 0 ? (
        <EmptyState title={filtrosAtivos ? "Nenhuma compra corresponde à busca/filtros atuais." : "Nenhuma compra registrada ainda."} />
      ) : (
        <Reveal className="space-y-5">
          <DataTable
            columns={[
              { key: "criado_em", header: "Data", className: "text-muted-foreground whitespace-nowrap", render: (c) => formatDateTime(c.criado_em) },
              {
                key: "aparelho",
                header: "Aparelho",
                render: (c) => (
                  <>
                    <p className="text-card-foreground">{[c.produto_label, c.produto_capacidade, c.produto_cor].filter(Boolean).join(" · ")}</p>
                    <p className="text-xs font-mono text-muted-foreground">{c.imei || "—"}</p>
                  </>
                ),
              },
              {
                key: "origem",
                header: "Origem",
                className: "text-muted-foreground",
                render: (c) => (
                  <>
                    <p>{labelDe(ORIGENS_COMPRA, c.origem)}</p>
                    <p className="text-xs">{c.origem === "troca" ? c.cliente_nome : c.vendedor_nome}</p>
                  </>
                ),
              },
              { key: "forma_pagamento", header: "Pagamento", className: "text-muted-foreground", render: (c) => labelDe(FORMAS_PAGAMENTO_COMPRA, c.forma_pagamento) },
              { key: "valor_pago", header: "Valor pago", className: "font-medium text-card-foreground whitespace-nowrap", render: (c) => formatCurrency(c.valor_pago) },
              {
                key: "unidade_status",
                header: "Aparelho está",
                render: (c) => (c.status === "cancelada"
                  ? <Badge variant="neutral">Compra cancelada</Badge>
                  : <Badge variant={statusAparelhoVariant(c.unidade_status)}>{STATUS_APARELHO_LABEL[c.unidade_status] || c.unidade_status}</Badge>),
              },
              {
                key: "acoes",
                header: "",
                render: (c) => (c.status === "ativa" && c.unidade_status !== "vendido" ? (
                  <Button variant="ghost" size="sm" onClick={() => { setCancelando(c); setMotivo(""); }}>Cancelar</Button>
                ) : null),
              },
            ]}
            rows={items}
            getRowKey={(c) => c.id}
            getRowProps={(c) => ({ "data-testid": `compra-row-${c.id}` })}
          />
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "compra" : "compras"}</span>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                <CaretLeft className="h-4 w-4 mr-1" /> Anterior
              </Button>
              <Button variant="outline" size="sm" disabled={page >= totalPaginas} onClick={() => setPage((p) => p + 1)}>
                Próxima <CaretRight className="h-4 w-4 ml-1" />
              </Button>
            </div>
          </div>
        </Reveal>
      )}

      <Dialog open={Boolean(cancelando)} onOpenChange={(open) => !open && setCancelando(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancelar compra #{cancelando?.id}</DialogTitle>
            <DialogDescription>
              A saída de {formatCurrency(cancelando?.valor_pago)} no caixa é estornada e o aparelho sai do estoque como Devolvido.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-1.5">
            <Label htmlFor="compra-motivo-cancelamento">Motivo *</Label>
            <Textarea id="compra-motivo-cancelamento" rows={2} value={motivo} onChange={(e) => setMotivo(e.target.value)} />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setCancelando(null)}>Voltar</Button>
            <Button variant="destructive" onClick={confirmarCancelamento} disabled={enviandoCancelamento}>
              {enviandoCancelamento && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
              Cancelar compra
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

const TABS = [
  { key: "nova", label: "Nova Compra" },
  { key: "historico", label: "Histórico" },
];

export default function ComprasAparelhos() {
  const [activeTab, setActiveTab] = useState("nova");

  return (
    <div className="space-y-5">
      <div className="flex gap-1 bg-secondary p-1 rounded-lg w-fit">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.key ? "bg-card text-card-foreground shadow" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>
      {activeTab === "nova" ? <NovaCompra /> : <Historico />}
    </div>
  );
}
