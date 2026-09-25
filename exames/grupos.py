# ============================================================
# OBSERVAÇÃO
# ============================================================
#
# CAUTERIZAÇÃO QUÍMICA é procedimento compartilhado SOMENTE
# para a AUDITORIA.
#
# Ela NÃO deve ser usada aqui para alterar automaticamente
# o total principal de Dermatologia, Otorrino ou Ginecologia.
# ============================================================

# ============================================================
# GRUPOS DE EXAMES
# ============================================================

GRUPOS = {

    # ========================================================
    # RX
    # ========================================================

    "RX": [
        "RAIO-X COM LAUDO",
    ],

    # ========================================================
    # MAMOGRAFIA
    # ========================================================

    "MAMOGRAFIA": [
        "MAMOGRAFIA",
        "MAMOGRAFIA RASTREAMENTO - PROGRAMA",
    ],

    # ========================================================
    # AUDIOMETRIA
    # ========================================================

    "AUDIOMETRIA": [
        "AUDIOMETRIA / IMITANCIOMETRIA",
        "AUDIOMETRIA TONAL/VOCAL",
    ],

    # ========================================================
    # ELETROENCEFALOGRAMA
    # ========================================================

    "ELETROENCEFALOGRAMA": [
        "ELETROENCEFALOGRAMA SEM SEDACAO",
    ],

    # ========================================================
    # ELETRONEUROMIOGRAFIA
    # ========================================================

    "ELETRONEUROMIOGRAFIA": [
        "ELETRONEUROMIOGRAFIA",
    ],

    # ========================================================
    # TESTE DE CONTATO
    # ========================================================

    "TESTE DE CONTATO": [
        "ALERGOLOGIA - TESTE DE CONTATO",
    ],

    # ========================================================
    # OCT
    # ========================================================

    "OCT": [
        "OCT - TOMOGRAFIA DE COERENCIA OPTICA",
    ],

    # ========================================================
    # OTONEUROLOGICO
    # ========================================================

    "OTONEUROLOGICO": [
        "OTONEUROLOGICO",
    ],

    # ========================================================
    # OTORRINO - PROCEDIMENTO
    # ========================================================

    "OTORRINO - PROCEDIMENTO": [
        "OTORRINO - PROCEDIMENTO",
    ],


    # ========================================================
    # PROVA DE FUNÇÃO PULMONAR
    # ========================================================

    "PROVA DE FUNCAO PULMONAR": [
        "PROVA DE FUNCAO PULMONAR",
    ],

    # ========================================================
    # US DOPPLER
    # ========================================================

    "US DOPPLER": [
        "US DOPPLER GERAL",
        "US DOPPLER VASCULAR",
    ],

    # ========================================================
    # USG
    # ========================================================

    "USG": [
        "US GERAL",
        "US MUSCULO ESQUELETICO",
        "ULTRASSOM PAFF MAMA",
        "ULTRASSOM PAFF TIREOIDE",
        "ULTRASSOM CORE BIOPSIA",
    ],

    # ========================================================
    # CATARATA
    # ========================================================

    "CIRURGIA CATARATA": [
        "CIRURGIA CATARATA - PROCEDIMENTO",
    ],

    # ========================================================
    # VASCULAR
    # ========================================================

    "CIRURGIA VASCULAR - ESPUMA": [
        "CIRURGIA VASCULAR - PROCEDIMENTO DE ESPUMA",
    ],

    # ========================================================
    # CAF
    # ========================================================

    "CAF": [
        "CAF - CIRURGIA DE ALTA FREQUENCIA",
    ],


    # ========================================================
    # DERMATOLOGIA
    # ========================================================

    "DERMATOLOGIA": [
        "DERMATOLOGIA - PROCEDIMENTO - DR IVAN",
    ],


    # ========================================================
    # DERMATOLOGIA
    # ========================================================
    # A cauterização química é compartilhada entre Dermato,
    # Gineco e Otorrino. O comparador distribui apenas a
    # quantidade necessária, sem duplicar o total do Global.

    "DERMATOLOGIA": [
        "DERMATOLOGIA - PROCEDIMENTO - DR IVAN",
    ],

    # ========================================================
    # OTORRINO - PROCEDIMENTO
    # ========================================================

    "OTORRINO - PROCEDIMENTO": [
        "OTORRINO - PROCEDIMENTO",
    ],

    # ========================================================
    # GASTRO
    # ========================================================

    "GASTRO": [
        "GASTROCLINICO - PROCEDIMENTO",
    ],

    # ========================================================
    # GINECOLOGIA
    # ========================================================

    "GINECOLOGIA": [
        "GINECOLOGIA - PROCEDIMENTO",
    ],

    # ========================================================
    # HEMATOLOGIA
    # ========================================================

    "HEMATOLOGIA": [
        "HEMATOLOGIA - PROCEDIMENTO - ATUAL",
    ],

    # ========================================================
    # PEQUENAS CIRURGIAS
    # ========================================================

    "PEQUENAS CIRURGIAS": [
        "PEQUENAS CIRURGIAS",
    ],

    # ========================================================
    # MASTOLOGIA - CIRURGIA MAIOR
    # ========================================================
    # O Global desta categoria é configurável pela interface.
    # Não há regra fixa porque os procedimentos podem variar.

    "MASTOLOGIA - PROCEDIMENTO - CIRURGIA MAIOR": [
        "MASTOLOGIA - PROCEDIMENTO - CIRURGIA MAIOR",
    ],

    # ========================================================
    # UROLOGIA - DIVERSOS
    # ========================================================

    "UROLOGIA DIVERSOS": [
        "UROLOGIA DIVERSOS",
    ],

    # ========================================================
    # UROLOGIA - MAIOR
    # ========================================================

    "UROLOGIA PROCEDIMENTO - MAIOR": [
        "UROLOGIA PROCEDIMENTO - MAIOR",
    ],

    # ========================================================
    # UROLOGIA - MENOR
    # ========================================================

    "UROLOGIA PROCEDIMENTO - MENOR": [
        "UROLOGIA PROCEDIMENTO - MENOR",
    ],

    # ========================================================
    # URODINAMICA
    # ========================================================

    "URODINAMICA": [
        "URODINAMICA",
    ],

    # ========================================================
    # NASOFIBROSCOPIA
    # ========================================================

    "NASOFIBROSCOPIA": [
        "NASOFIBROSCOPIA",
    ],

    # ========================================================
    # BIOPSIA DE PROSTATA
    # ========================================================

    "BIOPSIA DE PROSTATA SEM SEDACAO": [
        "BIOPSIA DE PROSTATA SEM SEDACAO",
    ],

}


# ============================================================
# PROCEDIMENTOS DO GLOBAL
# ============================================================

GLOBAL_GRUPOS = {

    # ========================================================
    # RX
    # ========================================================

    "RX": [
        "RX",
    ],

    # ========================================================
    # MAMOGRAFIA
    # ========================================================

    "MAMOGRAFIA": [
        "MAMOGRAFIA COM COMPRESSAO",
        "MAMOGRAFIA BILATERAL PARA RASTREAMENTO",
        "MAMOGRAFIA DIAGNOSTICA PARA RASTREAMENTO",
    ],

    # ========================================================
    # AUDIOMETRIA
    # ========================================================

    "AUDIOMETRIA": [
        "LOGOAUDIOMETRIA",
    ],

    # ========================================================
    # ELETROENCEFALOGRAMA
    # ========================================================

    "ELETROENCEFALOGRAMA": [
        "ELETROENCEFALOGRAFIA EM VIGILIA C/ OU S/ FOTO-",
        "ELETROENCEFALOGRAMA EM SONO INDUZIDO SEM",
        "ELETROENCEFALOGRAMA EM VIGILIA E SONO ESPONTANEO C/",
    ],

    # ========================================================
    # ELETRONEUROMIOGRAFIA
    # ========================================================

    "ELETRONEUROMIOGRAFIA": [
        "ELETRONEUROMIOGRAFIA DO MEMBRO INFERIOR",
        "ELETRONEUROMIOGRAFIA DO MEMBRO SUPERIOR",
    ],

    # ========================================================
    # TESTE DE CONTATO
    # ========================================================

    "TESTE DE CONTATO": [
        "TESTES ALERGICOS DE CONTATO",
    ],

    # ========================================================
    # OCT
    # ========================================================

    "OCT": [
        "TOMOGRAFIA DE COERENCIA OPTICA",
    ],

    # ========================================================
    # OTONEUROLOGICO
    # ========================================================

    "OTONEUROLOGICO": [
        "OTONEUROLOGICO / TESTES VESTIBULARES",
    ],

    # ========================================================
    # PROVA DE FUNÇÃO PULMONAR
    # ========================================================

    "PROVA DE FUNCAO PULMONAR": [
        "ESPIROMETRIA OU PROVA DE FUNCAO PULMONAR COMPLETA",
        "PROVA DE FUNCAO PULMONAR COMPLETA (ESPIROMETRIA)",
    ],

    # ========================================================
    # US DOPPLER
    # ========================================================

    "US DOPPLER": [
        "US DOPPLER",
    ],

    # ========================================================
    # USG
    # ========================================================

    "USG": [
        "USG",
    ],

    # ========================================================
    # CATARATA
    # ========================================================

    "CIRURGIA CATARATA": [
        "FACOEMULSIFICACAO C/ IMPLANTE DE LENTE INTRA-OCULAR",
    ],

    # ========================================================
    # VASCULAR
    # ========================================================

    "CIRURGIA VASCULAR - ESPUMA": [
        "TRATAMENTO ESCLEROSANTE NAO ESTETICO DE VARIZES DOS",
    ],

    # ========================================================
    # CAF
    # ========================================================

    "CAF": [
        "EXCISAO TIPO I DO COLO UTERINO",
    ],

    # ========================================================
    # DERMATOLOGIA / OTORRINO - procedimento compartilhado
    # ========================================================

    "DERMATOLOGIA": [
        "CAUTERIZACAO QUIMICA DE PEQUENAS LESOES",
    ],

    "OTORRINO - PROCEDIMENTO": [
        "CAUTERIZACAO QUIMICA DE PEQUENAS LESOES",
    ],

    # ========================================================
    # GASTRO
    # ========================================================

    "GASTRO": [
        "RETIRADA DE POLIPO DO TUBO DIGESTIVO POR ENDOSCOPIA",
        "RETIRADA DE CORPO ESTRANHO / POLIPOS DO RETO / COLO",
    ],

    # ========================================================
    # GINECOLOGIA
    # ========================================================

    "GINECOLOGIA": [
        "BIOPSIA DE VAGINA",
        "BIOPSIA DE VULVA",
        "BIOPSIA DE COLO UTERINO",
        "CAUTERIZACAO QUIMICA DE PEQUENAS LESOES",
    ],

    # ========================================================
    # HEMATOLOGIA
    # ========================================================

    "HEMATOLOGIA": [
        "MIELOGRAMA",
        "BIOPSIA DE MEDULA OSSEA",
    ],

    # ========================================================
    # PEQUENAS CIRURGIAS
    # ========================================================

    "PEQUENAS CIRURGIAS": [
        "ELETROCAUTERIZACAO DE LESAO CUTANEA",
        "EXCISAO DE LESAO E/OU SUTURA DE FERIMENTO DA PELE",
        "EXERESE DE TUMOR DE PELE E ANEXOS / CISTO SEBACEO /",
        "EXTIRPACAO E SUPRESSAO DE LESAO DE PELE E DE TECIDO",
        "RETIRADA DE LESAO POR SHAVING",
    ],

    # ========================================================
    # UROLOGIA - DIVERSOS
    # ========================================================

    "UROLOGIA DIVERSOS": [
        "UROFLUXOMETRIA",
    ],

    # ========================================================
    # UROLOGIA - MAIOR
    # ========================================================

    "UROLOGIA PROCEDIMENTO - MAIOR": [
        "DILATACAO DE URETRA",
        "DILATACAO PERCUTANEA DE ESTENOSES URETERAIS E JUNCAO",
        "PLASTICA DE FREIO BALANO-PREPUCIAL",
    ],

    # ========================================================
    # UROLOGIA - MENOR
    # ========================================================

    "UROLOGIA PROCEDIMENTO - MENOR": [
        "ELETROCAUTERIZACAO DE LESAO CUTANEA",
        "BIOPSIA DE PENIS",
    ],

    # ========================================================
    # URODINAMICA
    # ========================================================

    "URODINAMICA": [
        "URODINAMICA COMPLETA",
    ],

    # ========================================================
    # NASOFIBROSCOPIA
    # ========================================================

    "NASOFIBROSCOPIA": [
        "NASOFIBROSCOPIA",
    ],

    # ========================================================
    # BIOPSIA DE PROSTATA
    # ========================================================

    "BIOPSIA DE PROSTATA SEM SEDACAO": [
        "BIOPSIA DE PROSTATA SEM SEDACAO",
    ],

}