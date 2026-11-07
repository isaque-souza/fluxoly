import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { CircleNotch, Plus, Minus, MagnifyingGlass } from "@phosphor-icons/react";
import { constantes as constApi, reparos as reparosApi, estoque as estoqueApi, ordens as ordensApi, precos as precosApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Reveal } from "@/components/ui/reveal";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { LooseMetric } from "@/components/ui/loose-metric";
import { formatCurrency, OS_TYPES_FALLBACK, STATUS_OPTIONS_FALLBACK } from "@/lib/constants";

const EMPTY_FORM = {
  tipo: "Assistencia",
  cliente: "",
  modelo: "",
  cor: "",
  imei: "",
  tecnico: "",
  vendedor: "",
  status: "Em andamento",
  valor_cobrado: "",
  valor_descontado: "",
  data_os: new Date().toISOString().split("T")[0],
  observacoes: "",
};

export default function NewOrder() {
  const navigate = useNavigate();
  const [form, setForm] = useState(EMPTY_FORM);
  const [constants, setConstants] = useState(null);
  const [reparosList, setReparosList] = useState([]);
  const [estoqueList, setEstoqueList] = useState([]);
  const [selectedReparos, setSelectedReparos] = useState([]);
  const [pecas, setPecas] = useState({});
  const [stockSearch, setStockSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [suggestedPrice, setSuggestedPrice] = useState(null);

  useEffect(() => {
    Promise.all([constApi.get(), reparosApi.list(), estoqueApi.list()]).then(([c, r, e]) => {
      if (c?.ok) setConstants(c);
      if (r?.ok) setReparosList(r.reparos || []);
      if (e?.ok) setEstoqueList(e.items || []);
      setLoading(false);
    }).catch(() => {
      toast.error("Erro ao carregar dados da nova ordem");
      setLoading(false);
    });
  }, []);

  const setField = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  // Auto-preenche valor_cobrado a partir da tabela de preços
  useEffect(() => {
    if (!form.modelo || selectedReparos.length === 0) {
      setSuggestedPrice(null);
      return;
    }

    const tabela = "clientes";
    precosApi.sugerir({
      modelo: form.modelo,
      reparo_ids: selectedReparos.join(","),
      tabela,
    }).then((res) => {
      if (res?.ok && res.encontrado) {
        setSuggestedPrice(res.valor);
        if (!form.valor_cobrado) {
          setForm((p) => ({ ...p, valor_cobrado: String(res.valor) }));
        }
      } else {
        setSuggestedPrice(null);
      }
    });
  }, [form.modelo, form.valor_cobrado, selectedReparos]);

  const toggleReparo = (id) => {
    setSelectedReparos((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  const adjustPeca = (id, delta) => {
    setPecas((prev) => {
      const current = prev[id] || 0;
      const next = Math.max(0, current + delta);
      if (next === 0) {
        const { [id]: _, ...rest } = prev;
        return rest;
      }
      return { ...prev, [id]: next };
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        valor_cobrado: parseFloat(form.valor_cobrado) || 0,
        valor_descontado: parseFloat(form.valor_descontado) || 0,
        reparo_ids: selectedReparos,
        pecas_ids: Object.entries(pecas).flatMap(([k, v]) => Array.from({ length: v }, () => parseInt(k, 10))),
      };
      const res = await ordensApi.create(payload);
      if (res?.ok) {
        toast.success("Ordem criada com sucesso!");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao criar ordem");
      }
    } catch {
      toast.error("Erro ao criar ordem");
    } finally {
      setSubmitting(false);
    }
  };

  const normalizedModelo = form?.modelo?.toLowerCase().trim();
  const filteredEstoque = estoqueList.filter((item) => {
    const itemModelo = item.modelo?.toLowerCase().trim() || "";
    const matchesSearch = item.descricao?.toLowerCase().includes(stockSearch.toLowerCase()) || itemModelo.includes(stockSearch.toLowerCase());
    const matchesModelo = !normalizedModelo || itemModelo === "universal" || itemModelo === normalizedModelo;
    return matchesSearch && matchesModelo;
  });

  const pecasTotal = useMemo(() => {
    return Object.entries(pecas).reduce((sum, [id, quantity]) => {
      const estoqueItem = estoqueList.find((item) => String(item.id) === String(id));
      return sum + (estoqueItem?.valor || 0) * (quantity || 0);
    }, 0);
  }, [pecas, estoqueList]);

  const reparosDisponiveis = useMemo(() => {
    return [...reparosList]
      .filter((reparo) => {
        const nome = (reparo?.nome || "").trim().toLowerCase();
        return nome && !["nao informado", "não informado", "analise", "análise"].includes(nome);
      })
      .sort((a, b) => (a.nome || "").localeCompare(b.nome || "", "pt-BR"));
  }, [reparosList]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <CircleNotch className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Nova Ordem de Serviço</h1>
        <p className="text-muted-foreground text-sm">Preencha todos os dados da OS</p>
      </div>

      <Reveal>
      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Cliente / Tipo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Cliente</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 space-y-1.5">
                 <Label htmlFor="order-cliente">Nome do Cliente *</Label>
                 <Input id="order-cliente" value={form.cliente} onChange={(e) => setField("cliente", e.target.value)} placeholder="Nome completo" required />
              </div>
              <div className="space-y-1.5">
                <Label>Tipo de OS</Label>
                <Select value={form.tipo} onValueChange={(v) => setField("tipo", v)}>
                  <SelectTrigger aria-label="Tipo de OS"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(constants?.os_tipos || OS_TYPES_FALLBACK).map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                 <Label htmlFor="order-data-os">Data da OS</Label>
                 <Input id="order-data-os" type="date" value={form.data_os} onChange={(e) => setField("data_os", e.target.value)} />
              </div>
            </div>
          </PanelContent>
        </Panel>

        {/* Aparelho */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Aparelho</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Modelo *</Label>
                <Select value={form.modelo} onValueChange={(v) => { setField("modelo", v); setField("cor", ""); }}>
                  <SelectTrigger aria-label="Modelo"><SelectValue placeholder="Selecione o modelo" /></SelectTrigger>
                  <SelectContent>
                    {(constants?.iphone_models || []).map((m) => (
                      <SelectItem key={m} value={m}>{m}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Cor</Label>
                <Select value={form.cor} onValueChange={(v) => setField("cor", v)}>
                  <SelectTrigger aria-label="Cor"><SelectValue placeholder="Cor do aparelho" /></SelectTrigger>
                  <SelectContent>
                    {(constants?.iphone_colors?.[form.modelo] || []).map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2 space-y-1.5">
                 <Label htmlFor="order-imei">IMEI</Label>
                 <Input id="order-imei" value={form.imei} onChange={(e) => setField("imei", e.target.value)} placeholder="000000000000000" maxLength={16} />
              </div>
            </div>
          </PanelContent>
        </Panel>

        {/* Serviço */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Serviço</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label>Técnico</Label>
                <Select value={form.tecnico} onValueChange={(v) => setField("tecnico", v)}>
                  <SelectTrigger aria-label="Técnico"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {(constants?.tecnicos || []).map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Vendedor</Label>
                <Select value={form.vendedor} onValueChange={(v) => setField("vendedor", v)}>
                  <SelectTrigger aria-label="Vendedor"><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {(constants?.vendedores || []).map((v) => (
                      <SelectItem key={v} value={v}>{v}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Status</Label>
                <Select value={form.status} onValueChange={(v) => setField("status", v)}>
                  <SelectTrigger aria-label="Status"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {(constants?.status_opcoes || STATUS_OPTIONS_FALLBACK).map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {reparosDisponiveis.length > 0 && (
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <Label>Tipos de Reparo</Label>
                  <span className="text-xs text-muted-foreground">{selectedReparos.length} selecionado(s)</span>
                </div>
                <div className="rounded-xl border border-border/70 bg-secondary/30 p-3">
                  <div className="grid max-h-56 grid-cols-1 gap-2 overflow-y-auto pr-1 sm:grid-cols-2 xl:grid-cols-3">
                    {reparosDisponiveis.map((r) => {
                      const selecionado = selectedReparos.includes(r.id);
                      return (
                        <label
                          key={r.id}
                          className={[
                            "group flex cursor-pointer items-center gap-2 rounded-lg border px-2.5 py-2 text-sm transition-colors",
                            selecionado
                              ? "border-primary/60 bg-primary/10"
                              : "border-border/70 bg-background/50 hover:border-primary/40 hover:bg-background",
                          ].join(" ")}
                        >
                          <Checkbox
                            checked={selecionado}
                            onCheckedChange={() => toggleReparo(r.id)}
                          />
                          <span className="font-medium uppercase tracking-wide text-card-foreground">{r.nome}</span>
                        </label>
                      );
                    })}
                  </div>
                </div>
              </div>
            )}
          </PanelContent>
        </Panel>

        {/* Financeiro */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Financeiro</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-3">
              <LooseMetric label="Custo total de peças" value={formatCurrency(pecasTotal)} />
              <LooseMetric
                label="Sugestão de serviço"
                value={suggestedPrice !== null ? formatCurrency(suggestedPrice) : "—"}
                valueClassName="text-primary"
              />
              <div className="flex items-end justify-end">
                <Button type="button" disabled={!suggestedPrice} onClick={() => suggestedPrice !== null && setField("valor_cobrado", String(suggestedPrice))}>
                  Usar sugestão
                </Button>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <Label htmlFor="order-valor-cobrado">Valor Cobrado (R$)</Label>
                <Input id="order-valor-cobrado" type="number" step="0.01" min="0" value={form.valor_cobrado} onChange={(e) => setField("valor_cobrado", e.target.value)} placeholder="0,00" />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="order-valor-descontado">Valor com Desconto (R$)</Label>
                <Input id="order-valor-descontado" type="number" step="0.01" min="0" value={form.valor_descontado} onChange={(e) => setField("valor_descontado", e.target.value)} placeholder="0,00" />
              </div>
            </div>
          </PanelContent>
        </Panel>

        {/* Peças do Estoque */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Peças do Estoque</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="relative">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Buscar peça..."
                value={stockSearch}
                onChange={(e) => setStockSearch(e.target.value)}
                className="pl-8"
              />
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {filteredEstoque.length === 0 ? (
                <p className="text-muted-foreground text-sm text-center py-4">Nenhuma peça encontrada</p>
              ) : (
                filteredEstoque.map((item) => (
                  <div key={item.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-card-foreground truncate">{item.descricao}</p>
                      <p className="text-xs text-muted-foreground">
                        {item.modelo} • Estoque: {item.quantidade} • {formatCurrency(item.valor || 0)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={() => adjustPeca(item.id, -1)}>
                        <Minus className="h-3.5 w-3.5" />
                      </Button>
                      <span className="w-6 text-center text-sm font-medium">{pecas[item.id] || 0}</span>
                      <Button type="button" variant="ghost" size="icon" className="h-7 w-7" onClick={() => adjustPeca(item.id, 1)}>
                        <Plus className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </PanelContent>
        </Panel>

        {/* Observações */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Observações</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <Textarea
              value={form.observacoes}
              onChange={(e) => setField("observacoes", e.target.value)}
              placeholder="Observações adicionais sobre a OS..."
            />
          </PanelContent>
        </Panel>

        <div className="flex gap-3">
            <Button type="submit" disabled={submitting} data-testid="order-create-button">
              {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
              Criar Ordem
            </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/ordens")}>
            Cancelar
          </Button>
        </div>
      </form>
      </Reveal>
    </div>
  );
}
