import unicodedata

EQUIVALENCIAS = {

    # ==========================
    # ENDOSCOPIA
    # ==========================

    "ENDOSCOPIA DIGESTIVA ALTA (EDA)": "ENDOSCOPIA",
    "COLONOSCOPIA (COLOSCOPIA)": "COLONOSCOPIA",

    # ==========================
    # OTORRINO
    # ==========================

    "NASOFIBROSCOPIA": "NASOFIBROSCOPIA",

    # ==========================
    # PNEUMOLOGIA
    # ==========================

    "ESPIROMETRIA OU PROVA DE FUNCAO PULMONAR COMPLETA": "ESPIROMETRIA",
    "PROVA DE FUNCAO PULMONAR COMPLETA (ESPIROMETRIA)": "ESPIROMETRIA",

    # ==========================
    # CARDIOLOGIA
    # ==========================

    "ECOCARDIOGRAFIA TRANSTORACICA": "ECOCARDIOGRAFIA",
    "TESTE ERGOMETRICO": "TESTE ERGOMETRICO",
    "MAPA": "MAPA",
    "HOLTER": "HOLTER",

    # ==========================
    # OFTALMOLOGIA
    # ==========================

    "PAQUIMETRIA ULTRASSONICA": "PAQUIMETRIA",
    "CAMPIMETRIA COMPUTADORIZADA": "CAMPIMETRIA",
    "POTENCIAL DE ACUIDADE VISUAL": "PAM",
    "BIOMETRIA ULTRASSONICA": "BIOMETRIA",
    "RETINOGRAFIA COLORIDA": "RETINOGRAFIA",
    "TOPOGRAFIA COMPUTADORIZADA DE CORNEA": "TOPOGRAFIA",
    "TOMOGRAFIA DE COERENCIA OPTICA": "TOMOGRAFIA",
    "TONOMETRIA": "TONOMETRIA",
    "MAPEAMENTO DE RETINA": "MAPEAMENTO DE RETINA",
    "FUNDOSCOPIA": "FUNDOSCOPIA",
    "TESTE ORTOPTICO": "TESTE ORTOPTICO",
}


def normalizar(nome):

    nome = nome.upper().strip()

    # Remove acentos
    nome = ''.join(
        c for c in unicodedata.normalize('NFD', nome)
        if unicodedata.category(c) != 'Mn'
    )

    # Procura equivalência
    return EQUIVALENCIAS.get(nome, nome)