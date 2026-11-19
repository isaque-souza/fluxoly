import { useState, useEffect } from "react";
import { toast } from "sonner";
import { Loader2, Plus, Pencil, Lock } from "lucide-react";
import { tiposGarantia as tiposGarantiaApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle,
} from "@/components/ui/dialog";

const EMPTY_FORM = { nome: "", duracao_meses: "", texto: "", ativo: true };
const LIMITE_TEXTO = 4000;

// V1.5 -- Garantia (BR-055) + BR-105: o Termo de Garantia (nome + prazo + texto), compartilhado entre
// Vendas (por item) e Assistência (um por OS; o texto sai no PDF de entrega). Na API e no banco continua
// `tipos_garantia`. Sem DELETE -- desativar via ativo=false, mesmo padrão de Tipos de Reparo/Produtos.
export default function TiposGarantia() {
  const { user } = useAuth();
  const isAdmin = user?.perfil === "admin";

  const [tipos, setTipos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchTipos = () => {
    const params = isAdmin ? { incluir_inativos: 1 } : {};
    tiposGarantiaApi.list(params).then((res) => {
      if (res?.ok) setTipos(res.items || []);
      else toast.error("Erro ao carregar Termos de Garantia");
      setLoading(false);
    });
  };

  useEffect(() => { fetchTipos(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (t) => {
    setForm({ nome: t.nome || "", duracao_meses: String(t.duracao_meses ?? ""), texto: t.texto || "", ativo: t.ativo });
    setEditId(t.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    const duracao = parseInt(form.duracao_meses, 10);
    if (Number.isNaN(duracao) || duracao < 0) {
      toast.error("Informe uma duração válida (meses, >= 0).");
      return;
    }
    setSubmitting(true);
    try {
      const payload = { nome: form.nome, duracao_meses: duracao, texto: form.texto, ativo: form.ativo };
      const res = editId ? await tiposGarantiaApi.update(editId, payload) : await tiposGarantiaApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Termo de Garantia atualizado!" : "Termo de Garantia criado!");
        setDialogOpen(false);
        fetchTipos();
      } else {
        toast.error(res?.erro || "Erro ao salvar");
      }
    } catch {
      toast.error("Erro ao salvar Termo de Garantia");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Termos de Garantia</h1>
          <p className="text-muted-foreground text-sm">Prazo e texto da garantia — escolhidos na OS (sai no PDF de entrega) e na venda</p>
        </div>
        {isAdmin ? (
          <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Termo</Button>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-card border border-border rounded-lg px-3 py-2">
            <Lock className="h-4 w-4" />
            Somente administradores podem gerenciar Termos de Garantia
          </div>
        )}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      ) : tipos.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center text-muted-foreground text-sm">
          Nenhum Termo de Garantia cadastrado.
        </div>
      ) : (
        <div className="bg-card rounded-xl border border-border overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border">
                  {["Nome", "Duração", "Texto", "Status", ""].map((h) => (
                    <th key={h} className="text-left px-4 py-3 text-xs font-medium text-muted-foreground uppercase tracking-wider">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {tipos.map((t) => (
                  <tr key={t.id} className="hover:bg-accent/30 transition-colors">
                    <td className="px-4 py-3 font-medium text-card-foreground">{t.nome}</td>
                    <td className="px-4 py-3 text-muted-foreground">
                      {t.duracao_meses === 0 ? "Sem garantia" : `${t.duracao_meses} ${t.duracao_meses === 1 ? "mês" : "meses"}`}
                    </td>
                    <td className="px-4 py-3 text-muted-foreground max-w-xs">
                      <span className="line-clamp-2 whitespace-pre-line">{t.texto || "— (usa o texto padrão da loja)"}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={[
                        "inline-flex rounded-full border px-2 py-0.5 text-xs font-medium",
                        t.ativo ? "bg-success/10 text-success border-success/30" : "bg-secondary/70 text-muted-foreground border-border",
                      ].join(" ")}>
                        {t.ativo ? "Ativo" : "Inativo"}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {isAdmin && (
                        <div className="flex items-center justify-end">
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEdit(t)}>
                            <Pencil className="h-3.5 w-3.5" />
                          </Button>
                        </div>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? "Editar Termo de Garantia" : "Novo Termo de Garantia"}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label>Nome *</Label>
              <Input value={form.nome} onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))} required />
            </div>
            <div className="space-y-1.5">
              <Label>Duração (meses) *</Label>
              <Input
                type="number"
                min="0"
                step="1"
                value={form.duracao_meses}
                onChange={(e) => setForm((p) => ({ ...p, duracao_meses: e.target.value }))}
                required
              />
              <p className="text-xs text-muted-foreground">0 representa "sem garantia".</p>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="termo-garantia-texto">Texto do termo</Label>
              <Textarea
                id="termo-garantia-texto"
                rows={7}
                maxLength={LIMITE_TEXTO}
                value={form.texto}
                onChange={(e) => setForm((p) => ({ ...p, texto: e.target.value }))}
                placeholder="Ex.: a garantia cobre defeito no serviço executado e não cobre quedas, contato com líquidos..."
              />
              <p className="text-xs text-muted-foreground">
                Sai no PDF de entrega da OS. Em branco, vale o texto padrão de Dados da Loja. Editar não muda OS já finalizadas.
              </p>
            </div>
            {editId && (
              <label className="flex items-center gap-2 text-sm">
                <Checkbox checked={form.ativo} onCheckedChange={(v) => setForm((p) => ({ ...p, ativo: Boolean(v) }))} />
                Ativo
              </label>
            )}
            <DialogFooter className="mt-4">
              <Button type="button" variant="outline" onClick={() => setDialogOpen(false)}>Cancelar</Button>
              <Button type="submit" disabled={submitting}>
                {submitting && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
