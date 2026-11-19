"""
P1-2 (QA 2026-11-12) -- a sessão precisa refletir o estado atual do usuário no banco.

Antes, `usuario_id` e `usuario_perfil` eram gravados no cookie no login e nunca mais
conferidos: um usuário desativado, excluído ou rebaixado continuava com o acesso antigo
até a sessão expirar. Cada requisição autenticada agora relê `ativo` e `perfil` do banco.
"""

import app as _app


def _atualizar_usuario(user_id, **campos):
    sets = ", ".join(f"{k}=?" for k in campos)
    conn = _app.conectar()
    try:
        conn.execute(f"UPDATE usuarios SET {sets} WHERE id=?", (*campos.values(), user_id))
        conn.commit()
    finally:
        conn.close()


def _excluir_usuario(user_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM usuarios WHERE id=?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def _logar(app, login_como, usuario):
    c = app.test_client()
    assert login_como(c, usuario).status_code == 200
    return c


class TestUsuarioDesativado:
    def test_desativado_perde_acesso_na_proxima_requisicao(self, app, login_como, usuario_tecnico):
        c = _logar(app, login_como, usuario_tecnico)
        assert c.get("/api/ordens").status_code == 200

        _atualizar_usuario(usuario_tecnico["id"], ativo=0)

        assert c.get("/api/ordens").status_code == 401
        assert c.get("/api/auth/me").status_code == 401

    def test_reativar_nao_ressuscita_a_sessao_derrubada(self, app, login_como, usuario_tecnico):
        c = _logar(app, login_como, usuario_tecnico)
        _atualizar_usuario(usuario_tecnico["id"], ativo=0)
        assert c.get("/api/ordens").status_code == 401

        _atualizar_usuario(usuario_tecnico["id"], ativo=1)

        assert c.get("/api/ordens").status_code == 401
        assert login_como(c, usuario_tecnico).status_code == 200
        assert c.get("/api/ordens").status_code == 200

    def test_desativado_pelo_admin_via_api_perde_acesso(self, app, login_como, usuario_admin, usuario_tecnico):
        tecnico = _logar(app, login_como, usuario_tecnico)
        admin = _logar(app, login_como, usuario_admin)

        r = admin.put(
            f"/api/usuarios/{usuario_tecnico['id']}",
            json={"nome": usuario_tecnico["nome"], "perfil": "tecnico", "ativo": False},
        )
        assert r.status_code == 200

        assert tecnico.get("/api/ordens").status_code == 401

    def test_usuario_desativado_nao_consegue_logar_de_novo(self, app, login_como, usuario_tecnico):
        _atualizar_usuario(usuario_tecnico["id"], ativo=0)
        assert login_como(app.test_client(), usuario_tecnico).status_code == 401


class TestUsuarioExcluido:
    def test_excluido_perde_acesso_na_proxima_requisicao(self, app, login_como, usuario_tecnico):
        c = _logar(app, login_como, usuario_tecnico)
        assert c.get("/api/ordens").status_code == 200

        _excluir_usuario(usuario_tecnico["id"])

        assert c.get("/api/ordens").status_code == 401


class TestPerfilAlterado:
    def test_admin_rebaixado_para_vendedor_perde_rotas_de_admin(self, app, login_como, usuario_admin):
        c = _logar(app, login_como, usuario_admin)
        assert c.get("/api/usuarios").status_code == 200

        _atualizar_usuario(usuario_admin["id"], perfil="vendedor")

        assert c.get("/api/usuarios").status_code == 403
        assert (
            c.post("/api/usuarios", json={"nome": "X", "usuario": "x_rebaixado", "senha": "Senha#2026"}).status_code
            == 403
        )
        me = c.get("/api/auth/me")
        assert me.status_code == 200
        assert me.get_json()["usuario"]["perfil"] == "vendedor"

    def test_perfil_alterado_vale_nos_dois_sentidos(self, app, login_como, usuario_tecnico):
        c = _logar(app, login_como, usuario_tecnico)
        payload_estoque = {"descricao": "Peca P1-2", "modelo": "iPhone 13", "valor": 10, "quantidade": 1}
        assert c.post("/api/estoque", json=payload_estoque).status_code == 403

        _atualizar_usuario(usuario_tecnico["id"], perfil="estoque")

        assert c.post("/api/estoque", json=payload_estoque).status_code in (200, 201)
        assert c.post("/api/ordens", json={}).status_code == 403

    def test_rebaixamento_vale_para_rotas_que_leem_o_perfil_direto_da_sessao(self, app, login_como, usuario_admin):
        # Rotas como POST /api/estoque leem session["usuario_perfil"] sem passar por usuario_admin().
        c = _logar(app, login_como, usuario_admin)
        _atualizar_usuario(usuario_admin["id"], perfil="vendedor")

        r = c.post("/api/estoque", json={"descricao": "Peca", "modelo": "iPhone 13", "valor": 10, "quantidade": 1})
        assert r.status_code == 403

    def test_nome_alterado_aparece_no_auth_me(self, app, login_como, usuario_tecnico):
        c = _logar(app, login_como, usuario_tecnico)
        _atualizar_usuario(usuario_tecnico["id"], nome="Nome Novo P1-2")

        assert c.get("/api/auth/me").get_json()["usuario"]["nome"] == "Nome Novo P1-2"

    def test_novo_login_depois_da_alteracao_traz_o_perfil_novo(self, app, login_como, usuario_admin):
        c = _logar(app, login_como, usuario_admin)
        _atualizar_usuario(usuario_admin["id"], perfil="financeiro")
        c.post("/api/auth/logout")

        r = login_como(c, usuario_admin)
        assert r.get_json()["usuario"]["perfil"] == "financeiro"
        assert c.get("/api/usuarios").status_code == 403


class TestUsuarioValidoNaoEhAfetado:
    def test_sessao_valida_continua_funcionando(self, app, login_como, usuario_admin):
        c = _logar(app, login_como, usuario_admin)
        for _ in range(3):
            assert c.get("/api/usuarios").status_code == 200
        me = c.get("/api/auth/me").get_json()["usuario"]
        assert me["perfil"] == "admin"
        assert me["id"] == usuario_admin["id"]

    def test_alterar_outro_usuario_nao_afeta_a_sessao_do_admin(self, app, login_como, usuario_admin, usuario_tecnico):
        admin = _logar(app, login_como, usuario_admin)
        _atualizar_usuario(usuario_tecnico["id"], ativo=0, perfil="vendedor")

        assert admin.get("/api/usuarios").status_code == 200

    def test_sem_sessao_continua_401(self, client):
        assert client.get("/api/ordens").status_code == 401
        assert client.get("/api/auth/me").status_code == 401
