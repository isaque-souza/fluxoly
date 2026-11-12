# PLAN-dias-em-estoque — Dias em estoque na lista de unidades

**Data:** 2026-11-11
**Origem:** `docs/product/PRODUCT_BACKLOG.md` → Proposta do benchmark Mercado Phone, Onda 1 item 7
(Etapa 7); evidência em `MERCADO_PHONE.md` → "Compras / Estoque".
**Status:** Aprovado pelo Product Owner (2026-11-11, aprovação geral das etapas)

> Documento efêmero (ADR-010).

**Estado**

- [x] Discovery — a lista de unidades mostra só "Cadastrado em"; não dá para ver de relance o aparelho parado
- [x] Plano Técnico — este documento
- [x] Implementação — branch `feat/dias-em-estoque`
- [x] Testes — `TestDiasEmEstoque` (`tests/test_unidades_serializadas.py`, 2), `UnidadesSerializadas.test.jsx` (+1)
- [ ] QA Manual — pendente
- [x] Revisão Arquitetural — abaixo
- [x] Encerramento — `CHANGELOG.md`

## Escopo

- Campo calculado `dias_em_estoque` na unidade com origem (listagem e detalhe de `/api/unidades-serializadas`):
  dias desde `criado_em`, só para `disponivel`/`reservado`/`em_reparo`; `null` para vendida/devolvida.
- Coluna "Em estoque" na lista de unidades, com destaque visual a partir de 90 dias. A ordenação
  "Mais antigo" já existente põe os parados no topo.

## Regras

1. Calculado na hora, nunca gravado. Sem mudança de schema.
2. Data de entrada = `criado_em` da unidade (cadastro). Unidade que voltou de venda cancelada continua
   contando do cadastro original — é o tempo de casa do aparelho, não do último retorno.
3. `criado_em` é UTC (KI-061); diferença de no máximo 1 dia perto da meia-noite. Nunca negativo.
4. O limiar de 90 dias é só visual (frontend), não vira regra de negócio.

## Revisão Arquitetural

Coerência: cálculo no service de Unidades (dono do dado). Autorização: inalterada — o campo não é
financeiro. Vazamento: nenhum.
