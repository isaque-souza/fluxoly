"""
KI-067 -- atomicidade entre a checagem do cliente e a gravação de venda/compra por troca, e entre
inativação/exclusão do cliente e essas operações (BR-024b, hotfix complementar ao KI-066).

Antes, `iniciar_venda` e `registrar_compra` conferiam o cliente numa conexão própria e gravavam em
outra; inativar e excluir liam e escreviam sem trava. Uma inativação ou exclusão no intervalo gerava
venda/troca de cliente inativo ou venda órfã. Agora as quatro operações abrem a transação com
BEGIN IMMEDIATE e conferem o cliente no mesmo cursor que grava.

Grupos:
- A: os três cenários reproduzidos na análise (ação do admin logo depois da pré-checagem), invertidos.
- B: ordem fixada com threads e conexões SQLite reais -- quem pegou a trava primeiro é segurado por um
  evento dentro da própria transação, e o outro lado fica bloqueado de verdade no BEGIN IMMEDIATE.
- C: disputa sem nenhum patch (Barrier), nas duas ordens, repetida várias vezes, com os invariantes.
- D: fila de escrita acima do busy_timeout responde 503 (nunca 500) e não grava nada.

Banco temporário do conftest; nunca database.db.
"""

import sqlite3
import threading
import time
import uuid

import pytest

import app as _app
import fluxoly_caixa_service as caixa_service
import fluxoly_clientes_repository as clientes_repo
import fluxoly_clientes_service as clientes_service
import fluxoly_compras_aparelhos_service as compras_service
import fluxoly_vendas_service as vendas_service

REPETICOES = 25
ESPERA_BLOQUEIO = 0.3  # tempo para confirmar que o outro lado está parado no BEGIN IMMEDIATE


def _x(sql, params=()):
    conn = _app.conectar()
    try:
        cur = conn.execute(sql, params)
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _q(sql, params=()):
    conn = _app.conectar()
    try:
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def _imei():
    return f"35{uuid.uuid4().int % 10**13:013d}"


@pytest.fixture
def novo_cliente():
    criados = []

    def _criar():
        cid = _x("INSERT INTO clientes (nome) VALUES (?)", (f"Atomicidade {uuid.uuid4().hex[:6]}",))
        criados.append(cid)
        return cid

    yield _criar
    # Limpeza só do que este módulo criou (mesmo padrão de test_clientes_inativacao.py).
    for cid in criados:
        for (vid,) in _q("SELECT id FROM vendas WHERE cliente_id=?", (cid,)):
            _x("DELETE FROM vendas_itens WHERE venda_id=?", (vid,))
        _x("DELETE FROM vendas WHERE cliente_id=?", (cid,))
        _x("DELETE FROM compras_aparelhos WHERE cliente_id=?", (cid,))
        _x("DELETE FROM audit_log WHERE entidade='cliente' AND entidade_id=?", (cid,))
        _x("DELETE FROM clientes WHERE id=?", (cid,))


@pytest.fixture
def produto_id():
    return _x(
        "INSERT INTO produtos (categoria, marca, modelo, condicao, preco_venda, quantidade, requer_rastreio_unidade) "
        "VALUES ('iPhone', 'Apple', ?, 'Seminovo', 3500.0, 0, 1)",
        (f"iPhone Atomicidade {uuid.uuid4().hex[:6]}",),
    )


@pytest.fixture
def nova_unidade(produto_id):
    def _criar():
        return _x(
            "INSERT INTO unidades_serializadas (produto_id, imei, status) VALUES (?, ?, 'disponivel')",
            (produto_id, _imei()),
        )

    return _criar


@pytest.fixture
def admin_id(usuario_admin):
    return usuario_admin["id"]


def _vender(admin, cliente, unidade, tipo_garantia):
    return vendas_service.iniciar_venda(_app.conectar, admin, cliente, unidade, "pix", 3200.0, tipo_garantia)


def _trocar(admin, cliente, produto):
    return compras_service.registrar_compra(
        _app.conectar,
        admin,
        produto_id=produto,
        imei=_imei(),
        origem="troca",
        cliente_id=cliente,
        valor_pago=900.0,
        forma_pagamento="pix",
        estado="Bom estado",
    )


def _inativar(admin, cliente):
    return clientes_service.inativar_cliente(_app.conectar, admin, cliente)


def _excluir(admin, cliente):
    return clientes_service.excluir_cliente(_app.conectar, admin, cliente)


def _ativo(cliente):
    row = _q("SELECT ativo FROM clientes WHERE id=?", (cliente,))
    return row[0][0] if row else None


def _vendas_do_cliente(cliente):
    return [r[0] for r in _q("SELECT id FROM vendas WHERE cliente_id=?", (cliente,))]


def _compras_do_cliente(cliente):
    return [r[0] for r in _q("SELECT id FROM compras_aparelhos WHERE cliente_id=?", (cliente,))]


def _audit_id(entidade, entidade_id, acao):
    rows = _q("SELECT id FROM audit_log WHERE entidade=? AND entidade_id=? AND acao=?", (entidade, entidade_id, acao))
    assert len(rows) <= 1, f"auditoria duplicada: {entidade} {entidade_id} {acao}"
    return rows[0][0] if rows else None


def _assert_banco_integro():
    assert _q("PRAGMA integrity_check")[0][0] == "ok"
    orfas = _q(
        "SELECT 'vendas', id FROM vendas WHERE cliente_id IS NOT NULL AND cliente_id NOT IN (SELECT id FROM clientes) "
        "UNION ALL SELECT 'compras_aparelhos', id FROM compras_aparelhos "
        "WHERE cliente_id IS NOT NULL AND cliente_id NOT IN (SELECT id FROM clientes) "
        "UNION ALL SELECT 'os', id FROM os WHERE cliente_id IS NOT NULL AND cliente_id NOT IN (SELECT id FROM clientes)"
    )
    assert orfas == []
    assert _q("SELECT unidade_serializada_id, COUNT(*) FROM vendas_itens GROUP BY 1 HAVING COUNT(*) > 1") == []


def _depois_da_precheck(monkeypatch, acao):
    """Executa `acao` (outra conexão, commit próprio) logo depois da pré-checagem do cliente -- o mesmo
    intervalo em que a análise do KI-067 reproduziu os três cenários."""
    original = clientes_service.validar_cliente_para_nova_operacao
    resultado = {}

    def _com_corte(*a, **kw):
        retorno = original(*a, **kw)
        if "acao" not in resultado:
            resultado["acao"] = acao()
        return retorno

    monkeypatch.setattr(clientes_service, "validar_cliente_para_nova_operacao", _com_corte)
    return resultado


# ---------------------------------------------------------------------------
# A -- cenários da análise do KI-067, agora recusados
# ---------------------------------------------------------------------------
class TestCenariosOriginais:
    def test_venda_x_inativacao_no_intervalo_e_recusada(
        self, monkeypatch, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id
    ):
        cliente, unidade = novo_cliente(), nova_unidade()
        r = _depois_da_precheck(monkeypatch, lambda: _inativar(admin_id, cliente))

        venda_id, erro = _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id)

        assert r["acao"] == (True, None)
        assert venda_id is None and erro == clientes_service.MSG_CLIENTE_INATIVO
        assert _vendas_do_cliente(cliente) == []
        assert _q("SELECT status FROM unidades_serializadas WHERE id=?", (unidade,))[0][0] == "disponivel"
        _assert_banco_integro()

    def test_venda_x_exclusao_no_intervalo_nao_deixa_venda_orfa(
        self, monkeypatch, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id
    ):
        cliente, unidade = novo_cliente(), nova_unidade()
        r = _depois_da_precheck(monkeypatch, lambda: _excluir(admin_id, cliente))

        venda_id, erro = _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id)

        assert r["acao"] == (True, None, None)  # cliente sem vínculo: a exclusão em si é legítima
        assert venda_id is None and erro == "Cliente não encontrado."
        assert _q("SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cliente,))[0][0] == 0
        _assert_banco_integro()

    def test_troca_x_inativacao_no_intervalo_e_recusada(self, monkeypatch, admin_id, novo_cliente, produto_id):
        cliente = novo_cliente()
        r = _depois_da_precheck(monkeypatch, lambda: _inativar(admin_id, cliente))
        compras_antes = _q("SELECT COUNT(*) FROM compras_aparelhos")[0][0]

        compra_id, erro = _trocar(admin_id, cliente, produto_id)

        assert r["acao"] == (True, None)
        assert compra_id is None and erro == clientes_service.MSG_CLIENTE_INATIVO
        assert _q("SELECT COUNT(*) FROM compras_aparelhos")[0][0] == compras_antes
        _assert_banco_integro()


# ---------------------------------------------------------------------------
# B -- ordem fixada, threads e conexões reais
# ---------------------------------------------------------------------------
def _segurar_dentro_da_transacao(monkeypatch, alvo, nome):
    """Na primeira chamada de `alvo.nome` (que roda dentro da transação de escrita), avisa que entrou e
    espera a liberação. Devolve (dentro, liberar)."""
    original = getattr(alvo, nome)
    dentro, liberar = threading.Event(), threading.Event()

    def _segurando(*a, **kw):
        if not dentro.is_set():
            dentro.set()
            assert liberar.wait(20)
        return original(*a, **kw)

    monkeypatch.setattr(alvo, nome, _segurando)
    return dentro, liberar


def _em_thread(fn):
    resultado = {}

    def _rodar():
        try:
            resultado["valor"] = fn()
        except BaseException as exc:  # noqa: BLE001 -- reportado na thread principal
            resultado["erro"] = exc

    t = threading.Thread(target=_rodar)
    t.start()
    return t, resultado


def _concluir(t, resultado):
    t.join(30)
    assert not t.is_alive(), "thread não terminou"
    if "erro" in resultado:
        raise resultado["erro"]
    return resultado["valor"]


def _primeiro_segura_segundo_espera(monkeypatch, alvo, nome, primeira, segunda):
    dentro, liberar = _segurar_dentro_da_transacao(monkeypatch, alvo, nome)
    t1, r1 = _em_thread(primeira)
    assert dentro.wait(10), "a primeira operação não entrou na transação"
    t2, r2 = _em_thread(segunda)
    time.sleep(ESPERA_BLOQUEIO)
    bloqueada = t2.is_alive()
    liberar.set()
    return _concluir(t1, r1), _concluir(t2, r2), bloqueada


class TestOrdemFixadaComConexoesReais:
    def test_venda_primeiro_inativacao_depois(
        self, monkeypatch, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id
    ):
        cliente, unidade = novo_cliente(), nova_unidade()

        (venda_id, erro), inativacao, bloqueada = _primeiro_segura_segundo_espera(
            monkeypatch,
            caixa_service,
            "registrar_entrada_de_venda",
            lambda: _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id),
            lambda: _inativar(admin_id, cliente),
        )

        assert bloqueada, "a inativação deveria esperar a transação da venda"
        assert erro is None and venda_id
        assert inativacao == (True, None)
        assert _ativo(cliente) == 0 and _vendas_do_cliente(cliente) == [venda_id]  # histórico preservado
        assert _audit_id("venda", venda_id, "create") < _audit_id("cliente", cliente, "status_change")
        _assert_banco_integro()

    def test_venda_primeiro_exclusao_http_depois_recebe_409(
        self, monkeypatch, app, login_como, usuario_admin, novo_cliente, nova_unidade, tipo_garantia_padrao_id
    ):
        cliente, unidade = novo_cliente(), nova_unidade()
        http = app.test_client()
        assert login_como(http, usuario_admin).status_code == 200

        (venda_id, erro), resp, bloqueada = _primeiro_segura_segundo_espera(
            monkeypatch,
            caixa_service,
            "registrar_entrada_de_venda",
            lambda: _vender(usuario_admin["id"], cliente, unidade, tipo_garantia_padrao_id),
            lambda: http.delete(f"/api/clientes/{cliente}"),
        )

        assert bloqueada
        assert erro is None and venda_id
        assert resp.status_code == 409
        assert resp.get_json()["vinculos"]["vendas"] == 1
        assert _ativo(cliente) == 1 and _audit_id("cliente", cliente, "delete") is None
        _assert_banco_integro()

    def test_inativacao_primeiro_venda_depois_e_recusada(
        self, monkeypatch, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id
    ):
        cliente, unidade = novo_cliente(), nova_unidade()

        inativacao, (venda_id, erro), bloqueada = _primeiro_segura_segundo_espera(
            monkeypatch,
            clientes_repo,
            "definir_ativo",
            lambda: _inativar(admin_id, cliente),
            lambda: _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id),
        )

        # A pré-checagem da venda roda sem trava e ainda vê o cliente ativo; quem recusa é a checagem
        # dentro da transação, depois que a inativação libera a escrita.
        assert bloqueada
        assert inativacao == (True, None)
        assert venda_id is None and erro == clientes_service.MSG_CLIENTE_INATIVO
        assert _vendas_do_cliente(cliente) == []
        _assert_banco_integro()

    def test_exclusao_primeiro_venda_depois_e_recusada(
        self, monkeypatch, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id
    ):
        cliente, unidade = novo_cliente(), nova_unidade()

        exclusao, (venda_id, erro), bloqueada = _primeiro_segura_segundo_espera(
            monkeypatch,
            clientes_repo,
            "deletar",
            lambda: _excluir(admin_id, cliente),
            lambda: _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id),
        )

        assert bloqueada
        assert exclusao == (True, None, None)
        assert venda_id is None and erro == "Cliente não encontrado."
        assert _q("SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cliente,))[0][0] == 0
        _assert_banco_integro()

    def test_inativacao_primeiro_troca_depois_e_recusada(self, monkeypatch, admin_id, novo_cliente, produto_id):
        cliente = novo_cliente()

        inativacao, (compra_id, erro), bloqueada = _primeiro_segura_segundo_espera(
            monkeypatch,
            clientes_repo,
            "definir_ativo",
            lambda: _inativar(admin_id, cliente),
            lambda: _trocar(admin_id, cliente, produto_id),
        )

        assert bloqueada
        assert inativacao == (True, None)
        assert compra_id is None and erro == clientes_service.MSG_CLIENTE_INATIVO
        assert _compras_do_cliente(cliente) == []
        _assert_banco_integro()

    def test_troca_primeiro_inativacao_depois_preserva_historico(self, monkeypatch, admin_id, novo_cliente, produto_id):
        cliente = novo_cliente()

        (compra_id, erro), inativacao, bloqueada = _primeiro_segura_segundo_espera(
            monkeypatch,
            caixa_service,
            "registrar_saida_de_compra_aparelho",
            lambda: _trocar(admin_id, cliente, produto_id),
            lambda: _inativar(admin_id, cliente),
        )

        assert bloqueada
        assert erro is None and compra_id
        assert inativacao == (True, None)
        assert _ativo(cliente) == 0 and _compras_do_cliente(cliente) == [compra_id]
        assert _audit_id("compra_aparelho", compra_id, "create") < _audit_id("cliente", cliente, "status_change")
        _assert_banco_integro()


# ---------------------------------------------------------------------------
# C -- disputa real, sem patch, nas duas ordens e repetida
# ---------------------------------------------------------------------------
def _disputar(a, b, a_primeiro):
    """Libera as duas operações juntas (Barrier); `a_primeiro` dá uma folga mínima para um dos lados,
    para que as duas ordens de chegada apareçam ao longo das repetições."""
    barreira = threading.Barrier(2)
    resultados = {}

    def _lado(nome, fn, atraso):
        barreira.wait(10)
        if atraso:
            time.sleep(atraso)
        resultados[nome] = fn()

    folga = 0.002
    ta = threading.Thread(target=_lado, args=("a", a, 0 if a_primeiro else folga))
    tb = threading.Thread(target=_lado, args=("b", b, folga if a_primeiro else 0))
    ta.start()
    tb.start()
    ta.join(30)
    tb.join(30)
    assert not ta.is_alive() and not tb.is_alive()
    return resultados["a"], resultados["b"]


class TestDisputaReal:
    @pytest.mark.parametrize("venda_primeiro", [True, False], ids=["venda-primeiro", "inativacao-primeiro"])
    def test_venda_x_inativacao(self, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id, venda_primeiro):
        resultados = {"venda": 0, "recusada": 0}
        for _ in range(REPETICOES):
            cliente, unidade = novo_cliente(), nova_unidade()
            (venda_id, erro), inativacao = _disputar(
                lambda c=cliente, u=unidade: _vender(admin_id, c, u, tipo_garantia_padrao_id),
                lambda c=cliente: _inativar(admin_id, c),
                venda_primeiro,
            )

            assert inativacao == (True, None)
            assert _ativo(cliente) == 0
            mudanca = _audit_id("cliente", cliente, "status_change")
            if venda_id:
                resultados["venda"] += 1
                assert erro is None and _vendas_do_cliente(cliente) == [venda_id]
                assert _audit_id("venda", venda_id, "create") < mudanca  # gravada antes da inativação
            else:
                resultados["recusada"] += 1
                assert erro == clientes_service.MSG_CLIENTE_INATIVO
                assert _vendas_do_cliente(cliente) == []
        _assert_banco_integro()
        print(f"\n[KI-067 venda x inativacao venda_primeiro={venda_primeiro}] {resultados}")

    @pytest.mark.parametrize("venda_primeiro", [True, False], ids=["venda-primeiro", "exclusao-primeiro"])
    def test_venda_x_exclusao(self, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id, venda_primeiro):
        resultados = {"venda": 0, "excluido": 0}
        for _ in range(REPETICOES):
            cliente, unidade = novo_cliente(), nova_unidade()
            (venda_id, erro), (excluido, erro_exclusao, vinculos) = _disputar(
                lambda c=cliente, u=unidade: _vender(admin_id, c, u, tipo_garantia_padrao_id),
                lambda c=cliente: _excluir(admin_id, c),
                venda_primeiro,
            )

            # Exatamente uma das duas vence; nunca as duas, nunca nenhuma.
            assert bool(venda_id) != bool(excluido)
            if venda_id:
                resultados["venda"] += 1
                assert erro is None and vinculos == {"os": 0, "vendas": 1, "compras_aparelhos": 0}
                assert _ativo(cliente) == 1 and _audit_id("cliente", cliente, "delete") is None
            else:
                resultados["excluido"] += 1
                assert erro == "Cliente não encontrado." and erro_exclusao is None
                assert _ativo(cliente) is None and _audit_id("cliente", cliente, "delete")
                assert _q("SELECT COUNT(*) FROM vendas WHERE cliente_id=?", (cliente,))[0][0] == 0
        _assert_banco_integro()
        print(f"\n[KI-067 venda x exclusao venda_primeiro={venda_primeiro}] {resultados}")

    @pytest.mark.parametrize("troca_primeiro", [True, False], ids=["troca-primeiro", "inativacao-primeiro"])
    def test_troca_x_inativacao(self, admin_id, novo_cliente, produto_id, troca_primeiro):
        resultados = {"troca": 0, "recusada": 0}
        for _ in range(REPETICOES):
            cliente = novo_cliente()
            (compra_id, erro), inativacao = _disputar(
                lambda c=cliente: _trocar(admin_id, c, produto_id),
                lambda c=cliente: _inativar(admin_id, c),
                troca_primeiro,
            )

            assert inativacao == (True, None)
            mudanca = _audit_id("cliente", cliente, "status_change")
            if compra_id:
                resultados["troca"] += 1
                assert erro is None and _compras_do_cliente(cliente) == [compra_id]
                assert _audit_id("compra_aparelho", compra_id, "create") < mudanca
            else:
                resultados["recusada"] += 1
                assert erro == clientes_service.MSG_CLIENTE_INATIVO
                assert _compras_do_cliente(cliente) == []
        _assert_banco_integro()
        print(f"\n[KI-067 troca x inativacao troca_primeiro={troca_primeiro}] {resultados}")


# ---------------------------------------------------------------------------
# D -- fila de escrita acima do busy_timeout: 503, nada gravado, nunca 500
# ---------------------------------------------------------------------------
class TestEscritaOcupada:
    @pytest.fixture
    def banco_travado(self, monkeypatch):
        monkeypatch.setattr(_app, "SQLITE_TIMEOUT_SECONDS", 0.2)
        monkeypatch.setattr(_app, "SQLITE_BUSY_TIMEOUT_MS", 200)
        trava = sqlite3.connect(_app.DB_PATH, isolation_level=None)
        yield trava
        trava.execute("ROLLBACK")
        trava.close()

    def _travar(self, trava):
        trava.execute("BEGIN IMMEDIATE")

    def test_rotas_respondem_503_sem_gravar(
        self,
        app,
        login_como,
        usuario_admin,
        novo_cliente,
        nova_unidade,
        produto_id,
        tipo_garantia_padrao_id,
        banco_travado,
    ):
        cliente, unidade = novo_cliente(), nova_unidade()
        http = app.test_client()
        assert login_como(http, usuario_admin).status_code == 200

        def contagens():
            return [_q(f"SELECT COUNT(*) FROM {t}")[0][0] for t in ("vendas", "compras_aparelhos", "audit_log")]

        antes = contagens()

        self._travar(banco_travado)
        respostas = {
            "venda": http.post(
                "/api/vendas",
                json={
                    "cliente_id": cliente,
                    "unidade_serializada_id": unidade,
                    "forma_pagamento": "pix",
                    "valor_unitario": 3200.0,
                    "tipo_garantia_id": tipo_garantia_padrao_id,
                },
            ),
            "troca": http.post(
                "/api/compras-aparelhos",
                json={
                    "produto_id": produto_id,
                    "imei": _imei(),
                    "origem": "troca",
                    "cliente_id": cliente,
                    "valor_pago": 900.0,
                    "forma_pagamento": "pix",
                    "estado": "Bom estado",
                },
            ),
            "inativar": http.post(f"/api/clientes/{cliente}/inativar"),
            "reativar": http.post(f"/api/clientes/{cliente}/reativar"),
            "excluir": http.delete(f"/api/clientes/{cliente}"),
        }
        banco_travado.execute("ROLLBACK")
        banco_travado.execute("BEGIN")  # o fixture fecha com ROLLBACK

        for nome, resp in respostas.items():
            assert resp.status_code == 503, (nome, resp.status_code, resp.get_data(as_text=True))
            assert resp.get_json()["erro"] == clientes_service.MSG_ESCRITA_OCUPADA
        assert contagens() == antes
        assert _ativo(cliente) == 1
        _assert_banco_integro()


# ---------------------------------------------------------------------------
# E -- falha no meio da transação: tudo é revertido, a trava é liberada e a nova tentativa grava uma vez
# ---------------------------------------------------------------------------
class FalhaInjetada(Exception):
    pass


def _foto_do_banco():
    """Conteúdo de todas as tabelas (inclusive sqlite_sequence), na ordem do rowid."""
    tabelas = [r[0] for r in _q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    return {t: _q(f'SELECT * FROM "{t}" ORDER BY rowid') for t in tabelas}


def _falhar_depois_de(monkeypatch, alvo, nome, erro=None):
    """`alvo.nome` roda de verdade (grava no cursor da transação) e em seguida levanta `erro`."""
    original = getattr(alvo, nome)
    chamadas = []

    def _grava_e_falha(*a, **kw):
        original(*a, **kw)
        chamadas.append(nome)
        raise erro or FalhaInjetada(f"falha injetada depois de {nome}")

    monkeypatch.setattr(alvo, nome, _grava_e_falha)
    return chamadas


class TestRollbackEmFalhaIntermediaria:
    def test_venda_falha_no_caixa(self, monkeypatch, admin_id, novo_cliente, nova_unidade, tipo_garantia_padrao_id):
        cliente, unidade = novo_cliente(), nova_unidade()
        antes = _foto_do_banco()
        chamadas = _falhar_depois_de(monkeypatch, caixa_service, "registrar_entrada_de_venda")

        venda_id, erro = _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id)

        assert chamadas and venda_id is None and "falha injetada" in erro
        assert _foto_do_banco() == antes  # venda, item, unidade, auditoria e caixa revertidos
        monkeypatch.undo()
        venda_id, erro = _vender(admin_id, cliente, unidade, tipo_garantia_padrao_id)
        assert erro is None and _vendas_do_cliente(cliente) == [venda_id]
        assert (
            _q("SELECT COUNT(*) FROM movimentacoes_caixa WHERE origem='venda' AND origem_id=?", (venda_id,))[0][0] == 1
        )
        _assert_banco_integro()

    @pytest.mark.parametrize(
        "modulo, nome",
        [
            ("fluxoly_unidades_serializadas_service", "criar_unidade_de_compra"),
            ("fluxoly_compras_aparelhos_service", "registrar_log_auditoria"),
            ("fluxoly_caixa_service", "registrar_saida_de_compra_aparelho"),
        ],
    )
    def test_troca_falha_depois_de_iniciar_a_gravacao(
        self, monkeypatch, admin_id, novo_cliente, produto_id, modulo, nome
    ):
        cliente = novo_cliente()
        antes = _foto_do_banco()
        chamadas = _falhar_depois_de(monkeypatch, __import__(modulo), nome)

        with pytest.raises(FalhaInjetada):
            _trocar(admin_id, cliente, produto_id)

        assert chamadas
        assert _foto_do_banco() == antes  # unidade, compra, auditoria e caixa revertidos
        monkeypatch.undo()
        compra_id, erro = _trocar(admin_id, cliente, produto_id)
        assert erro is None and _compras_do_cliente(cliente) == [compra_id]
        _assert_banco_integro()

    def test_troca_erro_de_disco_nao_vira_ocupado(self, monkeypatch, admin_id, novo_cliente, produto_id):
        cliente = novo_cliente()
        antes = _foto_do_banco()
        _falhar_depois_de(
            monkeypatch, compras_service, "registrar_log_auditoria", sqlite3.OperationalError("disk I/O error")
        )

        with pytest.raises(sqlite3.OperationalError, match="disk I/O"):
            _trocar(admin_id, cliente, produto_id)

        assert _foto_do_banco() == antes

    @pytest.mark.parametrize("acao", ["inativar", "reativar"])
    def test_situacao_falha_na_auditoria(self, monkeypatch, admin_id, novo_cliente, acao):
        cliente = novo_cliente()
        if acao == "reativar":
            assert _inativar(admin_id, cliente) == (True, None)
        funcao = getattr(clientes_service, f"{acao}_cliente")
        antes = _foto_do_banco()
        chamadas = _falhar_depois_de(monkeypatch, clientes_service, "registrar_log_auditoria")

        with pytest.raises(FalhaInjetada):
            funcao(_app.conectar, admin_id, cliente)

        assert chamadas
        assert _foto_do_banco() == antes  # UPDATE de clientes.ativo e auditoria revertidos
        monkeypatch.undo()
        assert funcao(_app.conectar, admin_id, cliente) == (True, None)
        assert _ativo(cliente) == (1 if acao == "reativar" else 0)
        _assert_banco_integro()

    def test_exclusao_falha_na_auditoria(self, monkeypatch, admin_id, novo_cliente):
        cliente = novo_cliente()
        antes = _foto_do_banco()
        chamadas = _falhar_depois_de(monkeypatch, clientes_service, "registrar_log_auditoria")

        with pytest.raises(FalhaInjetada):
            _excluir(admin_id, cliente)

        assert chamadas
        assert _foto_do_banco() == antes  # DELETE e auditoria revertidos: o cliente continua lá
        monkeypatch.undo()
        assert _excluir(admin_id, cliente) == (True, None, None)
        assert _ativo(cliente) is None
        assert _audit_id("cliente", cliente, "delete")
        _assert_banco_integro()
