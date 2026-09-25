import pymupdf

from exames.equivalencias_exames import normalizar


# ============================================================
# NORMALIZAR PROCEDIMENTO DO GLOBAL
# ============================================================

def normalizar_procedimento_global(exame):

    exame = normalizar(
        exame
    )

    # ========================================================
    # RX
    # ========================================================
    #
    # O GLOBAL pode trazer:
    #
    # RX ...
    # RAIO-X ...
    #
    # Todos entram no grupo RX.
    # ========================================================

    if (
        exame.startswith("RX")
        or
        exame.startswith("RAIO-X")
        or
        exame.startswith("RAIO X")
    ):

        return "RX"

    # ========================================================
    # US DOPPLER
    # ========================================================

    if exame.startswith(
        "US DOPPLER"
    ):

        return "US DOPPLER"

    # ========================================================
    # USG
    # ========================================================
    #
    # Mantém os diferentes nomes de ultrassom no grupo USG.
    # ========================================================

    if (
        exame.startswith("US ")
        or
        exame.startswith("ULTRASSOM")
        or
        exame.startswith("ULTRASONOGRAFIA")
    ):

        return "USG"

    # ========================================================
    # BIÓPSIA DE PRÓSTATA
    # ========================================================
    #
    # Fica separada.
    # NÃO entra em Urologia Diversos.
    # ========================================================

    if (
        "BIOPSIA DE PROSTATA" in exame
        or
        "BIOPSIA PROSTATICA" in exame
        or
        "BIOPSIA DA PROSTATA" in exame
    ):

        return "BIOPSIA DE PROSTATA SEM SEDACAO"

    # ========================================================
    # CAUTERIZAÇÃO QUÍMICA
    # ========================================================
    #
    # IMPORTANTE:
    #
    # Este procedimento NÃO será usado para alterar o total
    # principal de Dermatologia.
    #
    # Ele fica identificado para a AUDITORIA como procedimento
    # compartilhado.
    # ========================================================

    if (
        "CAUTERIZACAO QUIMICA" in exame
    ):

        return "CAUTERIZACAO QUIMICA DE PEQUENAS LESOES"

    # ========================================================
    # GASTRO - PÓLIPOS
    # ========================================================
    #
    # Não juntar os procedimentos.
    # Cada procedimento continua separado.
    # ========================================================

    if (
        "RETIRADA DE POLIPO" in exame
        or
        "RETIRADA DE POLIPOS" in exame
        or
        "POLIPO DO TUBO DIGESTIVO" in exame
        or
        "POLIPOS DO RETO" in exame
    ):

        return exame

    # ========================================================
    # ELETROCAUTERIZAÇÃO
    # ========================================================
    #
    # Mantém identificada para a auditoria e para as regras
    # de Uro Menor / Pequenas Cirurgias.
    # ========================================================

    if (
        "ELETROCAUTERIZACAO" in exame
    ):

        return "ELETROCAUTERIZACAO DE LESAO CUTANEA"

    # ========================================================
    # BIÓPSIA DE PÊNIS
    # ========================================================

    if (
        "BIOPSIA DE PENIS" in exame
    ):

        return "BIOPSIA DE PENIS"

    # ========================================================
    # GINECOLOGIA
    # ========================================================

    if (
        "BIOPSIA DE VAGINA" in exame
    ):

        return "BIOPSIA DE VAGINA"

    if (
        "BIOPSIA DE VULVA" in exame
    ):

        return "BIOPSIA DE VULVA"

    if (
        "BIOPSIA DE COLO UTERINO" in exame
        or
        "BIOPSIA DO COLO UTERINO" in exame
    ):

        return "BIOPSIA DE COLO UTERINO"

    # ========================================================
    # HEMATOLOGIA
    # ========================================================

    if (
        "MIELOGRAMA" in exame
    ):

        return "MIELOGRAMA"

    if (
        "BIOPSIA DE MEDULA" in exame
        or
        "BIOPSIA DA MEDULA" in exame
        or
        "BIOPSIA DE MEDULA OSSEA" in exame
    ):

        return "BIOPSIA DE MEDULA OSSEA"

    # ========================================================
    # UROLOGIA
    # ========================================================

    if (
        "UROFLUXOMETRIA" in exame
    ):

        return "UROFLUXOMETRIA"

    if (
        "URODINAMICA" in exame
    ):

        return "URODINAMICA COMPLETA"

    if (
        "DILATACAO" in exame
        and
        "URETRA" in exame
    ):

        return exame

    if (
        "FREIO" in exame
    ):

        return exame

    # ========================================================
    # NASOFIBROSCOPIA
    # ========================================================

    if (
        "NASOFIBROSCOPIA" in exame
    ):

        return "NASOFIBROSCOPIA"

    # ========================================================
    # RETORNO PADRÃO
    # ========================================================

    return exame


# ============================================================
# LEITOR DO GLOBAL
# ============================================================


def _extrair_registros_global(caminho_pdf):
    """Extrai os registros do Demonstrativo Global sem perder o nome original."""

    doc = pymupdf.open(caminho_pdf)
    texto = ""

    try:
        for pagina in doc:
            texto += pagina.get_text() + "\n"
    finally:
        doc.close()

    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip()]
    registros = []
    i = 0

    while i < len(linhas):
        # Estrutura mais comum do Global:
        # CODIGO / NOME / QTDE / VALOR / SUBTOTAL
        if (
            i + 4 < len(linhas)
            and linhas[i].isdigit()
            and len(linhas[i]) == 10
            and not linhas[i + 1].isdigit()
            and linhas[i + 2].isdigit()
        ):
            codigo = linhas[i]
            nome_original = linhas[i + 1]
            quantidade = int(linhas[i + 2])

            nome_exato = normalizar(nome_original)
            nome_canonico = normalizar_procedimento_global(nome_original)

            registros.append({
                "codigo": codigo,
                "nome_original": nome_original,
                "nome_exato": nome_exato,
                "nome_normalizado": nome_canonico,
                "quantidade": quantidade,
            })
            i += 5
        else:
            i += 1

    return registros


def ler_faturamento_exames_detalhado(caminho_pdf):
    """Retorna dados canônicos, registros e totais por nome exato.

    - dados: usado pelas regras automáticas atuais;
    - registros: usado pela tela de auditoria/configuração;
    - bruto_por_nome: usado apenas nos mapeamentos manuais.
    """

    registros = _extrair_registros_global(caminho_pdf)
    dados = {}
    bruto_por_nome = {}

    for registro in registros:
        canonico = registro["nome_normalizado"]
        exato = registro["nome_exato"]
        quantidade = registro["quantidade"]

        dados[canonico] = dados.get(canonico, 0) + quantidade
        bruto_por_nome[exato] = bruto_por_nome.get(exato, 0) + quantidade

    return dados, registros, bruto_por_nome


def ler_faturamento_exames(caminho_pdf):
    """Compatibilidade com o restante do projeto: retorna somente os totais."""
    dados, _, _ = ler_faturamento_exames_detalhado(caminho_pdf)
    return dados
