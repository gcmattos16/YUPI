import customtkinter as ctk


def criar_card_auditoria(pai, auditoria):

    frame = ctk.CTkFrame(
        pai,
        corner_radius=10
    )

    frame.pack(
        fill="x",
        padx=8,
        pady=8
    )

    # -----------------------------
    # ESPECIALIDADE
    # -----------------------------

    titulo = ctk.CTkLabel(
        frame,
        text=f"📌 {auditoria['especialidade']}",
        font=("Segoe UI", 17, "bold"),
        anchor="w",
        justify="left"
    )

    titulo.pack(
        anchor="w",
        padx=15,
        pady=(12,6)
    )

    # -----------------------------
    # DIFERENÇA
    # -----------------------------

    ctk.CTkLabel(
        frame,
        text=f"Diferença: {auditoria['diferenca']}",
        anchor="w",
        justify="left"
    ).pack(anchor="w", padx=15)

    ctk.CTkLabel(
        frame,
        text=f"SIRESP: {auditoria['siresp']}",
        anchor="w",
        justify="left"
    ).pack(anchor="w", padx=15)

    ctk.CTkLabel(
        frame,
        text=f"Analítico: {auditoria['analitico']}",
        anchor="w",
        justify="left"
    ).pack(anchor="w", padx=15)

    # -----------------------------
    # CAUSAS
    # -----------------------------

    ctk.CTkLabel(
        frame,
        text="\n⚠ Possível causa",
        font=("Segoe UI",14,"bold"),
        anchor="w",
        justify="left"
    ).pack(anchor="w", padx=15)

    for causa in auditoria["causas"]:

        ctk.CTkLabel(
            frame,
            text="• " + causa,
            anchor="w",
            justify="left",
            wraplength=270
        ).pack(anchor="w", padx=25)

    # -----------------------------
    # ITENS
    # -----------------------------

    ctk.CTkLabel(
        frame,
        text="\n📋 Itens para conferência",
        font=("Segoe UI",14,"bold"),
        anchor="w",
        justify="left"
    ).pack(anchor="w", padx=15)

    for item in auditoria["itens"]:

        ctk.CTkLabel(
            frame,
            text="• " + item,
            anchor="w",
            justify="left",
            wraplength=270
        ).pack(anchor="w", padx=25)

    # -----------------------------
    # CÓDIGOS SUS
    # -----------------------------

    if "consulta" in auditoria:

        ctk.CTkLabel(
            frame,
            text=f"\nConsulta SUS: {auditoria['consulta']}",
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=15)

    if "sessao" in auditoria:

        ctk.CTkLabel(
            frame,
            text=f"Sessão SUS: {auditoria['sessao']}",
            anchor="w",
            justify="left"
        ).pack(anchor="w", padx=15)

    # -----------------------------
    # OBSERVAÇÃO
    # -----------------------------

    ctk.CTkLabel(
        frame,
        text="\n📝 Observação",
        font=("Segoe UI",14,"bold"),
        anchor="w",
        justify="left"
    ).pack(anchor="w", padx=15)

    ctk.CTkLabel(
        frame,
        text=auditoria["observacao"],
        wraplength=270,
        justify="left"
    ).pack(
        anchor="w",
        padx=25,
        pady=(0,12)
    )

    return frame