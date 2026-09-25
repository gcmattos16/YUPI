import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime


def criar_painel_auditoria(pai):
    frame = ctk.CTkFrame(pai, corner_radius=12)
    frame.pack(fill="both", expand=True)

    titulo = ctk.CTkLabel(frame, text="🔎 DETALHES & AUDITORIA", font=("Segoe UI", 18, "bold"))
    titulo.pack(pady=(12, 8))

    navegacao = ctk.CTkFrame(frame, fg_color="transparent")
    navegacao.pack(fill="x", padx=10, pady=(0, 10))

    btn_anterior = ctk.CTkButton(navegacao, text="◀", width=40)
    btn_anterior.pack(side="left")

    lbl_contador = ctk.CTkLabel(navegacao, text="0 / 0", font=("Segoe UI", 13, "bold"))
    lbl_contador.pack(side="left", expand=True)

    btn_proximo = ctk.CTkButton(navegacao, text="▶", width=40)
    btn_proximo.pack(side="right")

    scroll = ctk.CTkScrollableFrame(frame, fg_color="transparent")
    scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    return scroll, btn_anterior, lbl_contador, btn_proximo


def mostrar_detalhe_auditoria(scroll, auditoria, ao_corrigir=None):
    for widget in scroll.winfo_children():
        widget.destroy()

    if auditoria is None:
        ctk.CTkLabel(
            scroll,
            text="Selecione uma especialidade na tabela para ver a composição e a auditoria.",
            wraplength=300,
            justify="left",
            font=("Segoe UI", 13),
        ).pack(pady=20, padx=10)
        return

    _criar_card(scroll, auditoria, ao_corrigir)


def _linha_detalhe(pai, titulo, detalhes):
    if not detalhes:
        return
    ctk.CTkLabel(pai, text=titulo, font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=12, pady=(8, 2))
    for detalhe in detalhes:
        nome = detalhe.get("especialidade", "")
        quantidade = detalhe.get("quantidade", 0)
        ctk.CTkLabel(
            pai,
            text=f"• {nome}: {quantidade}",
            justify="left",
            anchor="w",
            wraplength=290,
            font=("Segoe UI", 11),
        ).pack(fill="x", padx=18, pady=1)


def _abrir_modal_correcao(auditoria, ao_corrigir):
    janela = ctk.CTkToplevel()
    janela.title("Marcar divergência como corrigida")
    janela.geometry("470x390")
    janela.resizable(False, False)
    janela.grab_set()

    ctk.CTkLabel(janela, text="✓ Registrar correção", font=("Segoe UI", 19, "bold")).pack(pady=(18, 4))
    ctk.CTkLabel(
        janela,
        text=auditoria.get("especialidade", ""),
        font=("Segoe UI", 13, "bold"),
        wraplength=420,
    ).pack(pady=(0, 14))

    ctk.CTkLabel(janela, text="Responsável", anchor="w").pack(fill="x", padx=24)
    entrada_responsavel = ctk.CTkEntry(janela, placeholder_text="Ex.: Gabriel")
    entrada_responsavel.pack(fill="x", padx=24, pady=(3, 12))

    ctk.CTkLabel(janela, text="Observação da correção", anchor="w").pack(fill="x", padx=24)
    entrada_obs = ctk.CTkTextbox(janela, height=130)
    entrada_obs.pack(fill="x", padx=24, pady=(3, 12))

    def confirmar():
        responsavel = entrada_responsavel.get().strip()
        observacao = entrada_obs.get("1.0", "end").strip()
        if not responsavel:
            messagebox.showwarning("YUPI", "Informe quem realizou a correção.")
            return
        auditoria["corrigido"] = True
        auditoria["responsavel"] = responsavel
        auditoria["observacao_correcao"] = observacao
        auditoria["data_correcao"] = datetime.now().isoformat(timespec="seconds")
        janela.destroy()
        if ao_corrigir:
            ao_corrigir(auditoria)

    botoes = ctk.CTkFrame(janela, fg_color="transparent")
    botoes.pack(fill="x", padx=24, pady=8)
    ctk.CTkButton(botoes, text="Cancelar", fg_color="gray", command=janela.destroy).pack(side="left", expand=True, fill="x", padx=(0, 5))
    ctk.CTkButton(botoes, text="Salvar correção", command=confirmar).pack(side="left", expand=True, fill="x", padx=(5, 0))


def _criar_card(scroll, auditoria, ao_corrigir=None):
    bloco = ctk.CTkFrame(scroll, corner_radius=10)
    bloco.pack(fill="x", padx=5, pady=6)

    diferenca = auditoria.get("diferenca", 0)
    corrigido = auditoria.get("corrigido", False)

    if corrigido:
        status_texto = "🟢 CORRIGIDO"
    elif diferenca == 0:
        status_texto = "✅ OK"
    else:
        status_texto = auditoria.get("prioridade", "❌ DIVERGÊNCIA")

    ctk.CTkLabel(bloco, text=status_texto, font=("Segoe UI", 14, "bold")).pack(pady=(12, 4))
    ctk.CTkLabel(
        bloco,
        text=auditoria.get("especialidade", ""),
        font=("Segoe UI", 15, "bold"),
        wraplength=300,
    ).pack(padx=12, pady=(0, 8))

    resumo = (
        f"SIRESP: {auditoria.get('siresp', 0)}\n"
        f"Analítico: {auditoria.get('analitico', 0)}\n"
        f"Diferença: {diferenca:+d}\n\n"
        f"{auditoria.get('diagnostico', auditoria.get('explicacao', ''))}"
    )
    ctk.CTkLabel(bloco, text=resumo, justify="left", anchor="w", wraplength=300, font=("Segoe UI", 12)).pack(fill="x", padx=12, pady=(0, 8))

    _linha_detalhe(bloco, "📄 Composição SIRESP", auditoria.get("detalhes_siresp", []))
    _linha_detalhe(bloco, "📄 Composição Analítico", auditoria.get("detalhes_analitico", []))

    if diferenca != 0:
        ctk.CTkLabel(bloco, text="⚠ Possíveis causas", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=12, pady=(10, 2))
        for causa in auditoria.get("causas", []):
            ctk.CTkLabel(bloco, text=f"• {causa}", justify="left", anchor="w", wraplength=290, font=("Segoe UI", 11)).pack(fill="x", padx=18)

        ctk.CTkLabel(bloco, text="📋 Conferir", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x", padx=12, pady=(10, 2))
        for item in auditoria.get("itens", []):
            ctk.CTkLabel(bloco, text=f"• {item}", justify="left", anchor="w", wraplength=290, font=("Segoe UI", 11)).pack(fill="x", padx=18)

        if "consulta" in auditoria or "sessao" in auditoria:
            codigo = []
            if "consulta" in auditoria:
                codigo.append(f"Consulta SUS: {auditoria['consulta']}")
            if "sessao" in auditoria:
                codigo.append(f"Sessão SUS: {auditoria['sessao']}")
            ctk.CTkLabel(bloco, text="\n".join(codigo), justify="left", anchor="w", font=("Segoe UI", 11, "bold")).pack(fill="x", padx=12, pady=(8, 0))

        if corrigido:
            correcao = (
                f"Responsável: {auditoria.get('responsavel', 'Não informado')}\n"
                f"Data: {auditoria.get('data_correcao', '')}\n"
                f"Observação: {auditoria.get('observacao_correcao', '') or 'Sem observação'}"
            )
            ctk.CTkLabel(bloco, text=correcao, justify="left", anchor="w", wraplength=300, font=("Segoe UI", 11)).pack(fill="x", padx=12, pady=10)
        elif ao_corrigir:
            ctk.CTkButton(
                bloco,
                text="✓ Marcar como corrigido",
                height=36,
                font=("Segoe UI", 12, "bold"),
                command=lambda: _abrir_modal_correcao(auditoria, ao_corrigir),
            ).pack(fill="x", padx=12, pady=12)
