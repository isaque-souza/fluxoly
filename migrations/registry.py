"""Lista explícita e ordenada de migrations -- sem reflexão/auto-discovery
sobre migrations/versions/ (mesma decisão deliberada da TD-02, ver
fluxoly_blueprint_registry.py). Uma migration nova sempre entra no fim da
lista, nunca no meio."""

from migrations.versions import (
    m0001_baseline,
    m0002_financeiro_minimo,
    m0003_compras_aparelhos,
    m0004_dados_loja,
    m0005_os_data_previsao,
)

MIGRATIONS = [
    m0001_baseline,
    m0002_financeiro_minimo,
    m0003_compras_aparelhos,
    m0004_dados_loja,
    m0005_os_data_previsao,
]
