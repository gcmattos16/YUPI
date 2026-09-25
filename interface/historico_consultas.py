import customtkinter as ctk
from consultas.historico import listar_conferencias


def abrir_historico_consultas(parent):
    janela = ctk.CTkToplevel(parent)
    janela.title("YUPI • Histórico de Consultas")
    janela.geometry("900x620")
    janela.minsize(780, 520)
    janela.grab_set()

    ctk.CTkLabel(janela, text="📚 Histórico de conferências", font=("Segoe UI", 21, "bold")).pack(pady=(16, 4))
    ctk.CTkLabel(janela, text="Últimas conferências salvas automaticamente pela YUPI.", font=("Segoe UI", 11)).pack(pady=(0, 12))

    scroll = ctk.CTkScrollableFrame(janela)
    scroll.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    conferencias = listar_conferencias(60)
    if not conferencias:
        ctk.CTkLabel(scroll, text="Ainda não há conferências salvas.").pack(pady=30)
        return

    for conf in conferencias:
        bloco = ctk.CTkFrame(scroll, corner_radius=10)
        bloco.pack(fill="x", pady=5)
        data = conf.get("data_hora", "").replace("T", " ")
        ctk.CTkLabel(bloco, text=f"🗓 {data}", font=("Segoe UI", 13, "bold"), anchor="w").pack(fill="x", padx=12, pady=(9, 2))
        texto = (
            f"SIRESP: {conf.get('siresp', '')}\n"
            f"Analítico: {conf.get('analitico', '')}\n"
            f"Total: {conf.get('total', 0)}   •   OK: {conf.get('ok', 0)}   •   Divergências: {conf.get('divergencias', 0)}   •   Conformidade: {conf.get('conformidade', 0)}%"
        )
        ctk.CTkLabel(bloco, text=texto, justify="left", anchor="w", wraplength=820, font=("Segoe UI", 11)).pack(fill="x", padx=12, pady=(0, 9))
