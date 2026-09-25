import customtkinter as ctk


def criar_barra_filtros(master):

    frame = ctk.CTkFrame(
        master,
        fg_color="transparent"
    )

    frame.pack(
        fill="x",
        pady=(0, 10)
    )

    # ==========================
    # Pesquisa
    # ==========================

    ctk.CTkLabel(
        frame,
        text="🔍 Pesquisar:"
    ).pack(
        side="left",
        padx=(5, 5)
    )

    entrada = ctk.CTkEntry(
        frame,
        width=260,
        placeholder_text="Digite uma especialidade..."
    )

    entrada.pack(
        side="left"
    )

    # ==========================
    # Filtro
    # ==========================

    ctk.CTkLabel(
        frame,
        text="Mostrar:"
    ).pack(
        side="left",
        padx=(20, 5)
    )

    filtro = ctk.CTkComboBox(
        frame,
        width=180,
        values=[
            "Todas",
            "Somente OK",
            "Somente Divergências"
        ]
    )

    filtro.set("Todas")

    filtro.pack(
        side="left"
    )

    return frame, entrada, filtro