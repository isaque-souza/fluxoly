import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, MagnifyingGlass, Barcode, DeviceMobile, MapPin, BatteryMedium, ClockCounterClockwise, CaretLeft, CaretRight, Pencil } from "@phosphor-icons/react";
import { unidadesSerializadas as unidadesApi, vendas as vendasApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Reveal } from "@/components/ui/reveal";
import { FilterBar, FilterSelect, FilterInput } from "@/components/ui/filter-bar";
import { interactiveRowClassName } from "@/lib/interaction";
import { formatCurrency, origemUnidadeLabel } from "@/lib/constants";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";

// Mesma máquina de estados de TRANSICOES_VALIDAS em
// fluxoly_unidades_serializadas_service.py — usada só para popular o select
// de status no modo de edição (o backend valida de novo, esta cópia é só UX).
const TRANSICOES_VALIDAS = {
  disponivel: ["em_reparo"],
  em_reparo: ["disponivel", "devolvido"],
  devolvido: ["disponivel"],
};

// Status -- vocabulário próprio desta tela, migrado para o Badge semântico.
// 'reservado' e 'vendido' existem no schema mas não são produzidos por
// nenhum fluxo ainda (aguardam Vendas) -- 'reservado' reaproveita 'warning'
// (mesmo tom de 'em_reparo': ambos "pendente de ação", e reservado não
// renderiza em nenhum fluxo real hoje).
const STATUS_LABEL = {
  disponivel: "Disponível",
  em_reparo: "Em Reparo",
  devolvido: "Devolvido",
  reservado: "Reservado",
  vendido: "Vendido",
};

function statusVariant(status) {
  if (status === "disponivel") return "success";
  if (status === "em_reparo") return "warning";
  if (status === "reservado") return "warning";
  if (status === "devolvido") return "info";
  if (status === "vendido") return "neutral";
  return "neutral";
}

function statusLabel(status) {
  return STATUS_LABEL[status] || status || "—";
}

// Faixas de saúde da bateria e ordenação (C1.3.3) — espelham
// FAIXAS_SAUDE_BATERIA/_ORDENACOES do backend, só os rótulos são daqui.
const SAUDE_BATERIA_OPTIONS = [
  { value: "100-95", label: "100% – 95%" },
  { value: "94-90", label: "94% – 90%" },
  { value: "89-85", label: "89% – 85%" },
  { value: "<85", label: "Abaixo de 85%" },
  { value: "nao_informado", label: "Não informado" },
];

const SORT_OPTIONS = [
  { value: "recente", label: "Mais recente" },
  { value: "antigo", label: "Mais antigo" },
  { value: "imei", label: "IMEI" },
  { value: "modelo", label: "Modelo" },
  { value: "status", label: "Status" },
];

const PER_PAGE = 20;

function formatDate(value) {
  if (!value) return "—";
  // criado_em vem como "YYYY-MM-DD HH:MM:SS" (datetime('now') do SQLite)
  const [data] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : value;
}

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

const ACAO_LABEL = {
  create: "Unidade cadastrada",
  status_change: "Mudança de status",
  update: "Localização/bateria atualizada",
};

function eventoDescricao(evento) {
  if (evento.acao === "status_change") {
    const de = statusLabel(evento.valor_anterior);
    const para = statusLabel(evento.valor_novo);
    return `${de} → ${para}`;
  }
  if (evento.acao === "update") {
    try {
      const depois = JSON.parse(evento.valor_novo);
      const partes = [];
      if (depois.localizacao) partes.push(`localização: ${depois.localizacao}`);
      if (depois.saude_bateria) partes.push(`bateria: ${depois.saude_bateria}%`);
      return partes.join(", ") || null;
    } catch {
      return null;
    }
  }
  return null;
}

const EMPTY_EDIT_FORM = { localizacao: "", saude_bateria: "", status: "" };

// Modal único para visualizar e editar uma unidade — evita duplicar a
// estrutura (IMEI/origem/status/bateria/localização/histórico) entre uma
// tela de "detalhe" e uma de "edição" separadas. `editing` alterna entre
// texto somente-leitura e campos de formulário para os mesmos dados.
function DetalheUnidade({ unidadeId, onClose, canEdit }) {
  const [loading, setLoading] = useState(true);
  const [unidade, setUnidade] = useState(null);
  const [historico, setHistorico] = useState([]);
  const [venda, setVenda] = useState(null);
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState(EMPTY_EDIT_FORM);
  const [submitting, setSubmitting] = useState(false);

  const carregar = () => {
    setLoading(true);
    return Promise.all([unidadesApi.get(unidadeId), unidadesApi.historico(unidadeId)]).then(([uRes, hRes]) => {
      if (uRes?.ok) setUnidade(uRes.unidade);
      else toast.error(uRes?.erro || "Erro ao carregar unidade");
      setHistorico(hRes?.ok ? (hRes.historico || []) : []);
      // KI-062 -- `venda_id` é gravado por marcar_vendida e limpo por liberar_venda (cancelamento).
      const vendaId = uRes?.ok ? uRes.unidade?.venda_id : null;
      if (!vendaId) { setVenda(null); return null; }
      return vendasApi.get(vendaId).then((vRes) => {
        if (!vRes?.ok) { setVenda(null); return; }
        const item = (vRes.itens || []).find((i) => i.unidade_serializada_id === unidadeId) || null;
        setVenda({ ...vRes.venda, item });
      }).catch(() => setVenda(null));
    }).finally(() => setLoading(false));
  };

  useEffect(() => {
    carregar();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [unidadeId]);

  const origem = origemUnidadeLabel(unidade?.origem_tipo);
  const transicoesDisponiveis = unidade ? (TRANSICOES_VALIDAS[unidade.status] || []) : [];

  const abrirEdicao = () => {
    setForm({
      localizacao: unidade.localizacao || "",
      saude_bateria: unidade.saude_bateria || "",
      status: unidade.status || "",
    });
    setEditing(true);
  };

  const salvar = async () => {
    setSubmitting(true);
    try {
      if (form.status && form.status !== unidade.status) {
        const resStatus = await unidadesApi.updateStatus(unidadeId, form.status);
        if (!resStatus?.ok) {
          toast.error(resStatus?.erro || "Erro ao atualizar status");
          setSubmitting(false);
          return;
        }
      }
      const resCampos = await unidadesApi.update(unidadeId, {
        localizacao: form.localizacao,
        saude_bateria: form.saude_bateria,
      });
      if (!resCampos?.ok) {
        toast.error(resCampos?.erro || "Erro ao salvar alterações");
        return;
      }
      toast.success("Unidade atualizada!");
      setEditing(false);
      await carregar();
    } catch {
      toast.error("Erro ao salvar alterações");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <DeviceMobile className="h-5 w-5 text-primary" />
            {loading ? "Carregando..." : (unidade?.origem_label || "Unidade")}
          </DialogTitle>
          <DialogDescription>
            {editing ? "Editando localização, saúde da bateria e status" : "Detalhes da unidade serializada — IMEI, status e histórico"}
          </DialogDescription>
        </DialogHeader>

        {loading ? (
          <div className="flex items-center justify-center h-24">
            <CircleNotch className="h-5 w-5 animate-spin text-primary" />
          </div>
        ) : !unidade ? (
          <p className="text-sm text-muted-foreground">Unidade não encontrada.</p>
        ) : (
          <div className="space-y-5 mt-2">
            <div className="grid grid-cols-2 gap-3 bg-secondary/40 rounded-xl p-4">
              <div className="col-span-2">
                <p className="text-xs text-muted-foreground uppercase tracking-wider">IMEI / Serial</p>
                <p className="font-mono text-card-foreground">{unidade.imei || "—"}</p>
                {editing && <p className="text-xs text-muted-foreground mt-0.5">Imutável após o cadastro</p>}
              </div>
              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Origem</p>
                <Badge variant="tag" className="mt-0.5">{origem}</Badge>
              </div>

              {editing ? (
                <div className="space-y-1.5">
                  <Label htmlFor="unidade-status">Status</Label>
                  <Select value={form.status} onValueChange={(v) => setForm((p) => ({ ...p, status: v }))}>
                    <SelectTrigger id="unidade-status" className="w-full" aria-label="Status"><SelectValue /></SelectTrigger>
                    <SelectContent>
                      <SelectItem value={unidade.status}>{statusLabel(unidade.status)} (atual)</SelectItem>
                      {transicoesDisponiveis.map((s) => (
                        <SelectItem key={s} value={s}>{statusLabel(s)}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              ) : (
                <div>
                  <p className="text-xs text-muted-foreground uppercase tracking-wider">Status</p>
                  <div className="mt-0.5">
                    <Badge variant={statusVariant(unidade.status)}>{statusLabel(unidade.status)}</Badge>
                  </div>
                </div>
              )}

              {editing ? (
                <div className="space-y-1.5">
                  <Label htmlFor="unidade-bateria">Saúde da bateria (%)</Label>
                  <Input
                    id="unidade-bateria" type="number" min="0" max="100"
                    value={form.saude_bateria}
                    onChange={(e) => setForm((p) => ({ ...p, saude_bateria: e.target.value }))}
                  />
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <BatteryMedium className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-card-foreground text-sm">
                    {unidade.saude_bateria != null && unidade.saude_bateria !== "" ? `${unidade.saude_bateria}% de saúde` : "Saúde da bateria não registrada"}
                  </span>
                </div>
              )}

              {editing ? (
                <div className="space-y-1.5">
                  <Label htmlFor="unidade-localizacao">Localização</Label>
                  <Input
                    id="unidade-localizacao"
                    placeholder="Ex.: Loja, Bancada, Gaveta 3..."
                    value={form.localizacao}
                    onChange={(e) => setForm((p) => ({ ...p, localizacao: e.target.value }))}
                  />
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-muted-foreground shrink-0" />
                  <span className="text-card-foreground text-sm">{unidade.localizacao || "Localização não registrada"}</span>
                </div>
              )}

              <div>
                <p className="text-xs text-muted-foreground uppercase tracking-wider">Cadastrado em</p>
                <p className="text-card-foreground text-sm">{formatDate(unidade.criado_em)}</p>
              </div>
            </div>

            {/* BR-092 -- custo do aparelho comprado; o backend só manda para admin/financeiro */}
            {unidade.custo_aparelho && (
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Custo do aparelho</p>
                <dl className="grid grid-cols-3 gap-3 bg-secondary/40 rounded-xl p-3 text-sm">
                  <div>
                    <dt className="text-xs text-muted-foreground">Compra</dt>
                    <dd className="text-card-foreground">{formatCurrency(unidade.custo_aparelho.valor_compra)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Peças do conserto</dt>
                    <dd className="text-card-foreground">{formatCurrency(unidade.custo_aparelho.custo_pecas)}</dd>
                  </div>
                  <div>
                    <dt className="text-xs text-muted-foreground">Custo total</dt>
                    <dd data-testid="unidade-custo-total" className="font-medium text-card-foreground">
                      {formatCurrency(unidade.custo_aparelho.custo_total)}
                    </dd>
                  </div>
                </dl>
              </div>
            )}

            {/* KI-062 -- comprador e garantia de venda vêm da venda vinculada (`venda_id`) */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Cliente atual</p>
                {venda ? (
                  <p data-testid="unidade-comprador" className="text-sm text-card-foreground bg-secondary/40 rounded-xl p-3">
                    {venda.cliente_nome || "—"}
                    <span className="block text-xs text-muted-foreground">Venda #{venda.id} · {formatDate(venda.criado_em)}</span>
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground bg-secondary/40 rounded-xl p-3">Sem venda registrada.</p>
                )}
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Garantia</p>
                {venda?.item?.garantia_data_fim ? (
                  <p data-testid="unidade-garantia" className="text-sm text-card-foreground bg-secondary/40 rounded-xl p-3">
                    {venda.item.garantia_nome || "Garantia"}
                    <span className="block text-xs text-muted-foreground">até {formatDate(venda.item.garantia_data_fim)}</span>
                  </p>
                ) : (
                  <p className="text-sm text-muted-foreground bg-secondary/40 rounded-xl p-3">
                    {venda ? "Venda sem garantia registrada." : "Não aplicável — sem venda."}
                  </p>
                )}
              </div>
            </div>

            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <ClockCounterClockwise className="h-3.5 w-3.5" /> Histórico {historico.length > 0 && `(${historico.length})`}
              </p>
              {historico.length === 0 ? (
                <p className="text-sm text-muted-foreground bg-secondary/40 rounded-xl p-3">Nenhum evento registrado.</p>
              ) : (
                <div className="space-y-1.5">
                  {historico.map((evento) => (
                    <div key={evento.id} className="flex items-center justify-between text-sm bg-secondary/40 rounded-xl px-3 py-2">
                      <div>
                        <span className="text-card-foreground font-medium">{ACAO_LABEL[evento.acao] || evento.acao}</span>
                        {eventoDescricao(evento) && (
                          <span className="text-muted-foreground ml-2">{eventoDescricao(evento)}</span>
                        )}
                      </div>
                      <div className="text-muted-foreground text-xs text-right">
                        {evento.usuario_nome && <div>{evento.usuario_nome}</div>}
                        <div>{formatDateTime(evento.criado_em)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        <DialogFooter className="mt-4">
          {editing ? (
            <>
              <Button type="button" variant="outline" onClick={() => setEditing(false)} disabled={submitting}>Cancelar</Button>
              <Button type="button" onClick={salvar} disabled={submitting}>
                {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                {submitting ? "Salvando..." : "Salvar"}
              </Button>
            </>
          ) : (
            <>
              <Button type="button" variant="outline" onClick={onClose}>Fechar</Button>
              {canEdit && unidade && (
                <Button type="button" onClick={abrirEdicao}>
                  <Pencil className="h-4 w-4 mr-2" /> Editar
                </Button>
              )}
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function UnidadesSerializadas() {
  const { user } = useAuth();
  const canEdit = user?.perfil === "admin" || user?.perfil === "tecnico";
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [detalheId, setDetalheId] = useState(null);

  // Campo de busca com debounce: o valor digitado (searchInput) só vira o
  // termo de busca de fato (search) 350ms depois de parar de digitar —
  // evita 1 requisição por tecla contra a API (C1.3.3: "busca rápida mesmo
  // com milhares de unidades").
  const [searchInput, setSearchInput] = useState("");
  const [search, setSearch] = useState("");
  const [origemFilter, setOrigemFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [saudeBateriaFaixa, setSaudeBateriaFaixa] = useState("");
  const [localizacaoInput, setLocalizacaoInput] = useState("");
  const [localizacao, setLocalizacao] = useState("");
  const [sort, setSort] = useState("recente");
  const [page, setPage] = useState(1);
  const [reloadToken, setReloadToken] = useState(0);

  // Debounce da busca/localização: volta para a página 1 junto (dentro do
  // callback assíncrono do setTimeout, não sincronamente no corpo do efeito).
  useEffect(() => {
    const t = setTimeout(() => { setSearch(searchInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [searchInput]);

  useEffect(() => {
    const t = setTimeout(() => { setLocalizacao(localizacaoInput); setPage(1); }, 350);
    return () => clearTimeout(t);
  }, [localizacaoInput]);

  // Filtros de seleção (origem/status/faixa de bateria/ordenação) resetam a
  // página diretamente no handler, não via efeito reativo — mesma correção
  // já aplicada em Clientes.jsx (evita setState síncrono no corpo do efeito).
  const handleOrigemChange = (v) => { setOrigemFilter(v === "all" ? "" : v); setPage(1); };
  const handleStatusChange = (v) => { setStatusFilter(v === "all" ? "" : v); setPage(1); };
  const handleSaudeBateriaChange = (v) => { setSaudeBateriaFaixa(v === "all" ? "" : v); setPage(1); };
  const handleSortChange = (v) => { setSort(v); setPage(1); };

  useEffect(() => {
    let ativo = true;

    async function buscar() {
      setLoading(true);
      const params = { page, per_page: PER_PAGE, sort };
      if (search) params.q = search;
      if (origemFilter) params.origem = origemFilter;
      if (statusFilter) params.status = statusFilter;
      if (saudeBateriaFaixa) params.saude_bateria_faixa = saudeBateriaFaixa;
      if (localizacao) params.localizacao = localizacao;

      try {
        const res = await unidadesApi.list(params);
        if (!ativo) return;
        if (res?.ok) {
          setItems(res.items || []);
          setTotal(res.total || 0);
          setLoadError(false);
        } else {
          toast.error(res?.erro || "Erro ao carregar unidades");
          setLoadError(true);
        }
      } catch {
        if (ativo) {
          toast.error("Erro ao carregar unidades");
          setLoadError(true);
        }
      } finally {
        if (ativo) setLoading(false);
      }
    }

    buscar();
    return () => { ativo = false; };
  }, [page, search, origemFilter, statusFilter, saudeBateriaFaixa, localizacao, sort, reloadToken]);

  const totalPaginas = Math.max(1, Math.ceil(total / PER_PAGE));
  const filtrosAtivos = Boolean(search || origemFilter || statusFilter || saudeBateriaFaixa || localizacao);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Unidades Serializadas</h1>
          <p className="text-muted-foreground text-sm">
            Localize qualquer aparelho da loja por IMEI, serial, modelo, marca ou localização
          </p>
        </div>
      </div>

      {loading ? (
        <ListSkeleton rows={6} />
      ) : loadError && items.length === 0 ? (
        <ErrorState title="Não foi possível carregar as unidades." onRetry={() => setReloadToken((t) => t + 1)} />
      ) : (
        <Reveal className="space-y-5">
          {/* Card de resumo — reflete o resultado filtrado atual, não o total global
              (calcular Disponíveis/Em Reparo globais exigiria consultas extras a
              cada filtro, contra o critério de manter a busca rápida). */}
          <div className="bg-card border border-border rounded-xl p-4 w-fit min-w-[160px]">
            <p className="text-2xl font-bold text-foreground">{total}</p>
            <p className="text-xs text-muted-foreground mt-0.5">
              {filtrosAtivos ? "unidades encontradas" : "unidades no total"}
            </p>
          </div>

          {/* Busca */}
          <div className="bg-card border border-border rounded-xl p-4">
            <div className="relative">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar por IMEI, serial, modelo, marca ou localização..."
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                className="pl-8"
              />
            </div>
          </div>

          {/* Filtros */}
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <FilterSelect
              value={origemFilter || "all"}
              onValueChange={handleOrigemChange}
              placeholder="Origem"
              className="w-40"
              options={[
                { value: "all", label: "Todas as origens" },
                { value: "estoque", label: "Estoque" },
                { value: "produto", label: "Produto" },
              ]}
            />

            <FilterSelect
              value={statusFilter || "all"}
              onValueChange={handleStatusChange}
              placeholder="Status"
              className="w-44"
              options={[{ value: "all", label: "Todos os status" }, ...Object.keys(STATUS_LABEL).map((value) => ({ value, label: STATUS_LABEL[value] }))]}
            />

            <FilterSelect
              value={saudeBateriaFaixa || "all"}
              onValueChange={handleSaudeBateriaChange}
              placeholder="Saúde da bateria"
              className="w-48"
              options={[{ value: "all", label: "Qualquer saúde de bateria" }, ...SAUDE_BATERIA_OPTIONS]}
            />

            <div className="relative w-48">
              <MapPin className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <FilterInput
                placeholder="Localização..."
                value={localizacaoInput}
                onChange={(e) => setLocalizacaoInput(e.target.value)}
                className="w-full pl-8"
              />
            </div>

            <FilterSelect
              value={sort}
              onValueChange={handleSortChange}
              placeholder="Ordenar por"
              className="w-44"
              options={SORT_OPTIONS}
            />
          </FilterBar>

          {items.length === 0 ? (
            <EmptyState
              icon={filtrosAtivos ? undefined : Barcode}
              title={filtrosAtivos ? "Nenhuma unidade corresponde à busca/filtros atuais." : "Nenhuma unidade serializada cadastrada ainda."}
            />
          ) : (
            <>
              <div className="bg-card rounded-xl border border-border overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b border-border">
                        {["IMEI", "Origem", "Status", "Localização", "Cadastrado em"].map((h) => (
                          <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">
                            {h}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border">
                      {items.map((item) => {
                        const origem = origemUnidadeLabel(item.origem_tipo);
                        return (
                          <tr
                            key={item.id}
                            className={`${interactiveRowClassName} cursor-pointer`}
                            data-testid={`unidade-row-${item.id}`}
                            onClick={() => setDetalheId(item.id)}
                          >
                            <td className="px-4 py-3">
                              <span className="font-medium text-card-foreground font-mono">{item.imei || "—"}</span>
                            </td>
                            <td className="px-4 py-3">
                              <div className="flex items-center gap-2">
                                <Badge variant="tag">{origem}</Badge>
                                <span className="text-muted-foreground text-xs">{item.origem_label || "—"}</span>
                              </div>
                            </td>
                            <td className="px-4 py-3">
                              <Badge variant={statusVariant(item.status)}>{statusLabel(item.status)}</Badge>
                            </td>
                            <td className="px-4 py-3 text-muted-foreground">{item.localizacao || "—"}</td>
                            <td className="px-4 py-3 text-muted-foreground">{formatDate(item.criado_em)}</td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="flex items-center justify-between text-sm text-muted-foreground">
                <span>Página {page} de {totalPaginas} — {total} {total === 1 ? "unidade" : "unidades"}</span>
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

      {detalheId && <DetalheUnidade unidadeId={detalheId} onClose={() => setDetalheId(null)} canEdit={canEdit} />}
    </div>
  );
}
