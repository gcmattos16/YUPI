import fitz
import re
import unicodedata


def normalizar_nome(nome):
    """
    Apenas normaliza o texto.

    NÃO agrupa especialidades.
    O agrupamento será feito posteriormente
    pelo comparador.
    """

    nome = nome.upper().strip()

    nome = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", nome)
        if unicodedata.category(caractere) != "Mn"
    )

    return nome


def ler_siresp(caminho_pdf):

    doc = fitz.open(caminho_pdf)

    dados = {}

    try:

        for pagina in doc:

            texto = pagina.get_text()

            linhas = [
                linha.strip()
                for linha in texto.splitlines()
                if linha.strip()
            ]

            i = 0

            while i < len(linhas):

                linha = linhas[i]

                # =====================================
                # ESTRUTURA DO SIRESP
                # =====================================
                #
                # ESPECIALIDADE
                # 1º número
                # 2º número
                # REALIZADO
                # 4º número
                # 5º número
                #
                # =====================================

                if (
                    i + 5 < len(linhas)
                    and re.search(r"[A-Za-zÀ-ÿ]", linha)
                    and linhas[i + 1].isdigit()
                    and linhas[i + 2].isdigit()
                    and linhas[i + 3].isdigit()
                    and linhas[i + 4].isdigit()
                    and linhas[i + 5].isdigit()
                ):

                    # =================================
                    # IGNORAR TOTAL
                    # =================================

                    if linha.upper() == "TOTAL":

                        i += 6
                        continue

                    # =================================
                    # NORMALIZAR SOMENTE O NOME
                    # =================================

                    nome = normalizar_nome(linha)

                    # =================================
                    # QUANTIDADE REALIZADA
                    # =================================

                    realizado = int(linhas[i + 3])

                    # =================================
                    # SOMAR CASO APAREÇA NOVAMENTE
                    # =================================

                    dados[nome] = (
                        dados.get(nome, 0)
                        + realizado
                    )

                    i += 6

                else:

                    i += 1

    finally:

        doc.close()

    return dados