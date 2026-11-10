"""
KI-059 -- valor da OS (`calcular_faturamento_os`): o "Valor com Desconto"
(`valor_descontado`) é o preço final e vale quando preenchido; sem ele, vale o
Valor Cobrado. A mesma função alimenta listagem, relatórios, lucro e os
documentos da OS para o cliente (BR-095/BR-096).
"""

import pytest

from fluxoly_core import calcular_faturamento_os, calcular_lucro_os


@pytest.mark.parametrize(
    ("cobrado", "com_desconto", "esperado"),
    [
        (500.0, 450.0, 450.0),  # os dois preenchidos: vale o com desconto
        (500.0, 0.0, 500.0),
        (500.0, None, 500.0),
        (0.0, 280.0, 280.0),
        (None, None, 0),
    ],
)
def test_valor_da_os(cobrado, com_desconto, esperado):
    assert calcular_faturamento_os(cobrado, com_desconto) == esperado


def test_lucro_usa_o_valor_com_desconto():
    assert calcular_lucro_os("Assistencia", 500.0, 450.0, 100.0) == 350.0


def test_documento_do_cliente_usa_o_valor_com_desconto(client, login_como, usuario_tecnico, criar_os):
    import app as _app

    conn = _app.conectar()
    try:
        conn.execute("DELETE FROM dados_loja")
        conn.execute("INSERT INTO dados_loja (id, nome_fantasia) VALUES (1, 'Loja KI-059')")
        conn.commit()
    finally:
        conn.close()
    try:
        login_como(client, usuario_tecnico)
        os_id = criar_os(valor_cobrado=500.0, valor_descontado=450.0)
        doc = client.get(f"/api/ordens/{os_id}/documento?tipo=entrada").get_json()["documento"]
        assert doc["ordem"]["valor_total"] == 450.0
    finally:
        conn = _app.conectar()
        try:
            conn.execute("DELETE FROM dados_loja")
            conn.commit()
        finally:
            conn.close()
