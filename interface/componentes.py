import customtkinter as ctk

import interface.cores as cores
import interface.estilos as estilos


def criar_card(pai, emoji, titulo, descricao, comando=None):

    card = ctk.CTkFrame(
        pai,
        width=220,
        height=220,
        corner_radius=18,
        fg_color=cores.CARD
    )

    card.grid_propagate(False)

    # Ícone
    icone = ctk.CTkLabel(
        card,
        text=emoji,
        font=("Segoe UI Emoji", 52)
    )
    icone.grid(row=0, column=0, pady=(20, 5), padx=20)

    # Título
    titulo_label = ctk.CTkLabel(
        card,
        text=titulo,
        font=estilos.FONTE_CARD,
        text_color=cores.TITULO
    )
    titulo_label.grid(row=1, column=0, pady=(5, 10))

    # Descrição
    descricao_label = ctk.CTkLabel(
        card,
        text=descricao,
        font=estilos.FONTE_TEXTO,
        text_color=cores.TEXTO
    )
    descricao_label.grid(row=2, column=0, pady=(0, 20))

    # Botão
    botao = ctk.CTkButton(
        card,
        text="▶ Abrir",
        width=220,
        height=40,
        corner_radius=12,
        font=("Segoe UI", 15, "bold"),
        fg_color=cores.AZUL,
        hover_color=cores.AZUL_HOVER,
        command=comando
    )
    botao.grid(row=3, column=0, pady=(0, 20))

    return card
