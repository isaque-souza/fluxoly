import json
import os
import sqlite3
import threading
import time
from datetime import datetime

from fluxoly_logging import get_logger

logger = get_logger("fluxoly.backup")


def carregar_configuracoes_integracoes(integrations_config_path):
    padrao = {
        "mercado_phone": {
            "api_token": "",
            "sync_enabled": True,
            "sync_interval_seconds": 30,
            "sync_start_date": "2026-04-01",
        }
    }
    if not os.path.exists(integrations_config_path):
        try:
            with open(integrations_config_path, "w", encoding="utf-8") as arquivo:
                json.dump(padrao, arquivo, ensure_ascii=False, indent=2)
        except OSError:
            return padrao
        return padrao

    try:
        with open(integrations_config_path, encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
            if isinstance(dados, dict):
                return dados
    except (OSError, json.JSONDecodeError):
        pass
    return padrao


def salvar_configuracoes_integracoes(integrations_config_path, dados):
    if not isinstance(dados, dict):
        raise ValueError("Configuracao de integracoes invalida.")

    pasta = os.path.dirname(integrations_config_path)
    if pasta:
        os.makedirs(pasta, exist_ok=True)

    with open(integrations_config_path, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def criar_arquivo_backup(destino, conectar):
    origem = conectar()
    copia = sqlite3.connect(destino)
    try:
        origem.backup(copia)
    finally:
        copia.close()
        origem.close()


def criar_backup(backup_dir, conectar, nome_arquivo=None):
    """Cria o backup só no diretório local (`backup_dir`). Destinos externos (Google Drive, e-mail)
    foram removidos em 2026-11-06 -- ver docs/operations/KNOWN_ISSUES.md KI-043."""
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    nome = nome_arquivo or f"backup-{timestamp}.db"
    destino_local = os.path.join(backup_dir, nome)
    criar_arquivo_backup(destino_local, conectar)

    return {
        "nome": nome,
        "destino_local": destino_local,
    }


def aplicar_retencao_backups_automaticos(backup_dir, limite=90, prefixo="backup-auto-"):
    def coletar_backups_automaticos(diretorio):
        if not diretorio or not os.path.isdir(diretorio):
            return []
        arquivos = []
        for nome in os.listdir(diretorio):
            if not nome.lower().endswith(".db"):
                continue
            if not nome.startswith(prefixo):
                continue
            caminho = os.path.join(diretorio, nome)
            if os.path.isfile(caminho):
                arquivos.append((nome, caminho))
        arquivos.sort(key=lambda item: item[0])
        return arquivos

    arquivos = coletar_backups_automaticos(backup_dir)
    excedentes = max(0, len(arquivos) - limite)
    for _, caminho in arquivos[:excedentes]:
        try:
            os.remove(caminho)
        except OSError as exc:
            logger.warning("backup_retencao_falha_ao_remover", extra={"caminho": caminho, "erro": str(exc)})


def executar_backup_diario_automatico(backup_dir, conectar):
    hoje = datetime.now().strftime("%Y%m%d")
    nome_arquivo = f"backup-auto-{hoje}.db"
    destino_local = os.path.join(backup_dir, nome_arquivo)
    if os.path.exists(destino_local):
        aplicar_retencao_backups_automaticos(backup_dir, limite=90)
        return None
    try:
        info = criar_backup(backup_dir, conectar, nome_arquivo=nome_arquivo)
        aplicar_retencao_backups_automaticos(backup_dir, limite=90)
        return info
    except Exception as exc:
        logger.error("backup_diario_falhou", extra={"erro": str(exc)}, exc_info=True)
        return None


def iniciar_thread_backup_automatico(
    backup_dir,
    conectar,
    intervalo_verificacao_segundos=3600,
):
    """
    Inicia thread daemon que verifica a cada hora se o backup do dia já existe.
    Se não existir, cria no diretório local.
    """

    def _loop():
        # Aguarda 30s após o boot para não competir com a inicialização do app
        time.sleep(30)
        while True:
            try:
                info = executar_backup_diario_automatico(backup_dir, conectar)
                if info:
                    logger.info("backup_automatico_criado", extra={"arquivo": info["nome"]})
            except Exception as exc:
                logger.error("backup_thread_erro_inesperado", extra={"erro": str(exc)}, exc_info=True)

            time.sleep(intervalo_verificacao_segundos)

    t = threading.Thread(target=_loop, daemon=True, name="backup-automatico")
    t.start()
    return t
