"""
Termo de Garantia único (BR-105, docs/engineering/plans/PLAN-termo-unico-garantia.md).

O Tipo de Garantia é o Termo de Garantia: nome + prazo (meses) + texto. Na OS se
escolhe um termo para a OS inteira (`tipo_garantia_id`): o prazo vale para todos
os reparos (snapshot por linha, BR-062) e o texto sai no comprovante de entrega.
Sem texto no termo, o comprovante usa o texto padrão de Dados da Loja.
"""

import pytest

import app as _app


def _inserir_tipo(nome="Garantia 3 meses", meses=3, texto="Cobre o serviço por 3 meses.", ativo=1):
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_garantia (nome, duracao_meses, texto, ativo) VALUES (?, ?, ?, ?)",
            (nome, meses, texto, ativo),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


@pytest.fixture(autouse=True)
def _loja_e_limpeza():
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute(
            "INSERT INTO dados_loja (id, nome_fantasia, termos_entrada, termos_garantia) "
            "VALUES (1, 'Loja Termos Teste', 'Entrada padrão.', 'Garantia padrão da loja.')"
        )
        conn.commit()
    finally:
        conn.close()
    criados = []
    yield criados
    conn = _app.conectar()
    try:
        conn.execute("UPDATE os SET termo_garantia_id=NULL, termo_garantia_nome=NULL, termo_garantia_texto=NULL")
        conn.execute("DELETE FROM dados_loja")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture
def termo_3m():
    tipo_id = _inserir_tipo()
    yield tipo_id
    _apagar_tipo(tipo_id)


@pytest.fixture
def termo_6m():
    tipo_id = _inserir_tipo("Garantia 6 meses", 6, "Cobre o serviço por 6 meses.")
    yield tipo_id
    _apagar_tipo(tipo_id)


def _apagar_tipo(tipo_id):
    conn = _app.conectar()
    try:
        conn.execute(
            "UPDATE os_reparos SET tipo_garantia_id=NULL, garantia_nome=NULL, garantia_duracao_meses=NULL, "
            "garantia_data_inicio=NULL, garantia_data_fim=NULL WHERE tipo_garantia_id=?",
            (tipo_id,),
        )
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (tipo_id,))
        conn.commit()
    finally:
        conn.close()


def _snapshot(os_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT termo_garantia_id, termo_garantia_nome, termo_garantia_texto FROM os WHERE id=?", (os_id,)
        ).fetchone()
    finally:
        conn.close()


def _garantias_reparos(os_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            "SELECT reparo_id, tipo_garantia_id, garantia_duracao_meses, garantia_data_inicio, garantia_data_fim "
            "FROM os_reparos WHERE os_id=? ORDER BY reparo_id",
            (os_id,),
        ).fetchall()
    finally:
        conn.close()


def _finalizar(client, os_id, tipo_garantia_id):
    return client.patch(
        f"/api/ordens/{os_id}/status", json={"status": "Finalizado", "tipo_garantia_id": tipo_garantia_id}
    )


def _termos_do_documento(client, os_id):
    resp = client.get(f"/api/ordens/{os_id}/documento?tipo=entrega")
    assert resp.status_code == 200, resp.get_json()
    return resp.get_json()["documento"]["termos"]


class TestCadastro:
    def test_admin_cria_e_edita_termo_com_texto(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/tipos-garantia", json={"nome": "Troca de tela", "duracao_meses": 3, "texto": " T. "})
        assert resp.status_code == 201
        tipo_id = resp.get_json()["id"]
        try:
            item = next(t for t in client.get("/api/tipos-garantia").get_json()["items"] if t["id"] == tipo_id)
            assert item["texto"] == "T."

            resp = client.put(
                f"/api/tipos-garantia/{tipo_id}", json={"nome": "Troca de tela", "duracao_meses": 3, "texto": "Novo."}
            )
            assert resp.status_code == 200
            item = next(t for t in client.get("/api/tipos-garantia").get_json()["items"] if t["id"] == tipo_id)
            assert item["texto"] == "Novo."
        finally:
            _apagar_tipo(tipo_id)

    def test_put_sem_texto_mantem_o_texto(self, client, login_como, usuario_admin, termo_3m):
        login_como(client, usuario_admin)
        resp = client.put(f"/api/tipos-garantia/{termo_3m}", json={"nome": "Renomeado", "duracao_meses": 3})
        assert resp.status_code == 200
        item = next(t for t in client.get("/api/tipos-garantia").get_json()["items"] if t["id"] == termo_3m)
        assert item["texto"] == "Cobre o serviço por 3 meses."

    def test_texto_acima_do_limite_400(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        resp = client.post("/api/tipos-garantia", json={"nome": "X", "duracao_meses": 1, "texto": "a" * 4001})
        assert resp.status_code == 400

    def test_cadastro_separado_de_termos_nao_existe_mais(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)
        assert client.get("/api/termos-garantia").status_code == 404


class TestFinalizacao:
    def test_um_termo_aplica_prazo_a_todos_os_reparos_e_texto_ao_documento(
        self, client, login_como, usuario_tecnico, criar_os, termo_3m
    ):
        from tests.conftest import _reparo_ids_existentes

        reparos = _reparo_ids_existentes(2)
        login_como(client, usuario_tecnico)
        os_id = criar_os(reparo_ids=reparos)
        assert _finalizar(client, os_id, termo_3m).status_code == 200

        linhas = _garantias_reparos(os_id)
        assert len(linhas) == 2
        assert all(linha[1] == termo_3m and linha[2] == 3 and linha[4] for linha in linhas)
        assert _snapshot(os_id) == (termo_3m, "Garantia 3 meses", "Cobre o serviço por 3 meses.")
        assert _termos_do_documento(client, os_id) == "Cobre o serviço por 3 meses."
        ordem = client.get(f"/api/ordens/{os_id}").get_json()["ordem"]
        assert ordem["termo_garantia"] == {"id": termo_3m, "nome": "Garantia 3 meses"}

    def test_termo_sem_texto_usa_texto_padrao_da_loja(self, client, login_como, usuario_tecnico, criar_os):
        tipo_id = _inserir_tipo("Sem texto", 3, "")
        try:
            login_como(client, usuario_tecnico)
            os_id = criar_os()
            assert _finalizar(client, os_id, tipo_id).status_code == 200
            assert _termos_do_documento(client, os_id) == "Garantia padrão da loja."
        finally:
            _apagar_tipo(tipo_id)

    def test_sem_termo_recusa_quando_ha_reparo(self, client, login_como, usuario_tecnico, criar_os):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})
        assert resp.status_code == 400
        assert client.get(f"/api/ordens/{os_id}").get_json()["ordem"]["status"] == "Em andamento"

    @pytest.mark.parametrize("valor", ["abc", True, 999999])
    def test_termo_invalido_recusa(self, client, login_como, usuario_tecnico, criar_os, valor):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        assert _finalizar(client, os_id, valor).status_code == 400

    def test_termo_inativo_recusa(self, client, login_como, usuario_tecnico, criar_os):
        tipo_id = _inserir_tipo("Inativo", 3, "x", ativo=0)
        try:
            login_como(client, usuario_tecnico)
            os_id = criar_os()
            assert _finalizar(client, os_id, tipo_id).status_code == 400
        finally:
            _apagar_tipo(tipo_id)

    def test_editar_termo_depois_nao_altera_os_finalizada(
        self, client, login_como, usuario_admin, criar_os, termo_3m
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _finalizar(client, os_id, termo_3m)
        client.put(f"/api/tipos-garantia/{termo_3m}", json={"nome": "Outro", "duracao_meses": 9, "texto": "Novo."})
        assert _termos_do_documento(client, os_id) == "Cobre o serviço por 3 meses."
        assert _garantias_reparos(os_id)[0][2] == 3

    def test_finalizar_via_put(self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, termo_3m):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        payload = payload_os_valido(status="Finalizado", tipo_garantia_id=termo_3m)
        payload.pop("garantias")
        resp = client.put(f"/api/ordens/{os_id}", json=payload)
        assert resp.status_code == 200, resp.get_json()
        assert _snapshot(os_id)[0] == termo_3m
        assert _garantias_reparos(os_id)[0][1] == termo_3m

    def test_mapa_antigo_por_reparo_continua_aceito_sem_termo_na_os(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, termo_3m
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os()
        resp = client.patch(
            f"/api/ordens/{os_id}/status",
            json={"status": "Finalizado", "garantias": {str(reparo_padrao_id): termo_3m}},
        )
        assert resp.status_code == 200
        assert _snapshot(os_id) == (None, None, None)
        assert _termos_do_documento(client, os_id) == "Garantia padrão da loja."

    def test_cancelar_zera_o_termo(self, client, login_como, usuario_admin, criar_os, termo_3m):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _finalizar(client, os_id, termo_3m)
        assert client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"}).status_code == 200
        assert _snapshot(os_id) == (None, None, None)


class TestTrocaPorAdmin:
    def test_troca_regrava_termo_e_prazo_dos_reparos(
        self, client, login_como, usuario_admin, criar_os, termo_3m, termo_6m
    ):
        login_como(client, usuario_admin)
        os_id = criar_os()
        _finalizar(client, os_id, termo_3m)
        inicio_antes = _garantias_reparos(os_id)[0][3]

        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"tipo_garantia_id": termo_6m})
        assert resp.status_code == 200
        assert resp.get_json()["termo_garantia"] == {"id": termo_6m, "nome": "Garantia 6 meses"}
        linha = _garantias_reparos(os_id)[0]
        assert linha[1] == termo_6m and linha[2] == 6 and linha[3] == inicio_antes
        assert _termos_do_documento(client, os_id) == "Cobre o serviço por 6 meses."

        conn = _app.conectar()
        try:
            acoes = {
                r[0]
                for r in conn.execute(
                    "SELECT acao FROM audit_log WHERE entidade IN ('os', 'os_reparo') AND entidade_id=?", (os_id,)
                ).fetchall()
            }
        finally:
            conn.close()
        assert {"termo_garantia_alterado", "garantia_alterada"} <= acoes

    def test_troca_cobre_reparo_sem_garantia_a_partir_da_finalizacao(
        self, client, login_como, usuario_admin, criar_os, dois_reparos_ids, termo_3m, termo_6m
    ):
        """KI-078 -- OS finalizada com um reparo sem garantia (perdida antes do
        hotfix #112, ou OS antiga): trocar o termo vale para todos os reparos; o
        sem garantia conta da data de finalização, o com garantia mantém o início."""
        login_como(client, usuario_admin)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(reparo_ids=[reparo_a, reparo_b])
        _finalizar(client, os_id, termo_3m)
        conn = _app.conectar()
        try:
            conn.execute("UPDATE os SET data_finalizado='2026-01-10' WHERE id=?", (os_id,))
            conn.execute("UPDATE os_reparos SET garantia_data_inicio='2026-01-05' WHERE os_id=?", (os_id,))
            conn.execute(
                "UPDATE os_reparos SET tipo_garantia_id=NULL, garantia_nome=NULL, garantia_duracao_meses=NULL, "
                "garantia_data_inicio=NULL, garantia_data_fim=NULL WHERE os_id=? AND reparo_id=?",
                (os_id, reparo_b),
            )
            conn.commit()
        finally:
            conn.close()

        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"tipo_garantia_id": termo_6m})
        assert resp.status_code == 200

        linhas = {r[0]: r for r in _garantias_reparos(os_id)}
        assert linhas[reparo_a][1:] == (termo_6m, 6, "2026-01-05", "2026-07-05")
        assert linhas[reparo_b][1:] == (termo_6m, 6, "2026-01-10", "2026-07-10")

    def test_sem_termo_400(self, client, login_como, usuario_admin, criar_os):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Finalizado")
        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"tipo_garantia_id": None})
        assert resp.status_code == 400

    def test_nao_admin_403(self, client, login_como, usuario_tecnico, criar_os, termo_3m):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado")
        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"tipo_garantia_id": termo_3m})
        assert resp.status_code == 403

    def test_os_nao_finalizada_409(self, client, login_como, usuario_admin, criar_os, termo_3m):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento")
        resp = client.patch(f"/api/ordens/{os_id}/termo-garantia", json={"tipo_garantia_id": termo_3m})
        assert resp.status_code == 409

    def test_os_inexistente_404(self, client, login_como, usuario_admin, termo_3m):
        login_como(client, usuario_admin)
        resp = client.patch("/api/ordens/999999/termo-garantia", json={"tipo_garantia_id": termo_3m})
        assert resp.status_code == 404
