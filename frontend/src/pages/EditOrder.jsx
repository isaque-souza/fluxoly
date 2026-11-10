import { useState, useEffect, useRef, useMemo } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { toast } from "sonner";
import { CircleNotch, Plus, Minus, MagnifyingGlass, QrCode, Copy, ArrowSquareOut, FilePdf } from "@phosphor-icons/react";
import ShoppingModal from "@/components/shopping/ShoppingModal";
import { constantes as constApi, reparos as reparosApi, estoque as estoqueApi, ordens as ordensApi, checklist as checklistApi, precos as precosApi, tiposGarantia as tiposGarantiaApi } from "@/api/client";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { formatCurrency, getOrderDisplayNumber, OS_TYPES_FALLBACK, STATUS_OPTIONS_FALLBACK, TIPO_OS_INTERNA } from "@/lib/constants";
import { Checkbox } from "@/components/ui/checkbox";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Reveal } from "@/components/ui/reveal";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { LooseMetric } from "@/components/ui/loose-metric";
import { useAuth } from "@/contexts/AuthContext";
import { baixarPdfOs } from "@/lib/osPdf";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";

export default function EditOrder() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [form, setForm] = useState(null);
  const [constants, setConstants] = useState(null);
  const [reparosList, setReparosList] = useState([]);
  const [estoqueList, setEstoqueList] = useState([]);
  const [selectedReparos, setSelectedReparos] = useState([]);
  const [pecas, setPecas] = useState({});
  const [stockSearch, setStockSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [cancelDialog, setCancelDialog] = useState(false);
  const [shoppingModalOpen, setShoppingModalOpen] = useState(false);
  const [suggestedPrice, setSuggestedPrice] = useState(null);
  const [checklistMeta, setChecklistMeta] = useState(null);
  const [checklistDialog, setChecklistDialog] = useState(false);
  const [checklistLoading, setChecklistLoading] = useState(false);
  const [pdfLoading, setPdfLoading] = useState(null);
  const isAdmin = useAuth()?.user?.perfil === "admin";
  const [orderDisplayNumber, setOrderDisplayNumber] = useState("");
  const initialized = useRef(false);

  // V1.5 -- Garantia de Reparo (BR-061): exige um Tipo de Garantia por
  // reparo selecionado na transição para Finalizado -- tanto pelo botão
  // dedicado quanto pelo formulário completo (troca de Status + Salvar).
  const [statusOriginal, setStatusOriginal] = useState("");
  const [tiposGarantiaList, setTiposGarantiaList] = useState([]);
  const [garantiaDialogOpen, setGarantiaDialogOpen] = useState(false);
  const [garantiaPorReparo, setGarantiaPorReparo] = useState({});
  const [garantiaAcaoPendente, setGarantiaAcaoPendente] = useState(null);
  const [enviandoGarantiaDialog, setEnviandoGarantiaDialog] = useState(false);

  useEffect(() => {
    Promise.all([
      ordensApi.get(id),
      constApi.get(),
      reparosApi.list(),
      estoqueApi.list(),
      tiposGarantiaApi.list(),
    ]).then(([osRes, constRes, rRes, eRes, tgRes]) => {
      if (tgRes?.ok) setTiposGarantiaList(tgRes.items || []);
      if (osRes?.ok && osRes.ordem) {
        const os = osRes.ordem;
        setOrderDisplayNumber(getOrderDisplayNumber(os));
        setStatusOriginal(os.status || "Em andamento");
        setForm({
          tipo: os.tipo || "Assistencia",
          cliente: os.cliente || "",
          modelo: os.modelo || "",
          cor: os.cor || "",
          imei: os.imei || "",
          tecnico: os.tecnico || "",
          vendedor: os.vendedor || "",
          status: os.status || "Em andamento",
          valor_cobrado: os.valor_cobrado || "",
          valor_descontado: os.valor_descontado || "",
          data_os: os.data ? os.data.split("T")[0] : new Date().toISOString().split("T")[0],
          observacoes: os.observacoes || "",
        });
        setSelectedReparos(os.reparo_ids || []);
        const pecasMap = {};
        (os.pecas_usadas || []).forEach((p) => {
          const estoqueId = String(p.estoque_id);
          const quantidade = Number(p.quantidade) || 0;
          pecasMap[estoqueId] = (pecasMap[estoqueId] || 0) + quantidade;
        });
        setPecas(pecasMap);

        const estoqueAtivo = eRes?.ok ? (eRes.items || []) : [];
        const idsAtivos = new Set(estoqueAtivo.map((item) => String(item.id)));
        const consumidosForaDoEstoque = [];
        const idsConsumidosIncluidos = new Set();

        (os.pecas_usadas || []).forEach((p) => {
          const estoqueId = String(p.estoque_id || "");
          if (!estoqueId || idsAtivos.has(estoqueId) || idsConsumidosIncluidos.has(estoqueId)) {
            return;
          }

          consumidosForaDoEstoque.push({
            id: p.estoque_id,
            descricao: p.descricao || "Peca consumida",
            valor: Number(p.valor) || 0,
            fornecedor: p.fornecedor || "Nao informado",
            quantidade: 0,
            modelo: p.modelo || os.modelo || "",
          });
          idsConsumidosIncluidos.add(estoqueId);
        });

        setEstoqueList([...estoqueAtivo, ...consumidosForaDoEstoque]);
      } else {
        toast.error("Ordem não encontrada");
        navigate("/ordens");
      }
      if (constRes?.ok) setConstants(constRes);
      if (rRes?.ok) setReparosList(rRes.reparos || []);
      setLoading(false);
      initialized.current = true;
    }).catch(() => {
      // `form` só é preenchido dentro do branch de sucesso do `.then()` acima -- em rejeição de
      // rede, `form` permanece `null` (useState inicial). Sem navegar para longe daqui, o restante
      // do componente tentaria renderizar `form.cliente`/etc. contra `null` e quebraria. Mesmo
      // destino (`/ordens`) já usado no branch de erro de negocio (`!osRes?.ok`) alguns paragrafos
      // acima, só que para rejeição de rede em vez de `{ok:false}`.
      toast.error("Erro ao carregar dados da ordem");
      setLoading(false);
      navigate("/ordens");
    });

    checklistApi.getByOrder(id).then((res) => {
      if (res?.ok) {
        setChecklistMeta(res.checklist || null);
      }
    });
  }, [id, navigate]);

  const setField = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  // Auto-preenche valor_cobrado a partir da tabela de preços (somente após carga inicial)
  useEffect(() => {
    if (!initialized.current || !form?.modelo || selectedReparos.length === 0) {
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
  }, [form?.modelo, form?.valor_cobrado, selectedReparos]);

  const toggleReparo = (rid) => {
    setSelectedReparos((prev) => prev.includes(rid) ? prev.filter((x) => x !== rid) : [...prev, rid]);
  };

  const adjustPeca = (pid, delta) => {
    setPecas((prev) => {
      const next = Math.max(0, (prev[pid] || 0) + delta);
      if (next === 0) { const { [pid]: _, ...rest } = prev; return rest; }
      return { ...prev, [pid]: next };
    });
  };

  // Transição real para Finalizado (não reafirmar um status já finalizado) --
  // só nesse caso a Garantia de Reparo é exigida (BR-061).
  // BR-090 -- OS interna (aparelho comprado): não tem garantia de reparo, cliente, vendedor nem valores,
  // e não pode virar OS de cliente (nem o contrário) depois de criada.
  const interna = form?.tipo === TIPO_OS_INTERNA;
  const precisaSelecionarGarantia = !interna && form?.status === "Finalizado" && statusOriginal !== "Finalizado";
  const tiposDisponiveis = (constants?.os_tipos || OS_TYPES_FALLBACK).filter((t) => (t === TIPO_OS_INTERNA) === interna);

  const executarSubmit = async (garantias) => {
    setSubmitting(true);
    try {
      const payload = {
        ...form,
        valor_cobrado: interna ? 0 : parseFloat(form.valor_cobrado) || 0,
        valor_descontado: interna ? 0 : parseFloat(form.valor_descontado) || 0,
        reparo_ids: selectedReparos,
        pecas_ids: Object.entries(pecas).flatMap(([k, v]) => Array.from({ length: v }, () => parseInt(k, 10))),
        ...(garantias ? { garantias } : {}),
      };
      const res = await ordensApi.update(id, payload);
      if (res?.ok) {
        toast.success("Ordem atualizada!");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao atualizar ordem");
      }
    } catch {
      toast.error("Erro ao atualizar ordem");
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (precisaSelecionarGarantia) {
      setGarantiaAcaoPendente("submit");
      setGarantiaDialogOpen(true);
      return;
    }
    await executarSubmit();
  };

  const handleCancelOrder = async () => {
    try {
      const res = await ordensApi.patchStatus(id, "Cancelado");
      if (res?.ok) {
        toast.success("Ordem cancelada");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao cancelar");
      }
    } catch {
      toast.error("Erro ao cancelar ordem");
    } finally {
      setCancelDialog(false);
    }
  };

  const executarFinalize = async (garantias) => {
    try {
      const res = await ordensApi.patchStatus(id, "Finalizado", garantias);
      if (res?.ok) {
        toast.success("Ordem finalizada!");
        navigate("/ordens");
      } else {
        toast.error(res?.erro || "Erro ao finalizar");
      }
    } catch {
      toast.error("Erro ao finalizar ordem");
    }
  };

  const handleFinalize = async () => {
    if (!interna && statusOriginal !== "Finalizado") {
      setGarantiaAcaoPendente("finalize");
      setGarantiaDialogOpen(true);
      return;
    }
    await executarFinalize();
  };

  const confirmarGarantiaDialog = async () => {
    const faltando = selectedReparos.some((rid) => !garantiaPorReparo[rid]);
    if (faltando) {
      toast.error("Selecione um Tipo de Garantia para cada reparo.");
      return;
    }
    setEnviandoGarantiaDialog(true);
    try {
      if (garantiaAcaoPendente === "finalize") {
        await executarFinalize(garantiaPorReparo);
      } else if (garantiaAcaoPendente === "submit") {
        await executarSubmit(garantiaPorReparo);
      }
      setGarantiaDialogOpen(false);
    } finally {
      setEnviandoGarantiaDialog(false);
    }
  };

  const handleChecklistQr = async () => {
    setChecklistLoading(true);
    try {
      const res = await checklistApi.generateToken(id);
      if (!res?.ok) {
        toast.error(res?.erro || "Nao foi possivel gerar o QR do checklist");
        return;
      }
      setChecklistMeta(res.checklist || null);
      setChecklistDialog(true);
    } catch {
      toast.error("Nao foi possivel gerar o QR do checklist");
    } finally {
      setChecklistLoading(false);
    }
  };

  const checklistLink = checklistMeta?.public_url || "";
  const checklistQr = checklistLink ? checklistApi.qrImageUrl(checklistLink) : "";

  const copyChecklistLink = async () => {
    if (!checklistLink) return;
    try {
      await navigator.clipboard.writeText(checklistLink);
      toast.success("Link do checklist copiado");
    } catch {
      toast.error("Nao foi possivel copiar o link");
    }
  };

  // BR-095 a BR-098 -- comprovante de entrada/entrega para o cliente. O conteúdo vem do backend
  // (allowlist, BR-097) e reflete a OS salva, não edições ainda não salvas neste formulário.
  const handlePdf = async (tipo) => {
    setPdfLoading(tipo);
    try {
      const res = await ordensApi.documento(id, tipo);
      if (!res?.ok) {
        const erro = res?.erro || "Não foi possível gerar o PDF";
        if (isAdmin && erro.includes("Dados da Loja")) {
          toast.error(erro, { action: { label: "Cadastrar", onClick: () => navigate("/dados-loja") } });
        } else {
          toast.error(erro);
        }
        return;
      }
      await baixarPdfOs(res.documento, orderDisplayNumber || getOrderDisplayNumber({ id }));
    } catch {
      toast.error("Não foi possível gerar o PDF");
    } finally {
      setPdfLoading(null);
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

  // `!form` cobre a janela entre o `.catch()` da carga inicial (que faz `setLoading(false)` e
  // `navigate("/ordens")`, mas não popula `form`) e o React efetivamente desmontar este componente
  // ao trocar de rota -- sem essa guarda, esse frame tentaria renderizar `form.cliente`/etc. contra
  // `null` e quebraria (KI-048).
  if (loading || !form) {
    return (
      <div className="flex items-center justify-center h-64">
        <CircleNotch className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="max-w-4xl space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Editar Ordem #{orderDisplayNumber || getOrderDisplayNumber({ id })}</h1>
          <p className="text-muted-foreground text-sm">Atualize os dados da OS</p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button type="button" variant="outline" onClick={() => setShoppingModalOpen(true)}>Adicionar à Lista de Compras</Button>
          <Button type="button" variant="outline" onClick={handleChecklistQr} disabled={checklistLoading}>
            {checklistLoading ? <CircleNotch className="mr-2 h-4 w-4 animate-spin" /> : <QrCode className="mr-2 h-4 w-4" />}
            Checklist QR
          </Button>
          {!interna && statusOriginal !== "Cancelado" && (
            <>
              <Button type="button" variant="outline" onClick={() => handlePdf("entrada")} disabled={pdfLoading !== null}>
                {pdfLoading === "entrada" ? <CircleNotch className="mr-2 h-4 w-4 animate-spin" /> : <FilePdf className="mr-2 h-4 w-4" />}
                PDF de entrada
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => handlePdf("entrega")}
                disabled={pdfLoading !== null || statusOriginal !== "Finalizado"}
                title={statusOriginal !== "Finalizado" ? "Disponível depois que a OS for finalizada" : undefined}
              >
                {pdfLoading === "entrega" ? <CircleNotch className="mr-2 h-4 w-4 animate-spin" /> : <FilePdf className="mr-2 h-4 w-4" />}
                PDF de entrega
              </Button>
            </>
          )}
          <Button type="button" variant="outline" onClick={handleFinalize}>Finalizar OS</Button>
          <Button type="button" variant="destructive" onClick={() => setCancelDialog(true)}>Cancelar OS</Button>
        </div>
      </div>

      <Reveal className="space-y-5">
      {checklistMeta ? (
        <Panel>
          <PanelHeader>
            <PanelTitle>Checklist do aparelho</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-3">
            <div className="flex items-center justify-between gap-3 flex-wrap">
              <p className="text-sm text-muted-foreground">
                Touch: {checklistMeta.status_touch} • Audio: {checklistMeta.status_audio} • Microfone: {checklistMeta.status_microfone}
              </p>
              <Button type="button" variant="outline" onClick={() => setChecklistDialog(true)} disabled={!checklistMeta.access_token}>
                Ver QR
              </Button>
            </div>
            <p className="text-xs text-muted-foreground">
              {checklistMeta.atualizado_em
                ? `Ultima atualizacao: ${checklistMeta.atualizado_em}`
                : "Checklist ainda nao preenchido."}
            </p>
          </PanelContent>
        </Panel>
      ) : null}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Cliente / Tipo */}
        <Panel>
          <PanelHeader>
            <PanelTitle>{interna ? "Aparelho comprado (OS interna)" : "Cliente"}</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              {interna ? (
                <p className="col-span-2 text-sm text-muted-foreground">
                  Conserto de aparelho da loja: sem cliente, vendedor nem valor cobrado. As peças entram no custo do aparelho,
                  e ele fica disponível para venda quando a OS for finalizada.
                </p>
              ) : (
                <div className="col-span-2 space-y-1.5">
                  <Label htmlFor="edit-order-cliente">Nome do Cliente *</Label>
                  <Input id="edit-order-cliente" value={form.cliente} onChange={(e) => setField("cliente", e.target.value)} required />
                </div>
              )}
              <div className="space-y-1.5">
                <Label>Tipo de OS</Label>
                <Select value={form.tipo} onValueChange={(v) => setField("tipo", v)} disabled={interna}>
                  <SelectTrigger aria-label="Tipo de OS"><SelectValue /></SelectTrigger>
                  <SelectContent>
                    {tiposDisponiveis.map((t) => (
                      <SelectItem key={t} value={t}>{t}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-order-data-os">Data da OS</Label>
                <Input id="edit-order-data-os" type="date" value={form.data_os} onChange={(e) => setField("data_os", e.target.value)} />
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
                    {/* Garante que o modelo atual apareça mesmo se não estiver na lista */}
                    {(!constants?.iphone_models?.includes(form.modelo) && form.modelo) && (
                      <SelectItem key={form.modelo} value={form.modelo}>{form.modelo}</SelectItem>
                    )}
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
                    {/* Garante que a cor atual apareça mesmo se não estiver na lista */}
                    {(!constants?.iphone_colors?.[form.modelo]?.includes(form.cor) && form.cor) && (
                      <SelectItem key={form.cor} value={form.cor}>{form.cor}</SelectItem>
                    )}
                    {(constants?.iphone_colors?.[form.modelo] || []).map((c) => (
                      <SelectItem key={c} value={c}>{c}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2 space-y-1.5">
                <Label htmlFor="edit-order-imei">IMEI</Label>
                <Input id="edit-order-imei" value={form.imei} onChange={(e) => setField("imei", e.target.value)} maxLength={16} readOnly={interna} />
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
              {!interna && (
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
              )}
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

        {/* Financeiro -- OS interna não tem valor cobrado (BR-090) */}
        {!interna && (
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
                <Label htmlFor="edit-order-valor-cobrado">Valor Cobrado (R$)</Label>
                <Input id="edit-order-valor-cobrado" type="number" step="0.01" min="0" value={form.valor_cobrado} onChange={(e) => setField("valor_cobrado", e.target.value)} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="edit-order-valor-descontado">Valor com Desconto (R$)</Label>
                <Input id="edit-order-valor-descontado" type="number" step="0.01" min="0" value={form.valor_descontado} onChange={(e) => setField("valor_descontado", e.target.value)} />
              </div>
            </div>
          </PanelContent>
        </Panel>
        )}

        {/* Peças */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Peças do Estoque</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <div className="relative">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Buscar peça..." value={stockSearch} onChange={(e) => setStockSearch(e.target.value)} className="pl-8" />
            </div>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {filteredEstoque.map((item) => (
                <div key={item.id} className="flex items-center justify-between bg-secondary rounded-lg px-3 py-2">
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-card-foreground truncate">{item.descricao}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.modelo} • Estoque: {item.quantidade} • {formatCurrency(item.valor || 0)}
                      {item.quantidade <= 0 && (pecas[item.id] || 0) > 0 ? " • Consumido nesta OS" : ""}
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
              ))}
            </div>
          </PanelContent>
        </Panel>

        {/* Observações */}
        <Panel>
          <PanelHeader>
            <PanelTitle>Observações</PanelTitle>
          </PanelHeader>
          <PanelContent className="space-y-4">
            <Textarea value={form.observacoes} onChange={(e) => setField("observacoes", e.target.value)} />
          </PanelContent>
        </Panel>

        <div className="flex gap-3">
          <Button type="submit" disabled={submitting} data-testid="order-save-button">
            {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
            Salvar Alterações
          </Button>
          <Button type="button" variant="outline" onClick={() => navigate("/ordens")}>Voltar</Button>
        </div>
      </form>
      </Reveal>

      <ShoppingModal open={shoppingModalOpen} onOpenChange={setShoppingModalOpen} osId={id} onCreated={() => {/* opcional: atualizar lista local */}} />

      <AlertDialog open={cancelDialog} onOpenChange={setCancelDialog}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Cancelar Ordem?</AlertDialogTitle>
            <AlertDialogDescription>A ordem será marcada como Cancelada. Deseja continuar?</AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Voltar</AlertDialogCancel>
            <AlertDialogAction onClick={handleCancelOrder} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Confirmar Cancelamento
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <Dialog open={checklistDialog} onOpenChange={setChecklistDialog}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Checklist por QR Code</DialogTitle>
            <DialogDescription>
              Abra no celular do cliente ou tecnico para testar touch, audio, microfone, camera e botoes.
            </DialogDescription>
          </DialogHeader>

          {checklistMeta?.access_token ? (
            <div className="space-y-4">
              <div className="rounded-xl border border-border bg-background p-4 flex justify-center">
                <img src={checklistQr} alt="QR code do checklist" className="h-60 w-60 rounded-lg" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="checklist-link">Link publico</Label>
                <Input id="checklist-link" value={checklistLink} readOnly />
              </div>
              <div className="rounded-xl border border-border bg-muted/40 p-3 text-sm text-muted-foreground">
                Ultima atualizacao: {checklistMeta.atualizado_em || "ainda nao preenchido"}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Gere o token para exibir o checklist.</p>
          )}

          <DialogFooter>
            <Button type="button" variant="outline" onClick={copyChecklistLink} disabled={!checklistMeta?.access_token}>
              <Copy className="mr-2 h-4 w-4" />
              Copiar link
            </Button>
            <Button type="button" asChild disabled={!checklistMeta?.access_token}>
                <a href={checklistLink} target="_blank" rel="noreferrer">
                <ArrowSquareOut className="mr-2 h-4 w-4" />
                Abrir checklist
              </a>
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={garantiaDialogOpen} onOpenChange={(open) => !open && setGarantiaDialogOpen(false)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Garantia de Reparo</DialogTitle>
            <DialogDescription>
              Selecione o Tipo de Garantia para cada reparo antes de concluir a OS.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3">
            {selectedReparos.map((rid) => {
              const reparo = reparosList.find((r) => r.id === rid);
              return (
                <div key={rid} className="space-y-1.5">
                  <Label>{reparo?.nome || `Reparo #${rid}`}</Label>
                  <Select
                    value={garantiaPorReparo[rid] ? String(garantiaPorReparo[rid]) : ""}
                    onValueChange={(v) => setGarantiaPorReparo((prev) => ({ ...prev, [rid]: parseInt(v, 10) }))}
                  >
                    <SelectTrigger><SelectValue placeholder="Selecione o Tipo de Garantia" /></SelectTrigger>
                    <SelectContent>
                      {tiposGarantiaList.map((tg) => (
                        <SelectItem key={tg.id} value={String(tg.id)}>
                          {tg.nome} ({tg.duracao_meses === 0 ? "sem garantia" : `${tg.duracao_meses}m`})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              );
            })}
            {tiposGarantiaList.length === 0 && (
              <p className="text-xs text-muted-foreground">
                Nenhum Tipo de Garantia cadastrado — crie um em Tipos de Garantia antes de concluir.
              </p>
            )}
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => setGarantiaDialogOpen(false)} disabled={enviandoGarantiaDialog}>
              Cancelar
            </Button>
            <Button type="button" onClick={confirmarGarantiaDialog} disabled={enviandoGarantiaDialog}>
              {enviandoGarantiaDialog && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
              Confirmar e concluir
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
