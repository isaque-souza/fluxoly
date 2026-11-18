"""
TD-02 Fatia 3 (docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md) -- registro
centralizado dos blueprints do Fluxoly Platform (22 desde o Financeiro Mínimo,
que adicionou Caixa/Contas a Pagar/Contas a Receber -- ver
docs/engineering/plans/PLAN-financeiro-minimo.md; 19 desde a TD-18, que removeu
o registro do blueprint vazio de fluxoly_blueprints_api.py -- ver KI-032).

registrar_blueprints(app, runtime) substitui as chamadas app.register_blueprint(...)
que antes viviam inline em app.py (bloco K). Nenhuma factory create_*_blueprint muda --
só o local onde o dict de deps de cada uma é montado.

runtime (RuntimeDeps) carrega só os valores que são construídos em runtime dentro de
app.py e por isso não podem ser importados diretamente daqui sem criar import circular
(app.py importaria este módulo, que importaria de volta de app.py). Tudo o mais que os
blueprints precisam -- constantes e funções puras de outros módulos -- é importado
direto no topo deste arquivo, exatamente como app.py fazia antes desta extração.
"""

import functools
from collections.abc import Callable
from dataclasses import dataclass

from werkzeug.security import check_password_hash, generate_password_hash

from api_auth import create_api_auth_blueprint
from api_backup import create_api_backup_blueprint
from api_costs import create_api_costs_blueprint
from api_garantias import create_api_garantias_blueprint
from api_mercadophone import create_api_mercadophone_blueprint
from api_os import create_api_os_blueprint
from api_prices import create_api_prices_blueprint
from api_reports import create_api_reports_blueprint
from api_shopping import create_api_shopping_blueprint
from api_stock import create_api_stock_blueprint
from api_system import create_api_system_blueprint
from api_users import create_api_users_blueprint
from fluxoly_audit import registrar_log_auditoria
from fluxoly_blueprints_auth import create_auth_blueprint
from fluxoly_blueprints_main import create_main_blueprint
from fluxoly_caixa_controller import create_caixa_blueprint
from fluxoly_clientes_controller import create_clientes_blueprint
from fluxoly_compras_aparelhos_controller import create_compras_aparelhos_blueprint
from fluxoly_config import (
    BACKUP_DIR,
    DB_PATH,
    INTEGRATIONS_CONFIG_PATH,
    PUBLIC_BASE_URL,
)
from fluxoly_contas_pagar_controller import create_contas_pagar_blueprint
from fluxoly_contas_receber_controller import create_contas_receber_blueprint
from fluxoly_dados_loja_controller import create_dados_loja_blueprint
from fluxoly_core import (
    GARANTIA_REPARO_DIAS_PADRAO,
    OS_TIPOS_OPCOES,
    PERFIS_OPCOES,
    STATUS_AGUARDANDO_PECA,
    STATUS_CANCELADO,
    STATUS_EM_ANDAMENTO,
    STATUS_FINALIZADO,
    STATUS_OS_OPCOES,
    calcular_faturamento_os,
    calcular_lucro_os,
    coletar_status_opcoes,
    normalizar_status_os,
    status_aberto,
    status_cancelado,
    status_finalizado,
)
from fluxoly_mercadophone import (
    reimportar_todas_os_mercado_phone,
    reprocessar_todas_os_mercado_phone,
    sincronizar_mercado_phone,
)
from fluxoly_os import (
    adicionar_peca_os_sem_consumir,
    buscar_garantia_reparo,
    buscar_historico_garantia_reparo,
    buscar_linhas_com_garantia_da_os,
    buscar_reparo_ids_da_os,
    carregar_os_com_relacoes,
    consumir_peca_da_os,
    corrigir_garantia_reparo,
    devolver_pecas_da_os,
    gravar_garantias_reparo,
    modelo_compativel,
    obter_reparos_por_os,
    registrar_movimentacao,
    resolver_garantias_reparo,
    salvar_reparos_os,
    validar_reparo_ids,
    vendedor_valido,
    zerar_garantia_reparo,
)
from fluxoly_produtos_controller import create_produtos_blueprint
from fluxoly_rate_limit import limite_excedido, registrar_tentativa, resolver_ip_cliente
from fluxoly_reference_data import (
    CATEGORIAS_CUSTOS_OPERACIONAIS,
    ESTOQUE_QUALIDADES,
    ESTOQUE_TIPOS,
    IPHONE_COLORS,
    IPHONE_MODELS,
    PRODUTOS_CATEGORIAS,
    PRODUTOS_CONDICOES,
    REPAROS_PADRAO,
    TECNICOS,
    VENDEDORES,
    modelo_para_os,
    normalizar_imei,
    normalizar_modelo_iphone,
)
from fluxoly_reports import (
    agrupar_relatorio_custos_operacionais,
    agrupar_relatorio_tecnicos,
    formatar_periodo_relatorio,
    montar_linhas_relatorio_custos_operacionais,
    montar_linhas_relatorio_tecnicos,
    montar_pdf_texto,
    texto_reparos_os,
)
from fluxoly_storage import (
    carregar_configuracoes_integracoes,
    criar_backup,
    salvar_configuracoes_integracoes,
)
from fluxoly_tipos_garantia_controller import create_tipos_garantia_blueprint
from fluxoly_auditoria_controller import create_auditoria_blueprint
from fluxoly_tipos_garantia_service import obter_tipo_garantia
from fluxoly_unidades_serializadas_controller import create_unidades_serializadas_blueprint
from fluxoly_vendas_controller import create_vendas_blueprint


@dataclass
class RuntimeDeps:
    """Valores construídos em runtime dentro de app.py -- não importáveis direto
    daqui sem criar import circular. Ver seção 3 de
    docs/operations/SPRINTS/SPRINT_TD02_BOOTSTRAP_APP.md (Phase 1) para a origem
    dos primeiros 8 campos.

    parse_data_ymd (9º campo, achado durante a implementação da Fatia 3, fora do
    mapeamento original de 8 campos da Phase 1): função pura definida em app.py
    (bloco E, "Helpers soltos"), sem closure sobre estado de runtime -- mas só
    existe em app.py hoje, então entra aqui pelo mesmo motivo que conectar:
    evitar import circular. Decisão do CTO (2026-08-08): não mover a função de
    lugar nesta fatia -- seria uma decisão arquitetural própria, fora do
    objetivo do registry -- só adicionar como campo.
    """

    conectar: Callable
    carregar_tabelas_preco: Callable
    salvar_tabelas_preco: Callable
    forcar_migracao_schema: Callable
    mercado_phone_runtime_config: dict
    mercado_phone_helpers: dict
    listar_custos_operacionais: Callable
    obter_alertas_sistema: Callable
    parse_data_ymd: Callable


def registrar_blueprints(app, runtime: RuntimeDeps) -> None:
    """Registra os blueprints do Fluxoly Platform, mesma ordem e mesmos
    dicts de deps que existiam inline em app.py antes da TD-02 Fatia 3."""

    conectar = runtime.conectar

    # ========================================================================
    # REGISTRO DO BLUEPRINT PRINCIPAL (views legadas server-rendered)
    # ========================================================================
    app.register_blueprint(
        create_main_blueprint(
            {
                "carregar_os_com_relacoes": carregar_os_com_relacoes,
                "texto_reparos_os": texto_reparos_os,
                "normalizar_status_os": normalizar_status_os,
                "status_cancelado": status_cancelado,
                "status_finalizado": status_finalizado,
                "status_aberto": status_aberto,
                "coletar_status_opcoes": coletar_status_opcoes,
                "calcular_faturamento_os": calcular_faturamento_os,
                "calcular_lucro_os": calcular_lucro_os,
                "listar_custos_operacionais": runtime.listar_custos_operacionais,
                "categorias_custos_operacionais": CATEGORIAS_CUSTOS_OPERACIONAIS,
                "agrupar_relatorio_tecnicos": functools.partial(agrupar_relatorio_tecnicos, conectar=conectar),
                "formatar_periodo_relatorio": formatar_periodo_relatorio,
                "montar_linhas_relatorio_tecnicos": functools.partial(
                    montar_linhas_relatorio_tecnicos, conectar=conectar
                ),
                "montar_pdf_texto": montar_pdf_texto,
                "obter_reparos_por_os": obter_reparos_por_os,
                "status_em_andamento": STATUS_EM_ANDAMENTO,
                "status_aguardando_peca_const": STATUS_AGUARDANDO_PECA,
                "status_finalizado_const": STATUS_FINALIZADO,
                "status_cancelado_const": STATUS_CANCELADO,
                "parse_data_ymd": runtime.parse_data_ymd,
                "backup_dir": BACKUP_DIR,
            }
        )
    )

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE AUTENTICAÇÃO
    # ========================================================================
    app.register_blueprint(
        create_auth_blueprint(
            {
                "conectar": conectar,
                "generate_password_hash": generate_password_hash,
                "check_password_hash": check_password_hash,
                "resolver_ip_cliente": resolver_ip_cliente,
                "limite_excedido": limite_excedido,
                "registrar_tentativa": registrar_tentativa,
                "perfis_opcoes": PERFIS_OPCOES,
            }
        )
    )

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE API (JSON — consumido pelo frontend React)
    # ========================================================================
    app.register_blueprint(
        create_api_shopping_blueprint(
            {
                "conectar": conectar,
            }
        )
    )

    app.register_blueprint(
        create_api_garantias_blueprint(
            {
                "conectar": conectar,
                "garantia_reparo_dias_padrao": GARANTIA_REPARO_DIAS_PADRAO,
                "parse_data_ymd": runtime.parse_data_ymd,
            }
        )
    )

    app.register_blueprint(
        create_api_costs_blueprint(
            {
                "conectar": conectar,
                "listar_custos_operacionais": runtime.listar_custos_operacionais,
            }
        )
    )

    app.register_blueprint(
        create_api_prices_blueprint(
            {
                "conectar": conectar,
                "carregar_tabelas_preco": runtime.carregar_tabelas_preco,
                "salvar_tabelas_preco": runtime.salvar_tabelas_preco,
            }
        )
    )

    app.register_blueprint(
        create_api_users_blueprint(
            {
                "conectar": conectar,
                "generate_password_hash": generate_password_hash,
                "perfis_opcoes": PERFIS_OPCOES,
            }
        )
    )

    app.register_blueprint(
        create_api_auth_blueprint(
            {
                "conectar": conectar,
                "check_password_hash": check_password_hash,
                "resolver_ip_cliente": resolver_ip_cliente,
                "limite_excedido": limite_excedido,
                "registrar_tentativa": registrar_tentativa,
            }
        )
    )

    app.register_blueprint(
        create_api_mercadophone_blueprint(
            {
                "conectar": conectar,
                "sincronizar_mercado_phone": sincronizar_mercado_phone,
                "reimportar_todas_os_mercado_phone": reimportar_todas_os_mercado_phone,
                "reprocessar_todas_os_mercado_phone": reprocessar_todas_os_mercado_phone,
                "mercado_phone_runtime_config": runtime.mercado_phone_runtime_config,
                "mercado_phone_helpers": runtime.mercado_phone_helpers,
                "integrations_config_path": INTEGRATIONS_CONFIG_PATH,
                "carregar_configuracoes_integracoes": carregar_configuracoes_integracoes,
                "salvar_configuracoes_integracoes": salvar_configuracoes_integracoes,
            }
        )
    )

    app.register_blueprint(
        create_api_reports_blueprint(
            {
                "agrupar_relatorio_tecnicos": functools.partial(agrupar_relatorio_tecnicos, conectar=conectar),
                "agrupar_relatorio_custos_operacionais": functools.partial(
                    agrupar_relatorio_custos_operacionais, conectar=conectar
                ),
                "montar_linhas_relatorio_tecnicos": functools.partial(
                    montar_linhas_relatorio_tecnicos, conectar=conectar
                ),
                "montar_linhas_relatorio_custos_operacionais": functools.partial(
                    montar_linhas_relatorio_custos_operacionais, conectar=conectar
                ),
                "formatar_periodo_relatorio": formatar_periodo_relatorio,
                "montar_pdf_texto": montar_pdf_texto,
            }
        )
    )

    app.register_blueprint(
        create_api_backup_blueprint(
            {
                "conectar": conectar,
                "backup_dir": BACKUP_DIR,
                "criar_backup": criar_backup,
                "db_path": DB_PATH,
                "forcar_migracao_schema": runtime.forcar_migracao_schema,
            }
        )
    )

    app.register_blueprint(
        create_api_system_blueprint(
            {
                "conectar": conectar,
                "normalizar_status_os": normalizar_status_os,
                "status_finalizado": status_finalizado,
                "status_cancelado": status_cancelado,
                "status_aberto": status_aberto,
                "calcular_faturamento_os": calcular_faturamento_os,
                "calcular_lucro_os": calcular_lucro_os,
                "carregar_os_com_relacoes": carregar_os_com_relacoes,
                "listar_custos_operacionais": runtime.listar_custos_operacionais,
                "obter_alertas_sistema": runtime.obter_alertas_sistema,
                "iphone_models": IPHONE_MODELS,
                "iphone_colors": IPHONE_COLORS,
                "vendedores": VENDEDORES,
                "tecnicos": TECNICOS,
                "status_os_opcoes": STATUS_OS_OPCOES,
                "os_tipos_opcoes": OS_TIPOS_OPCOES,
                "garantia_reparo_dias_padrao": GARANTIA_REPARO_DIAS_PADRAO,
                "categorias_custos": CATEGORIAS_CUSTOS_OPERACIONAIS,
                "reparos_padrao": REPAROS_PADRAO,
                "produtos_categorias": PRODUTOS_CATEGORIAS,
                "produtos_condicoes": PRODUTOS_CONDICOES,
                "estoque_tipos": ESTOQUE_TIPOS,
                "estoque_qualidades": ESTOQUE_QUALIDADES,
            }
        )
    )

    app.register_blueprint(
        create_api_stock_blueprint(
            {
                "conectar": conectar,
                "normalizar_modelo_iphone": normalizar_modelo_iphone,
                "registrar_movimentacao": registrar_movimentacao,
                "estoque_tipos": ESTOQUE_TIPOS,
                "estoque_qualidades": ESTOQUE_QUALIDADES,
            }
        )
    )

    # api_os.py -- domínio OS + Reparos catálogo (TD-01 Phase 2, 12º e último
    # domínio extraído, 2026-08-07). Único ponto que ainda importa
    # carregar_config_mercadophone/atualizar_runtime_mercadophone diretamente de
    # fluxoly_mercadophone.py (não via deps) -- listar_ordens() usa essas duas
    # funções para filtrar OS antigas da integração, mesmo padrão já usado no
    # monólito antes desta extração.
    app.register_blueprint(
        create_api_os_blueprint(
            {
                "conectar": conectar,
                "normalizar_status_os": normalizar_status_os,
                "status_finalizado": status_finalizado,
                "status_cancelado": status_cancelado,
                "status_aberto": status_aberto,
                "calcular_faturamento_os": calcular_faturamento_os,
                "calcular_lucro_os": calcular_lucro_os,
                "carregar_os_com_relacoes": carregar_os_com_relacoes,
                "validar_reparo_ids": validar_reparo_ids,
                "vendedor_valido": vendedor_valido,
                "salvar_reparos_os": salvar_reparos_os,
                "modelo_compativel": modelo_compativel,
                "consumir_peca_da_os": consumir_peca_da_os,
                "adicionar_peca_os_sem_consumir": adicionar_peca_os_sem_consumir,
                "devolver_pecas_da_os": devolver_pecas_da_os,
                "obter_reparos_por_os": obter_reparos_por_os,
                "buscar_reparo_ids_da_os": buscar_reparo_ids_da_os,
                "resolver_garantias_reparo": resolver_garantias_reparo,
                "gravar_garantias_reparo": gravar_garantias_reparo,
                "buscar_linhas_com_garantia_da_os": buscar_linhas_com_garantia_da_os,
                "zerar_garantia_reparo": zerar_garantia_reparo,
                "buscar_garantia_reparo": buscar_garantia_reparo,
                "corrigir_garantia_reparo": corrigir_garantia_reparo,
                "buscar_historico_garantia_reparo": buscar_historico_garantia_reparo,
                "obter_tipo_garantia": obter_tipo_garantia,
                "registrar_log_auditoria": registrar_log_auditoria,
                "modelo_para_os": modelo_para_os,
                "normalizar_imei": normalizar_imei,
                "texto_reparos_os": texto_reparos_os,
                "parse_data_ymd": runtime.parse_data_ymd,
                "vendedores": VENDEDORES,
                "mercado_phone_runtime_config": runtime.mercado_phone_runtime_config,
                "public_base_url": PUBLIC_BASE_URL,
                "integrations_config_path": INTEGRATIONS_CONFIG_PATH,
                "carregar_configuracoes_integracoes": carregar_configuracoes_integracoes,
            }
        )
    )

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE CLIENTES (Sprint P0.1 — primeiro domínio a seguir
    # a convenção controller/service/repository de ENGINEERING_GUIDE.md §3.1)
    # ========================================================================
    app.register_blueprint(create_clientes_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE UNIDADES_SERIALIZADAS (Sprint P0.1, evoluído na
    # migração ADR-007 — rastreamento individual por IMEI/serial, fonte única de
    # verdade para unidades originadas de Estoque OU de Produtos)
    # ========================================================================
    app.register_blueprint(create_unidades_serializadas_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE PRODUTOS (Sprint Comercial 0.1 — catálogo
    # comercial de venda, domínio novo e separado de Estoque/peças de reparo)
    # ========================================================================
    app.register_blueprint(create_produtos_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE VENDAS (Vendas MVP, 2026-07-27 — primeiro módulo a
    # nascer com o prefixo fluxoly_, ver docs/engineering/adr/ADR-008.md)
    # ========================================================================
    app.register_blueprint(create_vendas_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE TIPOS DE GARANTIA (V1.5 — Garantia, cadastro
    # compartilhado entre Vendas e Assistência, ver docs/engineering/plans/
    # PLAN-V1.5-Garantia.md)
    # ========================================================================
    app.register_blueprint(create_tipos_garantia_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DOS BLUEPRINTS DE FINANCEIRO MÍNIMO (Caixa, Contas a Pagar,
    # Contas a Receber -- BR-067 a BR-069, ver docs/engineering/plans/
    # PLAN-financeiro-minimo.md)
    # ========================================================================
    app.register_blueprint(create_caixa_blueprint({"conectar": conectar}))
    app.register_blueprint(create_contas_pagar_blueprint({"conectar": conectar}))
    app.register_blueprint(create_contas_receber_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE COMPRA DE APARELHOS (BR-083 a BR-093, ver
    # docs/engineering/plans/PLAN-compra-aparelhos.md)
    # ========================================================================
    app.register_blueprint(create_compras_aparelhos_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE DADOS DA LOJA (BR-094, cabeçalho dos documentos
    # da OS para o cliente -- ver docs/engineering/plans/PLAN-documentos-os-cliente.md)
    # ========================================================================
    app.register_blueprint(create_dados_loja_blueprint({"conectar": conectar}))

    # ========================================================================
    # REGISTRO DO BLUEPRINT DE AUDITORIA (leitura do audit_log, admin/financeiro
    # -- ver docs/engineering/plans/PLAN-tela-auditoria.md)
    # ========================================================================
    app.register_blueprint(create_auditoria_blueprint({"conectar": conectar}))
