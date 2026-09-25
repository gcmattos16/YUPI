import pymupdf
import re
import unicodedata


def normalizar_nome(nome):
    """
    Normaliza somente o texto.

    NÃO agrupa especialidades.
    O agrupamento será feito posteriormente
    pelo comparador.
    """

    nome = nome.upper().strip()

    nome = "".join(
        caractere
        for caractere in unicodedata.normalize(
            "NFD",
            nome
        )
        if unicodedata.category(caractere) != "Mn"
    )

    return nome


def ler_analitico(caminho_pdf):

    doc = pymupdf.open(caminho_pdf)

    dados = {}

    # Guarda a especialidade atual caso
    # ela continue em outra página.
    especialidade_atual = None

    try:

        for pagina in doc:

            texto = pagina.get_text()

            linhas = [
                linha.strip()
                for linha in texto.splitlines()
                if linha.strip()
            ]

            especialidade = especialidade_atual

            # =====================================
            # PROCURAR ESPECIALIDADE NA PÁGINA
            # =====================================

            for linha in linhas:

                if linha.startswith("Especialidade:"):

                    match = re.search(
                        r"Especialidade:\s*\d+\s*-\s*(.+)",
                        linha
                    )

                    if match:

                        especialidade = normalizar_nome(
                            match.group(1)
                        )

                    break

            # Se não encontrou especialidade,
            # usa a da página anterior.
            if especialidade is None:
                continue

            especialidade_atual = especialidade

            # =====================================
            # IGNORAR SERVIÇO SOCIAL
            # =====================================

            if especialidade == "SERVICO SOCIAL":
                continue

            # =====================================
            # PROCURAR TOTAL DA ESPECIALIDADE
            # =====================================

            encontrou_total = False

            for i, linha in enumerate(linhas):

                if (
                    "Total de Consultas Executadas por Profissional"
                    in linha
                ):

                    total = None

                    # ---------------------------------
                    # CASO 1
                    # Número está na própria linha
                    # ---------------------------------

                    match = re.search(
                        r"Total de Consultas Executadas por Profissional:\s*(\d+)",
                        linha
                    )

                    if match:

                        total = int(
                            match.group(1)
                        )

                    # ---------------------------------
                    # CASO 2
                    # Número está na linha anterior
                    # ---------------------------------

                    elif i > 0:

                        anterior = linhas[i - 1]

                        if anterior.isdigit():

                            total = int(
                                anterior
                            )

                    # ---------------------------------
                    # ADICIONAR TOTAL
                    # ---------------------------------

                    if total is not None:

                        dados[especialidade] = (
                            dados.get(
                                especialidade,
                                0
                            )
                            + total
                        )

                        encontrou_total = True

                    break

            # =====================================
            # SE NÃO EXISTIR TOTAL NA PÁGINA
            #
            # NÃO vamos colocar 0.
            #
            # A especialidade pode continuar
            # na próxima página.
            # =====================================

            if not encontrou_total:
                continue

    finally:

        doc.close()

    return dados