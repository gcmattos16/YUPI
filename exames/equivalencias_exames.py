import unicodedata


# ==========================================
# EQUIVALÊNCIAS DE EXAMES
# ==========================================

EQUIVALENCIAS = {

    # ==========================================
    # OFTALMOLOGIA
    # ==========================================

    "PAQUIMETRIA ULTRASSONICA":
        "PAQUIMETRIA",

    "CAMPIMETRIA COMPUTADORIZADA":
        "CAMPIMETRIA",

    "POTENCIAL DE ACUIDADE VISUAL":
        "PAM",

    "POTENCIAL DE ACUIDADE VISUAL (PAM)":
        "PAM",

    "PAM":
        "PAM",

    "BIOMETRIA ULTRASSONICA":
        "BIOMETRIA",

    "BIOMETRIA":
        "BIOMETRIA",


    # ==========================================
    # COLONOSCOPIA
    # ==========================================

    "COLONOSCOPIA (COLOSCOPIA)":
        "COLONOSCOPIA",


    # ==========================================
    # ENDOSCOPIA
    # ==========================================

    "ENDOSCOPIA DIGESTIVA ALTA (EDA)":
        "ENDOSCOPIA",


    # ==========================================
    # ECOCARDIOGRAFIA
    # ==========================================

    "ECOCARDIOGRAFIA TRANSTORACICA":
        "ECOCARDIOGRAFIA",


    # ==========================================
    # HOLTER
    # ==========================================

    "HOLTER 24 HORAS (3 CANAIS)":
        "HOLTER",


    # ==========================================
    # MAPA
    # ==========================================

    "MAPA - MONITORIZACAO AMBULATORIAL DE PRESSAO":
        "MAPA",


    # ==========================================
    # DENSITOMETRIA
    # ==========================================

    "DENSITOMETRIA OSSEA CORPO INTEIRO":
        "DENSITOMETRIA",

    "DENSITOMETRIA OSSEA DUO-ENERGETICA DE COLUNA":
        "DENSITOMETRIA",


    # ==========================================
    # TESTE ERGOMÉTRICO
    # ==========================================

    "TESTE DE ESFORCO / TESTE ERGOMETRICO":
        "TESTE ERGOMETRICO",


    # ==========================================
    # NASOFIBROSCOPIA
    # ==========================================

    "NASOFIBROSCOPIA":
        "NASOFIBROSCOPIA",


    # ==========================================
    # USG
    # ==========================================

    "USG":
        "USG",


    # ==========================================
    # US DOPPLER
    # ==========================================

    "US DOPPLER":
        "US DOPPLER",


    # ==========================================
    # BERA
    # ==========================================

    "BERA - AUDIOMETRIA DE TRONCO CEREBRAL (PEA)":
        "BERA",

    "BERA - AUDIOMETRIA DE TRONCO CEREBRAL (PEA) COM":
        "BERA COM SEDACAO",

}


def normalizar(nome):

    # ==========================================
    # MAIÚSCULAS
    # ==========================================

    nome = nome.upper().strip()

    # ==========================================
    # REMOVER ACENTOS
    # ==========================================

    nome = "".join(
        caractere
        for caractere in unicodedata.normalize(
            "NFD",
            nome
        )
        if unicodedata.category(
            caractere
        ) != "Mn"
    )

    # Colapsa espaços duplicados vindos da extração do PDF.
    nome = " ".join(nome.split())

    # ==========================================
    # EQUIVALÊNCIA
    # ==========================================

    return EQUIVALENCIAS.get(
        nome,
        nome
    )