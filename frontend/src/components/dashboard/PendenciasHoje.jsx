import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WarningCircle } from "@phosphor-icons/react";
import { pendencias as pendenciasApi } from "@/api/client";
import { useAuth } from "@/contexts/AuthContext";
import { formatCurrency } from "@/lib/constants";

// Pendências da tela inicial (docs/engineering/plans/PLAN-pendencias-tela-inicial.md):
// contas a pagar/receber vencidas e que vencem hoje. Só admin/financeiro (valor financeiro).
// Sem pendência, sem permissão ou com erro de rede, não renderiza nada -- não atrapalha o dashboard.

const PERFIS = ["admin", "financeiro"];

function Grupo({ titulo, resumo, testId }) {
  const itens = [
    { label: "vencida(s)", ...resumo.vencidas, className: "text-destructive" },
    { label: "vence(m) hoje", ...resumo.vencem_hoje, className: "text-warning" },
  ].filter((i) => i.quantidade > 0);
  if (itens.length === 0) return null;
  return (
    <div className="space-y-1" data-testid={testId}>
      <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">{titulo}</p>
      {itens.map((i) => (
        <p key={i.label} className="text-sm text-card-foreground">
          <span className={`font-semibold ${i.className}`}>{i.quantidade}</span> {i.label} ·{" "}
          {formatCurrency(i.total)}
        </p>
      ))}
    </div>
  );
}

export default function PendenciasHoje() {
  const { user } = useAuth() || {};
  const permitido = PERFIS.includes(user?.perfil);
  const [dados, setDados] = useState(null);

  useEffect(() => {
    if (!permitido) return undefined;
    let ativo = true;
    async function carregar() {
      try {
        const res = await pendenciasApi.get();
        if (ativo && res?.ok) setDados(res);
      } catch {
        // silencioso: pendência é informativa
      }
    }
    carregar();
    return () => { ativo = false; };
  }, [permitido]);

  if (!permitido || !dados) return null;
  const total = (r) => (r?.vencidas?.quantidade || 0) + (r?.vencem_hoje?.quantidade || 0);
  if (total(dados.contas_pagar) + total(dados.contas_receber) === 0) return null;

  return (
    <div className="rounded-xl border border-warning/50 bg-card p-4 flex flex-wrap items-start gap-x-10 gap-y-3" data-testid="pendencias-hoje">
      <div className="flex items-center gap-2">
        <WarningCircle className="h-5 w-5 text-warning" />
        <p className="text-sm font-semibold text-card-foreground">Pendências de hoje</p>
      </div>
      <Grupo titulo="Contas a pagar" resumo={dados.contas_pagar} testId="pendencias-pagar" />
      <Grupo titulo="Contas a receber" resumo={dados.contas_receber} testId="pendencias-receber" />
      <Link to="/financeiro" className="text-sm text-primary hover:underline self-center ml-auto">
        Abrir Financeiro
      </Link>
    </div>
  );
}
