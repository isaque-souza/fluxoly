"""
ADR-015 -- backup do banco no hook `pre-update` do Watchtower (`scripts/backup_pre_update.py`).
Nunca toca `database.db`: cada teste usa um banco e um diretório de backup em `tmp_path`.
"""

import importlib.util
import os
import sqlite3
from datetime import datetime
from pathlib import Path

import fluxoly_storage

_SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "backup_pre_update.py"
_spec = importlib.util.spec_from_file_location("backup_pre_update", _SCRIPT)
backup_pre_update = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(backup_pre_update)


def _criar_banco(tmp_path):
    caminho = tmp_path / "database.db"
    conn = sqlite3.connect(caminho)
    conn.execute("CREATE TABLE t (x INTEGER)")
    conn.execute("INSERT INTO t VALUES (7)")
    conn.commit()
    conn.close()
    return str(caminho)


class TestBackupPreUpdate:
    def test_copia_o_banco_com_prefixo_proprio(self, tmp_path):
        db = _criar_banco(tmp_path)
        backup_dir = tmp_path / "backups"

        codigo = backup_pre_update.executar(db, str(backup_dir), agora=datetime(2026, 11, 10, 14, 30, 5))

        assert codigo == 0
        assert os.listdir(backup_dir) == ["backup-pre-update-20261110-143005.db"]
        copia = sqlite3.connect(backup_dir / "backup-pre-update-20261110-143005.db")
        try:
            assert copia.execute("SELECT x FROM t").fetchone() == (7,)
        finally:
            copia.close()

    def test_sem_banco_nao_copia_e_libera_a_atualizacao(self, tmp_path):
        backup_dir = tmp_path / "backups"

        codigo = backup_pre_update.executar(str(tmp_path / "nao-existe.db"), str(backup_dir))

        assert codigo == 0
        assert not backup_dir.exists()

    def test_falha_na_copia_adia_a_atualizacao(self, tmp_path, monkeypatch):
        db = _criar_banco(tmp_path)

        def falhar(*args, **kwargs):
            raise OSError("disco cheio")

        monkeypatch.setattr(backup_pre_update, "criar_backup", falhar)

        codigo = backup_pre_update.executar(db, str(tmp_path / "backups"))

        assert codigo == backup_pre_update.EX_TEMPFAIL == 75

    def test_retencao_so_apaga_os_mais_antigos_do_proprio_prefixo(self, tmp_path):
        db = _criar_banco(tmp_path)
        backup_dir = tmp_path / "backups"
        backup_dir.mkdir()
        (backup_dir / "backup-auto-20260101.db").write_bytes(b"")
        (backup_dir / "backup-manual.db").write_bytes(b"")

        for i in range(backup_pre_update.LIMITE + 3):
            backup_pre_update.executar(db, str(backup_dir), agora=datetime(2026, 11, 1, 0, 0, i))

        pre_update = sorted(n for n in os.listdir(backup_dir) if n.startswith("backup-pre-update-"))
        assert len(pre_update) == backup_pre_update.LIMITE
        assert pre_update[0] == "backup-pre-update-20261101-000003.db"
        assert (backup_dir / "backup-auto-20260101.db").exists()
        assert (backup_dir / "backup-manual.db").exists()


class TestRetencaoPrefixoPadrao:
    def test_sem_prefixo_continua_so_nos_backups_automaticos(self, tmp_path):
        for nome in ("backup-auto-20260101.db", "backup-auto-20260102.db", "backup-pre-update-x.db"):
            (tmp_path / nome).write_bytes(b"")

        fluxoly_storage.aplicar_retencao_backups_automaticos(str(tmp_path), limite=1)

        assert sorted(os.listdir(tmp_path)) == ["backup-auto-20260102.db", "backup-pre-update-x.db"]
