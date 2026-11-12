import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { WhatsappLogo } from "@phosphor-icons/react";
import { vendas as vendasApi } from "@/api/client";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorState } from "@/components/ui/error-state";
import { ListSkeleton } from "@/components/ui/loading-state";
import { Panel, PanelHeader, PanelTitle, PanelContent } from "@/components/ui/panel";

// Lembretes de pós-venda e upgrade (BR-104, docs/engineering/plans/PLAN-lembretes-pos-venda.md).
// O sistema não envia nada: o botão abre o WhatsApp do aparelho (wa.me) com a mensagem sugerida, e
// quem atende revisa e envia.

export const MARCOS = {
  pos_venda: {
    titulo: "7 dias — pós-venda",
    mensagem: (nome, produto) =>
      `Olá, ${nome}! Passando para saber se está tudo certo com o seu ${produto}. Qualquer dúvida, estamos à disposição!`,
  },
  satisfacao: {
    titulo: "30 dias — satisfação",
    mensagem: (nome, produto) =>
      `Olá, ${nome}! O seu ${produto} completou um mês. Está gostando? Se precisar de película, capa ou carregador, é só chamar.`,
  },
  upgrade: {
    titulo: "1 ano — upgrade",
    mensagem: (nome, produto) =>
      `Olá, ${nome}! Faz um ano que você levou o seu ${produto}. Que tal ver as condições para trocar por um modelo mais novo?`,
  },
};

/** Telefone brasileiro → número para wa.me (só dígitos, com 55). `null` se não der para usar. */
export function numeroWhatsapp(telefone) {
  const digitos = String(telefone || "").replace(/\D/g, "");
  if (digitos.length === 10 || digitos.length === 11) return `55${digitos}`;
  if ((digitos.length === 12 || digitos.length === 13) && digitos.startsWith("55")) return digitos;
  return null;
}

export function linkWhatsapp(item, tipo) {
  const numero = numeroWhatsapp(item.telefone);
  if (!numero || !MARCOS[tipo]) return null;
  const primeiroNome = (item.cliente_nome || "").trim().split(/\s+/)[0] || "tudo bem";
  const texto = MARCOS[tipo].mensagem(primeiroNome, item.produtos || "aparelho");
  return `https://wa.me/${numero}?text=${encodeURIComponent(texto)}`;
}

function hojeLocal() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}

function formatarData(iso) {
  const [ano, mes, dia] = (iso || "").split("-");
  return ano && mes && dia ? `${dia}/${mes}/${ano}` : iso;
}

export default function Lembretes() {
  const [data, setData] = useState(hojeLocal);
  const [grupos, setGrupos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    let ativo = true;
    async function carregar() {
      setLoading(true);
      setLoadError(false);
      try {
        const res = await vendasApi.lembretes(data);
        if (!ativo) return;
        if (res?.ok) setGrupos(res.grupos || []);
        else setLoadError(true);
      } catch {
        if (ativo) setLoadError(true);
      } finally {
        if (ativo) setLoading(false);
      }
    }
    carregar();
    return () => { ativo = false; };
  }, [data, reload]);

  const total = grupos.reduce((n, g) => n + g.itens.length, 0);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Lembretes de pós-venda</h1>
          <p className="text-muted-foreground text-sm">Clientes para procurar no dia: 7 dias, 30 dias e 1 ano depois da compra</p>
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="lembretes-data">Dia</Label>
          <Input
            id="lembretes-data"
            type="date"
            value={data}
            onChange={(e) => e.target.value && setData(e.target.value)}
            className="w-44"
          />
        </div>
      </div>

      {loading ? (
        <ListSkeleton />
      ) : loadError ? (
        <ErrorState title="Não foi possível carregar os lembretes." onRetry={() => setReload((r) => r + 1)} />
      ) : total === 0 ? (
        <EmptyState title="Nenhum cliente para procurar neste dia." />
      ) : (
        grupos
          .filter((g) => g.itens.length > 0)
          .map((g) => (
            <Panel key={g.tipo} data-testid={`lembretes-${g.tipo}`}>
              <PanelHeader>
                <PanelTitle>
                  {MARCOS[g.tipo]?.titulo || `${g.dias} dias`} <Badge variant="neutral">{g.itens.length}</Badge>
                </PanelTitle>
              </PanelHeader>
              <PanelContent className="divide-y divide-border">
                {g.itens.map((item) => {
                  const link = linkWhatsapp(item, g.tipo);
                  return (
                    <div key={item.venda_id} data-testid="lembrete" className="py-3 flex flex-wrap items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-card-foreground">{item.cliente_nome || "Cliente"}</p>
                        <p className="text-xs text-muted-foreground">
                          {item.produtos} ·{" "}
                          <Link to={`/vendas/${item.venda_id}`} className="hover:underline">
                            Venda #{item.venda_id}
                          </Link>{" "}
                          de {formatarData(item.data_venda)}
                        </p>
                      </div>
                      {link ? (
                        <a
                          href={link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-2 rounded-lg border border-border px-3 py-1.5 text-sm text-card-foreground hover:bg-accent"
                        >
                          <WhatsappLogo className="h-4 w-4 text-success" />
                          Abrir WhatsApp
                        </a>
                      ) : (
                        <span className="text-xs text-muted-foreground">Sem telefone válido</span>
                      )}
                    </div>
                  );
                })}
              </PanelContent>
            </Panel>
          ))
      )}
    </div>
  );
}
