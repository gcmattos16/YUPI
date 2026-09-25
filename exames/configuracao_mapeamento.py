"""Mapeamentos manuais persistentes da conferência de exames.

Qualquer exame/grupo do SIRESP pode receber uma regra manual apontando para
um ou mais procedimentos do Demonstrativo Global. A regra salva o nome do
procedimento, nunca uma quantidade fixa; assim, a quantidade é sempre lida
do Global atual.
"""

from __future__ import annotations

import json
import os
from pathlib import Path


GRUPO_MASTOLOGIA_MAIOR = "MASTOLOGIA - PROCEDIMENTO - CIRURGIA MAIOR"
CHAVE_HISTORICO_GLOBAL = "__HISTORICO_GLOBAL__"
# Compatibilidade com versões anteriores.
CHAVE_HISTORICO_MASTOLOGIA = "__HISTORICO_MASTOLOGIA__"

_BASE_DADOS = Path(os.getenv("APPDATA") or Path.home()) / "YUPI"
_BASE_DADOS.mkdir(parents=True, exist_ok=True)
_ARQUIVO_CONFIG = _BASE_DADOS / "config_mapeamentos.json"
_PADRAO = {
    GRUPO_MASTOLOGIA_MAIOR: [],
    CHAVE_HISTORICO_GLOBAL: [],
    CHAVE_HISTORICO_MASTOLOGIA: [],
}


def _normalizar_lista(valores):
    resultado = []
    vistos = set()
    for valor in valores or []:
        nome = str(valor).strip().upper()
        if not nome or nome in vistos:
            continue
        vistos.add(nome)
        resultado.append(nome)
    return resultado


def _carregar_json():
    dados = dict(_PADRAO)
    if not _ARQUIVO_CONFIG.exists():
        return dados
    try:
        conteudo = json.loads(_ARQUIVO_CONFIG.read_text(encoding="utf-8"))
        if isinstance(conteudo, dict):
            for chave, valores in conteudo.items():
                if isinstance(valores, list):
                    dados[str(chave).strip().upper()] = _normalizar_lista(valores)
    except (OSError, json.JSONDecodeError, TypeError, ValueError):
        return dict(_PADRAO)
    return dados


def _salvar_json(dados):
    _ARQUIVO_CONFIG.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def carregar_mapeamentos():
    dados = _carregar_json()
    return {chave: valores for chave, valores in dados.items() if not chave.startswith("__")}


def salvar_mapeamento(grupo, procedimentos):
    grupo = str(grupo).strip().upper()
    dados = _carregar_json()
    dados[grupo] = _normalizar_lista(procedimentos)
    _salvar_json(dados)
    return dados[grupo]


def remover_mapeamento(grupo):
    grupo = str(grupo).strip().upper()
    dados = _carregar_json()
    dados.pop(grupo, None)
    _salvar_json(dados)


def obter_mapeamento(grupo):
    return carregar_mapeamentos().get(str(grupo).strip().upper(), [])


def carregar_historico_global():
    dados = _carregar_json()
    return _normalizar_lista([
        *dados.get(CHAVE_HISTORICO_GLOBAL, []),
        *dados.get(CHAVE_HISTORICO_MASTOLOGIA, []),
    ])


def registrar_historico_global(procedimentos):
    dados = _carregar_json()
    anteriores = carregar_historico_global()
    dados[CHAVE_HISTORICO_GLOBAL] = _normalizar_lista([*anteriores, *procedimentos])
    _salvar_json(dados)
    return dados[CHAVE_HISTORICO_GLOBAL]


# Compatibilidade com chamadas antigas.
def carregar_historico_mastologia():
    return carregar_historico_global()


def registrar_historico_mastologia(procedimentos):
    return registrar_historico_global(procedimentos)


def caminho_configuracao():
    return _ARQUIVO_CONFIG
