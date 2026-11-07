"""
Fluxoly - API Blueprint (Backup)
Rotas /api/backup/* -- consumidas pelo frontend React (Backup.jsx).
Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2 -- 7º domínio extraído).
"""

import contextlib
import os
import re
from datetime import datetime

from flask import Blueprint, request, send_from_directory

from fluxoly_api_helpers import _texto_limpo_local, err, ok, usuario_admin, usuario_logado
from fluxoly_validation import safe_json


def create_api_backup_blueprint(deps):
    api_backup = Blueprint("api_backup", __name__, url_prefix="/api")
    conectar = deps["conectar"]
    backup_dir = deps["backup_dir"]
    criar_backup = deps["criar_backup"]
    db_path = deps["db_path"]
    forcar_migracao_schema = deps["forcar_migracao_schema"]

    @api_backup.route("/backup/criar", methods=["POST"])
    def criar_backup_api():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        try:
            os.makedirs(backup_dir, exist_ok=True)
            body = safe_json(request)
            versao_bruta = _texto_limpo_local(body.get("versao"))
            versao = re.sub(r"[^A-Za-z0-9._-]", "", versao_bruta)[:40]
            nome_arquivo = None
            if versao:
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                nome_arquivo = f"backup-v{versao}-{stamp}.db"

            info = criar_backup(backup_dir, conectar, nome_arquivo=nome_arquivo)
            return ok(arquivo=info["nome"])
        except Exception as exc:
            return err(str(exc))

    @api_backup.route("/backup/listar")
    def listar_backups():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)

        backups = []
        if os.path.isdir(backup_dir):
            for f in os.listdir(backup_dir):
                if f.endswith(".db"):
                    full = os.path.join(backup_dir, f)
                    backups.append(
                        {
                            "nome": f,
                            "tamanho": os.path.getsize(full),
                            "data": datetime.fromtimestamp(os.path.getmtime(full)).strftime("%Y-%m-%d %H:%M"),
                            "modificado_em": os.path.getmtime(full),
                        }
                    )

        backups.sort(key=lambda item: item["modificado_em"], reverse=True)
        for item in backups:
            item.pop("modificado_em", None)

        return ok(backups=backups[:30])

    @api_backup.route("/backup/download/<path:filename>")
    def download_backup(filename):
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        return send_from_directory(backup_dir, filename, as_attachment=True)

    @api_backup.route("/backup/restaurar", methods=["POST"])
    def restaurar_backup_upload():
        if not usuario_logado() or not usuario_admin():
            return err("Acesso negado.", 403)
        if "arquivo" not in request.files:
            return err("Envie o arquivo no campo 'arquivo'.", 400)
        f = request.files["arquivo"]
        if not f.filename or not f.filename.lower().endswith(".db"):
            return err("O arquivo deve ter extensão .db", 400)
        # Valida que é um SQLite legítimo lendo o magic header
        header = f.read(16)
        if not header.startswith(b"SQLite format 3"):
            return err("Arquivo inválido: não é um banco SQLite.", 400)
        f.seek(0)
        import shutil
        import sqlite3 as _sqlite3
        import tempfile

        # Salva em temp para validar antes de sobrescrever. delete=False + unlink manual
        # no finally (nao um `with`) e proposital: no Windows, fechar o handle antes do
        # os.unlink() no finally abaixo falharia com PermissionError enquanto o arquivo
        # ainda esta em uso por sqlite3.connect()/shutil.copy2() no corpo do try.
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")  # noqa: SIM115
        try:
            f.save(tmp.name)
            # Testa integridade
            test_conn = _sqlite3.connect(tmp.name)
            result = test_conn.execute("PRAGMA integrity_check").fetchone()
            test_conn.close()
            if result[0] != "ok":
                return err(f"Banco corrompido: {result[0]}", 400)
            # Faz backup do atual antes de substituir
            if os.path.exists(db_path):
                stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                os.makedirs(backup_dir, exist_ok=True)
                shutil.copy2(db_path, os.path.join(backup_dir, f"pre-restore-{stamp}.db"))
            shutil.copy2(tmp.name, db_path)
            # Garante colunas/tabelas novas quando o backup é de schema antigo.
            forcar_migracao_schema()
        finally:
            with contextlib.suppress(Exception):
                os.unlink(tmp.name)
        return ok(mensagem="Backup restaurado com sucesso.")

    return api_backup
