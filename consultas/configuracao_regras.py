import json
import os
from copy import deepcopy

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_CONFIG = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "YUPI")
ARQUIVO_CONFIG = os.path.join(PASTA_CONFIG, "config_regras_consultas.json")

GRUPOS_PADRAO = {
    "ENDOCRINOLOGIA": [
        "ENDOCRINOLOGIA",
        "ENDOCRINOLOGIA - HORMONIO DO CRESCIMENTO",
        "ENDOCRINOLOGIA PEDIATRICA",
        "ENDOCRINOLOGIA PEDIATRICA - DIABETES",
    ],
    "CARDIOLOGIA": [
        "CARDIOLOGIA",
        "CARDIOLOGIA - AVALIACAO PRE-CIRURGICA",
    ],
    "FISIOTERAPIA": [
        "FISIOTERAPIA",
        "FISIOTERAPIA - SESSOES",
    ],
    "UROLOGIA": [
        "UROLOGIA",
        "UROLOGIA - AVALIACAO CIRURGICA",
        "UROLOGIA - AVALIACAO POS-CIRURGICA",
    ],
    "OFTALMOLOGIA": [
        "OFTALMOLOGIA",
        "OFTALMOLOGIA - CATARATA",
        "OFTALMOLOGIA - CATARATA - POS-OPERATORIO",
        "OFTALMOLOGIA - REFLEXO VERMELHO",
    ],
    "CIRURGIA GERAL": [
        "CIRURGIA GERAL",
        "CIRURGIA GERAL - AVALIACAO DE PEQUENAS CIRURGIAS",
    ],
    "PSICOLOGIA": [
        "PSICOLOGIA",
        "PSICOLOGIA - PSICOTERAPIA",
    ],
    "FONOAUDIOLOGIA": [
        "FONOAUDIOLOGIA",
        "FONOAUDIOLOGIA - SESSOES",
    ],
    "HEMATOLOGIA": [
        "HEMATOLOGIA",
        "HEMATOLOGIA - SANGRIA TERAPEUTICA",
        "HEMATOLOGIA - PROCEDIMENTOS",
    ],
    "NEUROLOGIA": [
        "NEUROLOGIA",
        "NEUROLOGIA - LIQUOR",
    ],
    "GINECOLOGIA": [
        "GINECOLOGIA",
        "GINECOLOGIA - COLPOSCOPIA",
        "GINECOLOGIA - LINHA DE CUIDADO",
        "GINECOLOGIA - PRE-OPERATORIO - CAF",
        "GINECOLOGIA - POS-OPERATORIO - CAF",
    ],
}


def _normalizar_grupos(grupos):
    saida = {}
    if not isinstance(grupos, dict):
        return deepcopy(GRUPOS_PADRAO)
    for nome, membros in grupos.items():
        nome = str(nome).strip().upper()
        if not nome or not isinstance(membros, (list, tuple, set)):
            continue
        limpos = []
        for membro in membros:
            membro = str(membro).strip().upper()
            if membro and membro not in limpos:
                limpos.append(membro)
        if limpos:
            saida[nome] = limpos
    return saida or deepcopy(GRUPOS_PADRAO)


def carregar_grupos():
    if not os.path.exists(ARQUIVO_CONFIG):
        return deepcopy(GRUPOS_PADRAO)
    try:
        with open(ARQUIVO_CONFIG, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        return _normalizar_grupos(dados.get("grupos", dados))
    except Exception:
        return deepcopy(GRUPOS_PADRAO)


def salvar_grupos(grupos):
    os.makedirs(os.path.dirname(ARQUIVO_CONFIG), exist_ok=True)
    dados = {"grupos": _normalizar_grupos(grupos)}
    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)
    return dados["grupos"]


def restaurar_padrao():
    grupos = deepcopy(GRUPOS_PADRAO)
    salvar_grupos(grupos)
    return grupos
