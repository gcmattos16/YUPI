import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from logica.leitor_siresp import ler_siresp
from logica.leitor_analitico import ler_analitico
from logica.comparador import comparar
from logica.exportador import exportar_excel, exportar_pdf
from interface.painel_pdf import criar_painel_pdf, atualizar_pdf
from interface.tabela import TabelaConsultas
from interface.filtros import criar_barra_filtros
from interface.auditoria import criar_painel_auditoria, mostrar_detalhe_auditoria
from interface.dashboard_consulta import DashboardConsulta
from interface.regras_consultas import abrir_editor_regras
from interface.historico_consultas import abrir_historico_consultas
from consultas.auditor import analisar, analisar_item
from consultas.historico import registrar_conferencia, obter_correcoes, salvar_correcao


def abrir_conferencia(app):
    for widget in app.winfo_children():
        widget.destroy()

    app.title("YUPI • Conferência de Consultas")
    caminho_siresp = ""
    caminho_analitico = ""
    conferencia_id = ""
    auditorias = []
    indice_auditoria = 0
    dados_conferencia = []

    topo = ctk.CTkFrame(app, height=70, corner_radius=0)
    topo.pack(fill="x")
    ctk.CTkLabel(topo, text="📋 Consultas Inteligentes", font=("Segoe UI", 24, "bold")).pack(side="left", padx=20, pady=15)

    def voltar():
        from home import abrir_home
        abrir_home(app)

    ctk.CTkButton(topo, text="← Voltar", width=110, command=voltar).pack(side="right", padx=20)

    corpo = ctk.CTkFrame(app, fg_color="transparent")
    corpo.pack(fill="both", expand=True, padx=20, pady=16)

    frame_pdf = ctk.CTkFrame(corpo, corner_radius=12)
    frame_pdf.pack(fill="x", pady=(0, 10))
    lbl_siresp, lbl_analitico, btn_siresp, btn_analitico = criar_painel_pdf(frame_pdf)

    # Ações da conferência
    barra_acoes = ctk.CTkFrame(corpo, fg_color="transparent")
    barra_acoes.pack(fill="x", pady=(0, 8))

    btn_regras = ctk.CTkButton(barra_acoes, text="⚙ Regras", width=105)
    btn_regras.pack(side="left", padx=(0, 6))
    btn_historico = ctk.CTkButton(barra_acoes, text="📚 Histórico", width=115, command=lambda: abrir_historico_consultas(app))
    btn_historico.pack(side="left", padx=6)
    btn_excel = ctk.CTkButton(barra_acoes, text="📗 Excel", width=100)
    btn_excel.pack(side="right", padx=(6, 0))
    btn_pdf = ctk.CTkButton(barra_acoes, text="📄 PDF", width=90)
    btn_pdf.pack(side="right", padx=6)

    lbl_status = ctk.CTkLabel(barra_acoes, text="Selecione os dois PDFs para iniciar.", font=("Segoe UI", 11))
    lbl_status.pack(side="left", padx=12)

    dashboard = DashboardConsulta(corpo)

    conteudo = ctk.CTkFrame(corpo, fg_color="transparent")
    conteudo.pack(fill="both", expand=True)

    frame_tabela = ctk.CTkFrame(conteudo, fg_color="transparent")
    frame_tabela.pack(side="left", fill="both", expand=True, padx=(0, 10))

    frame_auditoria = ctk.CTkFrame(conteudo, width=350, fg_color="transparent")
    frame_auditoria.pack(side="right", fill="both")
    frame_auditoria.pack_propagate(False)

    painel_auditoria, btn_anterior, lbl_contador, btn_proximo = criar_painel_auditoria(frame_auditoria)
    barra_filtros, entrada_pesquisa, combo_filtro = criar_barra_filtros(frame_tabela)
    tabela = None

    def aplicar_correcoes_salvas():
        if not conferencia_id:
            return
        correcoes = obter_correcoes(conferencia_id)
        for item in dados_conferencia:
            correcao = correcoes.get(item.get("especialidade"), {})
            if correcao.get("corrigido"):
                item["corrigido"] = True
                item["responsavel"] = correcao.get("responsavel", "")
                item["observacao_correcao"] = correcao.get("observacao", "")
                item["data_correcao"] = correcao.get("data_hora", "")

    def marcar_auditoria_corrigida(auditoria):
        if conferencia_id:
            salvar_correcao(
                conferencia_id,
                auditoria["especialidade"],
                auditoria.get("responsavel", ""),
                auditoria.get("observacao_correcao", ""),
            )
        for item in dados_conferencia:
            if item["especialidade"] == auditoria["especialidade"]:
                item.update({
                    "corrigido": True,
                    "responsavel": auditoria.get("responsavel", ""),
                    "observacao_correcao": auditoria.get("observacao_correcao", ""),
                    "data_correcao": auditoria.get("data_correcao", ""),
                })
                break
        for aud in auditorias:
            if aud["especialidade"] == auditoria["especialidade"]:
                aud.update(auditoria)
                break
        dashboard.atualizar(dados_conferencia)
        aplicar_filtros()
        mostrar_detalhe_auditoria(painel_auditoria, auditoria, ao_corrigir=marcar_auditoria_corrigida)

    def ao_selecionar_especialidade(especialidade):
        nonlocal indice_auditoria
        item = next((x for x in dados_conferencia if x.get("especialidade") == especialidade), None)
        if item is None:
            mostrar_detalhe_auditoria(painel_auditoria, None)
            return
        detalhe = analisar_item(item)
        detalhe.update({k: item[k] for k in ("corrigido", "responsavel", "observacao_correcao", "data_correcao") if k in item})
        mostrar_detalhe_auditoria(painel_auditoria, detalhe, ao_corrigir=marcar_auditoria_corrigida if item.get("diferenca", 0) != 0 else None)
        for idx, aud in enumerate(auditorias):
            if aud["especialidade"] == especialidade:
                indice_auditoria = idx
                lbl_contador.configure(text=f"{idx + 1} / {len(auditorias)}")
                return
        lbl_contador.configure(text=f"— / {len(auditorias)}" if auditorias else "0 / 0")

    tabela = TabelaConsultas(frame_tabela, callback=ao_selecionar_especialidade)

    def aplicar_filtros():
        texto = entrada_pesquisa.get().strip().lower()
        filtro = combo_filtro.get()
        dados_filtrados = []
        for item in dados_conferencia:
            if texto and texto not in str(item.get("especialidade", "")).lower():
                continue
            diferenca = item.get("diferenca", 0)
            if filtro == "Somente OK" and diferenca != 0:
                continue
            if filtro == "Somente Divergências" and diferenca == 0:
                continue
            dados_filtrados.append(item)
        tabela.preencher(dados_filtrados)

    entrada_pesquisa.bind("<KeyRelease>", lambda event: aplicar_filtros())
    combo_filtro.configure(command=lambda valor: aplicar_filtros())

    def executar_conferencia():
        nonlocal auditorias, indice_auditoria, dados_conferencia, conferencia_id
        if not caminho_siresp or not caminho_analitico:
            return
        try:
            lbl_status.configure(text="⏳ Lendo e comparando os relatórios...")
            app.update_idletasks()
            dados_siresp = ler_siresp(caminho_siresp)
            dados_analitico = ler_analitico(caminho_analitico)
            dados_conferencia = comparar(dados_siresp, dados_analitico)
            conferencia_id = registrar_conferencia(caminho_siresp, caminho_analitico, dados_conferencia)
            aplicar_correcoes_salvas()
            auditorias = analisar(dados_conferencia)
            # Levar correções salvas para a auditoria
            for aud in auditorias:
                item = next((x for x in dados_conferencia if x["especialidade"] == aud["especialidade"]), None)
                if item:
                    aud.update({k: item[k] for k in ("corrigido", "responsavel", "observacao_correcao", "data_correcao") if k in item})
            indice_auditoria = 0
            dashboard.atualizar(dados_conferencia)
            aplicar_filtros()
            if auditorias:
                mostrar_detalhe_auditoria(painel_auditoria, auditorias[0], ao_corrigir=marcar_auditoria_corrigida)
                lbl_contador.configure(text=f"1 / {len(auditorias)}")
            elif dados_conferencia:
                mostrar_detalhe_auditoria(painel_auditoria, analisar_item(dados_conferencia[0]))
                lbl_contador.configure(text="0 / 0")
            lbl_status.configure(text=f"✅ Conferência concluída • {len(dados_conferencia)} especialidades • {len(auditorias)} divergência(s)")
        except Exception as erro:
            lbl_status.configure(text="❌ Não foi possível concluir a conferência.")
            messagebox.showerror("YUPI", f"Erro ao processar os PDFs:\n\n{erro}")

    def selecionar_siresp():
        nonlocal caminho_siresp
        caminho = filedialog.askopenfilename(title="Selecione o PDF do SIRESP", filetypes=[("Arquivos PDF", "*.pdf")])
        if caminho:
            caminho_siresp = caminho
            atualizar_pdf(lbl_siresp, caminho_siresp)
            executar_conferencia()

    def selecionar_analitico():
        nonlocal caminho_analitico
        caminho = filedialog.askopenfilename(title="Selecione o PDF Analítico", filetypes=[("Arquivos PDF", "*.pdf")])
        if caminho:
            caminho_analitico = caminho
            atualizar_pdf(lbl_analitico, caminho_analitico)
            executar_conferencia()

    btn_siresp.configure(command=selecionar_siresp)
    btn_analitico.configure(command=selecionar_analitico)

    def navegar(delta):
        nonlocal indice_auditoria
        if not auditorias:
            return
        novo = indice_auditoria + delta
        if novo < 0 or novo >= len(auditorias):
            return
        indice_auditoria = novo
        aud = auditorias[indice_auditoria]
        mostrar_detalhe_auditoria(painel_auditoria, aud, ao_corrigir=marcar_auditoria_corrigida)
        lbl_contador.configure(text=f"{indice_auditoria + 1} / {len(auditorias)}")
        tabela.selecionar(aud["especialidade"])

    btn_anterior.configure(command=lambda: navegar(-1))
    btn_proximo.configure(command=lambda: navegar(1))

    def exportar(tipo):
        if not dados_conferencia:
            messagebox.showwarning("YUPI", "Faça uma conferência antes de exportar.")
            return
        metadados = {"siresp": os.path.basename(caminho_siresp), "analitico": os.path.basename(caminho_analitico)}
        if tipo == "xlsx":
            caminho = filedialog.asksaveasfilename(title="Exportar para Excel", defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")], initialfile="YUPI_Consultas.xlsx")
            if caminho:
                try:
                    exportar_excel(caminho, dados_conferencia, metadados)
                    messagebox.showinfo("YUPI", "Relatório Excel exportado com sucesso.")
                except Exception as erro:
                    messagebox.showerror("YUPI", f"Erro ao exportar Excel:\n\n{erro}")
        else:
            caminho = filedialog.asksaveasfilename(title="Exportar para PDF", defaultextension=".pdf", filetypes=[("PDF", "*.pdf")], initialfile="YUPI_Consultas.pdf")
            if caminho:
                try:
                    exportar_pdf(caminho, dados_conferencia, metadados)
                    messagebox.showinfo("YUPI", "Relatório PDF exportado com sucesso.")
                except Exception as erro:
                    messagebox.showerror("YUPI", f"Erro ao exportar PDF:\n\n{erro}")

    btn_excel.configure(command=lambda: exportar("xlsx"))
    btn_pdf.configure(command=lambda: exportar("pdf"))
    btn_regras.configure(command=lambda: abrir_editor_regras(app, ao_salvar=executar_conferencia if dados_conferencia else None))

    dashboard.limpar()
    mostrar_detalhe_auditoria(painel_auditoria, None)
    lbl_contador.configure(text="0 / 0")
