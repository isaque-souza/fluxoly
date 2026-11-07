"""
KI-043 (2026-11-06) -- os destinos externos de backup (Google Drive, e-mail) foram removidos. O backup
fica só no diretório local. Estes testes substituem `test_backup_contencao_externa.py`, que cobria a
contenção (`EXTERNAL_BACKUP_DESTINATIONS_ENABLED`) que deixou de existir junto com os destinos.
"""

import os
import sqlite3

import fluxoly_config
import fluxoly_storage


def _conectar_fake(caminho_origem):
    def conectar():
        return sqlite3.connect(caminho_origem)

    return conectar


def _criar_banco_origem(tmp_path):
    origem = tmp_path / "origem.db"
    conn = sqlite3.connect(origem)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (42)")
    conn.commit()
    conn.close()
    return _conectar_fake(str(origem))


class TestCriarBackupSomenteLocal:
    def test_cria_arquivo_so_no_diretorio_local(self, tmp_path):
        backup_dir = tmp_path / "backups"
        conectar = _criar_banco_origem(tmp_path)

        info = fluxoly_storage.criar_backup(str(backup_dir), conectar, nome_arquivo="backup-teste.db")

        assert info == {"nome": "backup-teste.db", "destino_local": str(backup_dir / "backup-teste.db")}
        assert os.listdir(backup_dir) == ["backup-teste.db"]
        copia = sqlite3.connect(backup_dir / "backup-teste.db")
        try:
            assert copia.execute("SELECT x FROM t").fetchone() == (42,)
        finally:
            copia.close()

    def test_backup_diario_cria_uma_vez_por_dia(self, tmp_path):
        backup_dir = tmp_path / "backups"
        conectar = _criar_banco_origem(tmp_path)

        primeiro = fluxoly_storage.executar_backup_diario_automatico(str(backup_dir), conectar)
        segundo = fluxoly_storage.executar_backup_diario_automatico(str(backup_dir), conectar)

        assert primeiro is not None and primeiro["nome"].startswith("backup-auto-")
        assert segundo is None
        assert len(os.listdir(backup_dir)) == 1

    def test_retencao_mantem_so_os_mais_recentes_no_diretorio_local(self, tmp_path):
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        for dia in range(1, 6):
            (backup_dir / f"backup-auto-202601{dia:02d}.db").write_bytes(b"")
        (backup_dir / "backup-manual.db").write_bytes(b"")

        fluxoly_storage.aplicar_retencao_backups_automaticos(str(backup_dir), limite=2)

        assert sorted(os.listdir(backup_dir)) == [
            "backup-auto-20260104.db",
            "backup-auto-20260105.db",
            "backup-manual.db",
        ]


class TestDestinosExternosRemovidos:
    def test_storage_nao_tem_mais_funcoes_de_drive_nem_email(self):
        for nome in ("enviar_backup_email", "diretorio_google_drive_disponivel", "garantir_pasta_backup_google_drive"):
            assert not hasattr(fluxoly_storage, nome), nome

    def test_config_nao_tem_mais_destinos_externos(self):
        for nome in (
            "EXTERNAL_BACKUP_DESTINATIONS_ENABLED",
            "GOOGLE_DRIVE_BACKUP_DIR",
            "BACKUP_EMAIL_REMETENTE",
            "BACKUP_EMAIL_SENHA_APP",
            "BACKUP_EMAIL_DESTINO",
        ):
            assert not hasattr(fluxoly_config, nome), nome

    def test_api_criar_backup_responde_so_o_nome_do_arquivo(self, client, login_como, usuario_admin):
        login_como(client, usuario_admin)

        resp = client.post("/api/backup/criar", json={})

        assert resp.status_code == 200
        corpo = resp.get_json()
        assert corpo["ok"] is True and corpo["arquivo"]
        assert "destino_drive" not in corpo and "erro_drive" not in corpo
        os.remove(os.path.join(fluxoly_config.BACKUP_DIR, corpo["arquivo"]))
