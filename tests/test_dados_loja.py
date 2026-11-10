"""
Dados da Loja (BR-094, docs/engineering/plans/PLAN-documentos-os-cliente.md):
leitura para qualquer usuário autenticado, escrita só para admin, nome
fantasia obrigatório, limite de tamanho por campo, linha única (upsert) e
auditoria de cada salvamento.
"""

import pytest

import app as _app

PAYLOAD = {
    "nome_fantasia": "Loja Teste Ação",
    "razao_social": "Loja Teste Ltda",
    "cnpj": "12.345.678/0001-90",
    "telefone": "(11) 99999-0000",
    "email": "contato@loja.teste",
    "endereco": "Rua das Flores, 100 — São Paulo/SP",
    "termos_entrada": "A loja não se responsabiliza por dados.",
    "termos_garantia": "Garantia não cobre mau uso.",
}


@pytest.fixture(autouse=True)
def _sem_dados_loja():
    def _limpar():
        conn = _app.conectar()
        try:
            conn.execute("DELETE FROM dados_loja")
            conn.commit()
        finally:
            conn.close()

    _limpar()
    yield
    _limpar()


def test_get_sem_login_retorna_401(client):
    assert client.get("/api/dados-loja").status_code == 401


def test_get_sem_cadastro_devolve_campos_vazios(client, login_como, usuario_tecnico):
    login_como(client, usuario_tecnico)
    resp = client.get("/api/dados-loja")
    assert resp.status_code == 200
    dados = resp.get_json()["dados_loja"]
    assert dados["nome_fantasia"] == ""
    assert set(PAYLOAD) <= set(dados)


def test_admin_salva_e_qualquer_perfil_le(client, login_como, usuario_admin, usuario_tecnico):
    login_como(client, usuario_admin)
    resp = client.put("/api/dados-loja", json=PAYLOAD)
    assert resp.status_code == 200
    assert resp.get_json()["dados_loja"]["nome_fantasia"] == "Loja Teste Ação"

    outro = _app.app.test_client()
    login_como(outro, usuario_tecnico)
    dados = outro.get("/api/dados-loja").get_json()["dados_loja"]
    for chave, valor in PAYLOAD.items():
        assert dados[chave] == valor


@pytest.mark.parametrize("fixture_usuario", ["usuario_tecnico", "usuario_vendedor", "usuario_financeiro"])
def test_nao_admin_nao_salva(client, login_como, request, fixture_usuario):
    login_como(client, request.getfixturevalue(fixture_usuario))
    assert client.put("/api/dados-loja", json=PAYLOAD).status_code == 403


def test_put_sem_login_retorna_401(client):
    assert client.put("/api/dados-loja", json=PAYLOAD).status_code == 401


def test_nome_fantasia_obrigatorio(client, login_como, usuario_admin):
    login_como(client, usuario_admin)
    resp = client.put("/api/dados-loja", json={**PAYLOAD, "nome_fantasia": "   "})
    assert resp.status_code == 400
    assert "Nome fantasia" in resp.get_json()["erro"]


def test_campo_acima_do_limite_rejeitado(client, login_como, usuario_admin):
    login_como(client, usuario_admin)
    resp = client.put("/api/dados-loja", json={**PAYLOAD, "termos_garantia": "x" * 4001})
    assert resp.status_code == 400


def test_campo_com_tipo_invalido_rejeitado(client, login_como, usuario_admin):
    login_como(client, usuario_admin)
    resp = client.put("/api/dados-loja", json={**PAYLOAD, "cnpj": 123})
    assert resp.status_code == 400


def test_segundo_salvamento_atualiza_a_mesma_linha(client, login_como, usuario_admin):
    login_como(client, usuario_admin)
    client.put("/api/dados-loja", json=PAYLOAD)
    client.put("/api/dados-loja", json={**PAYLOAD, "nome_fantasia": "Nome Novo", "cnpj": ""})

    conn = _app.conectar()
    try:
        linhas = conn.execute("SELECT id, nome_fantasia, cnpj FROM dados_loja").fetchall()
    finally:
        conn.close()
    assert linhas == [(1, "Nome Novo", "")]


def test_salvamento_registra_auditoria(client, login_como, usuario_admin):
    login_como(client, usuario_admin)
    client.put("/api/dados-loja", json=PAYLOAD)

    conn = _app.conectar()
    try:
        row = conn.execute(
            "SELECT usuario_id, acao FROM audit_log WHERE entidade='dados_loja' ORDER BY id DESC LIMIT 1"
        ).fetchone()
    finally:
        conn.close()
    assert row == (usuario_admin["id"], "update")
