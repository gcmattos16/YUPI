from consultas.regras import REGRAS


def _prioridade(diferenca):
    valor = abs(diferenca)
    if valor >= 20:
        return "🔴 CRÍTICA"
    if valor >= 5:
        return "🟠 MÉDIA"
    if valor > 0:
        return "🔵 BAIXA"
    return "🟢 OK"


def analisar_item(item):
    especialidade = item["especialidade"]
    diferenca = item.get("diferenca", 0)
    info = dict(item)
    info["prioridade"] = _prioridade(diferenca)

    if diferenca > 0:
        direcao = f"SIRESP está {diferenca} acima do Analítico."
    elif diferenca < 0:
        direcao = f"Analítico está {abs(diferenca)} acima do SIRESP."
    else:
        direcao = "SIRESP e Analítico estão com a mesma quantidade."
    info["diagnostico"] = direcao

    if especialidade in REGRAS:
        regra = REGRAS[especialidade]
        info["causas"] = regra["causas"]
        info["itens"] = regra["itens"]
        info["observacao"] = regra["observacao"]
        if "consulta" in regra:
            info["consulta"] = regra["consulta"]
        if "sessao" in regra:
            info["sessao"] = regra["sessao"]
    else:
        info["causas"] = ["Não existe uma regra específica cadastrada para esta especialidade."]
        info["itens"] = ["Conferir produção médica.", "Conferir código SUS.", "Comparar as subdivisões exibidas na composição."]
        info["observacao"] = "A YUPI está usando a regra padrão de auditoria."

    return info


def analisar(resultado):
    return [analisar_item(item) for item in resultado if item.get("diferenca", 0) != 0]
