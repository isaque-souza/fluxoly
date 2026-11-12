import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";

// Textos livres da OS (BR-102, docs/engineering/plans/PLAN-os-relato-laudo.md), compartilhado por
// Nova OS e Editar OS. Relato, laudo e observações saem no documento do cliente; a observação
// interna nunca sai da loja.
const CAMPOS = [
  { campo: "relato_cliente", label: "Relato do cliente", placeholder: "O que o cliente contou sobre o defeito..." },
  { campo: "laudo_tecnico", label: "Laudo técnico", placeholder: "Diagnóstico do técnico..." },
  { campo: "observacoes", label: "Observações", placeholder: "Observações adicionais sobre a OS..." },
  {
    campo: "observacao_interna",
    label: "Observação interna",
    placeholder: "Só para a equipe...",
    ajuda: "Não aparece em nenhum documento entregue ao cliente.",
  },
];

export const CAMPOS_TEXTO_OS_VAZIOS = { relato_cliente: "", laudo_tecnico: "", observacao_interna: "" };

export default function OrderTextosPanel({ form, setField, idPrefix = "order" }) {
  return (
    <Panel>
      <PanelHeader>
        <PanelTitle>Relato, laudo e observações</PanelTitle>
      </PanelHeader>
      <PanelContent className="space-y-4">
        {CAMPOS.map(({ campo, label, placeholder, ajuda }) => (
          <div key={campo} className="space-y-1.5">
            <Label htmlFor={`${idPrefix}-${campo}`}>{label}</Label>
            <Textarea
              id={`${idPrefix}-${campo}`}
              value={form[campo] || ""}
              onChange={(e) => setField(campo, e.target.value)}
              placeholder={placeholder}
            />
            {ajuda && <p className="text-xs text-muted-foreground">{ajuda}</p>}
          </div>
        ))}
      </PanelContent>
    </Panel>
  );
}
