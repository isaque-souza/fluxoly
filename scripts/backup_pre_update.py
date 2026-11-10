#!/usr/bin/env python
"""Backup do banco antes de o Watchtower trocar o container (ADR-015).

Roda dentro do container que está em execução, como hook `pre-update` do
Watchtower (label em `deploy/docker-compose.yml`):

  python /app/scripts/backup_pre_update.py

Copia `DB_PATH` para `BACKUP_DIR/backup-pre-update-AAAAMMDD-HHMMSS.db` pela API
de backup do sqlite3 (`criar_backup`, a mesma do backup manual e do diário) e
mantém só os últimos `LIMITE` arquivos com esse prefixo. Não toca nos backups
`backup-auto-*` nem nos manuais.

Se a cópia falhar, sai com 75 (EX_TEMPFAIL): o Watchtower não atualiza o
container nessa rodada e tenta de novo na próxima. Nenhuma atualização (e
nenhuma migration nova) entra sem backup. Sem banco ainda (primeiro boot), não
há o que copiar e a atualização segue.

Conecta direto no arquivo do banco, sem importar `app.py` -- importar o app
rodaria migrations e iniciaria threads de background dentro do container antigo.
"""

import os
import sqlite3
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fluxoly_config import BACKUP_DIR, DB_PATH  # noqa: E402
from fluxoly_storage import aplicar_retencao_backups_automaticos, criar_backup  # noqa: E402

EX_TEMPFAIL = 75
PREFIXO = "backup-pre-update-"
LIMITE = 20


def executar(db_path=DB_PATH, backup_dir=BACKUP_DIR, agora=None):
    if not os.path.exists(db_path):
        print(f"backup_pre_update: banco ainda nao existe em {db_path}; nada a copiar")
        return 0

    momento = agora or datetime.now()
    nome = f"{PREFIXO}{momento:%Y%m%d-%H%M%S}.db"
    try:
        info = criar_backup(backup_dir, lambda: sqlite3.connect(db_path), nome_arquivo=nome)
        aplicar_retencao_backups_automaticos(backup_dir, limite=LIMITE, prefixo=PREFIXO)
    except Exception as exc:  # qualquer falha bloqueia a atualização
        print(f"backup_pre_update: falhou ({exc}); atualizacao adiada", file=sys.stderr)
        return EX_TEMPFAIL

    print(f"backup_pre_update: ok -> {info['destino_local']}")
    return 0


if __name__ == "__main__":
    sys.exit(executar())
