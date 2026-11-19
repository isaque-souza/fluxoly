"""
Camada compartilhada de parsing e validação de entrada para rotas Flask.

Usada pelos endpoints JSON de `fluxoly_blueprints_api.py`. Os blueprints
HTML (admin/inventory/orders/auth) usam fluxo `flash()`/`redirect()` e não
consomem estes utilitários.

Números não finitos (Infinity, -Infinity, NaN e o que estoura o float, como 1e400) contam como
entrada inválida (P1-1, QA 2026-11-12): não são JSON válido na resposta e corrompem somas.
"""

import math

from flask import has_request_context, request
from flask.json.provider import DefaultJSONProvider

from fluxoly_logging import get_logger

logger = get_logger("fluxoly_validation")


def parse_int(value, default=0):
    """
    Converte `value` para int.

    Ausente ou string vazia -> `default`.
    Presente mas não conversível -> `None` (sinaliza entrada inválida;
    não mascara como `default`, para não transformar um erro de input em
    um valor de negócio silenciosamente aceito).
    """
    if value in (None, ""):
        return default
    if isinstance(value, float) and not math.isfinite(value):
        return None
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return None


def parse_float(value, default=0.0):
    """Mesmo contrato de `parse_int`, para valores de ponto flutuante."""
    if value in (None, ""):
        return default
    try:
        numero = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return numero if math.isfinite(numero) else None


def safe_json(request_obj):
    """Corpo JSON da requisição como dict, nunca `None` e nunca levanta exceção."""
    return request_obj.get_json(silent=True) or {}


def validate_positive_number(value):
    """True se `value` é conversível para float finito e estritamente positivo."""
    numero = parse_float(value, default=None)
    return numero is not None and numero > 0


def _sem_nao_finitos(obj):
    """Cópia de `obj` com cada float não finito trocado por None (dicts, listas e tuplas)."""
    if isinstance(obj, float):
        return obj if math.isfinite(obj) else None
    if isinstance(obj, dict):
        return {k: _sem_nao_finitos(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_sem_nao_finitos(v) for v in obj]
    return obj


class JSONProviderFinito(DefaultJSONProvider):
    """Respostas nunca saem com Infinity/NaN, que não são JSON válido (P1-1).

    Caminho normal: `allow_nan=False`, sem custo extra. Se a resposta tiver um valor não
    finito (só acontece com dado gravado antes da validação de entrada), ele sai como `null`
    e um aviso vai para o log com a rota -- a tela continua funcionando, nada é alterado no
    banco e o dado continua detectável. Não substitui a validação de entrada.
    """

    def dumps(self, obj, **kwargs):
        kwargs.setdefault("allow_nan", False)
        try:
            return super().dumps(obj, **kwargs)
        except ValueError:
            rota = request.path if has_request_context() else None
            logger.warning("resposta_com_valor_nao_finito", extra={"rota": rota})
            return super().dumps(_sem_nao_finitos(obj), **kwargs)
