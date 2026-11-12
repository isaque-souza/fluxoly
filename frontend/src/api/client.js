/**
 * Fluxoly API Client
 * Talks to Flask backend at /api/*.
 * Uses session cookies — credentials: 'include' on every request.
 * In Vite dev mode, the proxy in vite.config.js forwards /api → http://localhost:5080.
 */

const ENV_BASE = String(import.meta.env.VITE_API_URL || "").trim().replace(/\/$/, "");
const IS_BROWSER = typeof window !== "undefined";
const HOSTNAME = IS_BROWSER ? window.location.hostname : "";
const IS_VERCEL = /\.vercel\.app$/i.test(HOSTNAME);
const PROJECT_SLUG = IS_VERCEL ? HOSTNAME.split(".")[0] : "";
const GUESSED_RENDER_BASE = PROJECT_SLUG ? `https://${PROJECT_SLUG}.onrender.com/api` : "";
const BASE = ENV_BASE || (IS_VERCEL ? GUESSED_RENDER_BASE : "/api");

if (IS_BROWSER && IS_VERCEL && !ENV_BASE) {
  console.warn(
    "[Fluxoly] VITE_API_URL não configurado no Vercel. Usando fallback automático:",
    BASE,
    "| Recomendado: configurar VITE_API_URL com a URL real do backend (/api).",
  );
}

function expandPieceMap(pecas = {}) {
  return Object.entries(pecas).flatMap(([id, quantidade]) => {
    const itemId = Number.parseInt(id, 10);
    const total = Number.parseInt(quantidade, 10);
    if (!Number.isInteger(itemId) || !Number.isInteger(total) || total <= 0) {
      return [];
    }
    return Array.from({ length: total }, () => itemId);
  });
}

/**
 * Normaliza parâmetros de camelCase para snake_case para compatibilidade com backend
 * @param {Object} params - Parâmetros a normalizar
 * @returns {Object} Parâmetros normalizados
 */
function normalizeQueryParams(params = {}) {
  const normalized = {};
  for (const [key, value] of Object.entries(params)) {
    if (key === "startDate") normalized["start_date"] = value;
    else if (key === "endDate") normalized["end_date"] = value;
    else normalized[key] = value;
  }
  return normalized;
}

function normalizeStockResponse(data) {
  if (data?.ok && data.itens && !data.items) {
    return { ...data, items: data.itens };
  }
  return data;
}

function normalizeWarrantyResponse(data) {
  if (!data?.ok || !data.ordens) {
    return data;
  }

  // V1.5 -- cada item agora é uma linha de reparo (não mais uma OS inteira),
  // ver PLAN-V1.5-Garantia.md. `reparo_nome` substitui a antiga lista
  // `reparos` (múltiplos nomes por OS) -- mantido como `reparos_texto` aqui
  // só para não precisar renomear nas telas que já consomem esse campo.
  const garantias = data.ordens.map((item) => {
    const color = item.garantia?.color;
    const statusMap = {
      green: "ativa",
      amber: "vencendo",
      red: "vencida",
    };

    return {
      ...item,
      reparos_texto: item.reparo_nome || "",
      dias_restantes: item.garantia?.dias_restantes,
      status_garantia: statusMap[color] || "desconhecida",
    };
  });

  return { ...data, garantias };
}

function normalizeCostsResponse(data) {
  if (data?.ok && data.itens && !data.custos) {
    return { ...data, custos: data.itens };
  }
  return data;
}

function withPieceIds(data) {
  if (!data || !data.pecas) {
    return data;
  }

  const { pecas, ...rest } = data;
  return {
    ...rest,
    pecas_ids: expandPieceMap(pecas),
  };
}

async function request(method, path, body) {
  const opts = {
    method,
    credentials: "include",
    headers: {},
  };
  if (body !== undefined) {
    opts.headers["Content-Type"] = "application/json";
    opts.body = JSON.stringify(body);
  }
  const url = `${BASE}${path}`;
  const res = await fetch(url, opts);
  const text = await res.text();

  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    console.error("[Fluxoly] Resposta não-JSON da API", {
      method,
      url,
      status: res.status,
      bodyStart: (text || "").slice(0, 180),
    });
  }

  if (!res.ok) {
    console.error("[Fluxoly] Erro HTTP na API", {
      method,
      url,
      status: res.status,
      response: data,
    });
  }

  return data;
}

const get   = (path)        => request("GET",    path);
const post  = (path, body)  => request("POST",   path, body);
const put   = (path, body)  => request("PUT",    path, body);
const patch = (path, body)  => request("PATCH",  path, body);
const del   = (path)        => request("DELETE", path);

// ── Auth ────────────────────────────────────────────────────────────────────
export const auth = {
  login:  (usuario, senha) => post("/auth/login",  { usuario, senha }),
  logout: ()               => post("/auth/logout"),
  me:     ()               => get("/auth/me"),
};

// ── Constants ───────────────────────────────────────────────────────────────
function sanitizeConstants(data = {}) {
  if (!data || typeof data !== 'object') return data;
  const copy = { ...data };
  const sanitizeArray = (arr) => Array.isArray(arr)
    ? arr
        .map((s) => (typeof s === 'string' ? s.trim() : s))
        .filter((s) => s !== null && s !== undefined && !(typeof s === 'string' && s === ''))
    : arr;

  for (const k of Object.keys(copy)) {
    if (Array.isArray(copy[k])) {
      copy[k] = sanitizeArray(copy[k]);
    } else if (copy[k] && typeof copy[k] === 'object') {
      // sanitize nested objects where values may be arrays (e.g. iphone_colors)
      const obj = { ...copy[k] };
      for (const sk of Object.keys(obj)) {
        if (Array.isArray(obj[sk])) obj[sk] = sanitizeArray(obj[sk]);
      }
      copy[k] = obj;
    }
  }

  return copy;
}

export const constantes = {
  // Fetch and sanitize backend constants to avoid empty-string options being
  // rendered as SelectItem value="" which causes a runtime error in Radix.
  get: () => get("/constantes").then((d) => sanitizeConstants(d)),
};

// ── Alerts ──────────────────────────────────────────────────────────────────
export const alertas = {
  list: () => get("/alertas"),
};

// Pendências da tela inicial -- contas vencidas/vencendo hoje (admin/financeiro).
export const pendencias = {
  get: () => get("/pendencias"),
};

// ── Dashboard ───────────────────────────────────────────────────────────────
export const dashboard = {
  get: (params = {}) => {
    const normalized = normalizeQueryParams(params);
    const qs = new URLSearchParams(normalized).toString();
    return get(`/dashboard${qs ? "?" + qs : ""}`);
  },
};

// ── Ordens de Serviço ───────────────────────────────────────────────────────
export const ordens = {
  list:          (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/ordens${qs ? "?" + qs : ""}`);
  },
  get:           (id)         => get(`/ordens/${id}`),
  create:        (data)       => post("/ordens", withPieceIds(data)),
  update:        (id, data)   => put(`/ordens/${id}`, withPieceIds(data)),
  delete:        (id)         => del(`/ordens/${id}`),
  // V1.5 -- Garantia de Reparo (BR-061): `garantias` é opcional, {reparo_id: tipo_garantia_id} --
  // só é exigido pelo backend na transição para Finalizado.
  patchStatus:   (id, status, garantias) =>
    request("PATCH", `/ordens/${id}/status`, garantias ? { status, garantias } : { status }),
  clienteHistory:(nome)       => get(`/ordens/historico-cliente?cliente=${encodeURIComponent(nome)}`),
  corrigirGarantiaReparo: (osId, reparoId, data) =>
    patch(`/ordens/${osId}/reparos/${reparoId}/garantia`, data),
  historicoGarantiaReparo: (osId, reparoId) =>
    get(`/ordens/${osId}/reparos/${reparoId}/historico-garantia`),
  // BR-095 a BR-098 -- conteúdo do comprovante de entrada/entrega para o cliente (o PDF é gerado no navegador).
  documento: (id, tipo) => get(`/ordens/${id}/documento?tipo=${encodeURIComponent(tipo)}`),
};

// ── Dados da Loja (BR-094) ───────────────────────────────────────────────────
// ── Auditoria (leitura do audit_log, admin/financeiro) ─────────────────────
export const auditoria = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/auditoria${qs ? "?" + qs : ""}`);
  },
};

export const dadosLoja = {
  get:  ()     => get("/dados-loja"),
  save: (data) => put("/dados-loja", data),
};

// ── Checklist de Aparelho ──────────────────────────────────────────────────
export const checklist = {
  getByOrder:       (orderId)     => get(`/ordens/${orderId}/checklist`),
  generateToken:    (orderId)     => post(`/ordens/${orderId}/checklist/token`),
  getPublic:        (token)       => get(`/checklist/${encodeURIComponent(token)}`),
  savePublic:       (token, data) => post(`/checklist/${encodeURIComponent(token)}`, data),
  publicUrl:        (token, baseUrl = "") => {
    const suffix = `/app/checklist/${encodeURIComponent(token)}`;
    return baseUrl ? `${baseUrl.replace(/\/$/, "")}${suffix}` : suffix;
  },
  qrImageUrl:       (url)         => `https://api.qrserver.com/v1/create-qr-code/?size=240x240&data=${encodeURIComponent(url)}`,
};

// ── Estoque ─────────────────────────────────────────────────────────────────
export const estoque = {
  list:   async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return normalizeStockResponse(await get(`/estoque${qs ? "?" + qs : ""}`));
  },
  reposicaoSugestao: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return await get(`/estoque/reposicao-sugerida${qs ? "?" + qs : ""}`);
  },
  get:    (id)         => get(`/estoque/${id}`),
  create: (data)       => post("/estoque", data),
  update: (id, data)   => put(`/estoque/${id}`, data),
  delete: (id)         => del(`/estoque/${id}`),
};

// ── Produtos (Catálogo Comercial) ──────────────────────────────────────────
export const produtos = {
  list:   (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/produtos${qs ? "?" + qs : ""}`);
  },
  get:    (id)         => get(`/produtos/${id}`),
  create: (data)       => post("/produtos", data),
  update: (id, data)   => put(`/produtos/${id}`, data),
  delete: (id)         => del(`/produtos/${id}`),
};

// ── Unidades Serializadas (rastreamento por IMEI/serial, ADR-007) ─────────
export const unidadesSerializadas = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/unidades-serializadas${qs ? "?" + qs : ""}`);
  },
  get: (id) => get(`/unidades-serializadas/${id}`),
  historico: (id) => get(`/unidades-serializadas/${id}/historico`),
  create: (data) => post("/unidades-serializadas", data),
  updateStatus: (id, status) => request("PATCH", `/unidades-serializadas/${id}/status`, { status }),
  update: (id, data) => request("PATCH", `/unidades-serializadas/${id}`, data),
};

// ── Shopping List (Compras) ───────────────────────────────────────────────
export const shoppingList = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/shopping-list${qs ? `?${qs}` : ""}`);
  },
  get: (id) => get(`/shopping-list/${id}`),
  create: (data) => post(`/shopping-list`, data),
  update: (id, data) => put(`/shopping-list/${id}`, data),
  patchStatus: (id, statusBody) => request("PATCH", `/shopping-list/${id}/status`, statusBody),
  delete: (id) => del(`/shopping-list/${id}`),
};

// ── Reparos ─────────────────────────────────────────────────────────────────
export const reparos = {
  list:   ()          => get("/reparos"),
  create: (data)      => post("/reparos", data),
  update: (id, data)  => put(`/reparos/${id}`, data),
  delete: (id)        => del(`/reparos/${id}`),
};

// ── Custos Operacionais ──────────────────────────────────────────────────────
export const custos = {
  list:   async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return normalizeCostsResponse(await get(`/custos${qs ? "?" + qs : ""}`));
  },
  create: (data)        => post("/custos", data),
  update: (id, data)    => put(`/custos/${id}`, data),
  delete: (id)          => del(`/custos/${id}`),
};

// ── Tabelas de Preço ─────────────────────────────────────────────────────────
export const precos = {
  list:   ()     => get("/precos"),
  save:   (data) => post("/precos", data),          // { tabela, servico, modelo, valor }
  remove: (data) => post("/precos/excluir", data),  // { tabela, servico, modelo }
  sugerir: (params) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/precos/sugerir?${qs}`);
  },
};

// ── Garantias ────────────────────────────────────────────────────────────────
export const garantias = {
  list: async (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return normalizeWarrantyResponse(await get(`/garantias${qs ? "?" + qs : ""}`));
  },
};

// V1.5 -- Tipos de Garantia (BR-055): cadastro compartilhado entre Vendas e Assistência.
export const tiposGarantia = {
  list:   (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/tipos-garantia${qs ? "?" + qs : ""}`);
  },
  create: (data)     => post("/tipos-garantia", data),
  update: (id, data) => put(`/tipos-garantia/${id}`, data),
};

// ── Clientes ─────────────────────────────────────────────────────────────────
export const clientes = {
  list:   (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/clientes${qs ? "?" + qs : ""}`);
  },
  get:    (id)         => get(`/clientes/${id}`),
  create: (data)       => post("/clientes", data),
  update: (id, data)   => put(`/clientes/${id}`, data),
  delete: (id)         => del(`/clientes/${id}`),
  anonymize: (id)      => post(`/clientes/${id}/anonimizar`),
};

// ── Vendas ───────────────────────────────────────────────────────────────────
export const vendas = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/vendas${qs ? "?" + qs : ""}`);
  },
  create: (data) => post("/vendas", data),
  get:    (id)   => get(`/vendas/${id}`),
  // Painel de garantias unificado -- garantias de venda com dias restantes.
  garantias: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/vendas/garantias${qs ? "?" + qs : ""}`);
  },
  cancelar: (id, data) => post(`/vendas/${id}/cancelar`, data),
  // BR-103 -- conteúdo do recibo para o cliente (PDF desenhado em lib/vendaPdf.js).
  recibo: (id) => get(`/vendas/${id}/recibo`),
  // V1.3 -- Descontos e Aprovação (BR-043: Ajuste Comercial Autorizado).
  ajustarDescontoItem: (vendaId, itemId, data) =>
    patch(`/vendas/${vendaId}/itens/${itemId}/ajuste-desconto`, data),
  historicoDescontoItem: (vendaId, itemId) =>
    get(`/vendas/${vendaId}/itens/${itemId}/historico-desconto`),
  // V1.4 -- Comissão (BR-044 a BR-049).
  atribuirComissaoItem: (vendaId, itemId, data) =>
    patch(`/vendas/${vendaId}/itens/${itemId}/comissao`, data),
  historicoComissaoItem: (vendaId, itemId) =>
    get(`/vendas/${vendaId}/itens/${itemId}/historico-comissao`),
  // V1.5 -- Garantia de Venda (BR-059).
  corrigirGarantiaItem: (vendaId, itemId, data) =>
    patch(`/vendas/${vendaId}/itens/${itemId}/garantia`, data),
  historicoGarantiaItem: (vendaId, itemId) =>
    get(`/vendas/${vendaId}/itens/${itemId}/historico-garantia`),
};

// ── Compra de Aparelhos (BR-083 a BR-093) ───────────────────────────────────
export const comprasAparelhos = {
  list: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/compras-aparelhos${qs ? "?" + qs : ""}`);
  },
  get:       (id)        => get(`/compras-aparelhos/${id}`),
  create:    (data)      => post("/compras-aparelhos", data),
  cancelar:  (id, data)  => post(`/compras-aparelhos/${id}/cancelar`, data),
  relatorio: (mes)       => get(`/compras-aparelhos/relatorio?mes=${encodeURIComponent(mes)}`),
};

// ── Relatórios ───────────────────────────────────────────────────────────────
export const relatorios = {
  tecnicos:  (params = {}) => {
    const normalized = normalizeQueryParams(params);
    const qs = new URLSearchParams(normalized).toString();
    return get(`/relatorios/tecnicos${qs ? "?" + qs : ""}`);
  },
  custosOperacionais: (params = {}) => {
    const normalized = normalizeQueryParams(params);
    const qs = new URLSearchParams(normalized).toString();
    return get(`/relatorios/custos-operacionais${qs ? "?" + qs : ""}`);
  },
  pdfUrl:    (tipo, params = {}) => {
    const normalized = normalizeQueryParams(params);
    const qs = new URLSearchParams(normalized).toString();
    const endpoint = tipo === "custos" ? "custos-operacionais" : tipo;
    return `${BASE}/relatorios/pdf/${endpoint}${qs ? "?" + qs : ""}`;
  },
  downloadPdf: async (tipo, params = {}, fileName = "") => {
    // Faz download do PDF com autenticação (credentials inclusos)
    const normalized = normalizeQueryParams(params);
    const qs = new URLSearchParams(normalized).toString();
    const endpoint = tipo === "custos" ? "custos-operacionais" : tipo;
    const url = `${BASE}/relatorios/pdf/${endpoint}${qs ? "?" + qs : ""}`;
    
    try {
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) {
        throw new Error(`Erro ao baixar PDF: ${res.status}`);
      }
      
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = fileName || `relatorio-${tipo}-${Date.now()}.pdf`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error("[Fluxoly] Erro ao baixar PDF:", error);
      throw error;
    }
  },
};

// ── Usuários ─────────────────────────────────────────────────────────────────
export const usuarios = {
  list:   ()          => get("/usuarios"),
  create: (data)      => post("/usuarios", data),
  update: (id, data)  => put(`/usuarios/${id}`, data),
  delete: (id)        => del(`/usuarios/${id}`),
};

// ── Backup ───────────────────────────────────────────────────────────────────
export const backup = {
  criar:    (data)   => post("/backup/criar", data),
  list:     ()       => get("/backup/listar"),
  download: async (fileName) => {
    // Faz download do backup com autenticação (credentials inclusos)
    const url = `${BASE}/backup/download/${encodeURIComponent(fileName)}`;
    try {
      const res = await fetch(url, { credentials: "include" });
      if (!res.ok) {
        throw new Error(`Erro ao baixar backup: ${res.status}`);
      }
      
      const blob = await res.blob();
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(link.href);
    } catch (error) {
      console.error("[Fluxoly] Erro ao baixar backup:", error);
      throw error;
    }
  },
  restaurar: (formData) => fetch(`${BASE}/backup/restaurar`, {
    method: "POST",
    credentials: "include",
    body: formData,
  }).then((r) => r.json()),
};

// ── Financeiro Mínimo (BR-067 a BR-069) ─────────────────────────────────────
export const caixa = {
  list:     (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/caixa${qs ? "?" + qs : ""}`);
  },
  saldo:    () => get("/caixa/saldo"),
  create:   (data) => post("/caixa", data),
  estornar: (id)   => post(`/caixa/${id}/estornar`),
};

export const contasPagar = {
  list:      (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/contas-pagar${qs ? "?" + qs : ""}`);
  },
  get:       (id)         => get(`/contas-pagar/${id}`),
  create:    (data)       => post("/contas-pagar", data),
  update:    (id, data)   => put(`/contas-pagar/${id}`, data),
  delete:    (id)         => del(`/contas-pagar/${id}`),
  pagar:     (id)         => post(`/contas-pagar/${id}/pagar`),
  cancelar:  (id)         => post(`/contas-pagar/${id}/cancelar`),
};

export const contasReceber = {
  list:      (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return get(`/contas-receber${qs ? "?" + qs : ""}`);
  },
  get:       (id)         => get(`/contas-receber/${id}`),
  create:    (data)       => post("/contas-receber", data),
  update:    (id, data)   => put(`/contas-receber/${id}`, data),
  delete:    (id)         => del(`/contas-receber/${id}`),
  receber:   (id)         => post(`/contas-receber/${id}/receber`),
  cancelar:  (id)         => post(`/contas-receber/${id}/cancelar`),
};
