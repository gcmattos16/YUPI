import customtkinter as ctk


def criar_painel_alertas(pai):

    frame = ctk.CTkFrame(
        pai,
        corner_radius=8
    )

    frame.pack(
        fill="x",
        padx=20,
        pady=(5, 10)
    )

    titulo = ctk.CTkLabel(
        frame,
        text="⚠ ALERTAS",
        font=("Segoe UI", 14, "bold")
    )

    titulo.pack(
        anchor="w",
        padx=10,
        pady=(5, 2)
    )

    caixa = ctk.CTkTextbox(
        frame,
        height=60
    )

    caixa.pack(
        fill="x",
        padx=10,
        pady=(0, 8)
    )

    caixa.configure(state="disabled")

    return caixa


def mostrar_alertas(caixa, alertas):

    caixa.configure(state="normal")
    caixa.delete("1.0", "end")

    if not alertas:

        caixa.insert(
            "end",
            "✅ Nenhum alerta encontrado."
        )

    else:

        for alerta in alertas:

            caixa.insert(
                "end",
                alerta + "\n"
            )

    caixa.configure(state="disabled")