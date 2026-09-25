import pymupdf
import re

from exames.equivalencias_exames import normalizar


# ============================================================
# CRIAR REGISTRO
# ============================================================

def _criar_registro(dados, exame):

    if exame not in dados:

        dados[exame] = {
            "externo": 0,
            "interno": 0,
            "direto": 0
        }


# ============================================================
# SOMAR VALOR
# ============================================================

def _somar_valor(
    dados,
    exame,
    campo,
    quantidade
):

    _criar_registro(
        dados,
        exame
    )

    valor_atual = dados[exame].get(
        campo,
        0
    )

    if valor_atual is None:
        valor_atual = 0

    dados[exame][campo] = (
        valor_atual +
        quantidade
    )


# ============================================================
# IDENTIFICAR ORIGEM
# ============================================================

def _tipo_origem(nome):

    nome_upper = nome.upper().strip()

    # ========================================================
    # EXTERNO
    #
    # Exemplos:
    #
    # RAIO-X COM LAUDO - EXTERNO
    # PREPARO DE COLONOSCOPIA - EXTERNO - ENFERMAGEM
    # ========================================================

    if re.search(
        r"\bEXTERNO\b|\bEXTERNA\b",
        nome_upper
    ):

        return "externo"

    # ========================================================
    # INTERNO
    #
    # Exemplos:
    #
    # BIOPSIA DE PROSTATA SEM SEDACAO - INTERNO
    # DERMATOLOGIA - PROCEDIMENTO INTERNO - DR IVAN
    # PEQUENAS CIRURGIAS - INTERNA
    # ========================================================

    if re.search(
        r"\bINTERNO\b|\bINTERNA\b",
        nome_upper
    ):

        return "interno"

    return None


# ============================================================
# REMOVER ORIGEM DO NOME
# ============================================================

def _remover_origem(nome):

    nome_upper = nome.upper().strip()

    # ========================================================
    # REMOVE:
    #
    # - EXTERNO
    # - EXTERNA
    # - INTERNO
    # - INTERNA
    #
    # MESMO QUE ESTEJAM NO MEIO DO NOME
    # ========================================================

    nome_upper = re.sub(
        r"\s*-\s*(EXTERNO|EXTERNA|INTERNO|INTERNA)\b",
        "",
        nome_upper
    )

    nome_upper = re.sub(
        r"\b(EXTERNO|EXTERNA|INTERNO|INTERNA)\b",
        "",
        nome_upper
    )

    # ========================================================
    # LIMPAR HÍFENS DUPLICADOS
    # ========================================================

    nome_upper = re.sub(
        r"\s*-\s*-\s*",
        " - ",
        nome_upper
    )

    # ========================================================
    # LIMPAR ESPAÇOS
    # ========================================================

    nome_upper = re.sub(
        r"\s+",
        " ",
        nome_upper
    )

    return nome_upper.strip(
        " -"
    )


# ============================================================
# LEITOR SIRESP
# ============================================================

def ler_siresp_exames(caminho_pdf):

    doc = pymupdf.open(
        caminho_pdf
    )

    texto = ""

    try:

        for pagina in doc:

            texto += (
                pagina.get_text() +
                "\n"
            )

    finally:

        doc.close()

    # ========================================================
    # LINHAS
    # ========================================================

    linhas = [

        linha.strip()

        for linha in texto.splitlines()

        if linha.strip()

    ]

    dados = {}

    i = 0

    # ========================================================
    # PERCORRER PDF
    # ========================================================

    while i < len(linhas):

        # ====================================================
        # ESTRUTURA:
        #
        # EXAME
        # OFERTADO
        # AGENDADO
        # REALIZADO
        # ====================================================

        if (
            i + 3 < len(linhas)
            and not linhas[i].isdigit()
            and linhas[i + 1].isdigit()
            and linhas[i + 2].isdigit()
            and linhas[i + 3].isdigit()
        ):

            nome = linhas[i]

            realizado = int(
                linhas[i + 3]
            )

            nome_upper = nome.upper().strip()

            # =================================================
            # IDENTIFICAR ORIGEM
            # =================================================

            tipo = _tipo_origem(
                nome_upper
            )

            # =================================================
            # EXTERNO
            # =================================================

            if tipo == "externo":

                exame = _remover_origem(
                    nome_upper
                )

                exame = normalizar(
                    exame
                )

                _somar_valor(
                    dados,
                    exame,
                    "externo",
                    realizado
                )

            # =================================================
            # INTERNO
            # =================================================

            elif tipo == "interno":

                exame = _remover_origem(
                    nome_upper
                )

                exame = normalizar(
                    exame
                )

                _somar_valor(
                    dados,
                    exame,
                    "interno",
                    realizado
                )

            # =================================================
            # EXAME DIRETO
            #
            # Exemplo:
            #
            # UROLOGIA DIVERSOS
            # 81
            # 107
            # 96
            #
            # PEQUENAS CIRURGIAS - INTERNA
            # será tratado como interno
            # =================================================

            else:

                exame = normalizar(
                    nome_upper
                )

                ignorar = {

                    "GRUPO DE COTA",

                    "OFERTADO",

                    "AGENDADO",

                    "REALIZADO"

                }

                if exame not in ignorar:

                    _somar_valor(
                        dados,
                        exame,
                        "direto",
                        realizado
                    )

            # =================================================
            # AVANÇAR
            # =================================================

            i += 4

        else:

            i += 1

    return dados