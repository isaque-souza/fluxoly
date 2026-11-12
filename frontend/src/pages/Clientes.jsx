import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, Plus, Pencil, Trash, MagnifyingGlass, User, Phone, EnvelopeSimple, FileText, UserMinus } from "@phosphor-icons/react";
import { clientes as clientesApi, ordens as ordensApi, garantias as garantiasApi, vendas as vendasApi } from "@/api/client";
import { formatCurrency } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Reveal } from "@/components/ui/reveal";
import { FilterBar, FilterInput } from "@/components/ui/filter-bar";
import { DataTable } from "@/components/ui/data-table";
import { LooseMetric } from "@/components/ui/loose-metric";

const EMPTY_FORM = { nome: "", telefone: "", email: "", cpf_cnpj: "", observacoes: "" };

// GarantiaBadge -- status genuíno (vencida/vencendo/ativa), migrado para o
// Badge semântico da Foundation no PR 5.
function garantiaVariant(status) {
  if (status === "vencida") return "error";
  if (status === "vencendo") return "warning";
  return "success";
}

function GarantiaBadge({ status, dias }) {
  const label = status === "vencida" ? "Vencida" : status === "vencendo" ? `Vencendo (${dias}d)` : `${dias}d restantes`;
  return <Badge variant={garantiaVariant(status)}>{label}</Badge>;
}

function PerfilCliente({ cliente, onClose }) {
  const [loading, setLoading] = useState(true);
  const [ordens, setOrdens] = useState([]);
  const [garantiasCliente, setGarantiasCliente] = useState([]);
  const [compras, setCompras] = useState([]);

  useEffect(() => {
    let ativo = true;
    Promise.all([
      ordensApi.clienteHistory(cliente.nome),
      garantiasApi.list({ q: cliente.nome }),
      // KI-062 -- compras vêm por cliente_id (vínculo real gravado pela venda), não por nome.
      vendasApi.list({ cliente_id: cliente.id, per_page: 50 }),
    ]).then(([histRes, garRes, vendasRes]) => {
      if (!ativo) return;
      setOrdens(histRes?.ok ? (histRes.ordens || []) : []);
      setGarantiasCliente(garRes?.ok ? (garRes.garantias || []) : []);
      setCompras(vendasRes?.ok ? (vendasRes.items || []) : []);
    }).catch(() => {
      if (ativo) toast.error("Erro ao carregar histórico do cliente");
    }).finally(() => { if (ativo) setLoading(false); });
    return () => { ativo = false; };
  }, [cliente.id, cliente.nome]);

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <User className="h-5 w-5 text-primary" />
            {cliente.nome}
          </DialogTitle>
          <DialogDescription>Perfil do cliente — dados, histórico de OS, garantias e compras</DialogDescription>
        </DialogHeader>

        <div className="space-y-5 mt-2">
          <div className="grid grid-cols-2 gap-3 bg-secondary/40 rounded-lg p-4">
            <div className="flex items-center gap-2 text-sm">
              <Phone className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-card-foreground">{cliente.telefone || "—"}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <EnvelopeSimple className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-card-foreground">{cliente.email || "—"}</span>
            </div>
            <div className="flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-card-foreground">{cliente.cpf_cnpj || "—"}</span>
            </div>
          </div>

          {cliente.observacoes && (
            <div>
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Observações</p>
              <p className="text-sm text-card-foreground bg-secondary/40 rounded-lg p-3">{cliente.observacoes}</p>
            </div>
          )}

          {loading ? (
            <div className="flex items-center justify-center h-24">
              <CircleNotch className="h-5 w-5 animate-spin text-primary" />
            </div>
          ) : (
            <>
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Histórico de OS {ordens.length > 0 && `(${ordens.length})`}
                </p>
                {ordens.length === 0 ? (
                  <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">Nenhuma OS encontrada para este cliente.</p>
                ) : (
                  <div className="space-y-1.5">
                    {ordens.map((o) => (
                      <div key={o.id} className="flex items-center justify-between text-sm bg-secondary/40 rounded-lg px-3 py-2">
                        <span className="text-card-foreground">{o.modelo || "—"} <span className="text-muted-foreground">({o.tipo})</span></span>
                        <span className="text-muted-foreground text-xs">{o.status} · {o.data ? new Date(o.data).toLocaleDateString("pt-BR") : "—"}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Garantias {garantiasCliente.length > 0 && `(${garantiasCliente.length})`}
                </p>
                {garantiasCliente.length === 0 ? (
                  <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">Nenhuma garantia ativa para este cliente.</p>
                ) : (
                  <div className="space-y-1.5">
                    {garantiasCliente.map((g) => (
                      <div key={`${g.id}-${g.reparo_id}`} className="flex items-center justify-between text-sm bg-secondary/40 rounded-lg px-3 py-2">
                        <span className="text-card-foreground">
                          {g.modelo || "—"}
                          {g.reparo_nome && <span className="text-muted-foreground text-xs"> · {g.reparo_nome}</span>}
                        </span>
                        <GarantiaBadge status={g.status_garantia} dias={g.dias_restantes} />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2">
                  Compras {compras.length > 0 && `(${compras.length})`}
                </p>
                {compras.length === 0 ? (
                  <p className="text-sm text-muted-foreground bg-secondary/40 rounded-lg p-3">Nenhuma compra registrada para este cliente.</p>
                ) : (
                  <div className="space-y-1.5">
                    {compras.map((v) => (
                      <div key={v.id} data-testid="compra-cliente" className="flex items-center justify-between text-sm bg-secondary/40 rounded-lg px-3 py-2">
                        <span className="text-card-foreground">
                          {(v.itens_resumo || []).map((i) => i.produto_nome).join(", ") || `Venda #${v.id}`}
                          {v.status === "cancelada" && <Badge variant="error" className="ml-2">Cancelada</Badge>}
                        </span>
                        <span className="text-muted-foreground text-xs">
                          {formatCurrency(v.valor_total)} · {v.criado_em ? new Date(v.criado_em.replace(" ", "T")).toLocaleDateString("pt-BR") : "—"}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </>
          )}
        </div>

        <DialogFooter className="mt-4">
          <Button type="button" variant="outline" onClick={onClose}>Fechar</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default function Clientes() {
  const { user } = useAuth();
  const isAdmin = user?.perfil === "admin";
  // KI-045: leitura de CPF/CNPJ restrita a admin/financeiro -- escrita segue liberada a todo perfil
  // (docs/engineering/plans/PLAN-LGPD-Compliance.md). O backend já omite cpf_cnpj da resposta para
  // quem não pode ver; canSeeCpf só controla o hint do formulário de edição.
  const canSeeCpf = user?.perfil === "admin" || user?.perfil === "financeiro";

  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [search, setSearch] = useState("");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [deleteId, setDeleteId] = useState(null);
  const [deleting, setDeleting] = useState(false);
  const [anonymizeId, setAnonymizeId] = useState(null);
  const [anonymizing, setAnonymizing] = useState(false);
  const [perfilCliente, setPerfilCliente] = useState(null);

  const fetchItems = async () => {
    setLoading(true);
    try {
      const res = await clientesApi.list({ per_page: 500 });
      if (res?.ok) {
        setItems(res.items || []);
        setLoadError(false);
      } else {
        toast.error(res?.erro || "Erro ao carregar clientes");
        setLoadError(true);
      }
    } catch {
      toast.error("Erro ao carregar clientes");
      setLoadError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchItems();
  }, []);

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (item) => {
    setForm({
      nome: item.nome || "",
      telefone: item.telefone || "",
      email: item.email || "",
      cpf_cnpj: item.cpf_cnpj || "",
      observacoes: item.observacoes || "",
    });
    setEditId(item.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      const payload = { ...form };
      // KI-045: quem não vê o CPF atual (não-admin/financeiro) recebe o campo vazio ao editar --
      // se não digitou nada, omite a chave do payload em vez de mandar "" e apagar silenciosamente
      // o valor já salvo, que essa sessão nunca chegou a ver.
      if (editId && !canSeeCpf && !form.cpf_cnpj) {
        delete payload.cpf_cnpj;
      }
      const res = editId ? await clientesApi.update(editId, payload) : await clientesApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Cliente atualizado!" : "Cliente criado!");
        setDialogOpen(false);
        fetchItems();
      } else {
        toast.error(res?.erro || "Erro ao salvar cliente");
      }
    } catch {
      toast.error("Erro ao salvar cliente");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async () => {
    setDeleting(true);
    try {
      const res = await clientesApi.delete(deleteId);
      if (res?.ok) {
        toast.success("Cliente excluído");
        setItems((prev) => prev.filter((i) => i.id !== deleteId));
      } else {
        toast.error(res?.erro || "Erro ao excluir cliente");
      }
    } catch {
      toast.error("Erro ao excluir cliente");
    } finally {
      setDeleting(false);
      setDeleteId(null);
    }
  };

  const handleAnonymize = async () => {
    setAnonymizing(true);
    try {
      const res = await clientesApi.anonymize(anonymizeId);
      if (res?.ok) {
        toast.success("Cliente anonimizado");
        fetchItems();
      } else {
        toast.error(res?.erro || "Erro ao anonimizar cliente");
      }
    } catch {
      toast.error("Erro ao anonimizar cliente");
    } finally {
      setAnonymizing(false);
      setAnonymizeId(null);
    }
  };

  const filtered = items.filter((item) => {
    const termo = search.trim().toLowerCase();
    if (!termo) return true;
    const haystack = [item.nome, item.telefone, item.email, item.cpf_cnpj].filter(Boolean).join(" ").toLowerCase();
    return termo.split(/\s+/).every((t) => haystack.includes(t));
  });

  const totalClientes = items.length;
  const comTelefone = items.filter((i) => i.telefone).length;
  const comEmail = items.filter((i) => i.email).length;

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Clientes</h1>
          <p className="text-muted-foreground text-sm">Cadastro e histórico dos clientes da loja</p>
        </div>
        <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Cliente</Button>
      </div>

      {/* Contadores soltos, sem elemento dominante (tela de cadastro simples) */}
      <div className="grid grid-cols-3 gap-x-6 gap-y-4">
        <LooseMetric label="Clientes" value={totalClientes} />
        <LooseMetric label="Com telefone" value={comTelefone} valueClassName="text-success" />
        <LooseMetric label="Com e-mail" value={comEmail} valueClassName="text-info" />
      </div>

      {loading ? (
        <ListSkeleton rows={6} />
      ) : loadError && items.length === 0 ? (
        <ErrorState title="Não foi possível carregar os clientes." onRetry={fetchItems} />
      ) : (
        <Reveal className="space-y-5">
          <FilterBar className="bg-card border border-border rounded-xl p-4">
            <div className="relative flex-1 min-w-[220px]">
              <MagnifyingGlass className="absolute left-2.5 top-2 h-4 w-4 text-muted-foreground" />
              <FilterInput placeholder="Buscar por nome, telefone, e-mail, CPF/CNPJ..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full pl-8" />
            </div>
            <div className="ml-auto flex items-center text-xs text-muted-foreground">
              {filtered.length} {filtered.length === 1 ? "cliente" : "clientes"} exibidos
            </div>
          </FilterBar>

          {filtered.length === 0 ? (
            <EmptyState title={search ? "Nenhum cliente corresponde à busca atual." : "Nenhum cliente cadastrado ainda."} />
          ) : (
            <DataTable
              columns={[
                { key: "nome", header: "Nome", className: "font-medium text-card-foreground" },
                { key: "telefone", header: "Telefone", className: "text-muted-foreground", render: (item) => item.telefone || "—" },
                { key: "email", header: "E-mail", className: "text-muted-foreground", render: (item) => item.email || "—" },
                { key: "cpf_cnpj", header: "CPF/CNPJ", className: "text-muted-foreground", render: (item) => item.cpf_cnpj || "—" },
                {
                  key: "acoes",
                  header: "",
                  render: (item) => (
                    <div className="flex items-center gap-1 justify-end" onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon" className="h-7 w-7" aria-label={`Editar cliente ${item.id}`} onClick={() => openEdit(item)}>
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      {isAdmin && (
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-muted-foreground hover:text-foreground" aria-label={`Anonimizar cliente ${item.id}`} title="Anonimizar (LGPD)" onClick={() => setAnonymizeId(item.id)}>
                          <UserMinus className="h-3.5 w-3.5" />
                        </Button>
                      )}
                      {isAdmin && (
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive hover:text-destructive" aria-label={`Excluir cliente ${item.id}`} onClick={() => setDeleteId(item.id)}>
                          <Trash className="h-3.5 w-3.5" />
                        </Button>
                      )}
                    </div>
                  ),
                },
              ]}
              rows={filtered}
              getRowKey={(item) => item.id}
              getRowProps={(item) => ({ "data-testid": `cliente-row-${item.id}` })}
              onRowClick={(item) => setPerfilCliente(item)}
            />
          )}
        </Reveal>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? "Editar Cliente" : "Novo Cliente"}</DialogTitle>
            <DialogDescription>Preencha os dados do cliente para cadastrar ou atualizar.</DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label htmlFor="cliente-nome">Nome *</Label>
              <Input id="cliente-nome" value={form.nome} onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))} required />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label htmlFor="cliente-telefone">Telefone</Label>
                <Input id="cliente-telefone" value={form.telefone} onChange={(e) => setForm((p) => ({ ...p, telefone: e.target.value }))} />
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="cliente-email">E-mail</Label>
                <Input id="cliente-email" type="email" value={form.email} onChange={(e) => setForm((p) => ({ ...p, email: e.target.value }))} />
              </div>
              <div className="col-span-2 space-y-1.5">
                <Label htmlFor="cliente-cpf-cnpj">CPF/CNPJ</Label>
                <Input id="cliente-cpf-cnpj" value={form.cpf_cnpj} onChange={(e) => setForm((p) => ({ ...p, cpf_cnpj: e.target.value }))} placeholder={editId && !canSeeCpf ? "Deixe em branco para não alterar" : undefined} />
                {editId && !canSeeCpf && (
                  <p className="text-xs text-muted-foreground">
                    Seu perfil não vê o CPF/CNPJ já salvo. Deixe em branco para manter o valor atual, ou
                    digite um novo para substituí-lo.
                  </p>
                )}
              </div>
              <div className="col-span-2 space-y-1.5">
                <Label htmlFor="cliente-observacoes">Observações</Label>
                <Input id="cliente-observacoes" value={form.observacoes} onChange={(e) => setForm((p) => ({ ...p, observacoes: e.target.value }))} />
              </div>
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)} disabled={submitting}>Cancelar</Button>
              <Button type="submit" disabled={submitting} data-testid="clientes-save-button">
                {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                {submitting ? "Salvando..." : "Salvar"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {isAdmin && (
        <AlertDialog open={!!deleteId} onOpenChange={(open) => !open && setDeleteId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Excluir Cliente?</AlertDialogTitle>
              <AlertDialogDescription>
                Esta ação não pode ser desfeita. Clientes com OS vinculada não podem ser excluídos.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={deleting}>Cancelar</AlertDialogCancel>
              <AlertDialogAction onClick={handleDelete} disabled={deleting} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                {deleting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                {deleting ? "Excluindo..." : "Excluir"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {isAdmin && (
        <AlertDialog open={!!anonymizeId} onOpenChange={(open) => !open && setAnonymizeId(null)}>
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>Anonimizar Cliente?</AlertDialogTitle>
              <AlertDialogDescription>
                Remove nome, telefone, e-mail, CPF/CNPJ e observações deste cliente, preservando o
                histórico de OS/vendas vinculado (KI-044). Não pode ser desfeito.
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel disabled={anonymizing}>Cancelar</AlertDialogCancel>
              <AlertDialogAction onClick={handleAnonymize} disabled={anonymizing}>
                {anonymizing && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                {anonymizing ? "Anonimizando..." : "Anonimizar"}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      )}

      {perfilCliente && <PerfilCliente cliente={perfilCliente} onClose={() => setPerfilCliente(null)} />}
    </div>
  );
}
