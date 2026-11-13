# TESTING.md — Estratégia de Testes

Este documento define a estratégia oficial de testes do Fluxoly Platform: o que testar, como testar, com qual ferramenta e quando.

**Última revisão:** 2026-07-06

---

## A Pirâmide de Testes

```
           ╔═══════════╗
           ║    E2E    ║  ← poucos, lentos, caros
           ║  Playwright║     testam fluxos completos do usuário
           ╚═══════════╝
         ╔═════════════════╗
         ║   Integração    ║  ← moderados, rápidos
         ║  pytest-flask   ║     testam endpoints e regras de negócio
         ╚═════════════════╝
       ╔═══════════════════════╗
       ║       Unitário        ║  ← muitos, muito rápidos
       ║  pytest (futuro)      ║     testam funções isoladas
       ╚═══════════════════════╝
```

**Regra geral:** quanto mais próximo do topo, mais custoso para escrever e manter, mas mais confiança dá sobre o comportamento real do sistema. Mantenha a base larga e o topo estreito.

---

## Nível 1 — Testes Unitários

**Status:** Planejado (Sprint 2+)  
**Ferramenta:** pytest  
**Localização:** `tests/unit/`  

### Quando escrever

- Lógica de negócio pura que não depende de banco ou HTTP
- Funções de cálculo (ex: somar preços de múltiplos reparos)
- Formatação e transformação de dados
- Validação de inputs

### O que NÃO testar no nível unitário

- Endpoints HTTP (isso é integração)
- Comportamento que depende de banco de dados
- Lógica que depende de múltiplos módulos interagindo

### Exemplo típico

```python
# tests/unit/test_pricing_logic.py
def test_soma_precos_multiplos_reparos():
    precos = [{"valor": 150.0}, {"valor": 80.0}]
    assert calcular_total(precos) == 230.0

def test_soma_retorna_zero_sem_precos():
    assert calcular_total([]) == 0.0
```

### Requisitos de isolamento

- Sem banco de dados
- Sem chamadas HTTP
- Sem `import app`
- Execução < 1ms por teste

---

## Nível 2 — Testes de Integração

**Status:** Ativo (Sprint 2)  
**Ferramenta:** pytest + pytest-flask  
**Localização:** `tests/`  

### Quando escrever

- Todo endpoint REST novo ou modificado
- Toda regra de negócio que envolva banco de dados
- Toda transição de status (OS, shopping list)
- Ao corrigir qualquer bug — escreva primeiro o teste que falha, depois corrija

### O que testar em cada endpoint

```
Caso feliz    → status code correto, body com dados esperados
Caso de erro  → 400 (input inválido), 401 (sem sessão), 403 (sem permissão), 404 (não encontrado)
Edge cases    → campos opcionais ausentes, IDs inexistentes, strings vazias
```

### Isolamento de banco

Todos os testes de integração usam banco SQLite em memória. Nenhum teste toca `database.db`.

```python
# conftest.py — padrão
import os
os.environ.setdefault("IR_FLOW_TEST_DB", ":memory:")
os.environ.setdefault("IR_FLOW_ENABLE_BACKGROUND_JOBS", "0")

from app import app as flask_app, init_db

@pytest.fixture(scope="session")
def client(app):
    return app.test_client()
```

### Regras de isolamento entre testes

- Cada teste é independente — não depende de estado deixado por outro
- Use `scope="function"` para fixtures que criam dados mutáveis
- Use `scope="session"` para fixtures de configuração imutável (o app, o client)
- Não compartilhe IDs entre testes — cada teste cria e gerencia seus próprios dados

### Arquivos de teste existentes

| Arquivo | O que cobre |
|---------|-------------|
| `tests/test_auth.py` | Login, logout, sessão, acesso não autenticado |
| `tests/test_os.py` | CRUD de OS, transições de status, histórico de cliente |
| `tests/test_pricing.py` | Tabela de preços, endpoint `sugerir`, autorização admin |
| `tests/test_shopping.py` | CRUD shopping list, transições de status |

### Executar

```bash
# Todos os testes
pytest tests/

# Com cobertura
pytest tests/ --cov --cov-report=term-missing

# Apenas um arquivo
pytest tests/test_auth.py -v

# Apenas um teste
pytest tests/test_auth.py::test_login_invalido -v
```

---

## Nível 3 — Testes E2E

**Status:** Ativo  
**Ferramenta:** Playwright  
**Localização:** `frontend/tests/e2e/`  

### Quando escrever

- Fluxos completos do ponto de vista do usuário (login → criar OS → editar → fechar)
- Fluxos críticos de negócio que envolvem múltiplas páginas
- Regressões de bugs que envolvem interação visual

### O que NÃO testar no E2E

- Casos de erro de API (401, 404, 500) — isso é integração
- Validação de campos individuais — isso é integração ou unitário
- Lógica de backend — isso é integração

### Fluxos cobertos

| Teste | O que valida |
|-------|-------------|
| Login e dashboard | Autenticação funciona, dashboard carrega |
| Gerenciar item de estoque | CRUD completo via interface |
| Criar, editar e excluir OS | Fluxo principal do negócio |
| Criar backup e gerenciar usuário | Features de administração |

### Executar

```bash
cd frontend

# Build + E2E completo
npm run test:e2e

# Com interface gráfica (debug)
npx playwright test --ui

# Apenas um arquivo
npx playwright test tests/e2e/app.spec.js
```

### Observações

- O `playwright.config.js` sobe dois servidores, na mesma topologia da produção (KI-068): o backend
  Flask (`python app.py`; `python3` fora do Windows, ou o executável em `E2E_PYTHON`, com as dependências do
  `requirements.txt`) e o `vite preview` do build na raiz, que chega à API pelo proxy `/api`
- Cada execução usa um banco novo num diretório temporário (`IR_FLOW_DATA_DIR`), com jobs em background e
  MercadoPhone desligados — nunca o `database.db`
- Senha do admin de teste: variável `E2E_ADMIN_PASSWORD` (o config define um valor de teste quando ausente)
- A execução aborta se `VITE_API_URL` estiver definido (ambiente ou `frontend/.env*`)
- Ainda não roda no CI (decisão do PO, 2026-11-13: primeiro comprovar estabilidade local; o job entra num
  PR `chore/` separado, inicialmente não bloqueante)

---

## Cobertura de Testes

### Meta por fase

| Fase | Meta | Escopo |
|------|------|--------|
| Sprint 2 (atual) | >= 40% | Rotas críticas: auth, OS, preços, shopping |
| Sprint 3 | >= 60% | + segurança, checklist, estoque |
| Sprint 4+ | >= 80% | Após decomposição dos módulos |

### Medir cobertura

```bash
pytest tests/ --cov --cov-report=term-missing --cov-report=html
# Relatório em htmlcov/index.html
```

### Threshold configurado em `pyproject.toml`

```toml
[tool.coverage.report]
fail_under = 40
```

O CI falha automaticamente se a cobertura cair abaixo do threshold.

---

## Convenções

### Nomenclatura

```
tests/
├── test_auth.py          ← testes do domínio de autenticação
├── test_os.py            ← testes de Ordens de Serviço
├── test_pricing.py       ← testes de tabela de preços
├── test_shopping.py      ← testes de shopping list
└── unit/
    └── test_pricing_logic.py  ← testes unitários (futuro)
```

Nome de teste: `test_<o_que_faz>_quando_<condição>`:
```python
def test_login_retorna_401_quando_senha_errada():
def test_criar_os_retorna_201_com_campos_validos():
def test_sugerir_preco_retorna_zero_para_modelo_inexistente():
```

### Princípio AAA (Arrange, Act, Assert)

```python
def test_criar_item_shopping(admin_session):
    # Arrange
    payload = {"produto_nome": "Tela iPhone 14", "quantidade_solicitada": 2}

    # Act
    response = admin_session.post("/api/shopping-list", json=payload)

    # Assert
    assert response.status_code == 201
    data = response.get_json()
    assert data["data"]["produto_nome"] == "Tela iPhone 14"
```

---

## Regras Inegociáveis

1. **Nenhum teste toca `database.db`** — use banco in-memory.
2. **Testes falhando bloqueiam merge** — CI vermelho = PR não entra.
3. **Novo bug = novo teste** — ao corrigir, escreva o teste que o teria detectado.
4. **Cobertura não regride** — threshold configurado no CI.
5. **Testes independentes** — ordem de execução não importa.
