"""
Testes de Garantia de Reparo (V1.5, BR-061 a BR-065,
docs/engineering/plans/PLAN-V1.5-Garantia.md).

Escopo: concluir uma OS (PATCH /api/ordens/<id>/status e PUT /api/ordens/<id>,
as duas rotas que podem levar o status a Finalizado) passa a exigir um Tipo
de Garantia por linha de reparo (os_reparos); correção restrita a `admin`
(PATCH .../reparos/<reparo_id>/garantia) e histórico; cancelamento
pós-conclusão zera a garantia concedida, com auditoria.
"""

import uuid

import app as _app


def _criar_tipo_garantia(**overrides):
    dados = {"nome": f"Tipo Garantia Reparo Teste {uuid.uuid4().hex[:8]}", "duracao_meses": 6, "ativo": 1}
    dados.update(overrides)
    conn = _app.conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tipos_garantia (nome, duracao_meses, ativo) VALUES (?, ?, ?)",
            (dados["nome"], dados["duracao_meses"], dados["ativo"]),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def _remover_tipo_garantia(tipo_garantia_id):
    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM tipos_garantia WHERE id=?", (tipo_garantia_id,))
        conn.commit()
    finally:
        conn.close()


def _linha_os_reparo(os_id, reparo_id):
    conn = _app.conectar()
    try:
        return conn.execute(
            """
            SELECT tipo_garantia_id, garantia_nome, garantia_duracao_meses,
                   garantia_data_inicio, garantia_data_fim
            FROM os_reparos WHERE os_id=? AND reparo_id=?
            """,
            (os_id, reparo_id),
        ).fetchone()
    finally:
        conn.close()


def _finalizar(client, os_id, reparo_id, tipo_garantia_id):
    return client.patch(
        f"/api/ordens/{os_id}/status",
        json={"status": "Finalizado", "garantias": {str(reparo_id): tipo_garantia_id}},
    )


class TestGarantiaDeReparoViaStatus:
    def test_finalizar_sem_garantia_retorna_400(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})
        assert resp.status_code == 400

    def test_finalizar_com_tipo_inexistente_retorna_400(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])

        resp = _finalizar(client, os_id, reparo_padrao_id, 999999)
        assert resp.status_code == 400

    def test_finalizar_com_tipo_inativo_retorna_400(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        tipo_id = _criar_tipo_garantia(ativo=0)
        try:
            login_como(client, usuario_tecnico)
            os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
            resp = _finalizar(client, os_id, reparo_padrao_id, tipo_id)
            assert resp.status_code == 400
        finally:
            _remover_tipo_garantia(tipo_id)

    def test_finalizar_com_garantia_grava_snapshot(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])

        resp = _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)
        assert resp.status_code == 200

        linha = _linha_os_reparo(os_id, reparo_padrao_id)
        assert linha[0] == tipo_garantia_padrao_id
        assert linha[1] == "Garantia Teste Padrão (Reparo)"
        assert linha[2] == 12
        assert linha[3] is not None and linha[4] is not None
        assert linha[4] > linha[3]

    def test_multiplos_reparos_com_garantias_diferentes(
        self, client, login_como, usuario_tecnico, criar_os, dois_reparos_ids
    ):
        """BR-062 -- cada linha de os_reparos mantém sua própria garantia,
        não existe uma "garantia da OS" agregada."""
        tipo_a = _criar_tipo_garantia(nome="Garantia A", duracao_meses=3)
        tipo_b = _criar_tipo_garantia(nome="Garantia B", duracao_meses=9)
        try:
            login_como(client, usuario_tecnico)
            reparo_a, reparo_b = dois_reparos_ids
            os_id = criar_os(status="Em andamento", reparo_ids=[reparo_a, reparo_b])

            resp = client.patch(
                f"/api/ordens/{os_id}/status",
                json={
                    "status": "Finalizado",
                    "garantias": {str(reparo_a): tipo_a, str(reparo_b): tipo_b},
                },
            )
            assert resp.status_code == 200

            linha_a = _linha_os_reparo(os_id, reparo_a)
            linha_b = _linha_os_reparo(os_id, reparo_b)
            assert linha_a[2] == 3
            assert linha_b[2] == 9
            assert linha_a[4] != linha_b[4]
        finally:
            _remover_tipo_garantia(tipo_a)
            _remover_tipo_garantia(tipo_b)

    def test_reasserir_finalizado_nao_exige_garantia_de_novo(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id
    ):
        """BR-061 exige garantia só na transição PARA Finalizado -- reenviar
        o mesmo status (OS já finalizada) não é uma transição."""
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_padrao_id])

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Finalizado"})
        assert resp.status_code == 200


class TestGarantiaDeReparoViaEdicaoCompleta:
    """BR-061 também se aplica ao formulário completo de edição (PUT), não
    só ao botão de status dedicado -- ambos podem levar a OS a Finalizado."""

    def test_finalizar_via_put_sem_garantia_retorna_400(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, reparo_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])

        payload = payload_os_valido(status="Finalizado", reparo_ids=[reparo_padrao_id], garantias={})
        resp = client.put(f"/api/ordens/{os_id}", json=payload)
        assert resp.status_code == 400

    def test_finalizar_via_put_grava_snapshot(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, reparo_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])

        payload = payload_os_valido(status="Finalizado", reparo_ids=[reparo_padrao_id])
        resp = client.put(f"/api/ordens/{os_id}", json=payload)
        assert resp.status_code == 200

        linha = _linha_os_reparo(os_id, reparo_padrao_id)
        assert linha[0] is not None

    def test_editar_os_ja_finalizada_preserva_garantia_concedida(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, reparo_padrao_id
    ):
        """Regressão -- `salvar_reparos_os()` fazia DELETE+INSERT cego de
        `os_reparos`; qualquer edição via PUT apagava silenciosamente a
        Garantia de Reparo já concedida, mesmo sem tocar status/reparos."""
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        client.put(
            f"/api/ordens/{os_id}", json=payload_os_valido(status="Finalizado", reparo_ids=[reparo_padrao_id])
        )
        linha_antes = _linha_os_reparo(os_id, reparo_padrao_id)
        assert linha_antes[0] is not None

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(
                status="Finalizado", reparo_ids=[reparo_padrao_id], observacoes="Editado depois de concluído"
            ),
        )
        assert resp.status_code == 200

        assert _linha_os_reparo(os_id, reparo_padrao_id) == linha_antes


def _fixar_data_finalizacao(os_id, data_ymd):
    """Leva a OS e a garantia já concedida para uma data de finalização conhecida,
    para provar que a contagem parte dela e não do dia do teste."""
    conn = _app.conectar()
    try:
        conn.execute("UPDATE os SET data_finalizado=? WHERE id=?", (data_ymd, os_id))
        conn.execute(
            "UPDATE os_reparos SET garantia_data_inicio=?, garantia_data_fim=date(?, '+12 months') "
            "WHERE os_id=? AND tipo_garantia_id IS NOT NULL",
            (data_ymd, data_ymd, os_id),
        )
        conn.commit()
    finally:
        conn.close()


def _acoes_auditoria_os_reparo(os_id):
    conn = _app.conectar()
    try:
        return [
            r[0]
            for r in conn.execute(
                "SELECT acao FROM audit_log WHERE entidade='os_reparo' AND entidade_id=?", (os_id,)
            ).fetchall()
        ]
    finally:
        conn.close()


class TestReparoNovoEmOsFinalizadaHerdaGarantia:
    """KI-078 -- trocar ou acrescentar reparo numa OS já finalizada apagava a
    linha antiga (com a garantia) e criava a nova sem garantia, em silêncio: o
    comprovante de entrega saía com "Sem garantia registrada". O reparo novo
    herda a garantia que a OS já tem (BR-105), contada da data de finalização."""

    def test_trocar_reparo_herda_garantia_da_data_de_finalizacao(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, dois_reparos_ids,
        tipo_garantia_padrao_id,
    ):  # fmt: skip
        login_como(client, usuario_tecnico)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_a])
        assert _finalizar(client, os_id, reparo_a, tipo_garantia_padrao_id).status_code == 200
        _fixar_data_finalizacao(os_id, "2026-01-10")
        linha_a = _linha_os_reparo(os_id, reparo_a)

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(status="Finalizado", reparo_ids=[reparo_b], garantias={}),
        )
        assert resp.status_code == 200

        assert _linha_os_reparo(os_id, reparo_a) is None
        assert _linha_os_reparo(os_id, reparo_b) == linha_a
        assert _linha_os_reparo(os_id, reparo_b)[3] == "2026-01-10"
        assert "garantia_concedida" in _acoes_auditoria_os_reparo(os_id)

    def test_acrescentar_reparo_mantem_o_existente_e_herda(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, dois_reparos_ids,
        tipo_garantia_padrao_id,
    ):  # fmt: skip
        login_como(client, usuario_tecnico)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_a])
        _finalizar(client, os_id, reparo_a, tipo_garantia_padrao_id)
        _fixar_data_finalizacao(os_id, "2026-01-10")
        linha_a = _linha_os_reparo(os_id, reparo_a)

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(status="Finalizado", reparo_ids=[reparo_a, reparo_b], garantias={}),
        )
        assert resp.status_code == 200

        assert _linha_os_reparo(os_id, reparo_a) == linha_a
        assert _linha_os_reparo(os_id, reparo_b) == linha_a

    def test_os_finalizada_sem_garantia_continua_sem(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, dois_reparos_ids
    ):
        """OS finalizada sem garantia concedida (anterior à V1.5 ou importada,
        exceção da BR-061): nada a herdar -- nunca inventa uma garantia."""
        login_como(client, usuario_tecnico)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_a])

        resp = client.put(
            f"/api/ordens/{os_id}",
            json=payload_os_valido(status="Finalizado", reparo_ids=[reparo_b], garantias={}),
        )
        assert resp.status_code == 200
        assert _linha_os_reparo(os_id, reparo_b) == (None, None, None, None, None)


class TestCancelamentoPosConclusaoZeraGarantia:
    def test_cancelar_via_status_zera_garantia_com_auditoria(
        self, client, login_como, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        resp = client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"})
        assert resp.status_code == 200

        assert _linha_os_reparo(os_id, reparo_padrao_id) == (None, None, None, None, None)

        historico = client.get(
            f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/historico-garantia"
        ).get_json()["historico"]
        assert any(e["acao"] == "garantia_alterada" for e in historico)

    def test_cancelar_via_put_zera_garantia_com_auditoria(
        self, client, login_como, usuario_tecnico, criar_os, payload_os_valido, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_tecnico)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        resp = client.put(f"/api/ordens/{os_id}", json=payload_os_valido(status="Cancelado", reparo_ids=[reparo_padrao_id]))
        assert resp.status_code == 200

        assert _linha_os_reparo(os_id, reparo_padrao_id) == (None, None, None, None, None)


class TestCorrigirGarantiaReparo:
    def test_admin_corrige_com_sucesso(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        tipo_novo = _criar_tipo_garantia(nome="Garantia Estendida", duracao_meses=24)
        try:
            resp = client.patch(
                f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia",
                json={"tipo_garantia_id": tipo_novo},
            )
            assert resp.status_code == 200
            linha = _linha_os_reparo(os_id, reparo_padrao_id)
            assert linha[0] == tipo_novo
            assert linha[2] == 24
        finally:
            _remover_tipo_garantia(tipo_novo)

    def test_corrigir_reparo_sem_garantia_conta_da_data_de_finalizacao(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        """KI-078 -- reparo de OS finalizada que ficou sem garantia: a correção
        conta da data de finalização da OS (BR-062), não do dia da correção."""
        login_como(client, usuario_admin)
        os_id = criar_os(status="Finalizado", reparo_ids=[reparo_padrao_id])
        _fixar_data_finalizacao(os_id, "2026-01-10")

        resp = client.patch(
            f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia",
            json={"tipo_garantia_id": tipo_garantia_padrao_id},
        )
        assert resp.status_code == 200
        linha = _linha_os_reparo(os_id, reparo_padrao_id)
        assert linha[3] == "2026-01-10"
        assert linha[4] == "2027-01-10"

    def test_vendedor_nao_pode_corrigir(
        self, client, login_como, usuario_admin, usuario_vendedor, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        login_como(client, usuario_vendedor)
        resp = client.patch(
            f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia",
            json={"tipo_garantia_id": tipo_garantia_padrao_id},
        )
        assert resp.status_code == 403

    def test_tecnico_nao_pode_corrigir(
        self, client, login_como, usuario_admin, usuario_tecnico, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        """Diferente de finalizar a OS (admin/tecnico), corrigir a garantia é
        mais restrito -- só admin, mesma assimetria da Vendas (BR-059)."""
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        login_como(client, usuario_tecnico)
        resp = client.patch(
            f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia",
            json={"tipo_garantia_id": tipo_garantia_padrao_id},
        )
        assert resp.status_code == 403

    def test_corrigir_com_tipo_invalido_retorna_400(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        resp = client.patch(
            f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia",
            json={"tipo_garantia_id": 999999},
        )
        assert resp.status_code == 400

    def test_corrigir_em_os_cancelada_e_rejeitado(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)
        client.patch(f"/api/ordens/{os_id}/status", json={"status": "Cancelado"})

        resp = client.patch(
            f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia",
            json={"tipo_garantia_id": tipo_garantia_padrao_id},
        )
        assert resp.status_code == 400

    def test_corrigir_reparo_inexistente_na_os_retorna_404(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        resp = client.patch(
            f"/api/ordens/{os_id}/reparos/999999/garantia",
            json={"tipo_garantia_id": tipo_garantia_padrao_id},
        )
        assert resp.status_code == 404

    def test_corrigir_duas_vezes_gera_dois_eventos_de_correcao(
        self, client, login_como, usuario_admin, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        """O histórico inclui também o evento de concessão original
        (`garantia_concedida`, gravado na conclusão da OS) -- este teste
        confere só os eventos de correção (`garantia_alterada`)."""
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        tipo_a = _criar_tipo_garantia(nome="A", duracao_meses=3)
        tipo_b = _criar_tipo_garantia(nome="B", duracao_meses=6)
        try:
            client.patch(f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia", json={"tipo_garantia_id": tipo_a})
            client.patch(f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/garantia", json={"tipo_garantia_id": tipo_b})

            historico = client.get(
                f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/historico-garantia"
            ).get_json()["historico"]
            assert len(historico) == 3
            correcoes = [e for e in historico if e["acao"] == "garantia_alterada"]
            concessoes = [e for e in historico if e["acao"] == "garantia_concedida"]
            assert len(correcoes) == 2
            assert len(concessoes) == 1
        finally:
            _remover_tipo_garantia(tipo_a)
            _remover_tipo_garantia(tipo_b)

    def test_historico_aberto_a_qualquer_autenticado(
        self, client, login_como, usuario_admin, usuario_vendedor, criar_os, reparo_padrao_id, tipo_garantia_padrao_id
    ):
        login_como(client, usuario_admin)
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_padrao_id])
        _finalizar(client, os_id, reparo_padrao_id, tipo_garantia_padrao_id)

        login_como(client, usuario_vendedor)
        resp = client.get(f"/api/ordens/{os_id}/reparos/{reparo_padrao_id}/historico-garantia")
        assert resp.status_code == 200

    def test_historico_nao_mistura_linhas_de_reparo_diferentes(
        self, client, login_como, usuario_admin, criar_os, dois_reparos_ids, tipo_garantia_padrao_id
    ):
        """Prova de que o filtro por reparo_id (embutido no JSON de
        auditoria, já que os_reparos não tem id substituto) funciona: corrigir
        a garantia de um reparo não aparece no histórico do outro."""
        login_como(client, usuario_admin)
        reparo_a, reparo_b = dois_reparos_ids
        os_id = criar_os(status="Em andamento", reparo_ids=[reparo_a, reparo_b])
        client.patch(
            f"/api/ordens/{os_id}/status",
            json={
                "status": "Finalizado",
                "garantias": {str(reparo_a): tipo_garantia_padrao_id, str(reparo_b): tipo_garantia_padrao_id},
            },
        )

        tipo_novo = _criar_tipo_garantia(duracao_meses=18)
        try:
            client.patch(f"/api/ordens/{os_id}/reparos/{reparo_a}/garantia", json={"tipo_garantia_id": tipo_novo})

            historico_a = client.get(f"/api/ordens/{os_id}/reparos/{reparo_a}/historico-garantia").get_json()["historico"]
            historico_b = client.get(f"/api/ordens/{os_id}/reparos/{reparo_b}/historico-garantia").get_json()["historico"]
            # Ambos ganham 1 evento de concessão na conclusão da OS; só `a` recebe a correção.
            assert len(historico_a) == 2
            assert len(historico_b) == 1
        finally:
            _remover_tipo_garantia(tipo_novo)
