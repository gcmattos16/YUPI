import customtkinter as ctk
from tkinter import messagebox

from consultas.configuracao_regras import carregar_grupos, salvar_grupos, restaurar_padrao


def abrir_editor_regras(parent, ao_salvar=None):
    janela = ctk.CTkToplevel(parent)
    janela.title("YUPI • Regras de Consultas")
    janela.geometry("860x620")
    janela.minsize(760, 520)
    janela.grab_set()

    grupos = carregar_grupos()
    grupo_atual = ctk.StringVar(value=next(iter(grupos)) if grupos else "")

    topo = ctk.CTkFrame(janela)
    topo.pack(fill="x", padx=16, pady=(16, 10))
    ctk.CTkLabel(topo, text="⚙ Regras de agrupamento", font=("Segoe UI", 20, "bold")).pack(side="left", padx=12, pady=10)
    ctk.CTkLabel(topo, text="Edite somente quando a regra de negócio mudar.", font=("Segoe UI", 11)).pack(side="right", padx=12)

    corpo = ctk.CTkFrame(janela, fg_color="transparent")
    corpo.pack(fill="both", expand=True, padx=16, pady=(0, 10))

    lateral = ctk.CTkScrollableFrame(corpo, width=260)
    lateral.pack(side="left", fill="y", padx=(0, 10))
    editor = ctk.CTkFrame(corpo)
    editor.pack(side="left", fill="both", expand=True)

    ctk.CTkLabel(editor, text="Especialidade agrupadora", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=14, pady=(14, 4))
    lbl_grupo = ctk.CTkLabel(editor, text="", font=("Segoe UI", 17, "bold"), anchor="w")
    lbl_grupo.pack(fill="x", padx=14)

    ctk.CTkLabel(editor, text="Subespecialidades que serão somadas (uma por linha)", anchor="w").pack(fill="x", padx=14, pady=(16, 4))
    caixa = ctk.CTkTextbox(editor)
    caixa.pack(fill="both", expand=True, padx=14, pady=(0, 10))

    aviso = ctk.CTkLabel(
        editor,
        text="A regra de ENFERMAGEM continua protegida e não é alterada por este editor.",
        wraplength=520,
        justify="left",
        font=("Segoe UI", 11),
    )
    aviso.pack(fill="x", padx=14, pady=(0, 10))

    def salvar_editor_no_modelo():
        nome = grupo_atual.get()
        if not nome:
            return
        linhas = [l.strip().upper() for l in caixa.get("1.0", "end").splitlines() if l.strip()]
        if not linhas:
            messagebox.showwarning("YUPI", "O grupo precisa ter pelo menos uma especialidade.")
            return False
        grupos[nome] = list(dict.fromkeys(linhas))
        return True

    botoes_grupo = {}

    def selecionar(nome):
        if grupo_atual.get() and grupo_atual.get() != nome:
            salvar_editor_no_modelo()
        grupo_atual.set(nome)
        lbl_grupo.configure(text=nome)
        caixa.delete("1.0", "end")
        caixa.insert("1.0", "\n".join(grupos.get(nome, [])))
        for chave, botao in botoes_grupo.items():
            botao.configure(fg_color=("#3B8ED0" if chave == nome else "transparent"))

    def recriar_lateral():
        for w in lateral.winfo_children():
            w.destroy()
        botoes_grupo.clear()
        for nome in sorted(grupos):
            btn = ctk.CTkButton(lateral, text=nome, anchor="w", fg_color="transparent", command=lambda n=nome: selecionar(n))
            btn.pack(fill="x", pady=2)
            botoes_grupo[nome] = btn

    def salvar_tudo():
        if salvar_editor_no_modelo() is False:
            return
        salvar_grupos(grupos)
        if ao_salvar:
            ao_salvar()
        messagebox.showinfo("YUPI", "Regras salvas. Refaça a conferência para aplicar as alterações.")
        janela.destroy()

    def restaurar():
        if not messagebox.askyesno("YUPI", "Restaurar todas as regras originais de Consultas?"):
            return
        grupos.clear()
        grupos.update(restaurar_padrao())
        recriar_lateral()
        primeiro = next(iter(grupos))
        selecionar(primeiro)

    rodape = ctk.CTkFrame(janela, fg_color="transparent")
    rodape.pack(fill="x", padx=16, pady=(0, 16))
    ctk.CTkButton(rodape, text="Restaurar padrão", fg_color="gray", command=restaurar).pack(side="left")
    ctk.CTkButton(rodape, text="Cancelar", fg_color="gray", command=janela.destroy).pack(side="right", padx=(8, 0))
    ctk.CTkButton(rodape, text="Salvar regras", command=salvar_tudo).pack(side="right")

    recriar_lateral()
    if grupos:
        selecionar(grupo_atual.get())
