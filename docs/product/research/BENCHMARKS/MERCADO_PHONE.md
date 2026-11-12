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
| Vendas | Concluída — PDV, histórico, upgrade, trocas/devoluções, orçamentos (somente leitura; nenhuma venda criada ou finalizada) | 2026-11-11 |
| OS | Concluída — estrutura de telas, campos e menus (somente leitura; nenhuma OS criada ou editada) | 2026-11-11 |
| Compras / Estoque | Concluída — estoque por unidade, cadastro, busca de IMEI, movimentações, procedência (somente leitura) | 2026-11-11 |
| Financeiro | Concluída — despesas, despesas fixas, caixas, contas, movimentações, conciliação, DRE (somente leitura) | 2026-11-11 |
| Tela inicial e Configurações | Concluída — avisos, widgets, parâmetros, gestão de acesso, senhas mestras, situações de OS, notificações (somente leitura) | 2026-11-11 |
| Clientes e Relatórios | Concluída — cadastro de pessoas, histórico de compras, catálogo de 39 relatórios, alertas, dashboard diário (somente leitura) | 2026-11-11 |
| Fiscal | Concluída — score fiscal, NF-e, NF de entrada do usado, captura de XML, NFs de vendas (somente leitura; nenhuma nota emitida) | 2026-11-11 |

---

## Critérios deste documento

Combinados em conversa (2026-07-22), valem para qualquer módulo analisado aqui:

1. **Fato antes de interpretação** — registrar exatamente o que o sistema faz antes de analisar o valor da decisão.
2. **Observação separada de recomendação** — cada achado tem um bloco "Observado" e um bloco "Análise"/"Impacto na Fluxoly" distintos, nunca misturados na mesma frase.
3. **Nenhuma decisão implícita** — qualquer conclusão que dependa de estratégia de produto vira "Decisão pendente do PO", nunca é assumida como aprovada.
4. **Contexto registrado** — versão observada, data da análise e quais fluxos foram percorridos, para permitir revisão quando o concorrente evoluir.

---

## Vendas

*Walkthrough de 2026-11-11, somente leitura: menu Vendas, listagem de vendas (PDV) e menu de ações,
formulário de nova venda (todas as seções, fechado sem salvar), Histórico de vendas (filtros), Simulador de
Upgrade (abas Negociação e Comissão), Trocas e devoluções, Orçamentos e Simulador de taxa de cartão. Não
percorrido: finalizar uma venda (lançaria no caixa e no estoque reais da loja), a tela de Detalhes de uma
venda, o recibo impresso, Delivery, Seguros e as Configurações de vendas. Nenhum dado de cliente registrado.
Listas como tipo de venda, canal, formas de pagamento e vendedores são configuráveis pela loja.*

### Objetivo observado
Vender no balcão ou à distância (WhatsApp/Instagram) aparelho + acessórios numa mesma venda, com várias
formas de pagamento, troca de aparelho usado como parte do pagamento ("upgrade") e rastreio da origem do
cliente para marketing.

### Fluxo observado
- **Menu Vendas:** Clientes · Venda - PDV · Orçamentos · Histórico de vendas · Trocas e devoluções ·
  Consulta estoque · Simulador de upgrade · Simulador de taxa de cartão · Delivery · Seguros · Monitoramento
  de garantias · Configurações.
- **Listagem (Venda - PDV):** "Nova venda", "PDV rápido", modelo de lista, exportar. Colunas: código,
  cliente, vendedor, data, tipo de venda, valor, status (filtro padrão: Concluído + Pré venda).
- **Ações por venda:** Editar, Detalhes, Recibo (A4 e 80mm), WhatsApp, Devolução/Troca, Cancelar a venda,
  Arquivos, Imprimir delivery, Assinar, Enviar por e-mail, Pagamento TEF. Menu "NFs" separado.
- **Nova venda (uma página, sem abas):**
  1. *Dados da venda* — Modelo de venda (Venda normal / com upgrade / com downgrade), Cliente* (busca +
     cadastrar/editar), Vendedor*, Tipo de venda* (na prática, a origem do cliente: Google, Meta, Indicação,
     Cliente recorrente, Loja, parceria…), Data, Tipo de entrega (Entrega, Retirada, Correios, Uber). "Mais
     detalhes": Canal de venda, Termo de garantia, Natureza da operação (fiscal), Caixa (do dia, já
     selecionado), Status (Venda / Pré venda), Indicado por (cliente), Observações, Observação interna,
     Enviar WhatsApp? e Enviar e-mail? (chaves). Botão "Ver logs".
  2. *Itens da venda* — Produto* (busca no estoque, + cadastrar), Quantidade*, Valor unitário interno*,
     **Valor exibir p/ cliente** (com botão de cartão, provavelmente para embutir taxa), Desconto (R$ ou %),
     Observações; tabela com coluna Seguro. Desconto total com aplicar em R$ / % / limpar.
  3. *Dados do pagamento* — Forma de pagamento (inclui **"APARELHO"**, ou seja, o usado entra como
     pagamento; PIX, débito, crédito por maquininha, dinheiro, crédito do cliente…), Valor, Parcelas (1..N,
     com calculadora), Caixa, Detalhes; vários pagamentos por venda; "Calcular troco"; "Usar crédito".
  4. Cabeçalho fixo: **Produtos · Pagamentos · Saldo**. Botão final "Finalizar venda".
- **Histórico de vendas:** uma linha por **item** (não por venda): código, cliente, data, tipo de venda,
  status, tipo de produto (iPhone, case, película, carregador…), aparelho, IMEI, estado (Seminovo/Novo),
  canal, valor, desconto, vendedor; linha expansível com data de entrada do aparelho no estoque, observação,
  **saúde da bateria** e login de quem vendeu. Filtros: período, cliente, vendedor, tipo de venda, IMEI,
  serial, faixa de valor, aparelho, tipo de produto, data de entrada, canal, status, login. Status:
  Concluído, Cancelada, Orçamento. Ações: WhatsApp recibo, WhatsApp personalizado, Detalhes.
- **Simulador de upgrade:** menu com Iniciar upgrade · Ver negociações · Configurações (comissões,
  relações, valores mínimos, recomendações) · "DataPhone — Quanto vale?" (valor estimado do aparelho) ·
  Calculadora antiga. A proposta tem cliente/lead (opcional), validade (padrão +30 dias), **dispositivo
  desejado** (modelo, armazenamento, estado, valor, desconto, valor final), **dispositivo de troca**
  (modelo, armazenamento → valor mínimo e máximo calculados pela "relação cadastrada", outros descontos,
  valor avaliado/negociado), formas de pagamento e um resumo: Final desejado · Valor mínimo · Valor máximo ·
  Descontos · Spread · Avaliado · Saldo a pagar. Botões "Salvar negociação" e "Gerar venda". Aba Comissão:
  produto vendido, venda relacionada, comissão da venda e **comissão do upgrade**.
- **Trocas e devoluções:** indicadores do período (nº de trocas, créditos gerados, pagamentos adicionais,
  disponibilidade alterada) e lista com venda de origem, usuário, tipo (Troca/Devolução), itens devolvidos
  (ex.: 2/0), valor anterior × posterior, diferença, resultado (Neutro, Pagamento adicional, Crédito não
  gerado), disponibilidade do item devolvido (ex.: "Disponível para venda") e se veio danificado.
- **Orçamentos:** lista simples (cliente, vendedor, data, previsão de entrega, valor, venda gerada). Na
  conta observada há só 4 orçamentos, quase todos de 2024: a loja praticamente não usa.
- **Simulador de taxa de cartão:** valor + forma de pagamento → calcula o valor com taxa.

### Campos existentes
Ver "Fluxo observado" acima (formulário em seções na mesma página). Obrigatórios: cliente, vendedor, tipo
de venda, produto, quantidade, valor unitário interno.

### Regras percebidas
- Uma venda tem N itens (aparelho + acessórios) e N pagamentos; o saldo precisa zerar para finalizar
  (inferido pelo cabeçalho Produtos/Pagamentos/Saldo, não testado).
- Dois preços por item: **valor interno** (o que a loja registra) e **valor exibido ao cliente** (o que
  aparece no recibo, por exemplo com a taxa do cartão embutida).
- O aparelho usado do cliente é uma forma de pagamento; o upgrade calcula o valor dele por uma tabela de
  relação modelo × armazenamento (mínimo/máximo), com comissão separada para o vendedor.
- Venda dividida entre dois vendedores é cadastrada como um "vendedor" combinado ("A | B").
- O pagamento é lançado no caixa do dia escolhido na própria venda.
- Pré venda é um status da venda, não um documento separado.
- Na troca/devolução, o sistema decide se gera crédito ao cliente, cobra diferença ou fica neutro, e se o
  item volta disponível para venda.

### Integrações
TEF/maquininhas, NF-e/NFC-e (menu NFs), WhatsApp (recibo e mensagem personalizada), e-mail, assinatura
digital, impressão A4/80mm/delivery, "DataPhone" (precificação de usados), Seguros.

### Pontos positivos
- Venda multi-item + multi-pagamento na mesma tela, com saldo sempre visível.
- Upgrade estruturado: tabela de valor de usado + spread + comissão própria. É o processo central de uma
  loja de iPhone e eles tratam como produto, não como gambiarra.
- "Tipo de venda" como origem de marketing (Google/Meta/Indicação/Indicado por) permite medir o retorno do
  tráfego pago.
- Histórico por item com IMEI, estado e saúde da bateria: auditoria de qual aparelho saiu, para quem.
- Troca/devolução com resultado financeiro explícito e decisão sobre o estoque do item devolvido.
- Envio do recibo por WhatsApp direto da lista.

### Pontos negativos
- Nomes que confundem: "Tipo de venda" é a origem do cliente, "Canal de venda" é outro campo, e o
  "Modelo de venda" muda o fluxo. Três conceitos parecidos na mesma tela.
- O vendedor combinado ("A | B") gera dezenas de cadastros artificiais e impede a comissão por pessoa.
- O formulário mistura campos fiscais (natureza da operação) com o fluxo de balcão.
- Na troca de "Modelo de venda" para "com upgrade", nada visível mudou no formulário vazio; não ficou
  claro o efeito sem adicionar itens.
- Orçamentos existem mas não são usados (4 em ~2 anos): sinal de que o fluxo real de proposta passou para
  o Simulador de upgrade e para o WhatsApp.

### Perguntas em aberto
- O que "Venda com upgrade/downgrade" muda de fato (exige o aparelho de troca? gera entrada no estoque?).
- O aparelho recebido como pagamento ("APARELHO") entra automaticamente no estoque como seminovo?
- Como a "relação cadastrada" do upgrade é mantida (manual por modelo? vem do DataPhone?).
- O que "Valor exibir p/ cliente" faz no recibo e no financeiro (qual valor vira receita?).
- Finalizar a venda baixa o estoque e lança no caixa na hora? Cancelar estorna os dois?

### Impacto para Fluxoly

Comparado com a Vendas da Fluxoly em 2026-11-11 (`fluxoly_vendas_service.py`, `frontend/src/pages/Vendas.jsx`,
`docs/product/features/VENDAS.md`, tabelas `vendas`/`vendas_itens` em `DATABASE.md`).

**A Fluxoly já tem:** venda vinculada a cliente cadastrado e à unidade serializada (IMEI), vendedor = usuário
logado, cancelamento com motivo (V1.2), ajuste de valor/desconto por item com histórico, comissão por item,
garantia por item (Tipos de Garantia), custo/lucro por aparelho comprado (BR-092/093) e caixa
(`movimentacoes_caixa`).

**Já existe em parte:** o aparelho de troca pode ser registrado como Compra de aparelho com origem `troca`,
cliente, venda vinculada e forma de pagamento `abatido_na_venda` (BR-083 a BR-089). Mas a venda em si não
"enxerga" o abatimento: o valor e o pagamento da venda continuam separados da compra.

**Não tem (encontrado no Mercado Phone):** mais de um item por venda (acessórios); mais de uma forma de
pagamento por venda (hoje uma de 4: pix/cartão/dinheiro/transferência) e parcelas; aparelho usado como
forma de pagamento dentro da própria venda; simulador de upgrade com tabela de valor de usado; troca/devolução com crédito ao
cliente; origem do cliente (tipo de venda / indicado por); tipo de entrega; pré-venda; recibo por
WhatsApp/e-mail e impressão 80mm; valor exibido ao cliente separado do valor interno; nota fiscal.

#### Reaproveitar
TODO — depende de decisão do PO (ver abaixo); nada aqui foi aprovado.

#### Adaptar
TODO — depende de decisão do PO.

#### Não implementar
TODO — depende de decisão do PO.

#### Decisão pendente do PO
Candidatos por relação valor × esforço, na leitura deste benchmark (sugestão, não decisão):
1. **Venda com aparelho na troca (upgrade)**: o usado do cliente abate do valor e entra no estoque como
   unidade serializada. É o fluxo mais característico de loja de iPhone e a Fluxoly já tem metade da
   estrutura (Compra de aparelhos com origem `troca` e pagamento `abatido_na_venda`, BR-083+); falta
   juntar compra e venda numa operação só. Precisa de discovery (ADR-010).
2. **Vários pagamentos por venda (com parcelas)**: pré-requisito para upgrade e para "PIX + cartão", comum
   no balcão. Mexe em `vendas`/caixa (mudança de schema).
3. **Acessórios na mesma venda (multi-item)**: `vendas_itens` já foi modelada para isso; falta o item não
   serializado (produto com quantidade).
4. **Origem do cliente** (Google/Meta/Indicação + "indicado por"): esforço baixo e responde "o tráfego pago
   está dando retorno?".
5. **Recibo por WhatsApp e impressão 80mm**: reaproveitaria o gerador de PDF da OS (BR-094+).
6. **Troca/devolução com crédito do cliente**: depende de 2 e do conceito de crédito, que não existe.
7. **Venda com dois vendedores**: evitar o modelo "A | B" deles; se for necessário, modelar como divisão
   de comissão entre usuários.
8. **NF-e/NFC-e, TEF, Seguros, Delivery**: fora do escopo atual.

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

## Compras / Estoque

*Walkthrough de 2026-11-11, somente leitura: Estoque atual (filtros, menus Estoque geral / Cadastrar /
Ferramentas, ações por unidade, disponibilidade), formulário de cadastro de aparelho (todas as abas,
fechado sem salvar), Ordem de compra, Busca consolidada de IMEI, Movimentações de estoque, Inventário,
Produtos vendidos e Certificado de procedência. Não percorrido: Etiquetas, Configurações de estoque,
transferência entre unidades, gerar um certificado e criar inventário. Nenhum dado de cliente registrado.*

### Objetivo observado
Controlar o estoque **por unidade** (cada aparelho com IMEI, custo e situação próprios) junto com
acessórios e peças por quantidade, sabendo há quanto tempo cada aparelho está parado e de onde veio.

### Fluxo observado
- **Menu:** Estoque atual · Ordem de compra · Histórico de IMEI · Movimentações de estoque · Inventário ·
  Produtos vendidos/sem estoque · Etiquetas · Certificado de procedência / Teste IMEI · Configurações.
- **Estoque atual:** uma linha por unidade, colorida pela disponibilidade. Colunas: código, descrição
  completa (gerada: modelo - GB - cor - IMEI - serial - estado), IMEI, valor de venda, valor de custo,
  quantidade, data de entrada, **dias em estoque**, disponibilidade (alterável na própria linha), modelo,
  GB, marca, categoria, subcategoria, fornecedor. Filtros rápidos: "apenas estoque atual", "apenas com NF-e
  de entrada", "IMEI duplicados", tipo (aparelho/acessório/peça/bike). Visões: estoque de aparelhos,
  acessórios, peças, bikes/patinetes.
- **Disponibilidade** (configurável; na conta): Disponível para venda, Disponível com detalhe, Análise,
  Laboratório.
- **Ações por unidade:** Editar; Assinar termo de compra; Termo de compra; Excluir; Duplicar lançamento;
  Gerar etiqueta; **Transferir para outra unidade (loja)**; Gerar código de barras; Emitir NF-e de entrada;
  Informar status da NF-e de entrada; **Vender** (atalho para o PDV).
- **Ferramentas:** estoque multiempresa, editar em massa, alterar em lote, histórico de transferências,
  gerar inventário, importar produtos em massa, registros deletados, histórico de alterações em massa,
  exportar CSV/XLS/PDF/XML.
- **Cadastro (Aparelho / Acessório / Peça / Serviço / Bike):** modal com 10 abas — Dados gerais, Despesas,
  Forma de pagamento, Custos extras, Catálogo, Anexos, Movimentação de estoque, Checklist, Histórico de
  alterações, Outras informações.
- **Ordem de compra:** existe (lista com situação, fornecedor, valor), mas a conta tem **zero** registros:
  a loja cadastra a entrada direto no estoque.
- **Histórico de IMEI:** "Busca consolidada" — digita IMEI/IMEI 2/serial e vê todas as referências do
  aparelho no sistema (compra, estoque, consultas, OS e vendas).
- **Movimentações de estoque:** log de toda entrada/saída com produto, fornecedor, usuário, data, tipo
  (Saída…), origem (Venda…) e ID de origem, quantidade, **saldo após o movimento**, custo e venda unitários
  e totais, observação ("Adicionado produto à venda"). Ações: lançar movimento, alterar em lote, gerar
  inventário.
- **Inventário:** contagem de estoque com lista de inventários. A conta não tem nenhum.
- **Produtos vendidos:** unidades que saíram, com ID da venda, IMEI, serial, modelo, GB, cor.
- **Certificado de procedência / Teste IMEI:** digita o IMEI e o sistema consulta o aparelho Apple (devolve
  modelo, região/variante, capacidade, cor e IMEI 2) e gera um certificado. Usado várias vezes por dia na
  conta: é conferência de aparelho na compra/troca e documento para o cliente.

### Campos existentes
**Dados gerais (aparelho):** Tipo*, IMEI*, IMEI 2*, Modelo*, Serial, Cor*, Categoria*, **Saúde da bateria***,
Estado do aparelho* (Novo, Seminovo, Open box, Acessório…), SKU, Código de barras, Disponibilidade*, GB*,
Memória RAM, Marca, Subcategoria, Ciclo de bateria, Quantidade, Quantidade mínima, Valor de custo*, Valor
de venda*, Mark-up %, Margem %, Lucro R$, Data de entrada*, Dias de garantia, Observação, Tags. **Dados do
fornecedor:** Tipo de fornecedor (Fornecedor **ou Cliente** — aparelho comprado de pessoa física),
Fornecedor*. **Dados para NF:** CEST, NCM, origem, CST/CSOSN, CFOPs, código de benefício fiscal,
tributação.

**Outras abas:** Despesas (só depois de salvar); Forma de pagamento da compra (várias, com parcelas);
**Custos extras** (descrição, valor, "gerar despesa" no financeiro, "desconsiderar no relatório" — somam
ao custo do produto, ex.: frete, reparo); Catálogo (exibir no catálogo web, nome de exibição, valor a
prazo, nº de parcelas); Checklist (modelo); Outras informações (usuário, data de modificação, código da
ordem de compra, log).

### Regras percebidas
- IMEI 2 obrigatório para aparelho; há filtro dedicado a IMEI duplicado (a duplicidade não é bloqueada
  na entrada, é auditada depois).
- Custo do aparelho = custo de compra + custos extras, com opção de lançar cada custo como despesa.
- Mark-up, margem e lucro calculados no cadastro.
- Aparelho comprado de cliente usa o próprio cliente como "fornecedor".
- Toda saída por venda gera movimentação com saldo após o movimento.
- Estoque separado por loja (multiempresa), com transferência entre unidades.

### Integrações
Consulta de IMEI/procedência Apple, NF-e de entrada, catálogo web, impressão de etiqueta e código de barras,
importação em massa.

### Pontos positivos
- **Dias em estoque** por unidade: mostra o aparelho parado (capital imobilizado) sem relatório.
- **Busca consolidada de IMEI**: uma tela responde "o que aconteceu com este aparelho?".
- **Certificado de procedência**: confere o aparelho na compra e vira argumento de venda.
- **Custos extras** que sobem o custo do aparelho: lucro real por unidade.
- Disponibilidade operacional (análise, laboratório, com detalhe) separada de vendido/não vendido.
- Movimentação com saldo após o movimento e origem rastreável.

### Pontos negativos
- Cadastro com 10 abas e cerca de 30 campos para dar entrada em um aparelho; vários campos fiscais no
  mesmo formulário.
- IMEI duplicado é detectado por filtro, não impedido na entrada.
- Ordem de compra e inventário existem mas não são usados nesta conta: funcionalidades que o lojista não
  adotou.
- A lista de "Estado do aparelho" mistura estado (Novo/Seminovo) com tipo (Acessório, Serviços) e tem
  valores repetidos ("NOVO" duas vezes), sinal de lista livre sem governança.

### Perguntas em aberto
- De onde vem o dado do certificado de procedência (fonte da consulta) e qual o custo por consulta?
- "Transferir para outra unidade" move o custo e o histórico junto?
- A disponibilidade "Laboratório" se liga a uma OS interna automaticamente?

### Impacto para Fluxoly

Comparado com o estoque da Fluxoly em 2026-11-11 (`unidades_serializadas`, `produtos`, `estoque`,
`estoque_lotes`, `movimentacoes`, `compras_aparelhos` em `DATABASE.md`; `UnidadesSerializadas.jsx`).

**A Fluxoly já tem:** unidade serializada por IMEI com status (disponível, em reparo, vendido,
devolvido); IMEI único no banco (mais rígido que o Mercado Phone); saúde da bateria na unidade; catálogo
de produtos com custo, venda e margem calculada; peças por lote com custo FIFO; **compra de aparelho**
com origem (marketplace/troca/outro), cliente vendedor, forma de pagamento (inclusive "abatido na venda")
e saída de caixa (BR-083 a BR-089); OS interna para consertar aparelho comprado e lucro por aparelho
(BR-090 a BR-093).

**Não tem (encontrado no Mercado Phone):** dias em estoque; busca consolidada por IMEI (compra + estoque
+ OS + venda em uma tela); certificado/consulta de procedência; custos extras somados ao custo da unidade
(hoje só o custo da OS interna); disponibilidade operacional configurável (análise, com detalhe…);
movimentação com saldo e origem para unidades e produtos (hoje `movimentacoes` cobre só `estoque` de
peças); etiqueta e código de barras; IMEI 2; inventário; transferência entre lojas; importação em massa.

#### Reaproveitar
TODO — depende de decisão do PO (ver abaixo); nada aqui foi aprovado.

#### Adaptar
TODO — depende de decisão do PO.

#### Não implementar
TODO — depende de decisão do PO.

#### Decisão pendente do PO
Candidatos por relação valor × esforço, na leitura deste benchmark (sugestão, não decisão):
1. **Dias em estoque** na lista de unidades (com destaque acima de N dias): esforço baixo, todos os dados já
   existem (`criado_em` da unidade ou data da compra).
2. **Busca consolidada por IMEI**: uma tela juntando compra, unidade, OS e venda. Os vínculos já existem
   (`compras_aparelhos`, `os.imei`/`unidade_serializada_id`, `vendas_itens`); é só leitura, sem mudança de
   schema.
3. **Custos extras na unidade** (frete, peça, película aplicada…), somando ao custo e ao lucro por aparelho
   (BR-092): completa o "lucro real por aparelho" que a Fluxoly já começou.
4. **Etiqueta com código de barras/IMEI**: reaproveita o gerador de PDF no navegador.
5. **IMEI 2**: coluna nova e opcional em `unidades_serializadas`.
6. **Certificado de procedência**: depende de um serviço externo de consulta de IMEI (custo, contrato, LGPD).
   Precisa de decisão de negócio antes de qualquer discovery.
7. **Inventário, transferência entre lojas, ordem de compra**: a conta observada não usa os dois primeiros
   nem ordem de compra; multiloja depende da decisão de multiempresa (ADR-005). Baixa prioridade.

---

## Financeiro

*Walkthrough de 2026-11-11, somente leitura: Despesas (lista, filtros, ações, formulário de nova despesa
fechado sem salvar), Despesas fixas, Caixas (lista e menu de ações), Saldo bancário (contas), Movimentações
financeiras, Conciliação bancária, Calendário e Configurações (Formas de pagamento, Configuração do DRE,
fechada sem salvar). Receitas não aberta (o menu indica que espelha Despesas). Nenhum valor financeiro da
loja nem dado de pessoa foi registrado aqui.*

### Objetivo observado
Fazer a gestão financeira completa da loja (contas a pagar e receber, caixas diários, contas bancárias,
conciliação e DRE) alimentada automaticamente por vendas, OS e compras de estoque.

### Fluxo observado
- **Menu:** Despesas · Receitas · Caixas · Saldo bancário · Movimentações financeiras · Conciliação
  bancária · Calendário · Configurações (Parâmetros, Fornecedores, Categorias, Plano de contas, Tags,
  Formas de pagamento, Bancos, Configuração DRE, Modelos de WhatsApp).
- **Despesas:** cartões no topo (vencem hoje, vencidos, a vencer, pagos, total no período), filtro rápido
  (vencidos, vencem hoje, a vencer, pagos, total do período, pendente do mês atual), período de vencimento
  com setas mês a mês, ações em lote. Colunas: id, origem (Manual, Venda…, filtrável por código da venda),
  categoria, título, situação, pessoa, valor total, vencimento, valor pago, valor a pagar. Ações: editar,
  WhatsApp, duplicar lançamento, recibo, imprimir A4/80mm, excluir.
- **Nova despesa:** cabeçalho Valor total · Total do pagamento · Saldo; abas Dados gerais, Arquivos,
  Detalhes. Campos: título*, tipo (despesa), pessoa (+ cadastrar), vencimento*, competência*, situação*
  (Em aberto…), categoria (plano de contas hierárquico: 2. Despesas → 2.1 Compra de produtos, 2.2 Outras
  despesas, Despesas fixas), forma de cobrança, nº da parcela, tags, observações; valor*, multa/juros,
  desconto, valor total; pagamentos (forma*, valor*, parcelas, data*, caixa), vários por lançamento.
  Detalhes: considerar em relatórios? (sim/não), nº da venda, usuário criador.
- **Despesas fixas:** recorrência (mensal…) com próximo vencimento a gerar e quantos lançamentos futuros
  já existem; cartões de valor mensal, total de contas fixas e recorrências expirando.
- **Caixas:** um caixa por dia/operador ("Caixa do dia DD/MM HH:MM - Nome"), com abertura, fechamento,
  sangrias, suprimentos, troco, saldo final dos movimentos × **saldo final informado** (conferência) e
  status. Ações: fechar caixa, detalhes, editar abertura, nova sangria/suprimento, excluir. Botão de
  transferência bancária.
- **Saldo bancário (contas):** cada conta (bancos, maquininhas, "Dinheiro", "Fornecedor") com data inicial,
  saldo final, **saldo pela integração** e status da integração bancária (conectado / não conectado).
- **Movimentações financeiras:** extrato único de entradas e saídas, com origem (Vendas, Contas a pagar,
  Estoque…), forma de pagamento, banco e observação gerada ("Venda #N para: …", "Compra de produtos…");
  cartões total entrada / saída / saldo.
- **Conciliação bancária:** importação de extrato (OFX ou integração) por conta, com progresso de itens
  conciliados e status (não conciliado / parcial).
- **Calendário:** visão dia/semana/mês/agenda de contas a pagar/receber, crediários e pagamentos de OS.
- **Formas de pagamento:** cada forma ligada a uma conta bancária, com "dias para cair" (prazo de
  recebimento), ativo e "mostrar no PDV". Na conta há formas por maquininha e bandeira, crediário e
  cashback.
- **Configuração do DRE:** mapeia venda, OS, CMV de venda, CMV de OS, taxa de cartão e perdas de estoque
  para contas do plano de contas.

### Campos existentes
Ver "Fluxo observado" (formulário de despesa). Receita tem a mesma estrutura, com tipo Receita.

### Regras percebidas
- Venda, OS e entrada de estoque geram lançamentos financeiros automaticamente, com origem rastreável.
- Cada forma de pagamento cai numa conta bancária com prazo próprio: o saldo por conta e o calendário de
  recebimentos saem disso.
- Lançamento tem vencimento e competência separados (regime de caixa × competência no DRE).
- Caixa é por sessão (abrir/fechar), mas fechar não é obrigatório: na conta observada a maioria dos caixas
  recentes segue "Aberto" e o saldo informado no fechamento fica zerado.
- Lançamento pode ficar fora dos relatórios ("considerar em relatórios? não").

### Integrações
Open finance/integração bancária (saldo e extrato), importação OFX, maquininhas (TEF/POS), WhatsApp
(cobrança/recibo), impressão de recibo.

### Pontos positivos
- Uma visão de "o que vence hoje / está vencido / a vencer" logo no topo, com filtro rápido.
- Formas de pagamento ligadas à conta e ao prazo: responde "quanto vai cair amanhã e em qual banco".
- Movimentações com origem e texto gerado ("Venda #N…"): auditoria sem abrir cada documento.
- Despesas fixas com recorrência automática.
- Plano de contas + configuração do DRE: lucro por competência sem planilha.
- Conciliação com o extrato real do banco.

### Pontos negativos
- Muitos conceitos para um lojista (competência, plano de contas, natureza, DRE, conciliação), com pouca
  orientação na tela.
- Caixa diário existe mas não é fechado na prática (conferência perdida); o sistema não força nem alerta.
- Conciliação pouco usada na conta (3 importações, nenhuma completa).
- "Fornecedor" e "Dinheiro" cadastrados como bancos para caber no modelo.

### Perguntas em aberto
- A taxa da maquininha é descontada automaticamente do valor recebido (líquido × bruto)?
- Cancelar uma venda estorna o lançamento financeiro?
- O que acontece com um caixa que nunca é fechado (os lançamentos seguem válidos? entra no relatório?).

### Impacto para Fluxoly

Comparado com o Financeiro Mínimo da Fluxoly em 2026-11-11 (`movimentacoes_caixa`, `contas_pagar`,
`contas_receber` em `DATABASE.md`, BR-067 a BR-069; `Financeiro.jsx`).

**A Fluxoly já tem:** caixa único com entradas e saídas, estorno que preserva auditoria, origem rastreável
(manual, venda, conta a pagar, conta a receber, compra de aparelho) e garantia no banco contra lançamento
duplicado de venda/compra; contas a pagar e a receber com vencimento, categoria (texto) e baixa que lança
no caixa na mesma transação.

**Não tem (encontrado no Mercado Phone):** caixa por sessão (abrir/fechar com conferência, sangria,
suprimento); contas bancárias e saldo por conta; formas de pagamento cadastradas com prazo de recebimento
e taxa; recebimento de OS no financeiro (origem `os` não existe em `movimentacoes_caixa`); pagamento
parcial e parcelas; despesas recorrentes; indicadores vencidos/hoje/a vencer; calendário; plano de contas e
DRE; competência separada do vencimento; anexos no lançamento; conciliação bancária e integração com banco.

#### Reaproveitar
TODO — depende de decisão do PO (ver abaixo); nada aqui foi aprovado.

#### Adaptar
TODO — depende de decisão do PO.

#### Não implementar
TODO — depende de decisão do PO.

#### Decisão pendente do PO
Candidatos por relação valor × esforço, na leitura deste benchmark (sugestão, não decisão):
1. **Recebimento de OS no caixa** (origem `os`): hoje o dinheiro da assistência não aparece no financeiro;
   liga com "pagamento na OS" da seção OS.
2. **Indicadores vencidos / vencem hoje / a vencer** nas contas a pagar e receber: esforço baixo, dados já
   existem.
3. **Despesas recorrentes** (aluguel, sistema, salários): gera os lançamentos do mês automaticamente.
4. **Formas de pagamento cadastradas** (com taxa e prazo de recebimento): pré-requisito para vários
   pagamentos na venda, para lucro líquido de taxa de cartão e para previsão de recebimentos.
5. **Caixa por sessão com fechamento conferido**: só vale se a loja for de fato fechar o caixa; na conta
   observada ela não fecha. Decisão do PO sobre o processo, antes do sistema.
6. **Contas bancárias e saldo por conta**: depende do item 4.
7. **Plano de contas, DRE, competência, conciliação e integração bancária**: alto esforço; o próprio uso
   na conta observada é baixo. Fora do escopo agora.

---

## Fiscal

*Walkthrough de 2026-11-11, somente leitura: Score fiscal, NF-e (lista), NF de entrada (upgrade),
Capturador de XML de entrada, Histórico de NFs de vendas, TEF e Relatório de NF. Não abertos: "Atualizar
empresa - Fiscal" e Configurações fiscais (alteram cadastro fiscal da loja), nem o formulário de emissão.
Nenhuma nota foi emitida e nenhum dado de destinatário foi registrado.*

### Objetivo observado
Emitir as notas que uma loja de celular precisa (NFC-e no balcão, NF-e de saída, NF-e de entrada do usado
comprado de pessoa física, NFS-e da assistência) a partir das vendas, OS e entradas de estoque, sem outro
sistema.

### Fluxo observado
- **Menu:** Atualizar empresa - Fiscal · Score fiscal · NF-e · NF de entrada (upgrade) · Capturador - XML
  entrada · Histórico NFs - Vendas · TEF · Relatório de NF · Configurações.
- **Score fiscal:** nota percentual da configuração fiscal da loja (regime tributário avaliado), com atalhos
  (certificado digital, dados fiscais, séries de NF-e, editar produtos em massa, alíquota por estado,
  natureza da operação, tributações, tipos de produto) e checklist em duas partes: **Empresa** (certificado
  digital e validade, regime, CNPJ/IE/endereço, série) e **Produtos** (quantos produtos estão sem NCM, sem
  CFOP, sem CST/CSOSN, sem origem da mercadoria), mais uma lista de pendências.
- **NF-e:** lista de notas avulsas (código, número, tipo de operação, cliente, data, valor, status) com
  "Lançar NF-e". Pouco usada na conta.
- **NF de entrada (upgrade):** nota de entrada emitida pela própria loja para o aparelho comprado de
  pessoa física na troca. Lista com cliente/fornecedor, data, produto (modelo, bateria, IMEI), **se o
  aparelho já foi vendido**, valor e status na SEFAZ ("Autorizado o uso da NF-e"); totais de quantidade e
  valor. Usada com frequência na conta.
- **Capturador - XML entrada:** importar XML ou buscar pela chave as notas emitidas contra o CNPJ da loja
  (fornecedores), com status de estoque, método de captura e manifestação do destinatário.
- **Histórico NFs - Vendas:** vendas com nota (NFC-e/NF-e), com produtos e NCM, tipos de produto, valor da
  nota × valor da venda, número, série, formas de pagamento, CFOP.
- **TEF:** histórico de transações de cartão integradas (vazio na conta).
- **Relatório de NF:** totais de notas de entrada e saída por período.
- Emissão também a partir dos documentos: menu "NF" na OS (NFS-e e NF-e dos produtos), "NFs" na venda e
  "Emitir NF-e de entrada" na unidade de estoque.

### Campos existentes
No produto (ver Compras/Estoque): CEST, NCM, origem, CST/CSOSN, CFOP estadual/interestadual de entrada e
saída, código de benefício fiscal, tributação. Na venda/OS: natureza da operação.

### Regras percebidas
- A nota nasce do documento de negócio (venda, OS, entrada), não é digitada do zero.
- O aparelho comprado de pessoa física recebe NF-e de entrada da própria loja (sem nota do vendedor), e o
  sistema acompanha se ele já foi revendido.
- Valor da nota pode ser diferente do valor da venda (as duas colunas aparecem lado a lado).
- A qualidade do cadastro fiscal dos produtos é medida e cobrada (score).

### Integrações
SEFAZ (NF-e, NFC-e), prefeitura (NFS-e), Receita (consulta de notas emitidas contra o CNPJ / manifestação),
certificado digital A1, TEF.

### Pontos positivos
- **Score fiscal** transforma uma configuração difícil num checklist com porcentagem e pendências.
- **NF de entrada do usado** resolve um problema real e específico de loja de seminovos.
- Captura automática das notas de fornecedores pela chave/CNPJ.
- Emissão a partir da venda/OS: o lojista não redigita.

### Pontos negativos
- Exige cadastro fiscal completo de cada produto (NCM, CFOP, CST…); na conta, centenas de produtos ainda
  estão sem esses campos.
- O sistema permite valor da nota diferente do valor da venda sem nenhum alerta ou justificativa
  registrada; para a Fluxoly, qualquer divergência deveria ser explícita e auditável.
- Vários caminhos para emitir a mesma coisa (menu Fiscal, venda, OS, estoque).

### Perguntas em aberto
- Qual provedor de emissão eles usam (próprio ou intermediário) e o custo por nota?
- NFC-e é emitida automaticamente ao finalizar a venda ou só sob demanda?
- A NF de entrada do usado é exigência legal no estado da loja ou prática de proteção (procedência)?

### Impacto para Fluxoly

**A Fluxoly hoje:** não emite nenhuma nota. `RELEASE_STRATEGY.md` coloca Nota Fiscal na **Fase 3 —
Automação**, à frente de Multiempresa (decisão de 2026-08-05). Nenhuma discovery fiscal foi feita.

**Não tem (encontrado no Mercado Phone):** tudo do módulo: NFC-e/NF-e de saída, NF-e de entrada do usado,
NFS-e da OS, captura de XML de fornecedor, cadastro fiscal do produto, score fiscal, TEF.

#### Reaproveitar
TODO — depende de decisão do PO (ver abaixo); nada aqui foi aprovado.

#### Adaptar
TODO — depende de decisão do PO.

#### Não implementar
TODO — depende de decisão do PO.

#### Decisão pendente do PO
Fiscal é um domínio de alto risco (legal, certificado digital, SEFAZ/prefeitura por município); nenhuma
destas sugestões dispensa discovery própria (ADR-010) e decisão sobre provedor de emissão:
1. **Decidir primeiro se a Fluxoly emite nota ou integra com um emissor externo** (API de terceiro).
   Emitir direto exige certificado, homologação por estado e manutenção legal contínua.
2. Se emitir: **começar pela NFC-e da venda** (balcão), que cobre o caso mais frequente.
3. **NF-e de entrada do usado** como segundo passo: casa com a Compra de aparelhos que já existe
   (BR-083+) e é diferencial específico de loja de seminovos.
4. **NFS-e da OS**: depende do município da loja; avaliar por cliente.
5. **Score fiscal / checklist de configuração**: só depois de existir emissão; boa ideia de UX para
   onboarding.
6. **Captura de XML de fornecedor, TEF**: fora do escopo da primeira versão fiscal. — seções a adicionar quando cada módulo for analisado em sessão própria.

---

## Clientes

*Walkthrough de 2026-11-11, somente leitura: listagem de pessoas, ações por cliente, menu Ferramentas,
formulário de cadastro (fechado sem salvar) e "Ver histórico de compras" de um cliente (só a estrutura).
Nenhum dado de cliente registrado aqui.*

### Fluxo observado
- **Pessoas:** um cadastro só para Cliente, Fornecedor, Técnico e Motoboy (abas de categoria). Cartões no
  topo: total de pessoas, total de clientes e **índice de recompra (%)**. Colunas: código, nome, CPF/CNPJ,
  telefone, e-mail, **último produto comprado**, aniversário, mês de aniversário (filtrável), Instagram.
- **Ações por cliente:** Editar, Detalhes, WhatsApp, **Ver histórico de compras**, Transferir para outra
  unidade, Excluir.
- **Ferramentas:** gerar link para o cliente (cadastro preenchido pelo próprio cliente), lançar crédito,
  editar em massa, importar clientes/fornecedores, registros deletados, exportar XLS/PDF/XML.
- **Cadastro (seções):** Identificação (categoria, tipo PF/PJ, CPF/CNPJ com busca automática, origem*
  — mesma lista do "tipo de venda": Google, Meta, Indicação…, nome*, profissão, nascimento, gênero),
  Dados fiscais, Contato (telefone, alternativo, e-mail, Instagram, telefones extras), Endereço (CEP com
  busca), Observações e tags, **Crédito e "IA Blue"** (se o assistente de mensagens pode enviar para o
  cliente, valor de crédito, limite de crediário), Arquivos.
- **Histórico de compras:** abre o Relatório histórico de vendas filtrado pelo cliente, com cartões de
  faturamento, quantidade de vendas e de produtos, lucro médio %, ticket médio, margem média, lucro total,
  custo total e desconto total, e a lista de itens com IMEI e formas de pagamento.

### Pontos positivos
- Ficha do cliente com o que importa para recompra: último produto, aniversário, Instagram, histórico com
  lucro.
- Índice de recompra como indicador de topo.
- Link para o cliente preencher o próprio cadastro.

### Pontos negativos
- Origem do cliente quase nunca é preenchida no cadastro (no relatório Perfil de clientes, ~96% "não
  informado"), embora a origem seja registrada em cada venda. Duplicação de conceito que a loja não mantém.
- Cliente, fornecedor, técnico e motoboy no mesmo cadastro mistura papéis.

## Relatórios

*Walkthrough de 2026-11-11, somente leitura: catálogo "Visão geral - Atalhos", Dashboard de alertas
(estoque e vendas), Perfil de clientes, Dashboard diário e o relatório de histórico de vendas (via
cliente). Nenhum valor da loja registrado aqui.*

### Fluxo observado
- **Catálogo com 39 relatórios**, busca e favoritos, agrupados: Vendas (8: dashboard diário, dashboard
  geral mensal, canal de venda, estado do aparelho, **funil de venda**, tipo de entrega, histórico,
  consolidado), Vendedores (4: comissão, vendas por vendedor, por forma de pagamento), Estoque (7: por
  modelo/GB, por aparelho, itens vendidos, resumo por tipo com custo e venda), Financeiro (8: DRE mensal,
  DRE gerencial, DRE multilojas, **conta bancária × vendas** para conferir se as taxas batem, sangrias e
  suprimentos, por forma de pagamento, **taxa de cartão por venda**), Clientes (4: programa de indicação,
  perfil, **ranking**, **aniversariantes do dia**), OS (1: detalhado por serviço e peça), Integrações
  (Meta Ads × vendas), Técnicos (comissão), Outros (acessos ao catálogo online, alertas, metas, uso de
  recursos, retrospectiva anual).
- **Dashboard diário:** período, faturamento, quantidade de vendas, lucro, ticket médio, % de lucro, lucro
  médio e últimas vendas com **valor líquido (sem taxa) × valor total × lucro** por venda.
- **Dashboard de alertas:** o sistema aponta problemas de dados por módulo, com contagem.
  Estoque: produto 50% abaixo da média de preço, custo = 0, **valor de venda ≤ custo**, produto sem foto,
  estoque negativo. Vendas: **venda com prejuízo**, valor recebido < valor da venda, venda cancelada,
  venda sem termo de garantia. Fiscal; OS e Financeiro "em desenvolvimento". Alertas podem ser ignorados.
- **Perfil de clientes:** gráficos de PF × PJ, faixa etária, gênero e origem.

### Pontos positivos
- **Alertas de dados** (venda com prejuízo, custo zerado, preço abaixo do custo): o sistema avisa antes
  do erro virar prejuízo, sem o lojista montar relatório.
- Lucro **líquido de taxa de cartão** por venda, e conferência taxa configurada × o que caiu no banco.
- Relatórios de comissão por vendedor e por técnico prontos.
- Aniversariantes do dia e ranking de clientes: ação comercial direta.

### Pontos negativos
- 39 relatórios, com sobreposição (três de itens vendidos, três de detalhes de estoque) e uma pasta
  "Antigos": excesso de opção, difícil saber qual usar.
- Vários dependem de dados que a loja não preenche (origem do cliente, metas).

### Impacto para Fluxoly (Clientes e Relatórios)

**A Fluxoly já tem:** cadastro de cliente (nome, telefone, e-mail, CPF/CNPJ, observações) com perfil que
mostra histórico de OS e garantias; relatórios de faturamento, lucro bruto, custo de peças, custos
operacionais, técnicos, e a aba Compra e revenda (BR-093); Dashboard com lucro bruto, ticket médio e
resultado líquido — calculados só sobre OS (`api_system.py`: ticket médio = faturamento ÷ OS
finalizadas), sem as vendas.

**Achado na comparação (KI-062):** o perfil do cliente e o detalhe da unidade ainda mostram o placeholder
"módulo de Vendas em construção", embora Vendas exista e grave `cliente_id`/`unidade_serializada_id`. O
histórico de compras do cliente já está no banco, só não é exibido.

**Não tem (encontrado no Mercado Phone):** histórico de compras do cliente com totais; aniversário,
Instagram, endereço; crédito do cliente; índice de recompra; ranking de clientes e aniversariantes;
dashboard que some vendas + OS; lucro líquido de taxa; alertas de dados (venda com prejuízo, custo zerado);
relatórios de comissão.

#### Decisão pendente do PO
Candidatos por relação valor × esforço, na leitura deste benchmark (sugestão, não decisão):
1. **Corrigir KI-062**: mostrar compras no perfil do cliente e o comprador na unidade. Esforço baixo, dado
   já existe.
2. **Alertas de dados** começando por "venda abaixo do custo" e "unidade sem custo": consultas simples
   sobre dados que a Fluxoly já tem (custo por aparelho, BR-092); protege a margem.
3. **Dashboard diário** (faturamento, lucro, ticket médio do dia): agrega vendas + OS já existentes.
4. **Aniversário do cliente + lista de aniversariantes**: um campo novo e um filtro; ação de recompra via
   WhatsApp.
5. **Ranking / recompra de clientes**: depende de 1.
6. Não replicar o catálogo de 39 relatórios: preferir poucos relatórios com filtros.

---

## Tela inicial e Configurações

*Walkthrough de 2026-11-11, somente leitura: tela inicial (atalhos, avisos, widgets), Configurações →
Visão geral, Parâmetros gerais, Gestão de acesso (formulário de um usuário aberto e fechado sem salvar),
Situações da OS, Notificações, Modelos de documentos e Senhas mestras. Nenhum dado de usuário ou cliente
registrado aqui.*

### Tela inicial — fluxo observado
- **Atalhos** configuráveis (Nova venda, Clientes, Estoque, OS, Dashboard de alertas).
- **Avisos** com contagem e link direto para a lista: itens abaixo do mínimo, agendamentos,
  aniversariantes do dia, contas a receber vencendo hoje, **OS com previsão vencida**, **produtos com IMEI
  duplicado**. É a "lista de pendências do dia" — a tela abre dizendo o que precisa de ação.
- Carrossel de banners de terceiros (anúncios de agências, fornecedores) ocupando metade da área nobre.
- **Meus widgets**: filtro de período, gráfico de OS por situação, gráfico de vendas, dashboard diário de
  vendas e últimas vendas com lucro; widgets podem ser ocultados e o layout salvo por usuário.
- O lucro no dashboard pode ser escondido de vendedores (parâmetro "Bloquear lucro no dash para
  vendedores", ligado nesta loja).

### Configurações — fluxo observado
- **Visão geral**: todos os cadastros auxiliares agrupados por módulo — Global (configurações, gestão de
  acesso, dados da empresa), Pessoas (pessoas, vendedores), Venda (funil, canais, tipo de entrega, termos
  de garantia), Estoque (modelos, GB, estado do aparelho, cor, tipo, disponibilidade), Financeiro (formas
  de pagamento, bancos), OS (configurações, serviços, peças, modelos de checklist, situações), Fiscal.
- **Parâmetros gerais**: liga/desliga módulos (caixa, crédito do cliente, programa de indicação),
  preencher forma de pagamento automaticamente, logo nos termos, IMEI no código da NF-e, entrada no
  estoque pela NF-e de entrada, cabeçalho dos documentos (editor de texto rico).
- **Gestão de acesso**: usuário com permissões por módulo (Cadastros básicos, Estoque, Ferramentas,
  Financeiro, Fiscal, Informações gerenciais, OS, Relatórios, Tela inicial, Venda) + perfis customizados
  (esta loja não criou nenhum: usa só os módulos por usuário), tela inicial por usuário, lojas
  permitidas, **controle de visualização de vendas** (vendedor relacionado, ver todas as vendas ou só as
  próprias, só um tipo de venda, só as do dia) e **horário de acesso por dia da semana**.
- **Senhas mestras**: senhas de gerente com conjunto de permissões, pedidas na hora da ação sensível —
  cancelar/descancelar venda, devolução/troca, desconto acima do limite, editar/excluir estoque, excluir
  OS, transferir estoque ou cliente entre lojas, emitir NF-e/NFC-e, abrir/reabrir/editar/excluir caixa,
  editar/excluir contas; editar venda pode exigir senha "somente nas concluídas". A loja usa três (geral,
  estoque, comercial/atendente).
- **Situações da OS**: cadastráveis, com cor, finalidade (em andamento / finalizado / cancelada) e modelo
  de mensagem de WhatsApp por situação. A loja usa seis (inclui Orçamento, Aprovado, Aguardando peça).
- **Notificações**: resumos diários automáticos (contas a pagar, contas a receber, aniversariantes) e
  notificações de OS e de vendas, cada um ativável.
- **Modelos de documentos**: recibo de venda A4 e 80 mm (térmica), recibo de OS A4, cada um configurável.

### Pontos positivos
- **Avisos na tela inicial**: pendências operacionais com contagem e um clique até a lista.
- **Senha mestre**: o atendente executa a operação sensível na hora, com autorização do gerente, sem
  precisar de outro login — e fica registrado quem autorizou.
- Controle fino do que o vendedor vê (só as próprias vendas, sem lucro).
- Situações da OS com significado fixo (finalidade) mas nome livre — a loja adapta sem quebrar relatório.
- Configurações centralizadas por módulo numa tela só.

### Pontos negativos
- Banners de anúncio de terceiros na tela inicial do sistema de gestão.
- Muitos parâmetros sem explicação do efeito (dependem de ícone de ajuda/vídeo).
- Duas formas de controlar acesso (módulos por usuário e perfis customizados) para o mesmo fim.

### Impacto para Fluxoly (Tela inicial e Configurações)

**A Fluxoly já tem:** perfis fixos `admin`/`tecnico`/`vendedor`/`estoque`/`financeiro`
(`fluxoly_core.py::PERFIS_OPCOES`, sem hierarquia, BR-003) com restrição por rota; desativação de usuário;
dados da loja (`DadosLoja.jsx`); tipos de garantia e tipos de reparo cadastráveis; Dashboard (só OS — ver
Clientes e Relatórios). O botão "Imprimir" de Vendas existe, mas ainda só avisa "Impressão ainda não
disponível" (previsto na V1.8 do roadmap) — recibo de venda é lacuna, não diferença de modelo.

**Não tem:** avisos/pendências na tela inicial; autorização de gerente na hora (senha mestre) para
cancelamento, desconto acima do limite e exclusões; restringir vendedor às próprias vendas ou esconder
lucro; horário de acesso; situações de OS configuráveis (são 4 fixas em `fluxoly_core.py`);
notificações/resumos automáticos; parâmetros de módulo liga/desliga.

#### Decisão pendente do PO
Candidatos (sugestão, não decisão):
1. **Painel de pendências na tela inicial**: OS com previsão vencida, contas vencendo hoje, estoque abaixo
   do mínimo, IMEI duplicado. Só consultas sobre dados existentes.
2. **Autorização de gerente na operação** (cancelar venda, desconto acima do limite, excluir), com
   registro em `audit_log` de quem autorizou. Relevante para segurança e auditoria; exige plano (mexe em
   autorização — aprovação obrigatória pelo CLAUDE.md).
3. **Esconder lucro/custo do perfil vendedor** e limitar a listagem às próprias vendas: complementa os
   perfis fixos sem criar permissão granular completa.
4. Situações de OS configuráveis: só se a loja precisar de "Orçamento"/"Aprovado" — avaliar contra a
   máquina de estados atual antes.
5. Não implementar: banners de terceiros, horário de acesso, duplicidade perfis × módulos.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — especificação de negócio da Fluxoly (fonte de verdade, não este documento)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — consistência entre VENDAS.md e o código atual
- `docs/product/research/VENDAS_QUESTIONS.md` — perguntas em aberto para o discuss-phase do Épico Vendas
- `docs/product/research/VENDAS_DORES_REAIS.md` — dores reais observadas na operação, independente de concorrente
