import json
import os
import re

from fluxoly_core import normalizar_busca_texto, texto_limpo
from fluxoly_reference_data import IPHONE_ALIAS_MAP, normalizar_modelo_iphone


def tabelas_preco_vazias():
    return {"clientes": {}}


_SERVICO_STOPWORDS = {"troca", "reparo", "de", "do", "da", "dos", "das", "com"}


def _modelo_canonico_iphone(valor):
    texto = texto_limpo(valor).strip(" -–—")
    if not texto:
        return ""

    modelo = normalizar_modelo_iphone(texto)
    if modelo:
        return modelo

    normalizado = normalizar_busca_texto(texto)
    sem_prefixo = re.sub(r"^iphone\s+", "", normalizado).strip()
    return (
        IPHONE_ALIAS_MAP.get(normalizado)
        or IPHONE_ALIAS_MAP.get(sem_prefixo)
        or IPHONE_ALIAS_MAP.get(sem_prefixo.replace(" ", ""))
        or ""
    )


def _parece_modelo_iphone(valor):
    if _modelo_canonico_iphone(valor):
        return True
    normalizado = normalizar_busca_texto(valor)
    return bool(re.match(r"^(iphone\s+)?\d{1,2}(?:\s+(?:pro\s+max|pro|max|plus|mini|e))?$", normalizado))


def _normalizar_modelo_tabela(valor):
    texto = texto_limpo(valor).strip(" -–—")
    return _modelo_canonico_iphone(texto) or texto


def _normalizar_servico_tabela(valor):
    texto = " ".join(texto_limpo(valor).replace("\r", " ").replace("\n", " ").split())
    return texto.upper()


def _registrar_preco(destino, servico, modelo, valor):
    servico_key = _normalizar_servico_tabela(servico)
    modelo_key = _normalizar_modelo_tabela(modelo)
    if not servico_key or not modelo_key:
        return
    try:
        preco = float(valor)
    except (TypeError, ValueError):
        return
    destino.setdefault(servico_key, {})[modelo_key] = preco


def _normalizar_tabela_preco(tabela):
    normalizada = {}
    if not isinstance(tabela, dict):
        return normalizada

    for chave_externa, valores in tabela.items():
        if not isinstance(valores, dict):
            continue

        if _parece_modelo_iphone(chave_externa):
            modelo = _normalizar_modelo_tabela(chave_externa)
            for servico, valor in valores.items():
                _registrar_preco(normalizada, servico, modelo, valor)
            continue

        servico = _normalizar_servico_tabela(chave_externa)
        for modelo, valor in valores.items():
            _registrar_preco(normalizada, servico, modelo, valor)

    return normalizada


def _gerar_candidatos_servico(nome_reparo):
    texto = " ".join(texto_limpo(nome_reparo).replace("\r", " ").replace("\n", " ").split())
    if not texto:
        return []

    normalizado = normalizar_busca_texto(texto)
    candidatos = {normalizado}
    sem_prefixo = re.sub(r"^(troca|reparo)\s+(de|do|da|dos|das)\s+", "", normalizado).strip()
    if sem_prefixo:
        candidatos.add(sem_prefixo)

    if "bateria" in sem_prefixo:
        candidatos.add("bateria")
    if "tela" in sem_prefixo:
        candidatos.add("tela")
    if "tela" in sem_prefixo and "original" in sem_prefixo:
        candidatos.add("tela original")
    if "dock" in sem_prefixo or "conector" in sem_prefixo or "carga" in sem_prefixo:
        candidatos.update({"dock de carga", "conector de carga dock", "conector"})
    if "auricular" in sem_prefixo:
        candidatos.update({"auricular", "alto falante auricular"})
    if "alto falante" in sem_prefixo:
        candidatos.add("alto falante")
    if "camera frontal" in sem_prefixo:
        candidatos.add("camera frontal")
    if "camera traseira" in sem_prefixo:
        candidatos.add("camera traseira")
    if "lente" in sem_prefixo and "camera" in sem_prefixo:
        candidatos.add("lente da camera")
    if "face id" in sem_prefixo:
        candidatos.add("face id")
    if "flash" in sem_prefixo:
        candidatos.add("flash")
    if "botoes" in sem_prefixo or "botao" in sem_prefixo:
        candidatos.update({"botoes", "flex botoes"})
    if "vibra" in sem_prefixo or "vibr" in sem_prefixo:
        candidatos.add("motor de vibracao")
    if "placa" in sem_prefixo:
        candidatos.update({"placa", "placa mae"})
    if "carcaca" in sem_prefixo:
        candidatos.add("carcaca")
    if "tampa traseira" in sem_prefixo or "vidro traseiro" in sem_prefixo:
        candidatos.add("tampa traseira")

    return [c for c in candidatos if c]


def _tokens_relevantes(texto):
    tokens = []
    for token in normalizar_busca_texto(texto).split():
        if token in _SERVICO_STOPWORDS:
            continue
        if token.startswith("vibr"):
            token = "vibracao"
        if token == "vibra":
            token = "vibracao"
        tokens.append(token)
    return tokens


def _contar_tokens_compativeis(tokens_a, tokens_b):
    usados = set()
    total = 0
    for token_a in tokens_a:
        for index_b, token_b in enumerate(tokens_b):
            if index_b in usados:
                continue
            if token_a == token_b:
                usados.add(index_b)
                total += 1
                break
            if min(len(token_a), len(token_b)) >= 4 and (token_a.startswith(token_b) or token_b.startswith(token_a)):
                usados.add(index_b)
                total += 1
                break
    return total


def encontrar_servico_tabela(nome_reparo, tabela):
    if not nome_reparo or not isinstance(tabela, dict):
        return ""

    servicos = [servico for servico in tabela if isinstance(servico, str)]
    if not servicos:
        return ""

    servicos_normalizados = {servico: normalizar_busca_texto(servico) for servico in servicos}
    candidatos = _gerar_candidatos_servico(nome_reparo)

    for candidato in candidatos:
        for servico, servico_normalizado in servicos_normalizados.items():
            if candidato == servico_normalizado:
                return servico

    melhor_servico = ""
    melhor_pontuacao = 0.0
    for servico, servico_normalizado in servicos_normalizados.items():
        tokens_servico = _tokens_relevantes(servico_normalizado)
        if not tokens_servico:
            continue
        for candidato in candidatos:
            tokens_candidato = _tokens_relevantes(candidato)
            if not tokens_candidato:
                continue
            correspondencias = _contar_tokens_compativeis(tokens_candidato, tokens_servico)
            if not correspondencias:
                continue
            precisao = correspondencias / len(tokens_servico)
            cobertura = correspondencias / len(tokens_candidato)
            pontuacao = precisao + cobertura
            if candidato in servico_normalizado or servico_normalizado in candidato:
                pontuacao += 0.25
            if pontuacao > melhor_pontuacao:
                melhor_pontuacao = pontuacao
                melhor_servico = servico

    return melhor_servico if melhor_pontuacao >= 1.2 else ""


def sugerir_preco_tabela(tabelas, tabela, modelo, nomes_reparos):
    tabela_data = (tabelas or {}).get(tabela, {})
    modelo_key = _normalizar_modelo_tabela(modelo)
    if not modelo_key or not isinstance(tabela_data, dict):
        return 0.0, False

    total = 0.0
    encontrou = False
    servicos_usados = set()
    for nome_reparo in nomes_reparos or []:
        servico = encontrar_servico_tabela(nome_reparo, tabela_data)
        if not servico or servico in servicos_usados:
            continue
        valor = tabela_data.get(servico, {}).get(modelo_key)
        if valor is None:
            continue
        total += float(valor)
        encontrou = True
        servicos_usados.add(servico)
    return round(total, 2), encontrou


def carregar_tabelas_preco(caminho_arquivo):
    if not os.path.exists(caminho_arquivo):
        return tabelas_preco_vazias()
    try:
        with open(caminho_arquivo, encoding="utf-8") as arquivo:
            tabelas = json.load(arquivo)
    except (OSError, json.JSONDecodeError):
        return tabelas_preco_vazias()
    return {
        "clientes": _normalizar_tabela_preco((tabelas or {}).get("clientes", {})),
    }


def salvar_tabelas_preco(caminho_arquivo, tabelas):
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(tabelas, arquivo, ensure_ascii=False, indent=2)
