import json
import math
import re
import time
from datetime import datetime, timedelta
from urllib import error as urllib_error
from urllib import request as urllib_request

from fluxoly_api_helpers import _texto_limpo_local
from fluxoly_logging import get_logger

logger = get_logger("fluxoly.mercadophone")


def _to_bool(valor, padrao=False):
    if valor is None:
        return padrao
    if isinstance(valor, bool):
        return valor
    return str(valor).strip().lower() not in {"", "0", "false", "nao", "off"}


def carregar_config_mercadophone(carregar_configuracoes_integracoes, integrations_config_path):
    """Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2) -- compartilhado
    com OS (listar_ordens()), não migra para fluxoly_api_helpers.py porque é
    lógica de domínio (config de integração), não helper web genérico."""
    dados = carregar_configuracoes_integracoes(integrations_config_path)
    if not isinstance(dados, dict):
        dados = {}
    mp = dados.get("mercado_phone")
    if not isinstance(mp, dict):
        mp = {}
        dados["mercado_phone"] = mp
    return dados, mp


def atualizar_runtime_mercadophone(mp_cfg, mercado_phone_runtime_config):
    """Extraído de fluxoly_blueprints_api.py (TD-01, Phase 2) -- compartilhado
    com OS (listar_ordens())."""
    token_cfg = _texto_limpo_local(mp_cfg.get("api_token"))
    token_runtime = _texto_limpo_local(mercado_phone_runtime_config.get("api_token"))
    token = token_cfg or token_runtime

    intervalo_cfg = mp_cfg.get("sync_interval_seconds", mercado_phone_runtime_config.get("sync_interval_seconds", 180))
    timeout_cfg = mp_cfg.get("sync_timeout_seconds", mercado_phone_runtime_config.get("sync_timeout_seconds", 20))

    try:
        intervalo = max(30, int(intervalo_cfg or 180))
    except (TypeError, ValueError):
        intervalo = 180

    try:
        timeout = max(5, int(timeout_cfg or 20))
    except (TypeError, ValueError):
        timeout = 20

    start_date = _texto_limpo_local(
        mp_cfg.get("sync_start_date") or mercado_phone_runtime_config.get("sync_start_date") or "2026-04-01"
    )

    mercado_phone_runtime_config.update(
        {
            "api_token": token,
            "sync_enabled": _to_bool(mp_cfg.get("sync_enabled"), padrao=bool(token)),
            "sync_interval_seconds": intervalo,
            "sync_timeout_seconds": timeout,
            "sync_start_date": start_date,
        }
    )

    return {
        "configurado": bool(token),
        "sync_enabled": bool(mercado_phone_runtime_config.get("sync_enabled")),
        "sync_interval_seconds": int(mercado_phone_runtime_config.get("sync_interval_seconds") or 0),
        "sync_timeout_seconds": int(mercado_phone_runtime_config.get("sync_timeout_seconds") or 0),
        "sync_start_date": mercado_phone_runtime_config.get("sync_start_date") or "",
        "api_base": mercado_phone_runtime_config.get("api_base") or "",
    }


def _float_finito(valor):
    """float() que trata Infinity, NaN e números que estouram o float como valor inválido
    (ValueError), igual a um texto não numérico -- o chamador já ignora valor inválido (P1-1)."""
    try:
        numero = float(valor)
    except OverflowError as exc:
        raise ValueError("valor fora do intervalo") from exc
    if not math.isfinite(numero):
        raise ValueError("valor não finito")
    return numero


def valor_payload(payload, *caminhos):
    for caminho in caminhos:
        atual = payload
        for chave in caminho:
            if not isinstance(atual, dict):
                atual = None
                break
            atual = atual.get(chave)
        if atual not in (None, ""):
            return atual
    return ""


def lista_payload(payload, chave):
    valor = payload.get(chave) if isinstance(payload, dict) else None
    return valor if isinstance(valor, list) else []


def primeiro_item_lista(payload, chave):
    itens = lista_payload(payload, chave)
    return itens[0] if itens else {}


def obter_estado_integracao(cursor, chave, padrao=""):
    cursor.execute("SELECT valor FROM integracao_sync_estado WHERE chave=?", (chave,))
    row = cursor.fetchone()
    return row[0] if row else padrao


def definir_estado_integracao(cursor, chave, valor):
    cursor.execute(
        """
        INSERT INTO integracao_sync_estado (chave, valor)
        VALUES (?, ?)
        ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor
        """,
        (chave, str(valor)),
    )


_LOCK_SYNC_CHAVE = "mercado_phone_sync_lock"
_LOCK_SYNC_EPOCA = "0000-01-01 00:00:00"
# Intervalo padrao de sync e 30s (MERCADO_PHONE_SYNC_INTERVAL_SECONDS, app.py) e um ciclo
# sem novidades e rapido (so listagem, sem chamada por OS). 90s (3x o intervalo) da folga
# para ciclos com varias OS novas/atualizadas sem deixar um worker morto bloqueando a
# sincronizacao por muito tempo - revisado para baixo a partir de 300s por review do
# usuario (CTO): "5 minutos de espera apos um crash e mais do que o necessario".
LOCK_SYNC_TTL_SEGUNDOS_PADRAO = 90


def adquirir_lock_sync_mercado_phone(conectar, ttl_segundos=LOCK_SYNC_TTL_SEGUNDOS_PADRAO):
    """Lock cross-processo (INC-002): impede que mais de um worker do Gunicorn rode a
    sincronizacao do Mercado Phone ao mesmo tempo. `iniciar_sync_mercadophone_se_habilitado`
    (app.py) inicia uma thread de sync por processo, sem coordenacao entre eles - com
    --workers 2 em producao, dois processos concorrentes faziam SELECT-antes-de-INSERT
    (TOCTOU) na mesma OS nova e podiam duplica-la.

    Usa `integracao_sync_estado` (tabela ja existente, sem mudanca de schema) como um
    lease com expiracao: se o processo que detem o lock cair sem liberar, o lock expira
    sozinho depois de `ttl_segundos` em vez de travar a sincronizacao para sempre.
    Conexao propria e commit imediato, para que a reivindicacao fique visivel a outros
    processos antes de comecar o trabalho (potencialmente demorado) de sync.
    """
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR IGNORE INTO integracao_sync_estado (chave, valor) VALUES (?, ?)",
            (_LOCK_SYNC_CHAVE, _LOCK_SYNC_EPOCA),
        )
        agora = datetime.now()
        expira_em = (agora + timedelta(seconds=ttl_segundos)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            """
            UPDATE integracao_sync_estado
            SET valor = ?
            WHERE chave = ? AND valor < ?
            """,
            (expira_em, _LOCK_SYNC_CHAVE, agora.strftime("%Y-%m-%d %H:%M:%S")),
        )
        adquirido = cursor.rowcount == 1
        conn.commit()
        return adquirido
    finally:
        conn.close()


def liberar_lock_sync_mercado_phone(conectar):
    conn = conectar()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE integracao_sync_estado SET valor = ? WHERE chave = ?",
            (_LOCK_SYNC_EPOCA, _LOCK_SYNC_CHAVE),
        )
        conn.commit()
    finally:
        conn.close()


def os_integracao_ja_vista(cursor, origem, external_id):
    cursor.execute(
        "SELECT 1 FROM integracao_os_vistas WHERE origem=? AND id_externo=?",
        (origem, str(external_id)),
    )
    return cursor.fetchone() is not None


def marcar_os_integracao_vista(cursor, origem, external_id):
    cursor.execute(
        """
        INSERT OR IGNORE INTO integracao_os_vistas (origem, id_externo, primeira_visualizacao)
        VALUES (?, ?, ?)
        """,
        (origem, str(external_id), datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )


def os_integracao_bloqueada(cursor, origem, external_id):
    return os_integracao_ja_vista(cursor, f"{origem}_bloqueada", external_id)


def extrair_ids_os_listagem_mercado_phone(payload, texto_limpo):
    if isinstance(payload, list):
        itens = payload
    elif isinstance(payload, dict):
        itens = None
        data = payload.get("data")
        if isinstance(data, dict):
            for chave in ("itens", "items", "results", "ordens", "ordensServico", "rows"):
                valor = data.get(chave)
                if isinstance(valor, list):
                    itens = valor
                    break
        if itens is None:
            for chave in ("data", "items", "results", "ordens", "ordensServico", "rows"):
                valor = payload.get(chave)
                if isinstance(valor, list):
                    itens = valor
                    break
        if itens is None:
            itens = [payload]
    else:
        itens = []

    ids = []
    for item in itens:
        if not isinstance(item, dict):
            continue
        external_id = texto_limpo(item.get("codigo") or item.get("id"))
        if external_id and external_id not in ids:
            ids.append(external_id)
    return ids


def parse_json_response(conteudo):
    if not conteudo:
        return {}
    try:
        return json.loads(conteudo.decode("utf-8"))
    except UnicodeDecodeError:
        return json.loads(conteudo.decode("latin-1"))


def _erro_rede_transitorio(exc):
    if isinstance(exc, TimeoutError):
        return True

    texto = str(exc or "").lower()
    if "timed out" in texto or "timeout" in texto or "handshake" in texto:
        return True

    if isinstance(exc, urllib_error.URLError):
        reason = getattr(exc, "reason", None)
        texto_reason = str(reason or "").lower()
        if isinstance(reason, TimeoutError):
            return True
        if "timed out" in texto_reason or "timeout" in texto_reason or "handshake" in texto_reason:
            return True

    return False


def chamar_api_mercado_phone(method_name, payload, config):
    api_token = config["api_token"]
    if not api_token:
        raise RuntimeError("MERCADO_PHONE_API_TOKEN nao configurado.")

    url = f'{config["api_base"]}{method_name}'
    body = json.dumps(payload or {}).encode("utf-8")
    req = urllib_request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": api_token,
            "Content-Type": "application/json",
        },
    )

    retries = int(config.get("sync_request_retries") or 3)
    retries = max(1, retries)
    timeout_seconds = int(config.get("sync_timeout_seconds") or 20)

    for tentativa in range(1, retries + 1):
        try:
            with urllib_request.urlopen(req, timeout=timeout_seconds) as response:
                return parse_json_response(response.read())
        except (urllib_error.URLError, TimeoutError) as exc:
            if tentativa >= retries or not _erro_rede_transitorio(exc):
                raise
            espera = min(8, 2 * tentativa)
            logger.warning(
                "mercadophone_api_tentativa_falhou",
                extra={
                    "tentativa": tentativa,
                    "retries": retries,
                    "method": method_name,
                    "erro": f"{type(exc).__name__}: {exc}",
                    "espera_s": espera,
                },
            )
            time.sleep(espera)


def listar_os_mercado_phone(config, page=1, limit=300):
    return chamar_api_mercado_phone(
        "index",
        {
            "page": page,
            "limit": limit,
            "order": "id",
            "direction": "desc",
            "filters": {
                "codigo": "",
                "diagnostico": "",
                "clienteId": "",
                "situacaoId": "",
                "tipoId": "",
                "dataCriacaoInicial": config["sync_start_date"],
                "dataCriacaoFinal": "",
                "dataFinalizacaoInicial": "",
                "dataFinalizacaoFinal": "",
                "dataPrevisaoInicial": "",
                "dataPrevisaoFinal": "",
                "observacao": "",
                "defeito": "",
                "nomeCliente": "",
            },
        },
        config,
    )


def detalhar_os_mercado_phone(external_id, config):
    # A API do MercadoPhone retorna payload vazio quando recebe codigo e id juntos.
    # Primeiro consulta por codigo (ID visível); se vier vazio, tenta por id.
    tentativas_payload = [
        {"filters": {"codigo": str(external_id)}},
        {"filters": {"id": str(external_id)}},
    ]

    ultima_resposta = {}
    for payload in tentativas_payload:
        resposta = chamar_api_mercado_phone("get", payload, config)
        ultima_resposta = resposta if isinstance(resposta, dict) else {}
        data = ultima_resposta.get("data") if isinstance(ultima_resposta, dict) else None
        if isinstance(data, dict) and any(
            [
                data.get("codigo"),
                data.get("id"),
                data.get("clienteNome"),
                data.get("situacaoDescricao"),
                data.get("valorTotal"),
                bool(data.get("aparelhos")),
                bool(data.get("servicos")),
            ]
        ):
            return ultima_resposta

    return ultima_resposta


def _dividir_reparos_texto_mercado_phone(valor_texto, texto_limpo):
    texto = " ".join(texto_limpo(valor_texto).replace("\n", " ").split())
    if not texto:
        return []

    separadas = [p.strip() for p in re.split(r"\s*(?:\||;|,)\s*", texto) if p.strip()]
    partes = []

    for item in separadas:
        marcadores = [m.start() for m in re.finditer(r"\b(?:troca|reparo)\s+de\b", item, flags=re.IGNORECASE)]
        if len(marcadores) <= 1:
            partes.append(item)
            continue

        marcadores.append(len(item))
        for idx in range(len(marcadores) - 1):
            trecho = item[marcadores[idx] : marcadores[idx + 1]].strip(" -/|")
            if trecho:
                partes.append(trecho)

    return partes


def _normalizar_nome_reparo_mercado_phone(nome_reparo, normalizar_busca_texto, texto_limpo):
    nome = texto_limpo(nome_reparo)
    if not nome:
        return ""

    nome_norm = normalizar_busca_texto(nome)

    if nome_norm in {"analise", "analise tecnica", "diagnostico", "avaliacao", "nao informado"}:
        return ""

    if "bateria" in nome_norm:
        return "TROCA DE BATERIA"
    if (
        "dock" in nome_norm
        or ("conector" in nome_norm and "carga" in nome_norm)
        or ("porta" in nome_norm and "carga" in nome_norm)
    ):
        return "TROCA DE DOCK DE CARGA"
    if "reparo" in nome_norm and "face id" in nome_norm:
        return "REPARO FACE ID"
    if "face id" in nome_norm:
        return "TROCA DE FACE ID"
    if "camera traseira" in nome_norm:
        return "TROCA DE CAMERA TRASEIRA"
    if "camera frontal" in nome_norm:
        return "TROCA DE CAMERA FRONTAL"
    if "lente" in nome_norm and "camera" in nome_norm:
        return "TROCA DE LENTE DA CAMERA"
    if "vidro" in nome_norm and "traseir" in nome_norm:
        return "TROCA DE VIDRO TRASEIRO"
    if "tampa traseira" in nome_norm or (
        "traseira" in nome_norm and "camera" not in nome_norm and "lente" not in nome_norm and "vidro" not in nome_norm
    ):
        return "TROCA DE TAMPA TRASEIRA"
    if "vidro" in nome_norm and "tela" in nome_norm:
        return "TROCA DE VIDRO DA TELA"
    if "reparo" in nome_norm and "placa" in nome_norm:
        return "REPARO DE PLACA"
    if "reparo" in nome_norm and "tela" in nome_norm:
        return "REPARO DE TELA"
    if "tela" in nome_norm or "display" in nome_norm:
        return "TROCA DE TELA"
    if "flash" in nome_norm:
        return "TROCA DE FLASH"

    if "analise" in nome_norm or "diagnost" in nome_norm or "avaliac" in nome_norm:
        return ""

    return " ".join(nome.upper().split())


def _extrair_reparos_mercado_phone(texto, nome_reparo_importavel, normalizar_busca_texto, texto_limpo):
    reparos = []
    for trecho in _dividir_reparos_texto_mercado_phone(texto, texto_limpo):
        reparo_nome = _normalizar_nome_reparo_mercado_phone(trecho, normalizar_busca_texto, texto_limpo)
        if not reparo_nome:
            continue
        if nome_reparo_importavel(reparo_nome) and reparo_nome not in reparos:
            reparos.append(reparo_nome)

    texto_norm = normalizar_busca_texto(texto)
    reparos_por_termo = {
        "tampa traseira": "TROCA DE TAMPA TRASEIRA",
        "vidro traseiro": "TROCA DE VIDRO TRASEIRO",
        "face id": "TROCA DE FACE ID",
        "dock de carga": "TROCA DE DOCK DE CARGA",
        "bateria": "TROCA DE BATERIA",
        "tela": "TROCA DE TELA",
    }
    for termo, reparo_nome in reparos_por_termo.items():
        if termo in texto_norm and reparo_nome not in reparos and nome_reparo_importavel(reparo_nome):
            reparos.append(reparo_nome)

    return reparos


def _payload_tem_dados_suficientes_mercado_phone(payload, texto_limpo):
    if not isinstance(payload, dict):
        return False

    cliente = texto_limpo(valor_payload(payload, ("clienteNome",), ("cliente", "nome"), ("cliente",)))
    defeito = texto_limpo(valor_payload(payload, ("defeito",), ("observacao",), ("diagnostico",)))

    aparelho_info = primeiro_item_lista(payload, "aparelhos")
    descricao_aparelho = texto_limpo(
        valor_payload(payload, ("descricaoAparelho",), ("aparelho", "descricao"), ("descricao",))
        or valor_payload(aparelho_info, ("descricao",), ("modeloDescricao",), ("modeloDescricaoAparelho",))
    )

    servicos = []
    for chave_lista in ("servicos", "servicosOs", "servicos_os", "itensServico", "itens_servico"):
        servicos = lista_payload(payload, chave_lista)
        if servicos:
            break

    valor_total = valor_payload(payload, ("valorTotal",), ("valorTotalServicos",), ("valorTotalPecas",))
    tem_valor = False
    try:
        tem_valor = float(valor_total or 0) > 0
    except (TypeError, ValueError):
        tem_valor = False

    # Regra rigorosa: status isolado NAO caracteriza payload suficiente.
    # Só consideramos válido se vier pelo menos um dado de negócio relevante.
    return bool(cliente or descricao_aparelho or defeito or servicos or tem_valor)


def importar_os_mercado_phone(cursor, payload, config, helpers, fallback_external_id=""):
    if not isinstance(payload, dict):
        raise ValueError("Payload invalido.")

    texto_limpo = helpers["texto_limpo"]
    modelo_para_os = helpers["modelo_para_os"]
    extrair_modelo_da_descricao_aparelho = helpers["extrair_modelo_da_descricao_aparelho"]
    extrair_cor_da_descricao_aparelho = helpers["extrair_cor_da_descricao_aparelho"]
    normalizar_imei = helpers["normalizar_imei"]
    nome_reparo_importavel = helpers["nome_reparo_importavel"]
    obter_ou_criar_reparo = helpers["obter_ou_criar_reparo"]
    salvar_reparos_os = helpers["salvar_reparos_os"]
    normalizar_busca_texto = helpers["normalizar_busca_texto"]
    normalizar_status_os = helpers["normalizar_status_os"]
    canonicalizar_para_lista = helpers.get("canonicalizar_para_lista", lambda v, lista: "")
    lista_tecnicos = helpers.get("tecnicos", [])
    lista_vendedores = helpers.get("vendedores", [])

    external_id = texto_limpo(
        valor_payload(
            payload,
            ("id_externo",),
            ("external_id",),
            ("codigo",),
            ("id",),
            ("os_id",),
            ("ordem_servico_id",),
            ("ordem_servico", "id"),
        )
    ) or texto_limpo(fallback_external_id)
    if not external_id:
        raise ValueError("Nao foi encontrado um identificador externo da OS.")

    cursor.execute(
        """
        SELECT id
        FROM os
        WHERE origem_integracao=? AND id_externo_integracao=?
        """,
        ("mercado_phone", external_id),
    )
    existente = cursor.fetchone()

    # Se a OS já existe, atualizar o status e outras informações
    if existente:
        os_id = existente[0]
        status = normalizar_status_os(
            valor_payload(
                payload,
                ("situacaoDescricao",),
                ("status",),
            )
        )

        # Dados que podem ter chegado vazios na importação original
        cliente_novo = texto_limpo(
            valor_payload(payload, ("clienteNome",), ("cliente", "nome"), ("cliente_nome",), ("cliente",))
        )

        valor_cobrado_novo = 0.0
        try:
            vt = valor_payload(payload, ("valorTotal",), ("valorTotalServicos",))
            if vt not in (None, "", 0):
                valor_cobrado_novo = _float_finito(vt)
        except (ValueError, TypeError):
            pass

        servicos_existente = lista_payload(payload, "servicos") or lista_payload(payload, "servicosOs")
        custo_pecas_novo = 0.0
        for s in servicos_existente:
            try:
                custo = valor_payload(s, ("valorCusto",))
                if custo not in (None, "", 0):
                    custo_pecas_novo += _float_finito(custo)
            except (ValueError, TypeError):
                pass

        # Buscar estado atual da OS
        cursor.execute("SELECT status, cliente, valor_cobrado, custo_pecas FROM os WHERE id=?", (os_id,))
        row_atual = cursor.fetchone()
        status_anterior = row_atual[0] if row_atual else None
        cliente_atual = row_atual[1] if row_atual else None
        valor_cobrado_atual = row_atual[2] if row_atual else None
        custo_pecas_atual = row_atual[3] if row_atual else None

        updates = {}
        if status and status != status_anterior:
            # BR-061 (V1.5 -- Garantia de Reparo): esta escrita de status é
            # deliberadamente isenta da exigência de tipo_garantia_id por
            # linha de reparo -- não há humano no loop no momento do sync
            # para escolher o Tipo de Garantia. Uma OS finalizada aqui fica
            # com tipo_garantia_id NULL na linha, tratada como dado histórico
            # por listar_garantias() (mesmo fallback de OS pré-V1.5), com
            # correção manual disponível depois (PATCH .../reparos/<id>/garantia).
            # Ver docs/product/BUSINESS_RULES.md BR-061 e PLAN-V1.5-Garantia.md.
            updates["status"] = status
        if cliente_novo and (not cliente_atual or cliente_atual in ("Cliente nao informado", "")):
            updates["cliente"] = cliente_novo
        if valor_cobrado_novo and (not valor_cobrado_atual or float(valor_cobrado_atual) == 0):
            updates["valor_cobrado"] = valor_cobrado_novo
        if custo_pecas_novo and (not custo_pecas_atual or float(custo_pecas_atual) == 0):
            updates["custo_pecas"] = custo_pecas_novo

        if updates:
            set_clause = ", ".join(f"{col}=?" for col in updates)
            cursor.execute(
                f"UPDATE os SET {set_clause} WHERE id=?",
                (*updates.values(), os_id),
            )
            logger.info(
                "mercadophone_os_atualizada",
                extra={"os_id": os_id, "codigo_externo": external_id, "campos": list(updates.keys())},
            )

        return {"os_id": os_id, "duplicada": False, "atualizada": True}

    if not _payload_tem_dados_suficientes_mercado_phone(payload, texto_limpo):
        resumo = {
            "codigo": texto_limpo(valor_payload(payload, ("codigo",), ("id",))),
            "clienteNome": texto_limpo(valor_payload(payload, ("clienteNome",))),
            "descricaoAparelho": texto_limpo(valor_payload(payload, ("descricaoAparelho",), ("descricao",))),
            "situacao": texto_limpo(valor_payload(payload, ("situacaoDescricao",), ("status",))),
            "valorTotal": valor_payload(payload, ("valorTotal",), ("valorTotalServicos",)),
            "servicos": len(lista_payload(payload, "servicos") or lista_payload(payload, "servicosOs")),
            "aparelhos": len(lista_payload(payload, "aparelhos")),
        }
        logger.warning("mercadophone_payload_insuficiente", extra={"resumo": resumo})
        raise ValueError("Payload da OS sem dados suficientes para criar registro.")

    aparelho_info = primeiro_item_lista(payload, "aparelhos")
    if not aparelho_info and isinstance(payload.get("aparelho"), dict):
        aparelho_info = payload.get("aparelho")

    servicos = []
    for chave_lista in ("servicos", "servicosOs", "servicos_os", "itensServico", "itens_servico"):
        servicos = lista_payload(payload, chave_lista)
        if servicos:
            break

    cliente = texto_limpo(
        valor_payload(
            payload,
            ("clienteNome",),
            ("cliente", "nome"),
            ("cliente_nome",),
            ("nome_cliente",),
            ("cliente",),
        )
    )
    descricao_aparelho = texto_limpo(
        valor_payload(
            payload,
            ("descricaoAparelho",),
            ("aparelho", "descricao"),
            ("descricao",),
        )
        or valor_payload(
            aparelho_info,
            ("descricao",),
            ("modeloDescricao",),
            ("modeloDescricaoAparelho",),
        )
    )
    modelo = modelo_para_os(
        valor_payload(
            payload,
            ("modeloDescricao",),
            ("modeloDescricaoAparelho",),
            ("aparelho", "modelo"),
            ("aparelho", "modeloDescricao"),
            ("aparelho", "modeloDescricaoAparelho"),
            ("modelo",),
            ("modelo_celular",),
            ("celular_modelo",),
            ("descricao",),
        )
    )
    if not modelo:
        modelo = modelo_para_os(
            valor_payload(
                aparelho_info,
                ("modelo",),
                ("modeloDescricao",),
                ("modeloDescricaoAparelho",),
                ("nomeModelo",),
                ("descricao",),
            )
        )
    if not modelo:
        modelo = modelo_para_os(descricao_aparelho)
    if not modelo:
        modelo = extrair_modelo_da_descricao_aparelho(descricao_aparelho)

    cor = texto_limpo(
        valor_payload(
            payload,
            ("aparelho", "cor"),
            ("aparelho", "corDescricao"),
            ("aparelho", "corNome"),
            ("cor",),
            ("corDescricao",),
            ("corNome",),
            ("cor_celular",),
        )
    )
    if not cor:
        cor = texto_limpo(
            valor_payload(
                aparelho_info,
                ("cor",),
                ("corDescricao",),
                ("corNome",),
            )
        )
    cor = extrair_cor_da_descricao_aparelho(cor, modelo) or cor
    if not cor:
        cor = extrair_cor_da_descricao_aparelho(descricao_aparelho, modelo)

    imei = normalizar_imei(
        valor_payload(
            payload,
            ("aparelho", "imei"),
            ("aparelho", "imei1"),
            ("imei",),
            ("imei1",),
        )
    )
    if not imei:
        imei = normalizar_imei(
            valor_payload(
                aparelho_info,
                ("imei",),
                ("imei1",),
            )
        )

    reparos_nomes = []
    for servico in servicos:
        if not isinstance(servico, dict):
            continue
        nome_servico = texto_limpo(
            valor_payload(
                servico,
                ("servicoDescricao",),
                ("descricao",),
                ("nome",),
                ("tipoServico",),
            )
        )
        reparos_extraidos = _extrair_reparos_mercado_phone(
            nome_servico,
            nome_reparo_importavel,
            normalizar_busca_texto,
            texto_limpo,
        )
        for reparo_nome in reparos_extraidos:
            if reparo_nome not in reparos_nomes:
                reparos_nomes.append(reparo_nome)

    reparo_principal = texto_limpo(
        valor_payload(
            payload,
            ("tipo_reparo",),
            ("reparo", "nome"),
            ("reparo",),
            ("servico",),
            ("tipoServico",),
            ("solucao",),
        )
    )
    reparos_principais = _extrair_reparos_mercado_phone(
        reparo_principal,
        nome_reparo_importavel,
        normalizar_busca_texto,
        texto_limpo,
    )
    for reparo_nome in reversed(reparos_principais):
        if reparo_nome not in reparos_nomes:
            reparos_nomes.insert(0, reparo_nome)

    if not cliente:
        cliente = "Cliente nao informado"
    if not modelo:
        modelo = "Nao informado"
    if not reparos_nomes:
        reparos_nomes = ["Nao informado"]

    aparelho = descricao_aparelho or modelo

    reparo_ids = []
    for nome_reparo in reparos_nomes:
        reparo_id = obter_ou_criar_reparo(cursor, nome_reparo)
        if reparo_id and reparo_id not in reparo_ids:
            reparo_ids.append(reparo_id)

    data_os = texto_limpo(
        valor_payload(
            payload,
            ("dataCriacao",),
            ("data",),
            ("data_os",),
            ("created_at",),
            ("createdAt",),
        )
    )[:10] or datetime.now().strftime("%Y-%m-%d")
    status = normalizar_status_os(
        valor_payload(
            payload,
            ("situacaoDescricao",),
            ("status",),
        )
    )
    tipo_origem = texto_limpo(valor_payload(payload, ("tipoDescricao",), ("tipo",)))
    tipo = "Garantia" if "garantia" in normalizar_busca_texto(tipo_origem) else "Assistencia"
    _tecnico_raw = (
        texto_limpo(valor_payload(payload, ("tecnicoNome",), ("tecnico", "nome"))) or config["default_tecnico"]
    )
    tecnico = canonicalizar_para_lista(_tecnico_raw, lista_tecnicos) or _tecnico_raw
    _vendedor_raw = texto_limpo(valor_payload(payload, ("vendedorNome",), ("vendedor", "nome")))
    vendedor = canonicalizar_para_lista(_vendedor_raw, lista_vendedores) or _vendedor_raw
    observacoes_partes = [
        "Importada automaticamente do Mercado Phone.",
        texto_limpo(valor_payload(payload, ("defeito",))),
        texto_limpo(valor_payload(payload, ("diagnostico",))),
        texto_limpo(valor_payload(payload, ("observacao",))),
        texto_limpo(valor_payload(payload, ("observacaoInterna",))),
        texto_limpo(valor_payload(payload, ("solucao",))),
    ]
    observacoes = " | ".join(parte for parte in observacoes_partes if parte)

    # Valores financeiros
    valor_cobrado = 0.0
    try:
        vt = valor_payload(payload, ("valorTotal",), ("valorTotalServicos",))
        if vt not in (None, "", 0):
            valor_cobrado = _float_finito(vt)
    except (ValueError, TypeError):
        pass
    if not valor_cobrado:
        for servico in servicos:
            try:
                vc = valor_payload(servico, ("valorCobranca",))
                if vc not in (None, "", 0):
                    valor_cobrado += _float_finito(vc)
            except (ValueError, TypeError):
                pass

    custo_pecas = 0.0
    for servico in servicos:
        try:
            custo = valor_payload(servico, ("valorCusto",))
            if custo not in (None, "", 0):
                custo_pecas += _float_finito(custo)
        except (ValueError, TypeError):
            pass

    cursor.execute(
        """
        INSERT INTO os (
            tipo, cliente, aparelho, tecnico, reparo_id, status,
            valor_cobrado, valor_descontado, custo_pecas, data, observacoes,
            modelo, vendedor, cor, imei, origem_integracao, id_externo_integracao
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            tipo,
            cliente,
            aparelho,
            tecnico,
            reparo_ids[0],
            status,
            valor_cobrado,
            0,
            custo_pecas,
            data_os,
            observacoes,
            modelo,
            vendedor,
            cor,
            imei,
            "mercado_phone",
            external_id,
        ),
    )

    os_id = cursor.lastrowid
    salvar_reparos_os(cursor, os_id, reparo_ids)
    return {"os_id": os_id, "duplicada": False}


def sincronizar_mercado_phone(conectar, config, helpers):
    """Adquire o lock cross-processo (INC-002) antes de sincronizar - se outro worker do
    Gunicorn ja estiver sincronizando, retorna sem tocar na API nem no banco em vez de
    competir com ele."""
    if not adquirir_lock_sync_mercado_phone(conectar):
        logger.info("mercadophone_sync_ignorada_lock_ocupado")
        return {"ok": True, "importadas": 0, "ignoradas": 0, "inicializada": True, "lock_ocupado": True}
    try:
        return _sincronizar_mercado_phone_sem_lock(conectar, config, helpers)
    finally:
        liberar_lock_sync_mercado_phone(conectar)


def _sincronizar_mercado_phone_sem_lock(conectar, config, helpers):
    conn = conectar()
    cursor = conn.cursor()
    origem = "mercado_phone"

    try:
        ids_encontrados = []
        seen_ids = set()
        page = 1
        page_limit = 300
        max_pages = int(config.get("sync_max_pages", 100) or 100)

        while page <= max_pages:
            listagem = listar_os_mercado_phone(config, page=page, limit=page_limit)
            page_ids = extrair_ids_os_listagem_mercado_phone(listagem, helpers["texto_limpo"])
            if not page_ids:
                break

            added = 0
            for external_id in page_ids:
                if external_id not in seen_ids:
                    seen_ids.add(external_id)
                    ids_encontrados.append(external_id)
                    added += 1

            if added == 0 or len(page_ids) < page_limit:
                break

            page += 1

        if not ids_encontrados:
            definir_estado_integracao(
                cursor, "mercado_phone_sync_ultima_execucao", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            conn.commit()
            return {"ok": True, "importadas": 0, "ignoradas": 0, "inicializada": False}

        inicializada = obter_estado_integracao(cursor, "mercado_phone_sync_inicializado", "") == "1"
        importadas = 0
        ignoradas = 0

        if not inicializada and config["sync_only_after_boot"]:
            definir_estado_integracao(cursor, "mercado_phone_sync_inicializado", "1")
            definir_estado_integracao(
                cursor, "mercado_phone_sync_ultima_execucao", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            )
            conn.commit()
            return {"ok": True, "importadas": 0, "ignoradas": len(ids_encontrados), "inicializada": True}

        for external_id in ids_encontrados:
            try:
                # Se a OS foi apagada manualmente e ainda nao existe localmente,
                # a sincronizacao automatica nao deve recria-la.
                if os_integracao_bloqueada(cursor, origem, external_id):
                    cursor.execute(
                        """
                        SELECT 1
                        FROM os
                        WHERE origem_integracao=? AND id_externo_integracao=?
                        LIMIT 1
                        """,
                        (origem, str(external_id)),
                    )
                    if not cursor.fetchone():
                        ignoradas += 1
                        continue

                detalhes = detalhar_os_mercado_phone(external_id, config)
                payload_importacao = detalhes if isinstance(detalhes, dict) else {}
                if isinstance(payload_importacao.get("data"), dict):
                    payload_importacao = payload_importacao["data"]

                if not isinstance(payload_importacao, dict):
                    payload_importacao = {}

                if "codigo" not in payload_importacao and "id" not in payload_importacao:
                    payload_importacao["id_externo"] = external_id

                resultado = importar_os_mercado_phone(
                    cursor,
                    payload_importacao,
                    config,
                    helpers,
                    fallback_external_id=external_id,
                )

                if resultado.get("atualizada"):
                    ignoradas += 1
                else:
                    importadas += 1
            except ValueError as exc:
                ignoradas += 1
                logger.warning("mercadophone_os_ignorada", extra={"codigo_externo": external_id, "erro": str(exc)})
            except Exception as exc:
                ignoradas += 1
                logger.error(
                    "mercadophone_erro_ao_processar_os",
                    extra={"codigo_externo": external_id, "erro": f"{type(exc).__name__}: {exc}"},
                    exc_info=True,
                )
            finally:
                # INC-001 (causa raiz confirmada em producao, 2026-08-05): antes, o commit so
                # acontecia depois do loop inteiro -- ate centenas de registros, cada um com
                # uma chamada HTTP externa para a API do Mercado Phone -- mantendo a transacao
                # de escrita aberta por toda essa janela e bloqueando qualquer outro escritor
                # (ex.: login) pelo busy_timeout inteiro (30s). Commit por registro libera o
                # lock entre uma chamada externa e a proxima, preservando a atomicidade de
                # cada registro (ja isolado pelo try/except acima).
                conn.commit()

        definir_estado_integracao(cursor, "mercado_phone_sync_inicializado", "1")
        definir_estado_integracao(
            cursor, "mercado_phone_sync_ultima_execucao", datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        conn.commit()
        return {"ok": True, "importadas": importadas, "ignoradas": ignoradas, "inicializada": True}
    finally:
        conn.close()


def corrigir_dados_importados_mercado_phone(conectar, helpers):
    conn = conectar()
    cursor = conn.cursor()

    try:
        normalizar_busca_texto = helpers["normalizar_busca_texto"]
        extrair_modelo_da_descricao_aparelho = helpers["extrair_modelo_da_descricao_aparelho"]
        extrair_cor_da_descricao_aparelho = helpers["extrair_cor_da_descricao_aparelho"]
        nome_reparo_importavel = helpers["nome_reparo_importavel"]

        cursor.execute(
            """
            SELECT id, COALESCE(tipo, ''), COALESCE(modelo, ''), COALESCE(cor, ''), COALESCE(aparelho, '')
            FROM os
            WHERE origem_integracao='mercado_phone'
            """
        )
        for os_id, tipo, modelo, cor, aparelho in cursor.fetchall():
            novo_tipo = "Garantia" if "garantia" in normalizar_busca_texto(tipo) else "Assistencia"
            novo_modelo = modelo
            novo_cor = cor

            if (
                (not novo_modelo)
                or novo_modelo in {"Nao informado"}
                or "iphone" not in normalizar_busca_texto(novo_modelo)
            ):
                modelo_extraido = extrair_modelo_da_descricao_aparelho(aparelho or modelo)
                if modelo_extraido:
                    novo_modelo = modelo_extraido

            if not novo_cor:
                cor_extraida = extrair_cor_da_descricao_aparelho(aparelho or modelo, novo_modelo)
                if cor_extraida:
                    novo_cor = cor_extraida

            cursor.execute(
                "UPDATE os SET tipo=?, modelo=?, aparelho=?, cor=? WHERE id=?",
                (novo_tipo, novo_modelo, novo_modelo, novo_cor, os_id),
            )

        cursor.execute("SELECT id, nome FROM reparos")
        reparos = cursor.fetchall()
        reparos_invalidos = {reparo_id for reparo_id, nome in reparos if not nome_reparo_importavel(nome)}

        for reparo_id in reparos_invalidos:
            cursor.execute("DELETE FROM os_reparos WHERE reparo_id=?", (reparo_id,))

        cursor.execute(
            """
            UPDATE os
            SET reparo_id = (
                SELECT os_reparos.reparo_id
                FROM os_reparos
                WHERE os_reparos.os_id = os.id
                ORDER BY os_reparos.reparo_id
                LIMIT 1
            )
            WHERE origem_integracao='mercado_phone'
            """
        )

        cursor.execute(
            """
            DELETE FROM reparos
            WHERE id NOT IN (SELECT reparo_id FROM os_reparos)
              AND lower(COALESCE(nome, '')) IN ('iphone', 'ipad', 'smartphone', 'celular')
            """
        )
        conn.commit()
    finally:
        conn.close()


def loop_sincronizacao_mercado_phone(conectar, config, helpers):
    while True:
        try:
            if config["sync_enabled"] and config["api_token"]:
                resultado = sincronizar_mercado_phone(conectar, config, helpers)
                if resultado.get("importadas") > 0 or resultado.get("ignoradas") > 0:
                    logger.info(
                        "mercadophone_sync_resumo",
                        extra={"importadas": resultado.get("importadas"), "atualizadas": resultado.get("ignoradas")},
                    )
        except urllib_error.URLError as exc:
            logger.warning("mercadophone_sync_falha_rede", extra={"erro": f"{type(exc).__name__}: {exc}"})
        except Exception as exc:
            logger.error(
                "mercadophone_sync_falha_inesperada", extra={"erro": f"{type(exc).__name__}: {exc}"}, exc_info=True
            )
        time.sleep(max(30, config["sync_interval_seconds"]))


def reprocessar_todas_os_mercado_phone(conectar, config, helpers):
    """
    Busca TODOS os IDs externos de OSs vindas do MercadoPhone,
    obtém os dados atualizados da API e sobrescreve todos os campos locais.
    Também corrige o id_externo_integracao para usar o campo 'codigo' (ID visível).
    """
    texto_limpo = helpers["texto_limpo"]
    modelo_para_os = helpers["modelo_para_os"]
    extrair_modelo_da_descricao_aparelho = helpers["extrair_modelo_da_descricao_aparelho"]
    extrair_cor_da_descricao_aparelho = helpers["extrair_cor_da_descricao_aparelho"]
    normalizar_imei = helpers["normalizar_imei"]
    nome_reparo_importavel = helpers["nome_reparo_importavel"]
    obter_ou_criar_reparo = helpers["obter_ou_criar_reparo"]
    salvar_reparos_os = helpers["salvar_reparos_os"]
    normalizar_busca_texto = helpers["normalizar_busca_texto"]
    normalizar_status_os = helpers["normalizar_status_os"]
    canonicalizar_para_lista = helpers.get("canonicalizar_para_lista", lambda v, lista: "")
    lista_tecnicos = helpers.get("tecnicos", [])
    lista_vendedores = helpers.get("vendedores", [])

    conn = conectar()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id, id_externo_integracao FROM os WHERE origem_integracao='mercado_phone' ORDER BY id")
        registros = cursor.fetchall()
    finally:
        conn.close()

    atualizadas = 0
    erros = 0
    total = len(registros)

    for os_id_local, id_externo_atual in registros:
        if not id_externo_atual:
            erros += 1
            continue
        try:
            detalhes = detalhar_os_mercado_phone(id_externo_atual, config)
            payload = detalhes if isinstance(detalhes, dict) else {}
            if isinstance(payload.get("data"), dict):
                payload = payload["data"]
            if not isinstance(payload, dict) or not payload:
                erros += 1
                continue

            # ID correto: preferir campo 'codigo' (ID visível no Mercado Phone)
            id_externo_novo = texto_limpo(valor_payload(payload, ("codigo",), ("id",))) or id_externo_atual

            aparelho_info = primeiro_item_lista(payload, "aparelhos")
            servicos = lista_payload(payload, "servicos") or lista_payload(payload, "servicosOs")

            cliente = (
                texto_limpo(
                    valor_payload(payload, ("clienteNome",), ("cliente", "nome"), ("cliente_nome",), ("cliente",))
                )
                or "Cliente nao informado"
            )

            descricao_aparelho = texto_limpo(valor_payload(aparelho_info, ("descricao",)) or "")

            modelo = modelo_para_os(descricao_aparelho)
            if not modelo:
                modelo = extrair_modelo_da_descricao_aparelho(descricao_aparelho)
            if not modelo:
                modelo = "Nao informado"

            cor = extrair_cor_da_descricao_aparelho(descricao_aparelho, modelo)

            imei = normalizar_imei(valor_payload(aparelho_info, ("imei",), ("imei1",)))

            # Valores financeiros
            valor_cobrado = 0.0
            try:
                vt = valor_payload(payload, ("valorTotal",), ("valorTotalServicos",))
                if vt not in (None, "", 0):
                    valor_cobrado = _float_finito(vt)
            except (ValueError, TypeError):
                pass
            if not valor_cobrado:
                for s in servicos:
                    try:
                        vc = valor_payload(s, ("valorCobranca",))
                        if vc not in (None, "", 0):
                            valor_cobrado += _float_finito(vc)
                    except (ValueError, TypeError):
                        pass

            custo_pecas = 0.0
            for s in servicos:
                try:
                    custo = valor_payload(s, ("valorCusto",))
                    if custo not in (None, "", 0):
                        custo_pecas += _float_finito(custo)
                except (ValueError, TypeError):
                    pass

            # BR-061 (V1.5 -- Garantia de Reparo): mesma exceção deliberada da
            # sincronização incremental (ver importar_os_mercado_phone) --
            # reimportação em massa também está isenta da exigência de
            # tipo_garantia_id por linha de reparo.
            status = normalizar_status_os(valor_payload(payload, ("situacaoDescricao",), ("status",)))
            _tecnico_raw = (
                texto_limpo(valor_payload(payload, ("tecnicoNome",), ("tecnico", "nome"))) or config["default_tecnico"]
            )
            tecnico = canonicalizar_para_lista(_tecnico_raw, lista_tecnicos) or _tecnico_raw
            _vendedor_raw = texto_limpo(valor_payload(payload, ("vendedorNome",), ("vendedor", "nome")))
            vendedor = canonicalizar_para_lista(_vendedor_raw, lista_vendedores) or _vendedor_raw

            data_os = texto_limpo(valor_payload(payload, ("dataCriacao",), ("data",), ("created_at",), ("createdAt",)))[
                :10
            ]

            tipo_origem = texto_limpo(valor_payload(payload, ("tipoDescricao",), ("tipo",)))
            tipo = "Garantia" if "garantia" in normalizar_busca_texto(tipo_origem) else "Assistencia"

            observacoes_partes = [
                "Importada automaticamente do Mercado Phone.",
                texto_limpo(valor_payload(payload, ("defeito",))),
                texto_limpo(valor_payload(payload, ("diagnostico",))),
                texto_limpo(valor_payload(payload, ("observacao",))),
                texto_limpo(valor_payload(payload, ("observacaoInterna",))),
                texto_limpo(valor_payload(payload, ("solucao",))),
            ]
            observacoes = " | ".join(p for p in observacoes_partes if p)

            # Reparos
            reparos_nomes = []
            for servico in servicos:
                if not isinstance(servico, dict):
                    continue
                nome_servico = texto_limpo(valor_payload(servico, ("servicoDescricao",), ("descricao",), ("nome",)))
                for reparo_nome in _extrair_reparos_mercado_phone(
                    nome_servico, nome_reparo_importavel, normalizar_busca_texto, texto_limpo
                ):
                    if reparo_nome not in reparos_nomes:
                        reparos_nomes.append(reparo_nome)
            if not reparos_nomes:
                reparos_nomes = ["Nao informado"]

            conn2 = conectar()
            cursor2 = conn2.cursor()
            try:
                reparo_ids = []
                for nome_reparo in reparos_nomes:
                    reparo_id = obter_ou_criar_reparo(cursor2, nome_reparo)
                    if reparo_id and reparo_id not in reparo_ids:
                        reparo_ids.append(reparo_id)

                reparo_principal_id = reparo_ids[0] if reparo_ids else None

                cursor2.execute(
                    """
                    UPDATE os SET
                        tipo=?, cliente=?, aparelho=?, tecnico=?, reparo_id=?,
                        status=?, valor_cobrado=?, custo_pecas=?,
                        observacoes=?, modelo=?, vendedor=?, cor=?, imei=?,
                        id_externo_integracao=?
                    """
                    + (", data=?" if data_os else "")
                    + """
                    WHERE id=?
                    """,
                    (
                        tipo,
                        cliente,
                        descricao_aparelho or modelo,
                        tecnico,
                        reparo_principal_id,
                        status,
                        valor_cobrado,
                        custo_pecas,
                        observacoes,
                        modelo,
                        vendedor,
                        cor,
                        imei,
                        id_externo_novo,
                        *(([data_os]) if data_os else []),
                        os_id_local,
                    ),
                )
                salvar_reparos_os(cursor2, os_id_local, reparo_ids)
                conn2.commit()
                atualizadas += 1
                logger.info(
                    "mercadophone_os_local_reprocessada",
                    extra={
                        "os_id": os_id_local,
                        "codigo_externo_antigo": id_externo_atual,
                        "codigo_externo_novo": id_externo_novo,
                    },
                )
            except Exception as exc:
                conn2.rollback()
                erros += 1
                logger.error(
                    "mercadophone_erro_ao_salvar_os_local",
                    extra={"os_id": os_id_local, "erro": f"{type(exc).__name__}: {exc}"},
                    exc_info=True,
                )
            finally:
                conn2.close()

        except Exception as exc:
            erros += 1
            logger.error(
                "mercadophone_erro_ao_reprocessar_os_local",
                extra={"os_id": os_id_local, "erro": f"{type(exc).__name__}: {exc}"},
                exc_info=True,
            )

    return {"ok": True, "total": total, "atualizadas": atualizadas, "erros": erros}


def reimportar_todas_os_mercado_phone(conectar, config, helpers):
    """
    Remove todas as OSs importadas do MercadoPhone e importa novamente do zero.
    """
    # Ajustes mais tolerantes para importações longas em rede instável.
    config_forcada = dict(config)
    config_forcada["sync_only_after_boot"] = False
    config_forcada["sync_timeout_seconds"] = max(60, int(config.get("sync_timeout_seconds") or 20))
    config_forcada["sync_request_retries"] = max(5, int(config.get("sync_request_retries") or 3))

    # Só apaga se a API estiver acessível no momento.
    try:
        listar_os_mercado_phone(config_forcada, page=1, limit=1)
    except Exception as exc:
        raise RuntimeError(
            f"API MercadoPhone indisponível agora ({type(exc).__name__}: {exc}). "
            "Reimportação cancelada sem apagar dados locais."
        ) from exc

    conn = conectar()
    cursor = conn.cursor()
    removidas = 0

    try:
        cursor.execute("SELECT COUNT(1) FROM os WHERE origem_integracao='mercado_phone'")
        row = cursor.fetchone()
        removidas = int(row[0] or 0) if row else 0

        cursor.execute(
            """
            DELETE FROM os_reparos
            WHERE os_id IN (SELECT id FROM os WHERE origem_integracao='mercado_phone')
            """
        )
        cursor.execute("DELETE FROM os WHERE origem_integracao='mercado_phone'")
        cursor.execute("DELETE FROM integracao_os_vistas WHERE origem='mercado_phone'")
        definir_estado_integracao(cursor, "mercado_phone_sync_inicializado", "1")
        conn.commit()
    finally:
        conn.close()

    tentativas = max(1, int(config.get("reimport_retry_attempts") or 3))
    max_esperas_lock_ocupado = max(1, tentativas * 2)
    resultado_sync = {"importadas": 0, "ignoradas": 0}
    ultima_falha = ""
    tentativa = 0
    esperas_lock_ocupado = 0

    while tentativa < tentativas:
        tentativa += 1
        try:
            resultado_sync = sincronizar_mercado_phone(conectar, config_forcada, helpers)

            if resultado_sync.get("lock_ocupado"):
                # Outro worker esta sincronizando agora (INC-002) - nao e "nada para
                # importar", e sim "nao rodou ainda". Nao conta como tentativa real
                # (orcamento proprio, limitado) para nao deixar a limpeza acima sem
                # reimportacao so porque o lock estava ocupado no momento errado.
                esperas_lock_ocupado += 1
                tentativa -= 1
                ultima_falha = "lock de sincronizacao ocupado por outro worker"
                if esperas_lock_ocupado >= max_esperas_lock_ocupado:
                    break
                espera = min(15, 3 * esperas_lock_ocupado)
                logger.warning("mercadophone_reimportacao_retry", extra={"motivo": ultima_falha, "espera_s": espera})
                time.sleep(espera)
                continue

            importadas = int(resultado_sync.get("importadas") or 0)
            ignoradas = int(resultado_sync.get("ignoradas") or 0)

            # Após limpar tudo, esperamos importações > 0. Se vier 0 com muitas ignoradas,
            # normalmente houve instabilidade e vale tentar novamente.
            if importadas > 0 or ignoradas == 0:
                break

            ultima_falha = f"tentativa {tentativa}: importadas=0 e ignoradas={ignoradas}"
        except Exception as exc:
            ultima_falha = f"tentativa {tentativa}: {type(exc).__name__}: {exc}"

        if tentativa < tentativas:
            espera = min(15, 3 * tentativa)
            logger.warning("mercadophone_reimportacao_retry", extra={"motivo": ultima_falha, "espera_s": espera})
            time.sleep(espera)

    return {
        "ok": True,
        "removidas": removidas,
        "importadas": int(resultado_sync.get("importadas") or 0),
        "atualizadas": int(resultado_sync.get("ignoradas") or 0),
        "tentativas": tentativas,
        "observacao": ultima_falha,
    }
