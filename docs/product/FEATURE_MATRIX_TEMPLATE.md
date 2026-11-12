# FEATURE_MATRIX_TEMPLATE.md — Funcionalidades e Comparação com Concorrentes

**Status:** Seção 1 completa (extraída do código) · Seção 2 vazia — a preencher após pesquisa de mercado real.
**Última revisão:** 2026-07-09

---

Este documento tem duas seções com propósitos diferentes:

- **Seção 1 — Funcionalidades Atuais:** já nasce útil, sem depender de pesquisa nenhuma. Reflete o que o
  Fluxoly faz hoje, extraído de `docs/engineering/DOMAIN_MODEL.md` — não é suposição, é o estado real do código.
- **Seção 2 — Comparação com Concorrentes:** intencionalmente vazia. Comparar com concorrentes exige
  pesquisa de mercado real (testar o produto do concorrente, ler documentação pública, ou levantamento
  direto), não suposição. Quando a pesquisa for feita, copie este arquivo para `docs/FEATURE_MATRIX.md`
  e preencha as colunas — cada célula preenchida deve ter uma fonte rastreável na coluna "Fonte".

**Convenção de símbolos:** `✅` implementado · `🚧` em desenvolvimento/planejado · `❌` não oferece · `❓` não pesquisado ainda

---

## 1. Funcionalidades Atuais da Fluxoly

| Funcionalidade | Status | Domínio (ver `DOMAIN_MODEL.md`) |
|---|---|---|
| Ordens de Serviço | ✅ | 1.3 Ordens de Serviço |
| Controle de Estoque | ✅ | 1.4 Estoque |
| Tabela de Preços | ✅ | 1.6 Tabela de Preços |
| Lista de Compras | ✅ | 1.5 Compras / Shopping List |
| Garantias | ✅ | 1.3 Ordens de Serviço (checklist) |
| Relatórios (IR Phones, Técnicos) | ✅ | 1.8 Relatórios |
| Backup automático (local, e-mail, Google Drive) | ✅ | 1.9 Backup / Persistência |
| Login / Autenticação | ✅ (básico — sem recuperação de senha, 2FA, auditoria) | 1.1 Autenticação |
| Permissões granulares (por tela, não só por perfil) | ❌ | 1.2 Usuários |
| Integração MercadoPhone | ✅ | 1.10 Integrações |
| Vendas (peça/acessório/serviço/combo) | ❌ | Não existe como domínio ainda |
| Caixa (abertura/fechamento/sangria/suprimento) | ❌ | Não existe como domínio ainda |
| Financeiro (contas a pagar/receber, fluxo de caixa) | ❌ | Não existe como domínio ainda |
| Dashboard com indicadores comerciais (faturamento, lucro, ticket médio) | ❌ | Não existe como domínio ainda |
| CRM / Histórico de cliente por identidade | ❌ | `cliente` é campo texto em `os`, não entidade — ver `DOMAIN_MODEL.md` seção 2 |
| WhatsApp (notificações automáticas) | ❌ | Não existe como domínio ainda |
| Multiempresa | ❌ | Decisão de estratégia em ADR-005, implementação não iniciada |
| API pública documentada | ❌ | Não existe |

---

## 2. Comparação com Concorrentes

| Funcionalidade | Fluxoly | Concorrente | Fonte | Observações |
|---|---|---|---|---|
| Ordens de Serviço | ✅ | ❓ | | |
| Controle de Estoque | ✅ | ❓ | | |
| Tabela de Preços | ✅ | ❓ | | |
| Lista de Compras | ✅ | ❓ | | |
| Garantias | ✅ | ❓ | | |
| Relatórios | ✅ | ❓ | | |
| Backup automático | ✅ | ❓ | | |
| Login / Autenticação | ✅ (básico) | ❓ | | |
| Permissões granulares | ❌ | ❓ | | |
| Vendas (peça/acessório/serviço/combo) | ❌ | 🟡 (Mercado Phone) | `docs/product/research/BENCHMARKS/MERCADO_PHONE.md` | Walkthrough de Vendas e OS feito em 2026-11-11 (somente leitura) — ver seções "Vendas" e "OS" do benchmark |
| Caixa (abertura/fechamento/sangria) | ❌ | ❓ | | |
| Financeiro (contas a pagar/receber) | ❌ | ❓ | | |
| Dashboard com indicadores comerciais | ❌ | ❓ | | |
| CRM / Histórico de cliente | ❌ | ❓ | | |
| WhatsApp (notificações automáticas) | ❌ | ❓ | | |
| Multiempresa | ❌ | ❓ | | |
| API pública | ❌ | ❓ | | |
| Integração MercadoPhone | ✅ | ❓ | | |

### Concorrentes a Pesquisar

TODO — lista final a definir pelo Product Owner. Mencionados em discussão de roadmap (data original):
Mercado Phone, Nextsi, SisAssist. Mencionados em conversa posterior (2026-07-22, ainda não reconciliado
com a lista acima pelo PO): CellStore, Mobix, Tiny, Bling.

Evidência de pesquisa por módulo (fatos observados, não conclusões) passa a viver em
`docs/product/research/BENCHMARKS/` — um arquivo por concorrente, um walkthrough por módulo. Esta tabela
consome esse trabalho (coluna "Fonte"), não o duplica.

---

## Documentos relacionados

- `docs/company/PRODUCT_REQUIREMENTS.md` — seção "Diferenciais" depende da Seção 2 deste documento
- `docs/engineering/DOMAIN_MODEL.md` — fonte de verdade para a Seção 1 (refletem o código, não suposição)
