import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { CircleNotch, ArrowLeft, Printer, UserCircle, CreditCard, Calendar, FileText, Prohibit } from "@phosphor-icons/react";
import { vendas as vendasApi, tiposGarantia as tiposGarantiaApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { cn } from "@/lib/utils";
import { imprimirReciboVenda } from "@/lib/vendaPdf";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import { ErrorState } from "@/components/ui/error-state";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";
import { DataTable } from "@/components/ui/data-table";
import { formatCurrency, vendaStatusVariant, vendaStatusLabel } from "@/lib/constants";

const ITENS_COLUMNS = [
  { key: "produto", header: "Produto", className: "font-medium text-card-foreground", render: (item) => item.produto_nome },
  { key: "imei", header: "IMEI", className: "text-muted-foreground font-mono", render: (item) => item.imei || "—" },
  { key: "sku", header: "SKU", className: "text-muted-foreground", render: (item) => item.produto_sku || "—" },
  {
    key: "valor_tabela",
    header: "Valor de tabela",
    className: "text-muted-foreground",
    render: (item) => (item.valor_tabela != null ? formatCurrency(item.valor_tabela) : "—"),
  },
  { key: "valor_unitario", header: "Valor vendido", className: "text-card-foreground", render: (item) => formatCurrency(item.valor_unitario) },
  {
    key: "desconto",
    header: "Desconto",
    className: "text-muted-foreground",
    render: (item) => (item.desconto != null ? formatCurrency(item.desconto) : "—"),
  },
  { key: "subtotal", header: "Total", className: "font-medium text-card-foreground", render: (item) => formatCurrency(item.subtotal) },
];

const FORMA_PAGAMENTO_LABEL = {
  pix: "Pix",
  cartao: "Cartão",
  dinheiro: "Dinheiro",
  transferencia: "Transferência",
};

// V1.2 -- Cancelamento (BR-032): lista fechada, "outro" exige observação.
const MOTIVOS_CANCELAMENTO = [
  { value: "cliente_desistiu", label: "Cliente desistiu" },
  { value: "erro_lancamento", label: "Erro de lançamento" },
  { value: "imei_incorreto", label: "IMEI incorreto" },
  { value: "venda_duplicada", label: "Venda duplicada" },
  { value: "pagamento_nao_concluido", label: "Pagamento não concluído" },
  { value: "produto_indisponivel", label: "Produto indisponível" },
  { value: "outro", label: "Outro" },
];

function formatDateTime(value) {
  if (!value) return "—";
  const [data, hora] = value.split(" ");
  const [ano, mes, dia] = (data || "").split("-");
  const horaCurta = (hora || "").slice(0, 5);
  return ano && mes && dia ? `${dia}/${mes}/${ano} ${horaCurta}`.trim() : value;
}

// Estrutura pensada para ser reaproveitada como recibo quando a feature de
// Imprimir (V1.8 do roadmap) existir — por isso as seções (cabeçalho,
// cliente/vendedor/pagamento, itens, total) já ficam isoladas e limpas, sem
// nada específico de tela que atrapalharia virar impresso depois.
export default function VendaDetalhe() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [venda, setVenda] = useState(null);
  const [itens, setItens] = useState([]);
  const [erro, setErro] = useState(null);

  const [cancelando, setCancelando] = useState(false);
  const [motivoCancelamento, setMotivoCancelamento] = useState("");
  const [observacaoCancelamento, setObservacaoCancelamento] = useState("");
  const [enviandoCancelamento, setEnviandoCancelamento] = useState(false);

  // V1.3 -- Ajuste Comercial Autorizado (BR-043).
  const [ajustando, setAjustando] = useState(false);
  const [novoValorAjuste, setNovoValorAjuste] = useState("");
  const [motivoAjuste, setMotivoAjuste] = useState("");
  const [enviandoAjuste, setEnviandoAjuste] = useState(false);
  const [historicoAjustes, setHistoricoAjustes] = useState([]);

  // V1.4 -- Comissão (BR-044 a BR-049).
  const [editandoComissao, setEditandoComissao] = useState(false);
  const [novoValorComissao, setNovoValorComissao] = useState("");
  const [enviandoComissao, setEnviandoComissao] = useState(false);
  const [historicoComissao, setHistoricoComissao] = useState([]);

  // V1.5 -- Garantia de Venda (BR-057 a BR-059).
  const [tiposGarantiaList, setTiposGarantiaList] = useState([]);
  const [corrigindoGarantia, setCorrigindoGarantia] = useState(false);
  const [novoTipoGarantiaId, setNovoTipoGarantiaId] = useState("");
  const [enviandoGarantia, setEnviandoGarantia] = useState(false);
  const [historicoGarantia, setHistoricoGarantia] = useState([]);

  async function carregar() {
    setLoading(true);
    try {
      const res = await vendasApi.get(id);
      if (res?.ok) {
        setVenda(res.venda);
        setItens(res.itens || []);
      } else {
        setErro(res?.erro || "Venda não encontrada");
      }
    } catch {
      setErro("Erro ao carregar venda");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    async function carregarInicial() {
      await carregar();
    }
    carregarInicial();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const podeCancelar = Boolean(
    venda && user && venda.status === "concluida" &&
    (user.perfil === "admin" || (user.perfil === "vendedor" && venda.vendedor_id === user.id))
  );

  // V1.3 -- Ajuste Comercial Autorizado (BR-043): só admin, só em venda
  // concluída, e só o item (nunca a venda inteira) -- nesta fatia sempre o
  // primeiro/único item.
  const itemPrincipal = itens[0];
  const podeAjustar = Boolean(venda && user?.perfil === "admin" && venda.status === "concluida" && itemPrincipal);

  // V1.4 -- Comissão (BR-044/BR-047): visível só para admin/financeiro --
  // combina com a ocultação já feita pelo backend em `_ocultar_comissao_se_necessario`.
  const podeVerComissao = Boolean(user && (user.perfil === "admin" || user.perfil === "financeiro"));
  const podeEditarComissao = Boolean(podeVerComissao && venda && venda.status === "concluida" && itemPrincipal);

  // V1.5 -- Garantia de Venda (BR-057/BR-059): qualquer usuário autenticado
  // vê a garantia (diferente da comissão); só admin corrige, só em venda concluída.
  const podeCorrigirGarantia = Boolean(user?.perfil === "admin" && venda && venda.status === "concluida" && itemPrincipal);

  async function carregarHistoricoAjustes(itemId) {
    const res = await vendasApi.historicoDescontoItem(id, itemId);
    if (res?.ok) setHistoricoAjustes(res.historico || []);
  }

  async function carregarHistoricoComissao(itemId) {
    const res = await vendasApi.historicoComissaoItem(id, itemId);
    if (res?.ok) setHistoricoComissao(res.historico || []);
  }

  async function carregarHistoricoGarantia(itemId) {
    const res = await vendasApi.historicoGarantiaItem(id, itemId);
    if (res?.ok) setHistoricoGarantia(res.historico || []);
  }

  useEffect(() => {
    if (itemPrincipal) carregarHistoricoAjustes(itemPrincipal.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemPrincipal?.id]);

  useEffect(() => {
    if (itemPrincipal && podeVerComissao) carregarHistoricoComissao(itemPrincipal.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemPrincipal?.id, podeVerComissao]);

  useEffect(() => {
    if (itemPrincipal) carregarHistoricoGarantia(itemPrincipal.id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [itemPrincipal?.id]);

  useEffect(() => {
    if (podeCorrigirGarantia) {
      tiposGarantiaApi.list().then((res) => {
        if (res?.ok) setTiposGarantiaList(res.items || []);
      }).catch(() => {
        toast.error("Erro ao carregar tipos de garantia");
      });
    }
  }, [podeCorrigirGarantia]);

  const confirmarAjuste = async () => {
    const valor = parseFloat(novoValorAjuste);
    if (!valor || valor <= 0) {
      toast.error("Informe um valor válido.");
      return;
    }
    if (!motivoAjuste.trim()) {
      toast.error("Motivo é obrigatório para o ajuste comercial.");
      return;
    }
    setEnviandoAjuste(true);
    try {
      const res = await vendasApi.ajustarDescontoItem(id, itemPrincipal.id, {
        valor_unitario: valor,
        motivo: motivoAjuste,
      });
      if (res?.ok) {
        toast.success("Ajuste comercial aplicado.");
        setAjustando(false);
        setNovoValorAjuste("");
        setMotivoAjuste("");
        await carregar();
        await carregarHistoricoAjustes(itemPrincipal.id);
      } else {
        toast.error(res?.erro || "Erro ao aplicar o ajuste.");
      }
    } catch {
      toast.error("Erro ao aplicar o ajuste.");
    } finally {
      setEnviandoAjuste(false);
    }
  };

  const confirmarComissao = async () => {
    const valor = parseFloat(novoValorComissao);
    if (Number.isNaN(valor) || valor < 0) {
      toast.error("Informe um valor válido.");
      return;
    }
    setEnviandoComissao(true);
    try {
      const res = await vendasApi.atribuirComissaoItem(id, itemPrincipal.id, { valor });
      if (res?.ok) {
        toast.success("Comissão atribuída.");
        setEditandoComissao(false);
        setNovoValorComissao("");
        await carregar();
        await carregarHistoricoComissao(itemPrincipal.id);
      } else {
        toast.error(res?.erro || "Erro ao atribuir a comissão.");
      }
    } catch {
      toast.error("Erro ao atribuir a comissão.");
    } finally {
      setEnviandoComissao(false);
    }
  };

  const confirmarGarantia = async () => {
    if (!novoTipoGarantiaId) {
      toast.error("Selecione o Tipo de Garantia.");
      return;
    }
    setEnviandoGarantia(true);
    try {
      const res = await vendasApi.corrigirGarantiaItem(id, itemPrincipal.id, {
        tipo_garantia_id: parseInt(novoTipoGarantiaId, 10),
      });
      if (res?.ok) {
        toast.success("Garantia corrigida.");
        setCorrigindoGarantia(false);
        setNovoTipoGarantiaId("");
        await carregar();
        await carregarHistoricoGarantia(itemPrincipal.id);
      } else {
        toast.error(res?.erro || "Erro ao corrigir a garantia.");
      }
    } catch {
      toast.error("Erro ao corrigir a garantia.");
    } finally {
      setEnviandoGarantia(false);
    }
  };

  const confirmarCancelamento = async () => {
    if (!motivoCancelamento) {
      toast.error("Selecione o motivo do cancelamento.");
      return;
    }
    if (motivoCancelamento === "outro" && !observacaoCancelamento.trim()) {
      toast.error("Descreva o motivo quando selecionar 'Outro'.");
      return;
    }
    setEnviandoCancelamento(true);
    try {
      const res = await vendasApi.cancelar(id, {
        motivo: motivoCancelamento,
        observacao: observacaoCancelamento,
      });
      if (res?.ok) {
        toast.success("Venda cancelada.");
        setCancelando(false);
        setMotivoCancelamento("");
        setObservacaoCancelamento("");
        await carregar();
      } else {
        toast.error(res?.erro || "Erro ao cancelar venda");
      }
    } catch {
      toast.error("Erro ao cancelar venda");
    } finally {
      setEnviandoCancelamento(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <CircleNotch className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  if (erro || !venda) {
    return (
      <div className="space-y-4 max-w-2xl">
        <Button variant="outline" size="sm" onClick={() => navigate("/vendas")}>
          <ArrowLeft className="h-4 w-4 mr-2" />Voltar
        </Button>
        <ErrorState title={erro || "Venda não encontrada."} description={null} />
      </div>
    );
  }

  return (
    <div className="space-y-5 max-w-3xl">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <Button variant="outline" size="sm" onClick={() => navigate("/vendas")}>
          <ArrowLeft className="h-4 w-4 mr-2" />Voltar
        </Button>
        <div className="flex items-center gap-2">
          {podeCancelar && !cancelando && (
            <Button variant="outline" size="sm" onClick={() => setCancelando(true)}>
              <Prohibit className="h-4 w-4 mr-2" />Cancelar venda
            </Button>
          )}
          {venda.status === "concluida" && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => imprimirReciboVenda(venda.id, user?.perfil === "admin" ? () => navigate("/dados-loja") : undefined)}
            >
              <Printer className="h-4 w-4 mr-2" />Imprimir recibo
            </Button>
          )}
        </div>
      </div>

      <h1 className="sr-only">Venda #{venda.id}</h1>

      {cancelando && (
        <div className="bg-card border border-destructive/30 rounded-xl p-4 space-y-3">
          <p className="text-sm font-medium text-card-foreground">Cancelar venda #{venda.id}</p>
          <div className="space-y-1.5">
            <Label htmlFor="motivo-cancelamento">Motivo</Label>
            <Select value={motivoCancelamento} onValueChange={setMotivoCancelamento}>
              <SelectTrigger id="motivo-cancelamento" className="w-full"><SelectValue placeholder="Selecione o motivo" /></SelectTrigger>
              <SelectContent>
                {MOTIVOS_CANCELAMENTO.map((m) => <SelectItem key={m.value} value={m.value}>{m.label}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          {motivoCancelamento === "outro" && (
            <div className="space-y-1.5">
              <Label htmlFor="observacao-cancelamento">Descrição (obrigatória)</Label>
              <Textarea
                id="observacao-cancelamento"
                value={observacaoCancelamento}
                onChange={(e) => setObservacaoCancelamento(e.target.value)}
                rows={2}
              />
            </div>
          )}
          <div className="flex items-center gap-2 pt-1">
            <Button variant="destructive" size="sm" onClick={confirmarCancelamento} disabled={enviandoCancelamento}>
              {enviandoCancelamento && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
              Confirmar cancelamento
            </Button>
            <Button
              variant="ghost"
              size="sm"
              disabled={enviandoCancelamento}
              onClick={() => { setCancelando(false); setMotivoCancelamento(""); setObservacaoCancelamento(""); }}
            >
              Voltar
            </Button>
          </div>
        </div>
      )}

      {venda.status === "cancelada" && (
        <div className="bg-card border border-border rounded-xl p-4 text-sm space-y-1">
          <p className="font-medium text-card-foreground">Venda cancelada</p>
          <p className="text-muted-foreground">
            Motivo: {MOTIVOS_CANCELAMENTO.find((m) => m.value === venda.motivo_cancelamento)?.label || venda.motivo_cancelamento || "—"}
            {" — "}{formatDateTime(venda.cancelado_em)}
          </p>
          {venda.observacao_cancelamento && (
            <p className="text-muted-foreground">Observação: {venda.observacao_cancelamento}</p>
          )}
        </div>
      )}

      <Panel>
        <PanelHeader>
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div>
              <PanelTitle className="text-xl font-bold">Venda #{venda.id}</PanelTitle>
              <p className="text-muted-foreground text-sm flex items-center gap-1.5 mt-0.5">
                <Calendar className="h-3.5 w-3.5" />{formatDateTime(venda.criado_em)}
              </p>
            </div>
            <Badge variant={vendaStatusVariant(venda.status)}>{vendaStatusLabel(venda.status)}</Badge>
          </div>
        </PanelHeader>
        <PanelContent className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 bg-secondary/40 rounded-lg p-4">
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <UserCircle className="h-3.5 w-3.5" />Cliente
              </p>
              <p className="text-sm font-medium text-card-foreground mt-0.5">{venda.cliente_nome || "—"}</p>
              {venda.cliente_telefone && <p className="text-xs text-muted-foreground">{venda.cliente_telefone}</p>}
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider">Vendedor</p>
              <p className="text-sm font-medium text-card-foreground mt-0.5">{venda.vendedor_nome || "—"}</p>
            </div>
            <div>
              <p className="text-xs text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <CreditCard className="h-3.5 w-3.5" />Pagamento
              </p>
              <p className="text-sm font-medium text-card-foreground mt-0.5">
                {FORMA_PAGAMENTO_LABEL[venda.forma_pagamento] || venda.forma_pagamento || "—"}
              </p>
            </div>
          </div>

          {venda.observacoes && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1 flex items-center gap-1.5">
                <FileText className="h-3.5 w-3.5" />Observações
              </p>
              <p className="text-sm text-card-foreground bg-secondary/40 rounded-lg p-3">{venda.observacoes}</p>
            </div>
          )}

          <div>
            <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
              Itens {itens.length > 0 && `(${itens.length})`}
            </p>
            <DataTable columns={ITENS_COLUMNS} rows={itens} getRowKey={(item) => item.id} />
            {itemPrincipal && (itemPrincipal.motivo_desconto || itemPrincipal.desconto_aprovado_em) && (
              <div className="text-xs text-muted-foreground mt-2 space-y-0.5">
                {itemPrincipal.motivo_desconto && <p>Motivo do desconto: {itemPrincipal.motivo_desconto}</p>}
                {itemPrincipal.desconto_aprovado_em && (
                  <p>Desconto aprovado em {formatDateTime(itemPrincipal.desconto_aprovado_em)}</p>
                )}
              </div>
            )}
          </div>

          {/* Metrica dominante do painel -- Total da venda */}
          <div className="flex items-center justify-between pt-3 border-t border-border">
            <span className="text-sm text-muted-foreground">Total da venda</span>
            <span className="text-2xl sm:text-3xl font-bold text-foreground tracking-tight">{formatCurrency(venda.valor_total)}</span>
          </div>
        </PanelContent>
      </Panel>

      {/* BR-092 -- só vem do backend para admin/financeiro e só para aparelho que veio de compra */}
      {itemPrincipal?.custo_aparelho && (
        <Panel>
          <PanelHeader>
            <PanelTitle>Custo e lucro do aparelho</PanelTitle>
          </PanelHeader>
          <PanelContent>
            <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-sm">
              <div>
                <dt className="text-xs text-muted-foreground">Valor da compra</dt>
                <dd className="font-medium text-card-foreground">{formatCurrency(itemPrincipal.custo_aparelho.valor_compra)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Peças do conserto</dt>
                <dd className="font-medium text-card-foreground">{formatCurrency(itemPrincipal.custo_aparelho.custo_pecas)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Custo total</dt>
                <dd className="font-medium text-card-foreground">{formatCurrency(itemPrincipal.custo_aparelho.custo_total)}</dd>
              </div>
              <div>
                <dt className="text-xs text-muted-foreground">Lucro</dt>
                <dd
                  data-testid="venda-lucro"
                  className={cn("font-semibold", itemPrincipal.lucro < 0 ? "text-destructive" : "text-success")}
                >
                  {formatCurrency(itemPrincipal.lucro)}
                </dd>
              </div>
            </dl>
          </PanelContent>
        </Panel>
      )}

      {podeAjustar && (
        <Panel>
          <PanelHeader>
            <div className="flex items-center justify-between">
              <PanelTitle>Ajuste Comercial Autorizado</PanelTitle>
              {!ajustando && (
                <Button variant="outline" size="sm" onClick={() => { setAjustando(true); setNovoValorAjuste(String(itemPrincipal.valor_unitario)); }}>
                  Ajustar desconto
                </Button>
              )}
            </div>
          </PanelHeader>
          {(ajustando || historicoAjustes.length > 0) && (
            <PanelContent className="space-y-3">
              {ajustando && (
                <div className="space-y-3">
                  <p className="text-xs text-muted-foreground">
                    Só o valor deste item pode ser ajustado — cliente, IMEI, forma de pagamento, vendedor,
                    data e status da venda permanecem imutáveis.
                  </p>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="ajuste-valor">Novo valor</Label>
                      <Input
                        id="ajuste-valor"
                        type="number"
                        step="0.01"
                        min="0"
                        value={novoValorAjuste}
                        onChange={(e) => setNovoValorAjuste(e.target.value)}
                      />
                    </div>
                  </div>
                  <div className="space-y-1.5">
                    <Label htmlFor="ajuste-motivo">Motivo (obrigatório)</Label>
                    <Textarea
                      id="ajuste-motivo"
                      value={motivoAjuste}
                      onChange={(e) => setMotivoAjuste(e.target.value)}
                      rows={2}
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" onClick={confirmarAjuste} disabled={enviandoAjuste}>
                      {enviandoAjuste && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
                      Confirmar ajuste
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={enviandoAjuste}
                      onClick={() => { setAjustando(false); setNovoValorAjuste(""); setMotivoAjuste(""); }}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
              {historicoAjustes.length > 0 && (
                <div className={cn(ajustando && "pt-2 border-t border-border", "space-y-1.5")}>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Histórico de ajustes</p>
                  {historicoAjustes.map((evento) => (
                    <p key={evento.id} className="text-xs text-muted-foreground">
                      {formatDateTime(evento.criado_em)} — {evento.usuario_nome || "—"}
                    </p>
                  ))}
                </div>
              )}
            </PanelContent>
          )}
        </Panel>
      )}

      {podeVerComissao && itemPrincipal && (
        <Panel>
          <PanelHeader>
            <div className="flex items-center justify-between">
              <div>
                <PanelTitle>Comissão</PanelTitle>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {itemPrincipal.comissao_valor != null ? formatCurrency(itemPrincipal.comissao_valor) : "Não atribuída"}
                </p>
              </div>
              {podeEditarComissao && !editandoComissao && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => { setEditandoComissao(true); setNovoValorComissao(String(itemPrincipal.comissao_valor ?? "")); }}
                >
                  {itemPrincipal.comissao_valor != null ? "Editar comissão" : "Atribuir comissão"}
                </Button>
              )}
            </div>
          </PanelHeader>
          {(editandoComissao || historicoComissao.length > 0) && (
            <PanelContent className="space-y-3">
              {editandoComissao && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="comissao-valor">Valor da comissão</Label>
                    <Input
                      id="comissao-valor"
                      type="number"
                      step="0.01"
                      min="0"
                      value={novoValorComissao}
                      onChange={(e) => setNovoValorComissao(e.target.value)}
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" onClick={confirmarComissao} disabled={enviandoComissao}>
                      {enviandoComissao && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
                      Confirmar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={enviandoComissao}
                      onClick={() => { setEditandoComissao(false); setNovoValorComissao(""); }}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
              {historicoComissao.length > 0 && (
                <div className={cn(editandoComissao && "pt-2 border-t border-border", "space-y-1.5")}>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Histórico de comissão</p>
                  {historicoComissao.map((evento) => (
                    <p key={evento.id} className="text-xs text-muted-foreground">
                      {formatDateTime(evento.criado_em)} — {evento.usuario_nome || "—"}
                    </p>
                  ))}
                </div>
              )}
            </PanelContent>
          )}
        </Panel>
      )}

      {itemPrincipal && (
        <Panel>
          <PanelHeader>
            <div className="flex items-center justify-between">
              <div>
                <PanelTitle>Garantia de Venda</PanelTitle>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {itemPrincipal.garantia_nome
                    ? `${itemPrincipal.garantia_nome} — até ${itemPrincipal.garantia_data_fim ? formatDateTime(itemPrincipal.garantia_data_fim) : "—"}`
                    : "Sem garantia registrada"}
                </p>
              </div>
              {podeCorrigirGarantia && !corrigindoGarantia && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setCorrigindoGarantia(true);
                    setNovoTipoGarantiaId(itemPrincipal.tipo_garantia_id ? String(itemPrincipal.tipo_garantia_id) : "");
                  }}
                >
                  Corrigir garantia
                </Button>
              )}
            </div>
          </PanelHeader>
          {(corrigindoGarantia || historicoGarantia.length > 0) && (
            <PanelContent className="space-y-3">
              {corrigindoGarantia && (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="garantia-tipo">Novo Tipo de Garantia</Label>
                    <Select value={novoTipoGarantiaId} onValueChange={setNovoTipoGarantiaId}>
                      <SelectTrigger id="garantia-tipo" className="w-full"><SelectValue placeholder="Selecione" /></SelectTrigger>
                      <SelectContent>
                        {tiposGarantiaList.map((tg) => (
                          <SelectItem key={tg.id} value={String(tg.id)}>{tg.nome} ({tg.duracao_meses}m)</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button size="sm" onClick={confirmarGarantia} disabled={enviandoGarantia}>
                      {enviandoGarantia && <CircleNotch className="h-4 w-4 mr-2 animate-spin" />}
                      Confirmar
                    </Button>
                    <Button
                      variant="ghost"
                      size="sm"
                      disabled={enviandoGarantia}
                      onClick={() => { setCorrigindoGarantia(false); setNovoTipoGarantiaId(""); }}
                    >
                      Cancelar
                    </Button>
                  </div>
                </div>
              )}
              {historicoGarantia.length > 0 && (
                <div className={cn(corrigindoGarantia && "pt-2 border-t border-border", "space-y-1.5")}>
                  <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Histórico de garantia</p>
                  {historicoGarantia.map((evento) => (
                    <p key={evento.id} className="text-xs text-muted-foreground">
                      {formatDateTime(evento.criado_em)} — {evento.usuario_nome || "—"}
                    </p>
                  ))}
                </div>
              )}
            </PanelContent>
          )}
        </Panel>
      )}
    </div>
  );
}
