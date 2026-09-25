import unicodedata

EQUIVALENCIAS = {

   # ==========================
    # ENDOCRINOLOGIA
    # ==========================

    "ENDOCRINOLOGIA - HORMONIO DO CRESCIMENTO": "ENDOCRINOLOGIA",
    "ENDOCRINOLOGIA PEDIATRICA": "ENDOCRINOLOGIA",
    "ENDOCRINOLOGIA PEDIATRICA - DIABETES": "ENDOCRINOLOGIA",


    # ==========================
    # CARDIOLOGIA
    # ==========================

    "CARDIOLOGIA - AVALIACAO PRE-CIRURGICA": "CARDIOLOGIA",

    # ==========================
    # FISIOTERAPIA
    # ==========================

    "FISIOTERAPIA - SESSOES": "FISIOTERAPIA",

    # ==========================
    # UROLOGIA
    # ==========================

    "UROLOGIA - AVALIACAO CIRURGICA": "UROLOGIA",
    "UROLOGIA - AVALIACAO POS-CIRURGICA": "UROLOGIA",

    # ==========================
    # OFTALMOLOGIA
    # ==========================

    "OFTALMOLOGIA - CATARATA": "OFTALMOLOGIA",
    "OFTALMOLOGIA - CATARATA - POS-OPERATORIO": "OFTALMOLOGIA",
    "OFTALMOLOGIA - REFLEXO VERMELHO": "OFTALMOLOGIA",

    # ==========================
    # CIRURGIA GERAL
    # ==========================

    "CIRURGIA GERAL - AVALIACAO DE PEQUENAS CIRURGIAS": "CIRURGIA GERAL",

    # ==========================
    # PSICOLOGIA
    # ==========================

    "PSICOLOGIA - PSICOTERAPIA": "PSICOLOGIA",

    # ==========================
    # FONOAUDIOLOGIA
    # ==========================

    "FONOAUDIOLOGIA - SESSOES": "FONOAUDIOLOGIA",

    # ==========================
    # HEMATOLOGIA
    # ==========================

    "HEMATOLOGIA - SANGRIA TERAPEUTICA": "HEMATOLOGIA",
    "HEMATOLOGIA - PROCEDIMENTOS": "HEMATOLOGIA",

    # ==========================
    # NEUROLOGIA
    # ==========================

    "NEUROLOGIA - LIQUOR": "NEUROLOGIA",

    # ==========================
    # GINECOLOGIA
    # ==========================

    "GINECOLOGIA - COLPOSCOPIA": "GINECOLOGIA",
    "GINECOLOGIA - LINHA DE CUIDADO": "GINECOLOGIA",
    "GINECOLOGIA - PRE-OPERATORIO - CAF": "GINECOLOGIA",
    "GINECOLOGIA - POS-OPERATORIO - CAF": "GINECOLOGIA",
}
def normalizar(nome):

    nome = nome.upper().strip()

    nome = ''.join(
        c for c in unicodedata.normalize('NFD', nome)
        if unicodedata.category(c) != 'Mn'
    )

    # =====================================
    # TODAS AS ENFERMAGENS VIRAM ENFERMAGEM
    # =====================================

    if nome.startswith("ENFERMAGEM"):
        return "ENFERMAGEM"

    return EQUIVALENCIAS.get(nome, nome)
