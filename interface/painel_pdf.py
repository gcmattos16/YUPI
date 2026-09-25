import os
import customtkinter as ctk


def criar_painel_pdf(pai):

    frame = ctk.CTkFrame(
        pai,
        corner_radius=12,
        fg_color="#F5F5F5"
    )

    frame.pack(
        fill="x",
        padx=15,
        pady=(8, 10)
    )

    # ==========================
    # TÍTULO
    # ==========================

    titulo = ctk.CTkLabel(
        frame,
        text="📄 Arquivos da Conferência",
        font=("Segoe UI", 18, "bold")
    )

    titulo.grid(
        row=0,
        column=0,
        columnspan=3,
        sticky="w",
        padx=15,
        pady=(12, 10)
    )

    # ==========================
    # SIRESP
    # ==========================

    ctk.CTkLabel(
        frame,
        text="📄 SIRESP",
        font=("Segoe UI", 15, "bold")
    ).grid(
        row=1,
        column=0,
        sticky="w",
        padx=15,
        pady=6
    )

    lbl_siresp = ctk.CTkLabel(
        frame,
        text="Nenhum PDF selecionado",
        anchor="w",
        font=("Segoe UI", 13)
    )

    lbl_siresp.grid(
        row=1,
        column=1,
        sticky="ew",
        padx=10
    )

    btn_siresp = ctk.CTkButton(
        frame,
        text="📂 Alterar",
        width=120,
        height=34
    )

    btn_siresp.grid(
        row=1,
        column=2,
        padx=15
    )

    # ==========================
    # ANALÍTICO
    # ==========================

    ctk.CTkLabel(
        frame,
        text="📄 ANALÍTICO",
        font=("Segoe UI", 15, "bold")
    ).grid(
        row=2,
        column=0,
        sticky="w",
        padx=15,
        pady=(0, 12)
    )

    lbl_analitico = ctk.CTkLabel(
        frame,
        text="Nenhum PDF selecionado",
        anchor="w",
        font=("Segoe UI", 13)
    )

    lbl_analitico.grid(
        row=2,
        column=1,
        sticky="ew",
        padx=10
    )

    btn_analitico = ctk.CTkButton(
        frame,
        text="📂 Alterar",
        width=120,
        height=34
    )

    btn_analitico.grid(
        row=2,
        column=2,
        padx=15,
        pady=(0, 12)
    )

    frame.grid_columnconfigure(1, weight=1)

    return (
        lbl_siresp,
        lbl_analitico,
        btn_siresp,
        btn_analitico
    )


def atualizar_pdf(label, caminho):

    if not caminho:
        label.configure(text="Nenhum PDF selecionado")
        return

    nome = os.path.basename(caminho)

    if len(nome) > 45:
        nome = nome[:42] + "..."

    label.configure(
        text=f"✔ {nome}"
    )