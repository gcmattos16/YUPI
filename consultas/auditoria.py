from consultas.regras import REGRAS


def gerar_alertas(resultado):

    alertas = []

    for item in resultado:

        diferenca = item["diferenca"]

        if diferenca == 0:
            continue

        especialidade = item["especialidade"]

        siresp = item["siresp"]
        analitico = item["analitico"]

        # ----------------------------
        # PRIORIDADE
        # ----------------------------

        if abs(diferenca) >= 20:
            prioridade = "🔴 CRÍTICA"

        elif abs(diferenca) >= 5:
            prioridade = "🟠 MÉDIA"

        else:
            prioridade = "🔵 BAIXA"

        texto = []

        texto.append("🤖 AUDITORIA INTELIGENTE\n")

        texto.append(f"{prioridade}")
        texto.append(f"\n📌 {especialidade}")

        texto.append(f"\n\nDiferença: {diferenca}")

        texto.append(f"\nSIRESP: {siresp}")
        texto.append(f"\nAnalítico: {analitico}")

        # ----------------------------
        # REGRAS
        # ----------------------------

        if especialidade in REGRAS:

            regra = REGRAS[especialidade]

            texto.append("\n\n⚠ Possível causa")

            for causa in regra["causas"]:
                texto.append(f"\n• {causa}")

            texto.append("\n\n📋 Itens para conferência")

            for item_conferencia in regra["itens"]:
                texto.append(f"\n• {item_conferencia}")

            if "consulta" in regra:

                texto.append(
                    f"\n\nConsulta SUS: {regra['consulta']}"
                )

            if "sessao" in regra:

                texto.append(
                    f"\nSessão SUS: {regra['sessao']}"
                )

            texto.append("\n\n📝 Observação")

            texto.append(
                f"\n{regra['observacao']}"
            )

        else:

            texto.append("\n\n📋 Itens para conferência")

            texto.append("\n• Conferir produção médica.")
            texto.append("\n• Conferir código SUS.")
            texto.append("\n• Verificar procedimentos pendentes.")

        alertas.append(
            "".join(texto)
        )

    return alertas