import { useEffect, useState } from "react";
import { CircleNotch, MagnifyingGlass } from "@phosphor-icons/react";
import { unidadesSerializadas as unidadesApi } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

// OS interna (BR-090): escolhe um aparelho de compra ativa que ainda está no estoque
// (em reparo ou disponível). Busca em Unidades Serializadas com `origem=compra` -- e não
// em /api/compras-aparelhos -- porque quem abre OS é o técnico, que não vê as compras
// (elas guardam nome/telefone de quem vendeu, BR-088/BR-089). O backend valida de novo.

const STATUS_LABEL = { em_reparo: "Em reparo", disponivel: "Disponível" };

export function aparelhoLabel(unidade) {
  return [unidade.origem_label, unidade.produto_capacidade, unidade.produto_cor].filter(Boolean).join(" · ");
}

export default function AparelhoCompradoPicker({ selecionado, onSelecionar, onTrocar }) {
  const [query, setQuery] = useState("");
  const [resultados, setResultados] = useState([]);
  const [buscando, setBuscando] = useState(false);

  useEffect(() => {
    if (selecionado) return undefined;
    let ativo = true;
    const timer = setTimeout(() => {
      setBuscando(true);
      const params = { origem: "compra", per_page: 50 };
      if (query.trim()) params.q = query.trim();
      unidadesApi.list(params).then((res) => {
        if (!ativo) return;
        const noEstoque = (res?.ok ? res.items || [] : []).filter((u) => u.status in STATUS_LABEL);
        setResultados(noEstoque);
      }).catch(() => {
        if (ativo) setResultados([]);
      }).finally(() => { if (ativo) setBuscando(false); });
    }, 300);
    return () => { ativo = false; clearTimeout(timer); };
  }, [query, selecionado]);

  if (selecionado) {
    return (
      <div className="flex items-center justify-between bg-secondary/40 rounded-lg px-3 py-2">
        <div>
          <p className="text-sm font-medium text-card-foreground">{aparelhoLabel(selecionado) || "Aparelho comprado"}</p>
          <p className="text-xs text-muted-foreground font-mono">IMEI {selecionado.imei || "—"}</p>
        </div>
        {onTrocar && <Button type="button" variant="ghost" size="sm" onClick={onTrocar}>Trocar</Button>}
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <div className="relative">
        <MagnifyingGlass className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
        <Input
          aria-label="Buscar aparelho comprado"
          placeholder="Buscar aparelho comprado por IMEI ou modelo..."
          className="pl-8"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        {buscando && <CircleNotch className="absolute right-2.5 top-2.5 h-4 w-4 animate-spin text-muted-foreground" />}
      </div>
      {resultados.length > 0 ? (
        <div className="border border-border rounded-lg max-h-56 overflow-y-auto divide-y divide-border">
          {resultados.map((u) => (
            <button
              type="button"
              key={u.id}
              onClick={() => onSelecionar(u)}
              className="w-full text-left px-3 py-2 text-sm hover:bg-accent/50 transition-colors flex items-center justify-between gap-2"
            >
              <div>
                <p className="font-medium text-card-foreground">{aparelhoLabel(u)}</p>
                <p className="text-xs text-muted-foreground font-mono">IMEI {u.imei}</p>
              </div>
              <Badge variant={u.status === "em_reparo" ? "warning" : "success"}>{STATUS_LABEL[u.status]}</Badge>
            </button>
          ))}
        </div>
      ) : (
        !buscando && (
          <p className="text-xs text-muted-foreground">
            Nenhum aparelho comprado no estoque. Registre a compra em Compras de Aparelhos antes de abrir a OS interna.
          </p>
        )
      )}
    </div>
  );
}
