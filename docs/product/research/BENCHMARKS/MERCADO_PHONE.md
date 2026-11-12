# Benchmark — Mercado Phone

**Tipo de documento:** pesquisa de produto, não especificação. Nada aqui vira requisito automaticamente —
ver `docs/product/features/` para o que de fato foi aprovado para a Fluxoly.

**Sistema analisado:** Mercado Phone (ERP vertical para lojas de dispositivos móveis)
**Versão/ambiente observado:** web `app.mercadophone.tech`, conta de produção de uma loja usuária, observada
em 2026-11-11 (o sistema não exibe número de versão na interface)
**Análises realizadas:**

| Módulo | Status | Data |
|---|---|---|
| Visão geral (menus, telas principais, impressão de navegação) | Concluída — superficial, não é walkthrough de fluxo | 2026-07-22 |
| Vendas | Pendente | — |
| OS | Concluída — estrutura de telas, campos e menus (somente leitura; nenhuma OS criada ou editada) | 2026-11-11 |
| Financeiro | Pendente | — |
| Fiscal | Pendente | — |

---

## Critérios deste documento

Combinados em conversa (2026-07-22), valem para qualquer módulo analisado aqui:

1. **Fato antes de interpretação** — registrar exatamente o que o sistema faz antes de analisar o valor da decisão.
2. **Observação separada de recomendação** — cada achado tem um bloco "Observado" e um bloco "Análise"/"Impacto na Fluxoly" distintos, nunca misturados na mesma frase.
3. **Nenhuma decisão implícita** — qualquer conclusão que dependa de estratégia de produto vira "Decisão pendente do PO", nunca é assumida como aprovada.
4. **Contexto registrado** — versão observada, data da análise e quais fluxos foram percorridos, para permitir revisão quando o concorrente evoluir.

---

## Vendas

*Aguardando walkthrough completo do fluxo (cadastro → orçamento → PDV → histórico → estoque → garantia →
cancelamento). A visão geral de 2026-07-22 cobriu apenas menus/telas principais, não o fluxo de venda em
si — por isso as subseções abaixo estão vazias por decisão deliberada, não por esquecimento.*

### Objetivo observado
TODO

### Fluxo observado
TODO

### Campos existentes
TODO

### Regras percebidas
TODO

### Integrações
TODO

### Pontos positivos
TODO

### Pontos negativos
TODO

### Perguntas em aberto
TODO

### Impacto para Fluxoly

#### Reaproveitar
TODO

#### Adaptar
TODO

#### Não implementar
TODO

#### Decisão pendente do PO
TODO

---

## OS

*Walkthrough de 2026-11-11, somente leitura: listagem, menus de ação, formulário de nova OS (todas as abas,
fechado sem salvar), Kanban, Monitoramento de garantias, Dashboard e menu de Configurações. Não percorrido:
o fluxo de salvar/alterar situação/finalizar (exigiria criar uma OS na conta da loja), o link de
acompanhamento do cliente, o layout dos documentos impressos e as telas internas de Configurações. Nenhum
dado de cliente foi registrado aqui. Listas como situações, termos, tipos e canais de venda são
configuráveis pela loja (menu Configurações): os valores citados são os da conta observada, não padrão do
sistema.*

### Objetivo observado
Registrar o atendimento técnico do começo ao fim (entrada do aparelho → diagnóstico → orçamento → serviço →
pagamento → entrega → garantia) em uma única tela, já ligada a estoque de peças, financeiro e fiscal.

### Fluxo observado
- **Menu OS:** Listagem · Nova · Kanban · Estoque de Peças · Movimentações de estoque · Monitoramento de
  garantias · Dashboard · Configurações.
- **Listagem:** colunas Cód. OS, Situação, Cliente, Tags, Data de criação, Serviços, Técnico, Aparelhos,
  IMEI/Serial e Valor total, com filtro por coluna, soma do valor no rodapé e paginação de 50. Mostra há
  quantos dias uma OS está em andamento ("5 dias"). Topo: "Cadastrar nova OS", "Cadastro rápido",
  Ferramentas (modelo de etiqueta, importação, ver registros deletados, exportar CSV/XLS/PDF/XML/ZIP),
  "Modelo de lista" (colunas salvas) e "Limpar filtros".
- **Ações por OS:** Editar, Edição rápida, Detalhes, Alterar situação, Pagamento TEF; documentos: Assinar,
  Imprimir A4 / 80mm (térmica) / A4 duas vias / Etiqueta, Enviar por e-mail, WhatsApp, Link de
  acompanhamento; Excluir (exclusão lógica: existe "ver registros deletados").
- **Menu NF por OS:** NFS-e (emitir, preview, consultar, DANFSe, enviar por e-mail, XML, cancelar) e NF-e dos
  produtos usados na OS, cada uma com o próprio status ("Não enviada").
- **Kanban:** uma coluna por situação, com contagem. O cartão mostra nº, cliente, aparelho, ID, IMEI,
  serviços, vendedor, total, técnico executor, data e "há N meses".
- **Monitoramento de garantias:** abas Vendas em garantia · OS em garantia · Vendas expiradas · OS expiradas
  · Produtos em garantia · Produtos expirados, com data de vencimento e "dias restantes" por item.
- **Dashboard:** prazos (vencidas / hoje / amanhã / futuras, pela data de previsão), total por prioridade,
  total por situação, faturamento por dia, ranking de técnicos (nº de OS e valor), OS por hora de criação e
  últimas OS.

### Campos existentes
Formulário em modal com 8 abas e um cabeçalho fixo de totais: **Total Serviços · Total Peças/Produtos · Total
da OS · Total pago · Saldo · Lucro** (lucro oculto por padrão, com botão de olho).

| Aba | Campos |
|---|---|
| Informações gerais | Cliente* (busca + cadastrar + editar na hora), Vendedor, Técnico*, Prioridade (Alta/Média/Baixa, com cor), Situação*, Termo de entrada, Termo de saída, Data de criação, Data de finalização, Data de previsão, Natureza de operação (fiscal), Tipo de aparelho (iPhone, iPad, Apple Watch, MacBook…), Canal de venda* (WhatsApp, Instagram, Retirada loja, Garantia…), Código, Aparelho entregue? (sim/não), Mostrar senha no recibo? (sim/não), Destino (OS para cliente / OS interna), Relato do cliente, Tags, Laudo técnico, Solução, Observação, Observação interna |
| Aparelhos | Lista de aparelhos na OS (mais de um por OS): Equipamento, Tipo de produto, Modelo, Descrição*, Senha (com desenho de padrão), IMEI (com botão de leitura), Marca, GB, Cor, Serial Number |
| Serviços | Lista de serviços: Serviço (+ cadastrar), Modelo de checklist por serviço, Desconto, Valor de custo, Valor de cobrança, Valor de taxa |
| Peças/Produtos | Lista: Peça/Produto (do estoque, + cadastrar/editar), Quantidade, Desconto, Custo, Venda, Taxa |
| Checklists | Um ou mais modelos de checklist anexados à OS |
| Pagamento | Desconto total (R$ ou %); várias formas de pagamento, cada uma com situação (Pago…), tipo (Receita), forma, valor, parcelas (com gerador de parcelas), caixa do dia; "Usar crédito" do cliente |
| Anexos | Arquivos (habilitado só depois de salvar) |
| Assinaturas | Assinatura do cliente (habilitada só depois de salvar) |

Rodapé: Salvar · Salvar & fechar · Limpar formulário · Voltar · **Configurar campos** (a loja escolhe quais
campos aparecem). Configurações de OS: Parâmetros, Campos extras, Metas, Maquininhas POS (+ histórico),
Serviços, Técnicos, Modelos de etiquetas, Tipos, Situações, Prioridades, Tags, Dashboard, Modelos de
checklist, Termos de entrada/saída, Modelos de WhatsApp.

### Regras percebidas
- Situações da conta: Orçamento, Aprovado, Em andamento, Aguardando peça, Finalizado, Cancelado (nova OS
  abre em "Em andamento").
- Campos obrigatórios: Cliente, Técnico, Situação, Canal de venda; no aparelho, Descrição.
- Anexos e assinatura exigem a OS salva antes.
- Cada serviço e cada peça têm custo próprio, e o lucro da OS sai da soma deles.
- O pagamento fica na própria OS, ligado ao caixa do dia, e pode ser parcial (Total pago × Saldo).
- A garantia vem de "termos" com prazo (ex.: 30/90/180 dias), escolhidos na entrada e na saída; o
  monitoramento calcula o vencimento a partir da data de finalização.
- OS interna é um "Destino" do mesmo formulário, não um tipo à parte.

### Integrações
NFS-e e NF-e, TEF/maquininhas POS, WhatsApp (modelos de mensagem), e-mail, impressora térmica 80mm e de
etiquetas, link público de acompanhamento, importação e exportação em vários formatos.

### Pontos positivos
- Totais fixos no topo (pago, saldo, lucro): o técnico/vendedor vê a situação financeira da OS sem sair dela.
- Separar relato do cliente, laudo técnico e solução documenta o atendimento e protege a loja em disputa.
- Data de previsão + dashboard de prazos (vencidas/hoje/amanhã) deixa visível o que está atrasado.
- Indicador "há N dias" na listagem e no Kanban.
- Senha do aparelho com desenho de padrão, e opção de não imprimi-la no recibo.
- Assinatura do cliente e anexos (fotos) na OS.
- Monitoramento de garantias com dias restantes, cruzando OS e vendas.
- Envio por WhatsApp/e-mail e link de acompanhamento direto da listagem.

### Pontos negativos
- Formulário muito denso: 8 abas e cerca de 25 campos só na primeira, para uma troca de bateria simples. Para
  compensar, o próprio sistema precisou de "Cadastro rápido", "Edição rápida" e "Configurar campos".
- Anexos e assinatura só aparecem depois de salvar, o que obriga a um segundo passo no balcão.
- Listas configuráveis acumulam combinações (a lista de vendedores da conta tem dezenas de pares
  "Fulano | Ciclano"), sinal de que o modelo não cobre venda dividida entre duas pessoas.
- Modal em tela cheia por cima da listagem; o aviso de carregamento fica visível na troca de telas.
- Interface só em tema escuro, com texto pequeno e baixo contraste nas tabelas (observado nesta conta).

### Perguntas em aberto
- O que o "Link de acompanhamento" mostra ao cliente, e ele recebe atualização automática de situação?
- Mudar a situação dispara mensagem de WhatsApp automaticamente ou só pelo botão?
- Finalizar a OS baixa as peças do estoque e lança o pagamento no financeiro automaticamente?
- Como é o layout do recibo/termo impresso (A4 e 80mm)?
- O que "Parâmetros" e "Campos extras" permitem configurar?

### Impacto para Fluxoly

Comparado com a OS da Fluxoly em 2026-11-11 (código em `fluxoly_os.py`, `api_os.py`,
`frontend/src/pages/NewOrder.jsx`/`EditOrder.jsx`; schema em `docs/engineering/DATABASE.md`).

**A Fluxoly já tem:** cliente cadastrado (`cliente_id`), vários reparos por OS, peças do estoque com custo
(`os_pecas`), valor cobrado/com desconto, Kanban, checklist com link público, OS interna, tipos de
garantia, página de Garantias e PDF de entrada/entrega (BR-094 a BR-098).

**Não tem (encontrado no Mercado Phone):** prioridade; data de previsão e alerta de atraso; relato/laudo/
solução separados (hoje é um campo `observacoes`); observação interna; senha do aparelho; anexos/fotos;
assinatura do cliente; pagamento dentro da OS (parcial, várias formas, saldo); situações Orçamento e
Aprovado; tags; canal de venda; envio por WhatsApp/e-mail e link de acompanhamento; impressão térmica 80mm
e etiqueta; mais de um aparelho por OS; exportação da listagem; NFS-e.

#### Reaproveitar
TODO — depende de decisão do PO (ver abaixo); nada aqui foi aprovado.

#### Adaptar
TODO — depende de decisão do PO.

#### Não implementar
TODO — depende de decisão do PO.

#### Decisão pendente do PO
Candidatos por relação valor × esforço, na leitura deste benchmark (sugestão, não decisão):
1. **Data de previsão + destaque de OS atrasada** (listagem/Kanban/dashboard): impacto direto no balcão,
   esforço baixo (uma coluna nova + UI).
2. **Relato do cliente / Laudo técnico / Solução + Observação interna**: documenta o atendimento e alimenta
   o PDF de entrada/entrega já existente.
3. **Senha do aparelho (com opção de ocultar no documento)**: pedido comum na bancada. Por ser dado sensível,
   exige decisão de segurança (criptografia, quem vê).
4. **Situações Orçamento → Aprovado** antes de Em andamento: muda o fluxo de status (regra de negócio).
5. **Fotos/anexos e assinatura do cliente**: alto valor contra disputa; esforço maior (armazenamento de
   arquivos no servidor próprio).
6. **Pagamento na OS (parcial/saldo)**: depende do domínio Caixa/Financeiro, que já existe; precisa de
   discovery próprio (ADR-010).
7. **WhatsApp / link de acompanhamento**: pilar "Relacionamento" da marca; o link público reaproveitaria o
   padrão do checklist, mas KI-002 (token sem expiração) precisa ser resolvido antes.
8. **NFS-e**: fora do escopo atual; avaliar junto do módulo Fiscal.

---

## Financeiro, Fiscal

Ainda não percorridos — seções a adicionar quando cada módulo for analisado em sessão própria.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — especificação de negócio da Fluxoly (fonte de verdade, não este documento)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — consistência entre VENDAS.md e o código atual
- `docs/product/research/VENDAS_QUESTIONS.md` — perguntas em aberto para o discuss-phase do Épico Vendas
- `docs/product/research/VENDAS_DORES_REAIS.md` — dores reais observadas na operação, independente de concorrente
