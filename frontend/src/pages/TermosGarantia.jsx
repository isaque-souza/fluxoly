import { useState, useEffect } from "react";
import { toast } from "sonner";
import { CircleNotch, Plus, PencilSimple, FileText } from "@phosphor-icons/react";
import { termosGarantia as termosGarantiaApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import {
  Dialog, DialogContent, DialogHeader, DialogFooter, DialogTitle, DialogDescription,
} from "@/components/ui/dialog";

const EMPTY_FORM = { nome: "", texto: "", ativo: true };
const LIMITE_TEXTO = 4000;

// BR-105 -- cadastro de Termos de Garantia (só admin edita; o menu é adminOnly e o backend recusa
// os demais). Um termo é escolhido por OS ao finalizar e sai no comprovante de entrega. Sem DELETE:
// desativar via ativo=false, mesmo padrão de Tipos de Garantia.
export default function TermosGarantia() {
  const isAdmin = useAuth()?.user?.perfil === "admin";
  const [termos, setTermos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [editId, setEditId] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const fetchTermos = () => {
    termosGarantiaApi.list(isAdmin ? { incluir_inativos: 1 } : {}).then((res) => {
      if (res?.ok) setTermos(res.items || []);
      else toast.error("Erro ao carregar Termos de Garantia");
      setLoading(false);
    }).catch(() => {
      toast.error("Erro ao carregar Termos de Garantia");
      setLoading(false);
    });
  };

  useEffect(() => { fetchTermos(); }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const openCreate = () => {
    setForm(EMPTY_FORM);
    setEditId(null);
    setDialogOpen(true);
  };

  const openEdit = (t) => {
    setForm({ nome: t.nome || "", texto: t.texto || "", ativo: t.ativo });
    setEditId(t.id);
    setDialogOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome.trim() || !form.texto.trim()) {
      toast.error("Preencha o nome e o texto do termo.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = { nome: form.nome, texto: form.texto, ativo: form.ativo };
      const res = editId ? await termosGarantiaApi.update(editId, payload) : await termosGarantiaApi.create(payload);
      if (res?.ok) {
        toast.success(editId ? "Termo atualizado!" : "Termo criado!");
        setDialogOpen(false);
        fetchTermos();
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
          <p className="text-muted-foreground text-sm">
            Textos escolhidos ao finalizar a OS e impressos no comprovante de entrega
          </p>
        </div>
        {isAdmin && <Button onClick={openCreate}><Plus className="h-4 w-4 mr-2" />Novo Termo</Button>}
      </div>

      {loading ? (
        <ListSkeleton rows={3} />
      ) : termos.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="Nenhum Termo de Garantia cadastrado"
          description="Sem termo escolhido, o comprovante de entrega usa o texto padrão de Dados da Loja."
        />
      ) : (
        <div className="bg-card rounded-xl border border-border divide-y divide-border">
          {termos.map((t) => (
            <div key={t.id} className="flex items-start justify-between gap-3 px-4 py-3">
              <div className="min-w-0 space-y-1">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="font-medium text-card-foreground">{t.nome}</span>
                  <Badge variant={t.ativo ? "success" : "neutral"}>{t.ativo ? "Ativo" : "Inativo"}</Badge>
                </div>
                <p className="text-sm text-muted-foreground line-clamp-2 whitespace-pre-line">{t.texto}</p>
              </div>
              {isAdmin && (
                <Button variant="ghost" size="icon" className="h-7 w-7 shrink-0" onClick={() => openEdit(t)} aria-label={`Editar ${t.nome}`}>
                  <PencilSimple className="h-3.5 w-3.5" />
                </Button>
              )}
            </div>
          ))}
        </div>
      )}

      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editId ? "Editar Termo de Garantia" : "Novo Termo de Garantia"}</DialogTitle>
            <DialogDescription>
              Editar um termo não muda OS já finalizadas: cada OS guarda o texto do momento em que foi concluída.
            </DialogDescription>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3 mt-2">
            <div className="space-y-1.5">
              <Label htmlFor="termo-garantia-nome">Nome *</Label>
              <Input
                id="termo-garantia-nome"
                maxLength={120}
                value={form.nome}
                onChange={(e) => setForm((p) => ({ ...p, nome: e.target.value }))}
                placeholder="Ex.: Assistência 90 dias"
                required
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="termo-garantia-texto">Texto do termo *</Label>
              <Textarea
                id="termo-garantia-texto"
                rows={8}
                maxLength={LIMITE_TEXTO}
                value={form.texto}
                onChange={(e) => setForm((p) => ({ ...p, texto: e.target.value }))}
                placeholder="Ex.: a garantia cobre defeito no serviço executado e não cobre quedas, contato com líquidos..."
                required
              />
              <p className="text-xs text-muted-foreground">{form.texto.length}/{LIMITE_TEXTO}</p>
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
                {submitting && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
                Salvar
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
