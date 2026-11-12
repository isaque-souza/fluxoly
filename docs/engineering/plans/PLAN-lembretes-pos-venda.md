# PLAN-lembretes-pos-venda — Lembretes de pós-venda e upgrade (wa.me)

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 3 item 16
(Etapa 13); evidência em `MERCADO_PHONE.md` → "Ferramentas e Marketplace" (lembretes eram o recurso mais
usado da conta observada).
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — venda já tem cliente com telefone (KI-062 resolvido); não existia lista de recontato
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/lembretes-pos-venda`
- [x] Testes — `TestLembretesPosVenda` (`tests/test_vendas.py`, 6), `Lembretes.test.jsx` (4); frontend
      211/211; ruff e eslint ok
- [ ] QA Manual — pendente (abrir um link wa.me no celular da loja)
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`, BR-104

## Escopo (versão simples, sem API paga)

- `GET /api/vendas/lembretes?data=AAAA-MM-DD` (admin/vendedor; padrão hoje): vendas concluídas que
  completam **7** (pós-venda), **30** (satisfação) e **365** (upgrade) dias na data, agrupadas por marco,
  com cliente, telefone e produtos.
- Tela `/lembretes` (menu Vendas → Lembretes): escolhe o dia, lista por marco, botão "Abrir WhatsApp" que
  abre `https://wa.me/55…?text=…` com mensagem sugerida. Quem atende revisa e envia no próprio aparelho.

## Regras (BR-104)

1. Só venda concluída; cancelada some.
2. Lista do dia, sem "já contatado" — guardar contato exigiria schema (fica para a Fase 4, CRM). Dia
   perdido se recupera escolhendo a data.
3. Data da venda em UTC (`criado_em`, KI-061): venda feita entre 21h e 0h de Brasília conta como do dia
   seguinte.
4. As mensagens são texto fixo no frontend (sem promessa de preço ou condição); mudar o texto é mudança
   de código até existir configuração.

## Revisão Arquitetural

Privacidade: o telefone do cliente já é visível a esses perfis na venda; o sistema não envia nada a
serviço externo — o link só abre o WhatsApp no aparelho de quem clica. Autorização: perfis que vendem
(`usuario_pode_vender`), mesmo critério de criar venda. Sem schema.
