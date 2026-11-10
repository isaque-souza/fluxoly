import { useEffect, useState } from "react";
import { toast } from "sonner";
import { CircleNotch, Lock } from "@phosphor-icons/react";
import { dadosLoja as dadosLojaApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";

const CAMPOS_VAZIOS = {
  nome_fantasia: "",
  razao_social: "",
  cnpj: "",
  telefone: "",
  email: "",
  endereco: "",
  termos_entrada: "",
  termos_garantia: "",
};

// BR-094 -- dados da loja usados no cabeçalho dos documentos da OS para o cliente
// (BR-095/BR-096). Linha única: não há criar/excluir, só salvar. Edição só admin.
export default function DadosLoja() {
  const { user } = useAuth();
  const isAdmin = user?.perfil === "admin";

  const [form, setForm] = useState(CAMPOS_VAZIOS);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    dadosLojaApi
      .get()
      .then((res) => {
        if (res?.ok) {
          const dados = res.dados_loja || {};
          setForm(Object.fromEntries(Object.keys(CAMPOS_VAZIOS).map((k) => [k, dados[k] || ""])));
        } else {
          toast.error(res?.erro || "Erro ao carregar Dados da Loja");
        }
      })
      .catch(() => toast.error("Erro ao carregar Dados da Loja"))
      .finally(() => setLoading(false));
  }, []);

  const setField = (campo, valor) => setForm((f) => ({ ...f, [campo]: valor }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.nome_fantasia.trim()) {
      toast.error("Nome fantasia é obrigatório.");
      return;
    }
    setSaving(true);
    try {
      const res = await dadosLojaApi.save(form);
      if (res?.ok) toast.success("Dados da Loja salvos!");
      else toast.error(res?.erro || "Erro ao salvar");
    } catch {
      toast.error("Erro ao salvar Dados da Loja");
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-40">
        <CircleNotch className="h-6 w-6 animate-spin text-primary" />
      </div>
    );
  }

  const campoTexto = (id, rotulo, props = {}) => (
    <div className="space-y-1.5">
      <Label htmlFor={`dados-loja-${id}`}>{rotulo}</Label>
      <Input
        id={`dados-loja-${id}`}
        value={form[id]}
        onChange={(e) => setField(id, e.target.value)}
        disabled={!isAdmin}
        {...props}
      />
    </div>
  );

  return (
    <form onSubmit={handleSubmit} className="max-w-3xl space-y-5">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Dados da Loja</h1>
          <p className="text-muted-foreground text-sm">Aparecem no cabeçalho dos comprovantes de OS entregues ao cliente</p>
        </div>
        {isAdmin ? (
          <Button type="submit" disabled={saving}>
            {saving && <CircleNotch className="mr-2 h-4 w-4 animate-spin" />}
            Salvar
          </Button>
        ) : (
          <div className="flex items-center gap-2 text-sm text-muted-foreground bg-card border border-border rounded-lg px-3 py-2">
            <Lock className="h-4 w-4" />
            Somente administradores podem editar os Dados da Loja
          </div>
        )}
      </div>

      <Panel>
        <PanelHeader>
          <PanelTitle>Identificação</PanelTitle>
        </PanelHeader>
        <PanelContent className="space-y-4">
          {campoTexto("nome_fantasia", "Nome fantasia *", { maxLength: 120, required: true })}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {campoTexto("razao_social", "Razão social", { maxLength: 160 })}
            {campoTexto("cnpj", "CNPJ", { maxLength: 30 })}
            {campoTexto("telefone", "Telefone", { maxLength: 40 })}
            {campoTexto("email", "E-mail", { maxLength: 120, type: "email" })}
          </div>
          {campoTexto("endereco", "Endereço", { maxLength: 300 })}
        </PanelContent>
      </Panel>

      <Panel>
        <PanelHeader>
          <PanelTitle>Termos impressos nos comprovantes</PanelTitle>
        </PanelHeader>
        <PanelContent className="space-y-4">
          <div className="space-y-1.5">
            <Label htmlFor="dados-loja-termos_entrada">Termos de entrada</Label>
            <Textarea
              id="dados-loja-termos_entrada"
              rows={5}
              maxLength={4000}
              value={form.termos_entrada}
              onChange={(e) => setField("termos_entrada", e.target.value)}
              disabled={!isAdmin}
              placeholder="Ex.: a loja não se responsabiliza por dados do aparelho..."
            />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="dados-loja-termos_garantia">Termos de garantia</Label>
            <Textarea
              id="dados-loja-termos_garantia"
              rows={5}
              maxLength={4000}
              value={form.termos_garantia}
              onChange={(e) => setField("termos_garantia", e.target.value)}
              disabled={!isAdmin}
              placeholder="Ex.: a garantia não cobre quedas, contato com líquidos..."
            />
          </div>
        </PanelContent>
      </Panel>
    </form>
  );
}
