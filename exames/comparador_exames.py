from exames.multiplicadores import MULTIPLICADORES
from exames.grupos import GRUPOS, GLOBAL_GRUPOS
from exames.configuracao_mapeamento import GRUPO_MASTOLOGIA_MAIOR


# ============================================================
# ITENS QUE NÃO ENTRAM NA CONFERÊNCIA
# ============================================================

ITENS_IGNORADOS = {
    "PREPARO DE COLONOSCOPIA - EXTERNO - ENFERMAGEM",
    "PREPARO DE COLONOSCOPIA - INTERNO - ENFERMAGEM",
    "PREPARO DE COLONOSCOPIA - ENFERMAGEM",
    "SERVICO SOCIAL",
}


# ============================================================
# PROCEDIMENTOS COMPARTILHADOS
# ============================================================
#
# O mesmo procedimento do GLOBAL pode pertencer a mais de um
# grupo do SIRESP.
#
# A quantidade disponível do Global é controlada para que o
# mesmo procedimento NÃO seja contado duas vezes.
#
# Exemplo:
# ELETROCAUTERIZACAO
# -> UROLOGIA PROCEDIMENTO - MENOR
# -> PEQUENAS CIRURGIAS
#
# CAUTERIZACAO QUIMICA
# -> DERMATOLOGIA
# -> OTORRINO - PROCEDIMENTO
# -> GINECOLOGIA
# ============================================================

PROCEDIMENTOS_COMPARTILHADOS = {

    "ELETROCAUTERIZACAO DE LESAO CUTANEA": [
        "UROLOGIA PROCEDIMENTO - MENOR",
        "PEQUENAS CIRURGIAS",
    ],

    "CAUTERIZACAO QUIMICA DE PEQUENAS LESOES": [
        "DERMATOLOGIA",
        "OTORRINO - PROCEDIMENTO",
        "GINECOLOGIA",
    ],
}


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def valor(dados, chave):
    """
    Retorna um valor numérico.
    None, texto vazio ou valor inválido viram 0.
    """

    valor_chave = dados.get(chave)

    if valor_chave is None:
        return 0

    if valor_chave == "":
        return 0

    try:
        return int(valor_chave)
    except (TypeError, ValueError):
        try:
            return float(valor_chave)
        except (TypeError, ValueError):
            return 0


def possui_valor(dados, chave):
    """
    Verifica se a chave realmente veio preenchida.

    IMPORTANTE:
    0 é um valor válido, mas não significa necessariamente
    que o registro seja do tipo 'direto'.
    """

    if chave not in dados:
        return False

    return dados.get(chave) is not None


def total_siresp_item(dados):
    """
    Soma Externo + Interno + Direto.

    O comparador trabalha com os três campos separados.
    """

    externo = valor(dados, "externo")
    interno = valor(dados, "interno")
    direto = valor(dados, "direto")

    return externo + interno + direto


def obter_total_siresp_grupo(
    membros,
    siresp
):
    """
    Calcula o total de um grupo no SIRESP.

    Retorna:
        total
        detalhes
        encontrou
    """

    total = 0

    detalhes = []

    encontrou = False

    for exame in membros:

        if exame not in siresp:
            continue

        dados = siresp.get(
            exame,
            {}
        )

        externo = valor(
            dados,
            "externo"
        )

        interno = valor(
            dados,
            "interno"
        )

        direto = valor(
            dados,
            "direto"
        )

        quantidade = (
            externo +
            interno +
            direto
        )

        total += quantidade

        detalhes.append({

            "exame": exame,

            "externo": externo,

            "interno": interno,

            "direto": direto,

            "quantidade": quantidade

        })

        encontrou = True

    return (
        total,
        detalhes,
        encontrou
    )


# ============================================================
# GLOBAL BRUTO
# ============================================================

def obter_global_bruto(
    grupo,
    membros,
    faturamento,
    mapeamentos_manuais=None,
    faturamento_bruto=None
):
    """
    Soma os procedimentos correspondentes no Global.

    Não altera os valores originais.
    O ajuste de procedimentos compartilhados é feito depois.
    """

    mapeamentos_manuais = mapeamentos_manuais or {}
    faturamento_bruto = faturamento_bruto or {}

    # --------------------------------------------------------
    # MAPEAMENTO MANUAL (exceções controladas)
    # --------------------------------------------------------
    # Usado somente quando a regra automática não é segura.
    # Hoje, Mastologia - Cirurgia Maior é a única exceção.
    if grupo in mapeamentos_manuais:
        nomes_manuais = mapeamentos_manuais.get(grupo, [])

        if nomes_manuais:
            detalhes = []
            total = 0

            for nome_global in nomes_manuais:
                quantidade = faturamento_bruto.get(nome_global, 0)
                total += quantidade
                detalhes.append({
                    "exame": nome_global,
                    "quantidade": quantidade,
                    "quantidade_original": quantidade,
                    "quantidade_disponivel": quantidade,
                    "quantidade_utilizada": quantidade,
                    "ajustado": False,
                    "mapeamento_manual": True,
                })

            return total, detalhes

    nomes_global = GLOBAL_GRUPOS.get(
        grupo,
        []
    )

    detalhes = []

    total = 0

    # --------------------------------------------------------
    # GLOBAL ESPECÍFICO
    # --------------------------------------------------------

    if nomes_global:

        for nome_global in nomes_global:

            quantidade = faturamento.get(
                nome_global,
                0
            )

            total += quantidade

            detalhes.append({

                "exame": nome_global,

                "quantidade": quantidade,

                "quantidade_original": quantidade,

                "quantidade_disponivel": quantidade,

                "quantidade_utilizada": 0,

                "ajustado": False

            })

        return (
            total,
            detalhes
        )

    # --------------------------------------------------------
    # PRÓPRIO GRUPO NO GLOBAL
    # --------------------------------------------------------

    if grupo in faturamento:

        quantidade = faturamento.get(
            grupo,
            0
        )

        detalhes.append({

            "exame": grupo,

            "quantidade": quantidade,

            "quantidade_original": quantidade,

            "quantidade_disponivel": quantidade,

            "quantidade_utilizada": 0,

            "ajustado": False

        })

        return (
            quantidade,
            detalhes
        )

    # --------------------------------------------------------
    # SEM REGRA ESPECÍFICA
    # --------------------------------------------------------

    for membro in membros:

        quantidade = faturamento.get(
            membro,
            0
        )

        total += quantidade

        detalhes.append({

            "exame": membro,

            "quantidade": quantidade,

            "quantidade_original": quantidade,

            "quantidade_disponivel": quantidade,

            "quantidade_utilizada": 0,

            "ajustado": False

        })

    return (
        total,
        detalhes
    )


# ============================================================
# APLICAR MULTIPLICADOR
# ============================================================

def aplicar_multiplicador(
    grupo,
    total
):

    multiplicador = MULTIPLICADORES.get(
        grupo,
        1
    )

    return (
        total * multiplicador,
        multiplicador
    )


# ============================================================
# COMPARTILHADOS
# ============================================================

def nomes_compartilhados_do_grupo(grupo):
    """
    Retorna os nomes dos procedimentos compartilhados
    que pertencem ao grupo.
    """

    nomes = []

    for procedimento, grupos in PROCEDIMENTOS_COMPARTILHADOS.items():

        if grupo in grupos:

            nomes.append(
                procedimento
            )

    return nomes


def ajustar_global_compartilhado(
    grupo,
    total_siresp,
    detalhes_global,
    pool_compartilhado
):
    """
    Ajusta somente os procedimentos compartilhados.

    Regra:
    - procedimentos normais do grupo permanecem integralmente;
    - procedimentos compartilhados usam somente o saldo disponível
      no Global;
    - o saldo é consumido uma única vez entre os grupos;
    - o valor utilizado aparece em quantidade_utilizada;
    - quantidade_original continua mostrando o valor bruto do Global.
    """

    nomes_compartilhados = set(
        nomes_compartilhados_do_grupo(grupo)
    )

    if not nomes_compartilhados:
        return [dict(item) for item in detalhes_global]

    resultado = []

    # O grupo pode possuir procedimentos próprios no Global.
    # Primeiro calculamos quanto do SIRESP ainda precisa ser coberto
    # pelos procedimentos compartilhados.
    total_nao_compartilhado = 0

    for detalhe in detalhes_global:
        nome = detalhe.get("exame", "")

        if nome in nomes_compartilhados:
            continue

        total_nao_compartilhado += valor(
            detalhe,
            "quantidade"
        )

    necessario_compartilhado = max(
        total_siresp - total_nao_compartilhado,
        0
    )

    restante = necessario_compartilhado

    for detalhe in detalhes_global:
        novo = dict(detalhe)

        nome = novo.get("exame", "")

        quantidade_original = valor(
            novo,
            "quantidade_original"
        )

        if quantidade_original == 0:
            quantidade_original = valor(
                novo,
                "quantidade"
            )

        novo["quantidade_original"] = quantidade_original

        # --------------------------------------------------------
        # PROCEDIMENTO NORMAL
        # --------------------------------------------------------
        if nome not in nomes_compartilhados:
            novo["quantidade"] = quantidade_original
            novo["quantidade_disponivel"] = quantidade_original
            novo["quantidade_utilizada"] = quantidade_original
            novo["ajustado"] = False

            resultado.append(novo)
            continue

        # --------------------------------------------------------
        # PROCEDIMENTO COMPARTILHADO
        # --------------------------------------------------------
        disponivel = valor(
            pool_compartilhado,
            nome
        )

        quantidade_usada = min(
            disponivel,
            restante
        )

        novo["quantidade"] = quantidade_usada
        novo["quantidade_disponivel"] = disponivel
        novo["quantidade_utilizada"] = quantidade_usada
        novo["ajustado"] = (
            quantidade_usada != quantidade_original
        )

        resultado.append(novo)

        pool_compartilhado[nome] = (
            disponivel - quantidade_usada
        )

        restante -= quantidade_usada

    return resultado


# ============================================================
# COMPARAR EXAMES
# ============================================================

def comparar_exames(
    siresp,
    faturamento,
    mapeamentos_manuais=None,
    faturamento_bruto=None
):

    resultado = []

    mapeamentos_manuais = mapeamentos_manuais or {}
    faturamento_bruto = faturamento_bruto or {}

    # ========================================================
    # CONTROLAR EXAMES PROCESSADOS
    # ========================================================

    processados = set()

    # ========================================================
    # QUANTIDADE RESTANTE DOS PROCEDIMENTOS COMPARTILHADOS
    # ========================================================
    #
    # Exemplo:
    #
    # Global possui 10 eletrocauterizações.
    #
    # Uro menor usa 4.
    # Pequenas Cirurgias poderá usar somente 6.
    #
    # Nunca teremos:
    # Uro = 4
    # Pequenas = 10
    #
    # total usado = 14
    # quando o Global só tinha 10.
    # ========================================================

    pool_compartilhado = {}

    for procedimento in PROCEDIMENTOS_COMPARTILHADOS:

        pool_compartilhado[procedimento] = faturamento.get(
            procedimento,
            0
        )

    # ========================================================
    # 1. PROCESSAR GRUPOS
    # ========================================================

    for grupo, membros in GRUPOS.items():

        # ----------------------------------------------------
        # SIRESP
        # ----------------------------------------------------

        (
            qtd_siresp_bruta,
            detalhes_siresp,
            encontrou
        ) = obter_total_siresp_grupo(
            membros,
            siresp
        )

        if not encontrou:
            continue

        # ----------------------------------------------------
        # MARCAR PROCESSADOS
        # ----------------------------------------------------

        for detalhe in detalhes_siresp:

            processados.add(
                detalhe["exame"]
            )

        # ----------------------------------------------------
        # EXTERNO / INTERNO / DIRETO
        # ----------------------------------------------------

        externo_grupo = sum(
            detalhe["externo"]
            for detalhe in detalhes_siresp
        )

        interno_grupo = sum(
            detalhe["interno"]
            for detalhe in detalhes_siresp
        )

        direto_grupo = sum(
            detalhe["direto"]
            for detalhe in detalhes_siresp
        )

        # ----------------------------------------------------
        # GLOBAL
        # ----------------------------------------------------

        (
            total_global_bruto,
            detalhes_global
        ) = obter_global_bruto(
            grupo,
            membros,
            faturamento,
            mapeamentos_manuais=mapeamentos_manuais,
            faturamento_bruto=faturamento_bruto
        )

        # ----------------------------------------------------
        # AJUSTE DE COMPARTILHADOS
        # ----------------------------------------------------

        detalhes_global_ajustados = (
            ajustar_global_compartilhado(
                grupo,
                qtd_siresp_bruta,
                detalhes_global,
                pool_compartilhado
            )
        )

        # ----------------------------------------------------
        # TOTAL GLOBAL
        # ----------------------------------------------------

        total_global = sum(
            valor(
                detalhe,
                "quantidade"
            )
            for detalhe in detalhes_global_ajustados
        )

        # ----------------------------------------------------
        # MULTIPLICADOR
        # ----------------------------------------------------

        (
            total_siresp,
            multiplicador
        ) = aplicar_multiplicador(
            grupo,
            qtd_siresp_bruta
        )

        # ----------------------------------------------------
        # DIFERENÇA
        # ----------------------------------------------------

        diferenca = (
            total_siresp -
            total_global
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        configuracao_pendente = (
            grupo == GRUPO_MASTOLOGIA_MAIOR
            and not mapeamentos_manuais.get(GRUPO_MASTOLOGIA_MAIOR)
        )

        if configuracao_pendente:
            status = "CONFIGURAR"
        elif grupo in ("NASOFIBROSCOPIA", "RX") and diferenca != 0:
            # O SIRESP e o Global podem ter escopos diferentes (externo x total).
            # A divergência precisa de revisão, não deve ser tratada como erro puro.
            status = "ATENCAO"
        elif diferenca == 0:
            status = "OK"
        else:
            status = "ERRO"

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        resultado.append({

            "exame": grupo,

            "externo": externo_grupo,

            "interno": interno_grupo,

            "direto": direto_grupo,

            "multiplicador": multiplicador,

            "siresp": total_siresp,

            "global": total_global,

            "global_bruto": total_global_bruto,

            "diferenca": diferenca,

            "status": status,

            "grupo": True,

            "configuracao_pendente": configuracao_pendente,
            "mapeamento_manual": grupo in mapeamentos_manuais,
            "observacao": (
                "SIRESP externo x Global total: revisar escopo"
                if grupo == "NASOFIBROSCOPIA" and diferenca != 0
                else (
                    "SIRESP possui apenas RAIO-X COM LAUDO - EXTERNO; Global reúne todos os RX. Revisar escopo."
                    if grupo == "RX" and diferenca != 0
                    else ""
                )
            ),

            "detalhes_siresp": detalhes_siresp,

            "detalhes_global": detalhes_global_ajustados

        })

    # ========================================================
    # 2. PROCESSAR EXAMES NORMAIS
    # ========================================================

    for exame in sorted(
        siresp.keys()
    ):

        # Itens administrativos/auxiliares que não participam
        # da conferência principal.
        if exame in ITENS_IGNORADOS:
            continue

        if exame in processados:
            continue

        dados_siresp = siresp.get(
            exame,
            {}
        )

        # ----------------------------------------------------
        # VALORES
        # ----------------------------------------------------

        externo = valor(
            dados_siresp,
            "externo"
        )

        interno = valor(
            dados_siresp,
            "interno"
        )

        # IMPORTANTE:
        # Só usamos "direto" como modalidade quando ele
        # realmente foi informado pelo leitor.
        #
        # Um direto = 0 NÃO pode fazer o sistema ignorar
        # Externo + Interno.
        # ----------------------------------------------------

        tem_direto = possui_valor(
            dados_siresp,
            "direto"
        )

        direto = valor(
            dados_siresp,
            "direto"
        )

        if tem_direto and externo == 0 and interno == 0:

            total_siresp_bruto = direto

        else:

            total_siresp_bruto = (
                externo +
                interno
            )

            # Se houver direto junto com externo/interno,
            # ele também entra na soma.
            if direto:
                total_siresp_bruto += direto

        # ----------------------------------------------------
        # GLOBAL
        # ----------------------------------------------------

        nomes_manuais = mapeamentos_manuais.get(exame, [])
        detalhes_global = []

        if nomes_manuais:
            total_global = 0
            for nome_global in nomes_manuais:
                quantidade = faturamento_bruto.get(nome_global, 0)
                total_global += quantidade
                detalhes_global.append({
                    "exame": nome_global,
                    "quantidade": quantidade,
                    "quantidade_original": quantidade,
                    "quantidade_disponivel": quantidade,
                    "quantidade_utilizada": quantidade,
                    "ajustado": False,
                    "mapeamento_manual": True,
                })
        else:
            total_global = faturamento.get(
                exame,
                0
            )

        # ----------------------------------------------------
        # MULTIPLICADOR
        # ----------------------------------------------------

        multiplicador = MULTIPLICADORES.get(
            exame,
            1
        )

        total_siresp = (
            total_siresp_bruto *
            multiplicador
        )

        # ----------------------------------------------------
        # DIFERENÇA
        # ----------------------------------------------------

        diferenca = (
            total_siresp -
            total_global
        )

        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        if diferenca == 0:

            status = "OK"

        else:

            status = "ERRO"

        # ----------------------------------------------------
        # DETALHAMENTO SIRESP
        # ----------------------------------------------------

        quantidade_detalhe = (
            total_siresp
            if multiplicador != 1
            else total_siresp_bruto
        )

        detalhes_siresp = [{

            "exame": exame,

            "externo": externo,

            "interno": interno,

            "direto": direto,

            "quantidade": quantidade_detalhe,

            "quantidade_bruta": total_siresp_bruto,

            "multiplicador": multiplicador

        }]

        # ----------------------------------------------------
        # DETALHAMENTO GLOBAL
        # ----------------------------------------------------

        if not detalhes_global:
            detalhes_global = [{

                "exame": exame,

                "quantidade": total_global,

                "quantidade_original": total_global,

                "quantidade_disponivel": total_global,

                "quantidade_utilizada": total_global,

                "ajustado": False

            }]

        # ----------------------------------------------------
        # RESULTADO
        # ----------------------------------------------------

        resultado.append({

            "exame": exame,

            "externo": externo,

            "interno": interno,

            "direto": direto,

            "multiplicador": multiplicador,

            "siresp": total_siresp,

            "global": total_global,

            "global_bruto": total_global,

            "diferenca": diferenca,

            "status": status,

            "grupo": False,

            "mapeamento_manual": bool(nomes_manuais),

            "detalhes_siresp": detalhes_siresp,

            "detalhes_global": detalhes_global

        })

    # ========================================================
    # 3. ORDENAR
    # ========================================================

    resultado.sort(
        key=lambda item:
        item["exame"]
    )

    return resultado