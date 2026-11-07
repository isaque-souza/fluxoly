import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Trash2, ChevronDown, ChevronRight, Lock } from "lucide-react";
import { precos as precosApi, reparos as reparosApi, constantes } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from "@/components/ui/select";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog, AlertDialogContent, AlertDialogHeader, AlertDialogFooter,
  AlertDialogTitle, AlertDialogDescription, AlertDialogAction, AlertDialogCancel,
} from "@/components/ui/alert-dialog";
import { formatCurrency } from "@/lib/constants";

const TABELAS = [
  { id: "clientes",  label: "Clientes" },
];

export default function PriceTables() {
  const { user } = useAuth();
  const [tabelas, setTabelas]       = useState({});
  const [loading, setLoading]       = useState(true);
  const [expanded, setExpanded]     = useState({});
  const [reparosList, setReparosList] = useState([]);
  const [modelos, setModelos]       = useState([]);

  const [dialog, setDialog]         = useState(false);
  const [form, setForm]             = useState({ tabela: "clientes", servico: "", modelo: "", valor: "" });
  const [submitting, setSubmitting] = useState(false);
  const [toDelete, setToDelete]     = useState(null); // { tabela, servico, modelo }

  const isAdmin = user?.perfil === "admin";

  const fetchData = () => {
    setLoading(true);
    Promise.all([precosApi.list(), reparosApi.list(), constantes.get()]).then(([p, r, c]) => {
      if (p?.ok) setTabelas(p.tabelas || {});
      if (r?.ok) setReparosList(r.reparos || []);
      if (c?.ok) setModelos(c.iphone_models || []);
      setLoading(false);
    });
  };

  useEffect(() => { fetchData(); }, []);

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-muted-foreground">
        <Lock className="h-10 w-10" />
        <p>Somente administradores podem gerenciar tabelas de preço.</p>
      </div>
    );
  }

  const toggleExpand = (key) => setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.servico || !form.modelo) return toast.error("Preencha serviço e modelo.");
    setSubmitting(true);
    try {
      const res = await precosApi.save({
        tabela: form.tabela,
        servico: form.servico.toUpperCase(),
        modelo: form.modelo,
        valor: parseFloat(form.valor) || 0,
      });
      if (res?.ok) {
        toast.success("Entrada salva!");
        setDialog(false);
        setForm({ tabela: "clientes", servico: "", modelo: "", valor: "" });
        fetchData();
      } else toast.error(res?.erro || "Erro ao salvar");
    } catch { toast.error("Erro ao salvar"); }
    finally { setSubmitting(false); }
  };

  const handleDelete = async () => {
    if (!toDelete) return;
    try {
      const res = await precosApi.remove(toDelete);
      if (res?.ok) { toast.success("Entrada removida"); fetchData(); }
      else toast.error(res?.erro || "Erro ao remover");
    } catch { toast.error("Erro ao remover"); }
    finally { setToDelete(null); }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Tabelas de Preço</h1>
          <p className="text-muted-foreground text-sm">Preços por modelo e serviço</p>
        </div>
        <Button onClick={() => setDialog(true)}><Plus className="h-4 w-4 mr-2" />Adicionar Entrada</Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40"><Loader2 className="h-6 w-6 animate-spin text-primary" /></div>
      ) : (
        <div className="space-y-4">
          {TABELAS.map(({ id, label }) => {
            const tabelaData = tabelas[id] || {};
            const servicos = Object.keys(tabelaData);
            return (
              <div key={id} className="bg-card border border-border rounded-xl overflow-hidden">
                <div className="px-5 py-4 border-b border-border flex items-center justify-between">
                  <h2 className="font-semibold text-card-foreground">{label}</h2>
                  <span className="text-xs text-muted-foreground">{servicos.length} serviços</span>
                </div>
                {servicos.length === 0 ? (
                  <p className="text-muted-foreground text-sm text-center py-8">Nenhuma entrada cadastrada.</p>
                ) : (
                  <div className="divide-y divide-border">
                    {servicos.map((servico) => {
                      const key = `${id}-${servico}`;
                      const modelsObj = tabelaData[servico] || {};
                      const entries = Object.entries(modelsObj);
                      return (
                        <div key={servico}>
                          <button
                            className="w-full flex items-center justify-between px-5 py-3 hover:bg-accent/30 transition-colors text-left"
                            onClick={() => toggleExpand(key)}
                          >
                            <div className="flex items-center gap-3">
                              {expanded[key]
                                ? <ChevronDown className="h-4 w-4 text-muted-foreground" />
                                : <ChevronRight className="h-4 w-4 text-muted-foreground" />}
                              <span className="font-medium text-sm text-card-foreground">{servico}</span>
                            </div>
                            <span className="text-xs text-muted-foreground">{entries.length} modelos</span>
                          </button>
                          {expanded[key] && (
                            <div className="overflow-x-auto border-t border-border">
                              <table className="w-full text-sm">
                                <thead>
                                  <tr className="bg-secondary/30">
                                    <th className="text-left px-5 py-2 text-xs font-medium text-muted-foreground">Modelo</th>
                                    <th className="text-left px-5 py-2 text-xs font-medium text-muted-foreground">Preço</th>
                                    <th className="px-3 py-2" />
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-border">
                                  {entries.map(([modelo, preco]) => (
                                    <tr key={modelo} className="hover:bg-accent/20">
                                      <td className="px-5 py-2 text-card-foreground">{modelo}</td>
                                      <td className="px-5 py-2 font-medium text-primary">{formatCurrency(preco)}</td>
                                      <td className="px-3 py-2">
                                        <Button
                                          variant="ghost" size="icon"
                                          className="h-6 w-6 text-muted-foreground hover:text-destructive"
                                          onClick={() => setToDelete({ tabela: id, servico, modelo })}
                                        >
                                          <Trash2 className="h-3 w-3" />
                                        </Button>
                                      </td>
                                    </tr>
                                  ))}
                                </tbody>
                              </table>
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Add Entry Dialog */}
      <Dialog open={dialog} onOpenChange={setDialog}>
        <DialogContent>
          <DialogHeader><DialogTitle>Adicionar Entrada de Preço</DialogTitle></DialogHeader>
          <form onSubmit={handleAdd} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Tabela</Label>
              <Select value={form.tabela} onValueChange={(v) => setForm((p) => ({ ...p, tabela: v }))}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  {TABELAS.map((t) => <SelectItem key={t.id} value={t.id}>{t.label}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>Serviço *</Label>
                <Select value={form.servico} onValueChange={(v) => setForm((p) => ({ ...p, servico: v }))}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {reparosList.map((r) => <SelectItem key={r.id} value={r.nome}>{r.nome}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label>Modelo *</Label>
                <Select value={form.modelo} onValueChange={(v) => setForm((p) => ({ ...p, modelo: v }))}>
                  <SelectTrigger><SelectValue placeholder="Selecione" /></SelectTrigger>
                  <SelectContent>
                    {modelos.map((m) => <SelectItem key={m} value={m}>{m}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>Preço (R$) *</Label>
              <Input type="number" step="0.01" min="0" value={form.valor}
                onChange={(e) => setForm((p) => ({ ...p, valor: e.target.value }))} required />
            </div>
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialog(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Delete Confirm */}
      <AlertDialog open={!!toDelete} onOpenChange={(open) => !open && setToDelete(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Remover entrada?</AlertDialogTitle>
            <AlertDialogDescription>
              {toDelete && `${toDelete.servico} / ${toDelete.modelo} será removido.`}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancelar</AlertDialogCancel>
            <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
              Remover
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
