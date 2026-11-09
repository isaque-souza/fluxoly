// Fallback caso /api/constantes não retorne as listas (rede/erro) — espelha
// STATUS_OS_OPCOES/OS_TIPOS_OPCOES (fluxoly_core.py). Fonte de verdade real é
// a API — mesmo padrão de Produtos.jsx/Stock.jsx.
export const STATUS_OPTIONS_FALLBACK = ["Em andamento", "Aguardando peca", "Finalizado", "Cancelado"];
export const OS_TYPES_FALLBACK = ["Assistencia", "Garantia", "Interna"];
export const TIPO_OS_INTERNA = "Interna";

export function formatCurrency(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(value || 0);
}

// Compartilhado entre VendaDetalhe.jsx e Vendas.jsx (Historico) -- status de
// venda, migrado para o Badge semântico da Foundation no PR 5 (mesmo padrão
// de getStatusVariant/OrderStatusBadge).
export const VENDA_STATUS_LABEL = {
  concluida: "Concluída",
  cancelada: "Cancelada",
};

export function vendaStatusVariant(status) {
  if (status === "concluida") return "success";
  if (status === "cancelada") return "error";
  return "neutral";
}

export function vendaStatusLabel(status) {
  return VENDA_STATUS_LABEL[status] || status || "—";
}

// Compartilhado entre Vendas.jsx e UnidadesSerializadas.jsx -- de onde veio a
// unidade vendida (estoque ou produto). Badge taxonômico (Badge
// variant="tag"), não de status -- por isso só rótulo, sem variante/cor por
// valor (PLAN-design-system-fase2.md, seção "PR 5 -- Foundation").
export const ORIGEM_UNIDADE_LABEL = {
  estoque: "Estoque",
  produto: "Produto",
};

export function origemUnidadeLabel(tipo) {
  return ORIGEM_UNIDADE_LABEL[tipo] || tipo || "—";
}

export function getOrderDisplayNumber(order) {
  if (!order) {
    return "";
  }

  // OS importada do MercadoPhone: usar o número real da integração, não o id
  // interno do Fluxoly — permite localizar a OS pelo número que o cliente/
  // MercadoPhone já usa, sincronizar atualizações e evitar duplicidade.
  if (order.origem_integracao === "mercado_phone" && order.id_externo_integracao) {
    return String(order.id_externo_integracao);
  }

  // OS nativa do Fluxoly: id interno, sem truncar (truncar via .slice(-5) foi
  // o bug real corrigido em 2026-06-09, não a preferência pelo número externo).
  if (order.id !== undefined && order.id !== null) {
    return String(order.id);
  }

  return String(order.id_externo_integracao || "");
}

// Fonte única de verdade da semântica visual de status de OS -- consumida por
// OrderStatusBadge.jsx (Orders/EditOrder) e Kanban.jsx (cor das colunas), para
// que as duas telas nunca divirjam na interpretação de cor de um mesmo status
// (achado da auditoria da Fase 2 do Design System, PLAN-design-system-fase2.md
// PR 3). Variantes correspondem às do Badge semântico (components/ui/badge.jsx).
export function getStatusVariant(status) {
  switch (status) {
    case "Em andamento":    return "info";
    case "Aguardando peca": return "warning";
    case "Finalizado":      return "success";
    case "Cancelado":       return "error";
    default:                return "neutral";
  }
}

export function isStatusOpen(status) {
  return status !== "Finalizado" && status !== "Cancelado";
}

export function calcularFaturamento(valor_cobrado, valor_descontado) {
  return (valor_cobrado || 0) > 0 ? (valor_cobrado || 0) : (valor_descontado || 0);
}

export function normalizeImei(imei) {
  const digits = (imei || "").replace(/\D/g, "");
  return digits.length >= 14 && digits.length <= 16 ? digits : "";
}
