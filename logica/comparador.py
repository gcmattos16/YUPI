from consultas.configuracao_regras import carregar_grupos


def _status(diferenca):
    return "✅ OK" if diferenca == 0 else "❌ DIVERGÊNCIA"


def _explicacao(qtd_siresp, qtd_analitico):
    diferenca = qtd_siresp - qtd_analitico
    if diferenca == 0:
        return "As quantidades do SIRESP e do Analítico conferem."
    if diferenca > 0:
        return f"O SIRESP possui {diferenca} consulta(s) a mais que o Analítico."
    return f"O Analítico possui {abs(diferenca)} consulta(s) a mais que o SIRESP."


def comparar(siresp, analitico):
    resultado = []
    processadas = set()
    especialidades_normais = set(siresp.keys()) | set(analitico.keys())
    grupos_agrupados = carregar_grupos()

    # Grupos configuráveis
    for grupo, membros in grupos_agrupados.items():
        qtd_siresp = 0
        qtd_analitico = 0
        detalhes_siresp = []
        detalhes_analitico = []
        encontrou = False

        for especialidade in membros:
            if especialidade in siresp:
                quantidade = siresp[especialidade]
                qtd_siresp += quantidade
                detalhes_siresp.append({"especialidade": especialidade, "quantidade": quantidade})
                processadas.add(especialidade)
                encontrou = True

        for especialidade in membros:
            if especialidade in analitico:
                quantidade = analitico[especialidade]
                qtd_analitico += quantidade
                detalhes_analitico.append({"especialidade": especialidade, "quantidade": quantidade})
                processadas.add(especialidade)
                encontrou = True

        if not encontrou:
            continue

        diferenca = qtd_siresp - qtd_analitico
        resultado.append({
            "especialidade": grupo,
            "siresp": qtd_siresp,
            "analitico": qtd_analitico,
            "diferenca": diferenca,
            "status": _status(diferenca),
            "explicacao": _explicacao(qtd_siresp, qtd_analitico),
            "agrupado": True,
            "detalhes_siresp": detalhes_siresp,
            "detalhes_analitico": detalhes_analitico,
        })

    # Enfermagem permanece com a regra original: todas as subdivisões somadas.
    enfermagem_siresp = []
    enfermagem_analitico = []
    qtd_siresp_enfermagem = 0
    qtd_analitico_enfermagem = 0

    for especialidade, quantidade in siresp.items():
        if especialidade.startswith("ENFERMAGEM"):
            qtd_siresp_enfermagem += quantidade
            enfermagem_siresp.append({"especialidade": especialidade, "quantidade": quantidade})
            processadas.add(especialidade)

    for especialidade, quantidade in analitico.items():
        if especialidade.startswith("ENFERMAGEM"):
            qtd_analitico_enfermagem += quantidade
            enfermagem_analitico.append({"especialidade": especialidade, "quantidade": quantidade})
            processadas.add(especialidade)

    if enfermagem_siresp or enfermagem_analitico:
        diferenca = qtd_siresp_enfermagem - qtd_analitico_enfermagem
        resultado.append({
            "especialidade": "ENFERMAGEM",
            "siresp": qtd_siresp_enfermagem,
            "analitico": qtd_analitico_enfermagem,
            "diferenca": diferenca,
            "status": _status(diferenca),
            "explicacao": _explicacao(qtd_siresp_enfermagem, qtd_analitico_enfermagem),
            "agrupado": True,
            "detalhes_siresp": enfermagem_siresp,
            "detalhes_analitico": enfermagem_analitico,
        })

    # Especialidades normais
    for especialidade in sorted(especialidades_normais):
        if especialidade in processadas:
            continue
        qtd_siresp = siresp.get(especialidade, 0)
        qtd_analitico = analitico.get(especialidade, 0)
        diferenca = qtd_siresp - qtd_analitico
        resultado.append({
            "especialidade": especialidade,
            "siresp": qtd_siresp,
            "analitico": qtd_analitico,
            "diferenca": diferenca,
            "status": _status(diferenca),
            "explicacao": _explicacao(qtd_siresp, qtd_analitico),
            "agrupado": False,
            "detalhes_siresp": [{"especialidade": especialidade, "quantidade": qtd_siresp}] if especialidade in siresp else [],
            "detalhes_analitico": [{"especialidade": especialidade, "quantidade": qtd_analitico}] if especialidade in analitico else [],
        })

    resultado.sort(key=lambda item: item["especialidade"])
    return resultado
