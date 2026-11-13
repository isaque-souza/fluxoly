import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { CircleNotch, MagnifyingGlass, UserCircle, DeviceMobile, Check, Plus, Eye, Printer, CaretLeft, CaretRight } from "@phosphor-icons/react";
import { clientes as clientesApi, unidadesSerializadas as unidadesApi, vendas as vendasApi, tiposGarantia as tiposGarantiaApi } from "@/api/client";
import { imprimirReciboVenda } from "@/lib/vendaPdf";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Reveal } from "@/components/ui/reveal";
import { FilterBar, FilterSelect, FilterInput } from "@/components/ui/filter-bar";
import { DataTable } from "@/components/ui/data-table";
import { Panel, PanelContent } from "@/components/ui/panel";
import { formatCurrency, vendaStatusVariant, vendaStatusLabel, origemUnidadeLabel } from "@/lib/constants";
import { readListContext, saveListContext, useRestoreScroll } from "@/hooks/useListContext";

const NAV_CONTEXT_KEY = "vendas-historico";

const FORMAS_PAGAMENTO = [
  { value: "pix", label: "Pix" },
  { value: "cartao", label: "Cartão" },
  { value: "dinheiro", label: "Dinheiro" },
  { value: "transferencia", label: "Transferência" },
];

const STATUS_VENDA_OPCOES = [
  { value: "concluida", label: "Concluída" },
  { value: "cancelada", label: "Cancelada" },
];

const SORT_OPTIONS = [
  { value: "recente", label: "Mais recente" },
  { value: "antigo", label: "Mais antigo" },
];

const PER_PAGE_HISTORICO = 20;

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

function Historico() {
  const navigate = useNavigate();
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [erro, setErro] = useState(false);
  const [reloadToken, setReloadToken] = useState(0);

  // UX-001 -- restaura filtros/paginação salvos ao voltar do detalhe de uma venda.
  const [ctxInicial] = useState(() => readListContext(NAV_CONTEXT_KEY) || {});
  const [searchInput, setSearchInput] = useState(ctxInicial.search || "");
  const [search, setSearch] = useState(ctxInicial.search || "");
  const [formaPagamentoFilter, setFormaPagamentoFilter] = useState(ctxInicial.formaPagamentoFilter || "");
  const [statusFilter, setStatusFilter] = useState(ctxInicial.statusFilter || "");
  const [dataInicio, setDataInicio] = useState(ctxInicial.dataInicio || "");
  const [dataFim, setDataFim] = useState(ctxInicial.dataFim || "");
  const [sort, setSort] = useState(ctxInicial.sort || "recente");
  const [page, setPage] = useState(ctxInicial.page || 1);

  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  const handleFormaPagamentoChange = (v) => { setFormaPagamentoFilter(v === "all" ? "" : v); setPage(1); };
  const handleStatusChange = (v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); };
  const handleSortChange = (v) => { setSort(v); setPage(1); };
  const handleDataInicioChange = (v) => { setDataInicio(v); setPage(1); };
  const handleDataFimChange = (v) => { setDataFim(v); setPage(1); };

  useEffect(() => {
    let ativo = true;

    async function buscar() {
      setLoading(true);
      setErro(false);
      const params = { page, per_page: PER_PAGE_HISTORICO, sort };
      if (search) params.q = search;
      if (formaPagamentoFilter) params.forma_pagamento = formaPagamentoFilter;
      if (statusFilter) params.status = statusFilter;
      if (dataInicio) params.data_inicio = dataInicio;
      if (dataFim) params.data_fim = dataFim;

      try {
        const res = await vendasApi.list(params);
        if (!ativo) return;
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
        } else {
          setErro(true);
          toast.error(res?.erro || "Erro ao carregar histórico de vendas");
        }
      } catch {
        if (ativo) {
          setErro(true);
          toast.error("Erro ao carregar histórico de vendas");
        }
      } finally {
        if (ativo) setLoading(false);
      }
    }

    buscar();
    return () => { ativo = false; };
  }, [page, search, formaPagamentoFilter, statusFilter, dataInicio, dataFim, sort, reloadToken]);

  // UX-001 -- rola de volta para a venda em foco (ou posição salva) assim
  // que a listagem carrega.
  useRestoreScroll(NAV_CONTEXT_KEY, !loading);

  const handleRowClick = (id) => {
    saveListContext(NAV_CONTEXT_KEY, {
      search, formaPagamentoFilter, statusFilter, dataInicio, dataFim, sort, page, focusId: id,
    });
    navigate(`/vendas/${id}`);
  };

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE_HISTORICO));
  const filtrosAtivos = Boolean(search || formaPagamentoFilter || statusFilter || dataInicio || dataFim);

  return (
    <div className="space-y-5">
      {loading ? (
        <ListSkeleton rows={6} />
      ) : erro ? (
        <ErrorState title="Não foi possível carregar o histórico de vendas." onRetry={() => setReloadToken((t) => t + 1)} />
      ) : (
        <Reveal className="space-y-5">
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <div className="relative flex-1 min-w-[200px]">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <FilterInput
                placeholder="Buscar por cliente, IMEI ou produto..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="w-full pl-8"
              />
            </div>
            <FilterSelect
              value={formaPagamentoFilter || "all"}
              onValueChange={handleFormaPagamentoChange}
              placeholder="Pagamento"
              className="w-44"
              options={[{ value: "all", label: "Todas as formas" }, ...FORMAS_PAGAMENTO]}
            />
            <FilterSelect
              value={statusFilter || "all"}
              onValueChange={handleStatusChange}
              placeholder="Status"
              className="w-44"
              options={[{ value: "all", label: "Todas" }, ...STATUS_VENDA_OPCOES]}
            />
            <FilterInput type="date" value={dataInicio} onChange={(e) => handleDataInicioChange(e.target.value)} className="w-40" aria-label="Data inicial" />
            <FilterInput type="date" value={dataFim} onChange={(e) => handleDataFimChange(e.target.value)} className="w-40" aria-label="Data final" />
            <FilterSelect
              value={sort}
              onValueChange={handleSortChange}
              placeholder="Ordenar por"
              className="w-44"
              options={SORT_OPTIONS}
            />
            <div className="ml-auto flex items-center text-xs text-muted-foreground">
              {total} {total === 1 ? "venda" : "vendas"} {filtrosAtivos ? "encontradas" : "no total"}
            </div>
          </FilterBar>

          {items.length === 0 ? (
            <EmptyState
              title={filtrosAtivos ? "Nenhuma venda corresponde à busca/filtros atuais." : "Nenhuma venda registrada ainda."}
            />
          ) : (
            <>
              <DataTable
                columns={[
                  {
                    key: "criado_em",
                    header: "Data",
                    className: "text-muted-foreground whitespace-nowrap",
                    render: (item) => formatDateTime(item.criado_em),
                  },
                  {
                    key: "cliente_nome",
                    header: "Cliente",
                    className: "font-medium text-card-foreground",
                    render: (item) => item.cliente_nome || "—",
                  },
                  {
                    key: "aparelho",
                    header: "Aparelho",
                    className: "text-muted-foreground",
                    render: (item) => {
                      const primeiroItem = item.itens_resumo?.[0];
                      return primeiroItem ? (
                        <>
                          <p className="text-card-foreground">{primeiroItem.produto_nome}</p>
                          <p className="text-xs font-mono">{primeiroItem.imei || "—"}</p>
                        </>
                      ) : "—";
                    },
                  },
                  {
                    key: "vendedor_nome",
                    header: "Vendedor",
                    className: "text-muted-foreground",
                    render: (item) => item.vendedor_nome || "—",
                  },
                  {
                    key: "forma_pagamento",
                    header: "Pagamento",
                    className: "text-muted-foreground",
                    render: (item) => FORMAS_PAGAMENTO.find((f) => f.value === item.forma_pagamento)?.label || item.forma_pagamento || "—",
                  },
                  {
                    key: "valor_total",
                    header: "Valor",
                    className: "font-medium text-card-foreground whitespace-nowrap",
                    render: (item) => formatCurrency(item.valor_total),
                  },
                  {
                    key: "status",
                    header: "Status",
                    render: (item) => <Badge variant={vendaStatusVariant(item.status)}>{vendaStatusLabel(item.status)}</Badge>,
                  },
                ]}
                rows={items}
                getRowKey={(item) => item.id}
                getRowProps={(item) => ({ "data-testid": `venda-row-${item.id}`, "data-context-row": item.id })}
                onRowClick={(item) => handleRowClick(item.id)}
              />

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "venda" : "vendas"}</span>
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
    </div>
  );
}

function useDebounced(value, delay = 300) {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

function aparelhoDetalhes(unidade) {
  const partes = [unidade.origem_label, unidade.produto_capacidade, unidade.produto_cor].filter(Boolean);
  return partes.join(" · ");
}

const EMPTY_STATE = {
  clienteQuery: "",
  clienteSelecionado: null,
  aparelhoQuery: "",
  aparelhoSelecionado: null,
  valorVenda: "",
  formaPagamento: "",
  observacoes: "",
  motivoDesconto: "",
  tipoGarantiaId: "",
};

const TABS = [
  { key: "nova", label: "Nova Venda" },
  { key: "historico", label: "Histórico" },
];

function NovaVenda() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_STATE);
  const [clienteResultados, setClienteResultados] = useState([]);
  const [buscandoCliente, setBuscandoCliente] = useState(false);
  const [aparelhoResultados, setAparelhoResultados] = useState([]);
  const [buscandoAparelho, setBuscandoAparelho] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [vendaConcluida, setVendaConcluida] = useState(null);
  const [tiposGarantiaList, setTiposGarantiaList] = useState([]);

  // V1.5 -- Garantia de Venda (BR-056): lista de tipos ativos para o select
  // obrigatório abaixo, sem default vindo do produto do catálogo.
  useEffect(() => {
    tiposGarantiaApi.list().then((res) => {
      if (res?.ok) setTiposGarantiaList(res.items || []);
    }).catch(() => {
      toast.error("Erro ao carregar tipos de garantia");
    });
  }, []);

  const clienteQueryDebounced = useDebounced(form.clienteQuery);
  const aparelhoQueryDebounced = useDebounced(form.aparelhoQuery);

  useEffect(() => {
    if (form.clienteSelecionado || clienteQueryDebounced.trim().length < 2) {
      setClienteResultados([]);
      return;
    }
    let ativo = true;
    setBuscandoCliente(true);
    clientesApi.list({ q: clienteQueryDebounced, status: "ativos" }).then((res) => {
      if (!ativo) return;
      setClienteResultados(res?.ok ? res.items || [] : []);
    }).catch(() => {
      if (ativo) setClienteResultados([]);
    }).finally(() => { if (ativo) setBuscandoCliente(false); });
    return () => { ativo = false; };
  }, [clienteQueryDebounced, form.clienteSelecionado]);

  useEffect(() => {
    if (!form.clienteSelecionado || form.aparelhoSelecionado || aparelhoQueryDebounced.trim().length < 2) {
      setAparelhoResultados([]);
      return;
    }
    let ativo = true;
    setBuscandoAparelho(true);
    unidadesApi.list({ q: aparelhoQueryDebounced, status: "disponivel", per_page: 10 }).then((res) => {
      if (!ativo) return;
      setAparelhoResultados(res?.ok ? res.items || [] : []);
    }).catch(() => {
      if (ativo) setAparelhoResultados([]);
    }).finally(() => { if (ativo) setBuscandoAparelho(false); });
    return () => { ativo = false; };
  }, [aparelhoQueryDebounced, form.clienteSelecionado, form.aparelhoSelecionado]);

  const selecionarCliente = (cliente) => {
    setForm((p) => ({ ...p, clienteSelecionado: cliente, clienteQuery: cliente.nome }));
    setClienteResultados([]);
  };

  const trocarCliente = () => {
    setForm((p) => ({ ...p, clienteSelecionado: null, clienteQuery: "", aparelhoSelecionado: null, aparelhoQuery: "", valorVenda: "" }));
  };

  const selecionarAparelho = (unidade) => {
    const precoSugerido = unidade.preco_catalogo != null ? String(unidade.preco_catalogo) : "";
    setForm((p) => ({ ...p, aparelhoSelecionado: unidade, aparelhoQuery: unidade.imei, valorVenda: precoSugerido }));
    setAparelhoResultados([]);
  };

  const trocarAparelho = () => {
    setForm((p) => ({ ...p, aparelhoSelecionado: null, aparelhoQuery: "", valorVenda: "" }));
  };

  const novaVenda = () => {
    setForm(EMPTY_STATE);
    setVendaConcluida(null);
  };

  // Desconto (BR-053): sempre permitido, sempre registrado -- nunca bloqueia
  // a venda. `desconto` só existe aqui para decidir se mostra o campo de
  // motivo (nenhum efeito de validação).
  const precoTabela = form.aparelhoSelecionado?.preco_catalogo;
  const valorVendaNum = parseFloat(form.valorVenda) || 0;
  const desconto = precoTabela != null ? Math.round((precoTabela - valorVendaNum) * 100) / 100 : null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    const valor = parseFloat(form.valorVenda);
    if (!form.clienteSelecionado || !form.aparelhoSelecionado) {
      toast.error("Selecione o cliente e o aparelho.");
      return;
    }
    if (!form.formaPagamento) {
      toast.error("Selecione a forma de pagamento.");
      return;
    }
    if (!valor || valor <= 0) {
      toast.error("Informe um valor de venda válido.");
      return;
    }
    if (!form.tipoGarantiaId) {
      toast.error("Selecione o Tipo de Garantia.");
      return;
    }

    setSubmitting(true);
    try {
      const res = await vendasApi.create({
        cliente_id: form.clienteSelecionado.id,
        unidade_serializada_id: form.aparelhoSelecionado.id,
        forma_pagamento: form.formaPagamento,
        valor_unitario: valor,
        observacoes: form.observacoes,
        motivo_desconto: form.motivoDesconto,
        tipo_garantia_id: parseInt(form.tipoGarantiaId, 10),
      });
      if (res?.ok) {
        toast.success("Venda concluída!");
        setVendaConcluida({
          id: res.id,
          cliente: form.clienteSelecionado,
          aparelho: form.aparelhoSelecionado,
          valor,
          formaPagamento: form.formaPagamento,
        });
      } else {
        toast.error(res?.erro || "Erro ao concluir a venda");
      }
    } catch {
      toast.error("Erro ao concluir a venda");
    } finally {
      setSubmitting(false);
    }
  };

  if (vendaConcluida) {
    const formaLabel = FORMAS_PAGAMENTO.find((f) => f.value === vendaConcluida.formaPagamento)?.label;
    return (
      <div className="space-y-5 max-w-xl">
        <Panel>
          <PanelContent className="text-center space-y-4 pt-6">
            <div className="mx-auto h-12 w-12 rounded-full bg-success/10 flex items-center justify-center">
              <Check className="h-6 w-6 text-success" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-foreground">Venda concluída</h1>
              <p className="text-muted-foreground text-sm">Venda #{vendaConcluida.id}</p>
            </div>

            <div className="bg-secondary/40 rounded-lg p-4 text-left space-y-1.5 text-sm">
              <p><span className="text-muted-foreground">Cliente:</span> {vendaConcluida.cliente.nome}</p>
              <p><span className="text-muted-foreground">Aparelho:</span> {aparelhoDetalhes(vendaConcluida.aparelho)} — IMEI {vendaConcluida.aparelho.imei}</p>
              <p><span className="text-muted-foreground">Pagamento:</span> {formaLabel}</p>
              <p><span className="text-muted-foreground">Valor:</span> {formatCurrency(vendaConcluida.valor)}</p>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-2 pt-2">
              <Button onClick={novaVenda}><Plus className="h-4 w-4 mr-2" />Nova venda</Button>
              <Button variant="outline" onClick={() => navigate(`/vendas/${vendaConcluida.id}`)}>
                <Eye className="h-4 w-4 mr-2" />Ver venda
              </Button>
              <Button variant="outline" onClick={() => imprimirReciboVenda(vendaConcluida.id)}>
                <Printer className="h-4 w-4 mr-2" />Imprimir recibo
              </Button>
            </div>
          </PanelContent>
        </Panel>
      </div>
    );
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Nova Venda</h1>
        <p className="text-muted-foreground text-sm">Venda de um aparelho a um cliente</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Cliente */}
        <div className="bg-card border border-border rounded-xl p-4 space-y-2">
          <Label className="flex items-center gap-2"><UserCircle className="h-4 w-4" />Cliente</Label>
          {form.clienteSelecionado ? (
            <div className="flex items-center justify-between bg-secondary/40 rounded-lg px-3 py-2">
              <div>
                <p className="text-sm font-medium text-card-foreground">{form.clienteSelecionado.nome}</p>
                <p className="text-xs text-muted-foreground">{form.clienteSelecionado.telefone || form.clienteSelecionado.email || "—"}</p>
              </div>
              <Button type="button" variant="ghost" size="sm" onClick={trocarCliente}>Trocar</Button>
            </div>
          ) : (
            <div className="relative">
              <MagnifyingGlass className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar cliente por nome, telefone ou e-mail..."
                className="pl-8"
                value={form.clienteQuery}
                onChange={(e) => setForm((p) => ({ ...p, clienteQuery: e.target.value }))}
              />
              {buscandoCliente && <CircleNotch className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />}
              {clienteResultados.length > 0 && (
                <div className="absolute z-10 mt-1 w-full bg-popover border border-border rounded-lg shadow-lg max-h-56 overflow-y-auto">
                  {clienteResultados.map((c) => (
                    <button
                      type="button"
                      key={c.id}
                      onClick={() => selecionarCliente(c)}
                      className="w-full text-left px-3 py-2 text-sm hover:bg-accent/50 transition-colors"
                    >
                      <p className="font-medium text-card-foreground">{c.nome}</p>
                      <p className="text-xs text-muted-foreground">{c.telefone || c.email || "—"}</p>
                    </button>
                  ))}
                </div>
              )}
              {!form.clienteSelecionado && form.clienteQuery.trim().length >= 2 && !buscandoCliente && clienteResultados.length === 0 && (
                <p className="text-xs text-muted-foreground mt-1">Nenhum cliente encontrado — cadastre em Clientes antes de continuar.</p>
              )}
            </div>
          )}
        </div>

        {/* Aparelho */}
        {form.clienteSelecionado && (
          <div className="bg-card border border-border rounded-xl p-4 space-y-2">
            <Label className="flex items-center gap-2"><DeviceMobile className="h-4 w-4" />Aparelho</Label>
            {form.aparelhoSelecionado ? (
              <div className="flex items-center justify-between bg-secondary/40 rounded-lg px-3 py-2">
                <div>
                  <p className="text-sm font-medium text-card-foreground">{aparelhoDetalhes(form.aparelhoSelecionado)}</p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-xs text-muted-foreground">IMEI {form.aparelhoSelecionado.imei}</span>
                    <Badge variant="tag">{origemUnidadeLabel(form.aparelhoSelecionado.origem_tipo)}</Badge>
                  </div>
                </div>
                <Button type="button" variant="ghost" size="sm" onClick={trocarAparelho}>Trocar</Button>
              </div>
            ) : (
              <div className="relative">
                <MagnifyingGlass className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Buscar por IMEI, modelo ou SKU..."
                  className="pl-8"
                  value={form.aparelhoQuery}
                  onChange={(e) => setForm((p) => ({ ...p, aparelhoQuery: e.target.value }))}
                />
                {buscandoAparelho && <CircleNotch className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />}
                {aparelhoResultados.length > 0 && (
                  <div className="absolute z-10 mt-1 w-full bg-popover border border-border rounded-lg shadow-lg max-h-64 overflow-y-auto">
                    {aparelhoResultados.map((u) => (
                      <button
                        type="button"
                        key={u.id}
                        onClick={() => selecionarAparelho(u)}
                        className="w-full text-left px-3 py-2 text-sm hover:bg-accent/50 transition-colors flex items-center justify-between gap-2"
                      >
                        <div>
                          <p className="font-medium text-card-foreground">{aparelhoDetalhes(u)}</p>
                          <p className="text-xs text-muted-foreground">IMEI {u.imei} · {u.origem_sku || "sem SKU"}</p>
                        </div>
                        <span className="text-sm font-medium text-card-foreground shrink-0">
                          {u.preco_catalogo != null ? formatCurrency(u.preco_catalogo) : "—"}
                        </span>
                      </button>
                    ))}
                  </div>
                )}
                {form.aparelhoQuery.trim().length >= 2 && !buscandoAparelho && aparelhoResultados.length === 0 && (
                  <p className="text-xs text-muted-foreground mt-1">Nenhuma unidade disponível encontrada.</p>
                )}
              </div>
            )}
          </div>
        )}

        {/* Resumo automático + preço + pagamento -- único elemento dominante desta tela (Panel) */}
        {form.clienteSelecionado && form.aparelhoSelecionado && (
          <Panel>
            <PanelContent className="space-y-4 pt-6">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="venda-valor">Preço da venda</Label>
                <Input
                  id="venda-valor"
                  type="number"
                  step="0.01"
                  min="0"
                  value={form.valorVenda}
                  onChange={(e) => setForm((p) => ({ ...p, valorVenda: e.target.value }))}
                  required
                />
                {form.aparelhoSelecionado.preco_catalogo != null && (
                  <p className="text-xs text-muted-foreground">
                    Preço de catálogo: {formatCurrency(form.aparelhoSelecionado.preco_catalogo)}
                  </p>
                )}
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="venda-pagamento">Forma de pagamento</Label>
                <Select value={form.formaPagamento} onValueChange={(v) => setForm((p) => ({ ...p, formaPagamento: v }))}>
                  <SelectTrigger id="venda-pagamento" className="w-full"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {FORMAS_PAGAMENTO.map((f) => <SelectItem key={f.value} value={f.value}>{f.label}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5 col-span-2">
                <Label htmlFor="venda-garantia">Tipo de Garantia *</Label>
                <Select value={form.tipoGarantiaId} onValueChange={(v) => setForm((p) => ({ ...p, tipoGarantiaId: v }))}>
                  <SelectTrigger id="venda-garantia" className="w-full"><SelectValue placeholder="Selecione o Tipo de Garantia" /></SelectTrigger>
                  <SelectContent>
                    {tiposGarantiaList.map((tg) => (
                      <SelectItem key={tg.id} value={String(tg.id)}>
                        {tg.nome} ({tg.duracao_meses === 0 ? "sem garantia" : `${tg.duracao_meses}m`})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                {tiposGarantiaList.length === 0 && (
                  <p className="text-xs text-muted-foreground">
                    Nenhum Tipo de Garantia cadastrado — crie um em Tipos de Garantia antes de vender.
                  </p>
                )}
              </div>
            </div>

            {desconto != null && desconto > 0 && (
              <div className="space-y-1.5">
                <Label htmlFor="venda-motivo-desconto">Motivo do desconto (opcional)</Label>
                <Input
                  id="venda-motivo-desconto"
                  placeholder="Ex.: negociação, pagamento à vista..."
                  value={form.motivoDesconto}
                  onChange={(e) => setForm((p) => ({ ...p, motivoDesconto: e.target.value }))}
                />
              </div>
            )}

            <div className="space-y-1.5">
              <Label htmlFor="venda-observacoes">Observações (opcional)</Label>
              <Textarea
                id="venda-observacoes"
                placeholder="Ex.: retirada amanhã, venda corporativa, NF enviada..."
                value={form.observacoes}
                onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))}
                rows={2}
              />
            </div>

            <div className="flex items-center justify-between pt-2 border-t border-border">
              <span className="text-sm text-muted-foreground">Total</span>
              <span className="text-2xl font-bold text-foreground tracking-tight">
                {formatCurrency(parseFloat(form.valorVenda) || 0)}
              </span>
            </div>

            <Button type="submit" className="w-full" disabled={submitting}>
              {submitting && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
              {submitting ? "Confirmando..." : "Confirmar Venda"}
            </Button>
          </PanelContent>
          </Panel>
        )}
      </form>
    </div>
  );
}

export default function Vendas() {
  // UX-001 -- se havia um contexto salvo do Histórico (usuário estava lá
  // antes de sair para ver o detalhe de uma venda), volta para essa aba em
  // vez de sempre cair em "Nova Venda".
  const [activeTab, setActiveTab] = useState(() => (readListContext(NAV_CONTEXT_KEY) ? "historico" : "nova"));

  return (
    <div className="space-y-5">
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

      {activeTab === "nova" ? <NovaVenda /> : <Historico />}
    </div>
  );
}
