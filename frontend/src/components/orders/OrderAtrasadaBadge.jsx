import { Badge } from "@/components/ui/badge";

// BR-101 (docs/engineering/plans/PLAN-os-data-previsao.md): a regra de atraso mora no backend
// (`atrasada`). O status é checado de novo aqui só porque o Kanban muda o status localmente
// antes de recarregar -- OS arrastada para Finalizado/Cancelado não pode continuar "Atrasada".
const STATUS_FECHADOS = ["Finalizado", "Cancelado"];

export function formatPrevisao(data) {
  const [ano, mes, dia] = (data || "").split("-");
  return ano && mes && dia ? `${dia}/${mes}` : "";
}

export default function OrderAtrasadaBadge({ os }) {
  if (!os?.atrasada || STATUS_FECHADOS.includes(os.status)) return null;
  return (
    <Badge variant="error" title={`Previsão de entrega: ${formatPrevisao(os.data_previsao)}`} data-testid="os-atrasada">
      Atrasada
    </Badge>
  );
}
