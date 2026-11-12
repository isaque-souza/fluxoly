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

## Financeiro, Fiscal

Ainda não percorridos — seções a adicionar quando cada módulo for analisado em sessão própria.

---

## Documentos relacionados

- `docs/product/features/VENDAS.md` — especificação de negócio da Fluxoly (fonte de verdade, não este documento)
- `docs/product/features/VENDAS_GAP_ANALYSIS.md` — consistência entre VENDAS.md e o código atual
- `docs/product/research/VENDAS_QUESTIONS.md` — perguntas em aberto para o discuss-phase do Épico Vendas
- `docs/product/research/VENDAS_DORES_REAIS.md` — dores reais observadas na operação, independente de concorrente
