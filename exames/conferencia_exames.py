import csv
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox

from exames.leitor_siresp_exames import ler_siresp_exames
from exames.leitor_faturamento_exames import (
    ler_faturamento_exames,
    ler_faturamento_exames_detalhado,
)
from exames.comparador_exames import comparar_exames
from exames.configuracao_mapeamento import (
    GRUPO_MASTOLOGIA_MAIOR,
    carregar_mapeamentos,
    salvar_mapeamento,
    carregar_historico_global,
    registrar_historico_global,
)

from interface.tabela_exames import TabelaExames


# ============================================================
# AJUSTE DE STATUS DOS PROCEDIMENTOS COMPARTILHADOS
# ============================================================

def _ajustar_resultado_compartilhado(resultado):
    """Compatibilidade.

    A distribuição de procedimentos compartilhados agora é resolvida
    diretamente no comparador_exames, onde existe controle de saldo.
    Esta função não altera mais os números depois da comparação.
    """
    return resultado


# ============================================================
# AUDITORIA
# ============================================================

def _abrir_auditoria(app, dados):

    janela = ctk.CTkToplevel(
        app
    )

    janela.title(
        f"Auditoria - {dados.get('exame', '')}"
    )

    janela.geometry(
        "820x680"
    )

    janela.minsize(
        700,
        560
    )

    janela.grab_set()

    # ========================================================
    # CABEÇALHO
    # ========================================================

    topo = ctk.CTkFrame(
        janela,
        height=80,
        corner_radius=0
    )

    topo.pack(
        fill="x"
    )

    ctk.CTkLabel(
        topo,
        text="🔎 Auditoria do Exame",
        font=(
            "Segoe UI",
            24,
            "bold"
        )
    ).pack(
        side="left",
        padx=24,
        pady=18
    )

    ctk.CTkButton(
        topo,
        text="Fechar",
        width=100,
        command=janela.destroy
    ).pack(
        side="right",
        padx=20
    )

    # ========================================================
    # SCROLL
    # ========================================================

    scroll = ctk.CTkScrollableFrame(
        janela,
        fg_color="transparent"
    )

    scroll.pack(
        fill="both",
        expand=True,
        padx=20,
        pady=15
    )

    # ========================================================
    # TÍTULO
    # ========================================================

    exame = dados.get(
        "exame",
        ""
    )

    status = dados.get(
        "status",
        "ERRO"
    )

    if status in ("OK", "✅ OK"):
        texto_status = "✅ CONFERIDO"
    elif status == "CONFIGURAR":
        texto_status = "⚙ CONFIGURAÇÃO PENDENTE"
    elif status == "ATENCAO":
        texto_status = "⚠ REVISAR ESCOPO"
    else:
        texto_status = "🔴 DIVERGÊNCIA"

    ctk.CTkLabel(
        scroll,
        text=exame,
        font=(
            "Segoe UI",
            20,
            "bold"
        ),
        anchor="w"
    ).pack(
        fill="x",
        pady=(0, 4)
    )

    ctk.CTkLabel(
        scroll,
        text=texto_status,
        font=(
            "Segoe UI",
            14,
            "bold"
        ),
        anchor="w"
    ).pack(
        fill="x",
        pady=(0, 8)
    )

    observacao = dados.get("observacao", "")
    if observacao:
        ctk.CTkLabel(
            scroll,
            text=f"ℹ {observacao}",
            anchor="w",
            wraplength=730,
        ).pack(fill="x", pady=(0, 18))
    else:
        ctk.CTkFrame(scroll, height=1, fg_color="transparent").pack(pady=(0, 10))

    # ========================================================
    # CARDS RESUMO
    # ========================================================

    resumo = ctk.CTkFrame(
        scroll,
        fg_color="transparent"
    )

    resumo.pack(
        fill="x",
        pady=(0, 18)
    )

    resumo.grid_columnconfigure(
        (0, 1, 2),
        weight=1
    )

    def card(
        parent,
        coluna,
        titulo,
        valor_card
    ):

        frame = ctk.CTkFrame(
            parent,
            corner_radius=14
        )

        frame.grid(
            row=0,
            column=coluna,
            sticky="ew",
            padx=5
        )

        ctk.CTkLabel(
            frame,
            text=titulo,
            font=(
                "Segoe UI",
                12,
                "bold"
            )
        ).pack(
            pady=(12, 2)
        )

        ctk.CTkLabel(
            frame,
            text=str(valor_card),
            font=(
                "Segoe UI",
                24,
                "bold"
            )
        ).pack(
            pady=(0, 12)
        )

    card(
        resumo,
        0,
        "SIRESP",
        dados.get("siresp", 0)
    )

    card(
        resumo,
        1,
        "GLOBAL",
        dados.get("global", 0)
    )

    card(
        resumo,
        2,
        "DIFERENÇA",
        dados.get("diferenca", 0)
    )

    # ========================================================
    # AUDITORIA ESTRUTURADA
    # ========================================================

    auditoria = dados.get(
        "auditoria",
        {}
    )

    siresp_auditoria = auditoria.get(
        "siresp",
        {}
    )

    global_auditoria = auditoria.get(
        "global",
        {}
    )

    # ========================================================
    # CARD SIRESP
    # ========================================================

    frame_siresp = ctk.CTkFrame(
        scroll,
        corner_radius=14
    )

    frame_siresp.pack(
        fill="x",
        pady=7
    )

    ctk.CTkLabel(
        frame_siresp,
        text="📄 SIRESP",
        font=(
            "Segoe UI",
            16,
            "bold"
        ),
        anchor="w"
    ).pack(
        fill="x",
        padx=18,
        pady=(14, 8)
    )

    def linha(
        parent,
        nome,
        valor_linha
    ):

        frame = ctk.CTkFrame(
            parent,
            fg_color="transparent"
        )

        frame.pack(
            fill="x",
            padx=18,
            pady=3
        )

        ctk.CTkLabel(
            frame,
            text=nome,
            anchor="w"
        ).pack(
            side="left"
        )

        ctk.CTkLabel(
            frame,
            text=str(valor_linha),
            font=(
                "Segoe UI",
                13,
                "bold"
            )
        ).pack(
            side="right"
        )

    # Externo / interno / direto ficam SOMENTE aqui.
    linha(
        frame_siresp,
        "Externo",
        siresp_auditoria.get(
            "externo",
            dados.get("externo", 0)
        )
    )

    linha(
        frame_siresp,
        "Interno",
        siresp_auditoria.get(
            "interno",
            dados.get("interno", 0)
        )
    )

    linha(
        frame_siresp,
        "Direto",
        siresp_auditoria.get(
            "direto",
            dados.get("direto", 0)
        )
    )

    linha(
        frame_siresp,
        "Total",
        siresp_auditoria.get(
            "total_bruto",
            dados.get("siresp", 0)
        )
    )

    if (
        siresp_auditoria.get(
            "multiplicador",
            1
        ) != 1
    ):

        linha(
            frame_siresp,
            "Multiplicador",
            siresp_auditoria.get(
                "multiplicador",
                1
            )
        )

    linha(
        frame_siresp,
        "Total final",
        siresp_auditoria.get(
            "total_final",
            dados.get("siresp", 0)
        )
    )

    # ========================================================
    # CARD GLOBAL
    # ========================================================

    frame_global = ctk.CTkFrame(
        scroll,
        corner_radius=14
    )

    frame_global.pack(
        fill="x",
        pady=7
    )

    ctk.CTkLabel(
        frame_global,
        text="📊 GLOBAL",
        font=(
            "Segoe UI",
            16,
            "bold"
        ),
        anchor="w"
    ).pack(
        fill="x",
        padx=18,
        pady=(14, 8)
    )

    detalhes_global = global_auditoria.get(
        "detalhes",
        dados.get(
            "detalhes_global",
            []
        )
    )

    if detalhes_global:

        for detalhe in detalhes_global:

            nome_detalhe = detalhe.get(
                "exame",
                ""
            )

            quantidade = detalhe.get(
                "quantidade",
                0
            )

            linha(
                frame_global,
                nome_detalhe,
                quantidade
            )

    linha(
        frame_global,
        "Total",
        global_auditoria.get(
            "total_final",
            dados.get("global", 0)
        )
    )

    # ========================================================
    # PROCEDIMENTOS COMPARTILHADOS
    # ========================================================

    compartilhados = auditoria.get(
        "procedimentos_compartilhados",
        []
    )

    if compartilhados:

        frame_compartilhado = ctk.CTkFrame(
            scroll,
            corner_radius=14
        )

        frame_compartilhado.pack(
            fill="x",
            pady=7
        )

        ctk.CTkLabel(
            frame_compartilhado,
            text="🔗 PROCEDIMENTOS COMPARTILHADOS",
            font=(
                "Segoe UI",
                16,
                "bold"
            ),
            anchor="w"
        ).pack(
            fill="x",
            padx=18,
            pady=(14, 4)
        )

        ctk.CTkLabel(
            frame_compartilhado,
            text=(
                "Esses procedimentos aparecem na auditoria "
                "e não ficam poluindo a tabela principal."
            ),
            anchor="w",
            wraplength=720
        ).pack(
            fill="x",
            padx=18,
            pady=(0, 10)
        )

        for proc in compartilhados:

            bloco = ctk.CTkFrame(
                frame_compartilhado,
                corner_radius=10
            )

            bloco.pack(
                fill="x",
                padx=14,
                pady=5
            )

            ctk.CTkLabel(
                bloco,
                text=proc.get(
                    "procedimento",
                    ""
                ),
                font=(
                    "Segoe UI",
                    13,
                    "bold"
                ),
                anchor="w"
            ).pack(
                fill="x",
                padx=12,
                pady=(10, 5)
            )

            linha(
                bloco,
                "Global disponível",
                proc.get(
                    "quantidade_global",
                    0
                )
            )

            linha(
                bloco,
                "Utilizado",
                proc.get(
                    "quantidade_utilizada",
                    0
                )
            )

            linha(
                bloco,
                "Disponível após",
                proc.get(
                    "quantidade_disponivel",
                    0
                )
            )

            if proc.get(
                "somente_auditoria",
                False
            ):

                ctk.CTkLabel(
                    bloco,
                    text="ℹ Somente auditoria",
                    font=(
                        "Segoe UI",
                        11,
                        "bold"
                    ),
                    anchor="w"
                ).pack(
                    fill="x",
                    padx=12,
                    pady=(5, 10)
                )

    # ========================================================
    # BOTÃO FECHAR
    # ========================================================

    ctk.CTkButton(
        scroll,
        text="Fechar auditoria",
        height=40,
        command=janela.destroy
    ).pack(
        fill="x",
        pady=18
    )


# ============================================================
# CONFIGURAÇÃO MANUAL - QUALQUER EXAME
# ============================================================

def _abrir_configuracao_exame(
    app,
    grupo,
    registros_global,
    total_siresp=None,
    mapeamento_temporario=None,
    ao_aplicar=None,
):
    """Editor de regra manual reutilizável para qualquer exame do SIRESP.

    O usuário pode apontar um ou mais procedimentos do Global para o exame
    selecionado. A seleção pode valer só nesta conferência ou ser persistida.
    """
    grupo = str(grupo or "").strip().upper()
    if not grupo:
        return
    if not registros_global:
        messagebox.showwarning(
            "Global não carregado",
            "Selecione ou confira um Demonstrativo Global antes de configurar a regra.",
        )
        return

    agregados = {}
    for registro in registros_global:
        nome = registro.get("nome_exato", "").strip().upper()
        if not nome:
            continue
        item = agregados.setdefault(nome, {"quantidade": 0, "codigos": set(), "originais": set()})
        item["quantidade"] += int(registro.get("quantidade", 0) or 0)
        if registro.get("codigo"):
            item["codigos"].add(str(registro["codigo"]))
        if registro.get("nome_original"):
            item["originais"].add(str(registro["nome_original"]))

    salvos = set(carregar_mapeamentos().get(grupo, []))
    historico = set(carregar_historico_global())
    novos = set(agregados) - historico if historico else set()
    selecionados = set(mapeamento_temporario if mapeamento_temporario is not None else salvos)

    janela = ctk.CTkToplevel(app)
    janela.title(f"Configurar regra - {grupo}")
    janela.geometry("1040x760")
    janela.minsize(900, 650)
    janela.grab_set()

    topo = ctk.CTkFrame(janela, corner_radius=0)
    topo.pack(fill="x")
    ctk.CTkLabel(
        topo,
        text="⚙ Configurar regra de exame",
        font=("Segoe UI", 22, "bold"),
    ).pack(side="left", padx=24, pady=16)
    ctk.CTkButton(topo, text="Fechar", width=90, command=janela.destroy).pack(side="right", padx=20)

    corpo = ctk.CTkFrame(janela, fg_color="transparent")
    corpo.pack(fill="both", expand=True, padx=22, pady=16)

    ctk.CTkLabel(
        corpo,
        text=grupo,
        anchor="w",
        font=("Segoe UI", 16, "bold"),
    ).pack(fill="x")
    ctk.CTkLabel(
        corpo,
        text=(
            "Selecione os procedimentos do Demonstrativo Global que devem formar este exame. "
            "A YUPI salvará os nomes/códigos da regra e sempre puxará as quantidades do Global atual."
        ),
        anchor="w",
        justify="left",
        wraplength=970,
        text_color=("gray35", "gray70"),
    ).pack(fill="x", pady=(3, 12))

    painel_meta = ctk.CTkFrame(corpo, corner_radius=10)
    painel_meta.pack(fill="x", pady=(0, 12))
    lbl_meta = ctk.CTkLabel(painel_meta, text="", font=("Segoe UI", 13, "bold"))
    lbl_meta.pack(side="left", padx=14, pady=11)
    lbl_diferenca = ctk.CTkLabel(painel_meta, text="", font=("Segoe UI", 13, "bold"))
    lbl_diferenca.pack(side="right", padx=14, pady=11)

    barra = ctk.CTkFrame(corpo, fg_color="transparent")
    barra.pack(fill="x", pady=(0, 10))
    pesquisa = ctk.CTkEntry(
        barra,
        placeholder_text="Pesquisar procedimento ou código SIGTAP...",
        width=500,
        height=38,
    )
    pesquisa.pack(side="left")

    somente_relacionados = ctk.BooleanVar(value=False)
    ctk.CTkCheckBox(
        barra,
        text="Mostrar só nomes relacionados",
        variable=somente_relacionados,
    ).pack(side="left", padx=16)

    lbl_total = ctk.CTkLabel(barra, text="0 selecionados · total 0", font=("Segoe UI", 12, "bold"))
    lbl_total.pack(side="right")

    scroll = ctk.CTkScrollableFrame(corpo)
    scroll.pack(fill="both", expand=True)

    palavras_ignoradas = {
        "PROCEDIMENTO", "INTERNO", "EXTERNO", "COM", "SEM", "DE", "DA", "DO", "DAS", "DOS",
        "CIRURGIA", "MAIOR", "MENOR", "GERAL", "ATUAL", "LAUDO"
    }
    tokens_grupo = [
        t for t in grupo.replace("-", " ").replace("/", " ").split()
        if len(t) >= 4 and t not in palavras_ignoradas
    ]

    def quantidade_selecionada():
        return sum(agregados[n]["quantidade"] for n in selecionados if n in agregados)

    def atualizar_resumo():
        quantidade = quantidade_selecionada()
        lbl_total.configure(text=f"{len(selecionados)} selecionados · total {quantidade}")
        if total_siresp is None:
            lbl_meta.configure(text="SIRESP: não carregado")
            lbl_diferenca.configure(text="Carregue o SIRESP para comparar a meta")
            return
        alvo = int(total_siresp or 0)
        diferenca = alvo - quantidade
        lbl_meta.configure(text=f"SIRESP: {alvo}   |   Selecionado no Global: {quantidade}")
        if diferenca > 0:
            lbl_diferenca.configure(text=f"Faltam {diferenca}")
        elif diferenca < 0:
            lbl_diferenca.configure(text=f"⚠ {abs(diferenca)} acima")
        else:
            lbl_diferenca.configure(text="✓ Quantidade fechou")

    def alternar(nome, marcado):
        if marcado:
            selecionados.add(nome)
        else:
            selecionados.discard(nome)
        atualizar_resumo()

    def reconstruir(event=None):
        for widget in scroll.winfo_children():
            widget.destroy()
        termo = pesquisa.get().strip().upper()
        nomes = sorted(agregados)
        if somente_relacionados.get() and tokens_grupo:
            nomes = [n for n in nomes if any(t in n for t in tokens_grupo) or n in selecionados]

        exibidos = 0
        for nome in nomes:
            info = agregados[nome]
            texto_busca = " ".join([nome, *info["codigos"], *info["originais"]]).upper()
            if termo and termo not in texto_busca:
                continue
            exibidos += 1
            linha = ctk.CTkFrame(scroll, corner_radius=8)
            linha.pack(fill="x", padx=3, pady=2)

            var = ctk.BooleanVar(value=nome in selecionados)
            ctk.CTkCheckBox(
                linha,
                text="",
                width=26,
                variable=var,
                command=lambda n=nome, v=var: alternar(n, v.get()),
            ).pack(side="left", padx=(10, 4), pady=10)

            bloco = ctk.CTkFrame(linha, fg_color="transparent")
            bloco.pack(side="left", fill="x", expand=True, pady=6)
            titulo = nome
            if nome in novos:
                titulo += "   NOVO"
            if nome in salvos:
                titulo += "   ✓ REGRA SALVA"
            ctk.CTkLabel(bloco, text=titulo, anchor="w", font=("Segoe UI", 12, "bold")).pack(fill="x")
            codigos = ", ".join(sorted(info["codigos"])) or "sem código"
            ctk.CTkLabel(
                bloco,
                text=f"SIGTAP: {codigos}",
                anchor="w",
                font=("Segoe UI", 10),
                text_color=("gray40", "gray65"),
            ).pack(fill="x")
            ctk.CTkLabel(
                linha,
                text=f"Qtd. {info['quantidade']}",
                width=90,
                font=("Segoe UI", 12, "bold"),
            ).pack(side="right", padx=12)

        if exibidos == 0:
            ctk.CTkLabel(scroll, text="Nenhum procedimento encontrado.", font=("Segoe UI", 13)).pack(pady=30)

    def aplicar(salvar_regra):
        lista = sorted(selecionados)
        registrar_historico_global(agregados.keys())
        if salvar_regra:
            salvar_mapeamento(grupo, lista)
        janela.destroy()
        if ao_aplicar:
            ao_aplicar(lista, salvar_regra)
        messagebox.showinfo(
            "YUPI",
            (
                f"Regra de {grupo} salva com {len(lista)} procedimento(s)."
                if salvar_regra
                else f"Seleção aplicada somente nesta conferência ({len(lista)} procedimento(s))."
            ),
        )

    rodape = ctk.CTkFrame(corpo, fg_color="transparent")
    rodape.pack(fill="x", pady=(12, 0))
    ctk.CTkButton(
        rodape,
        text="Limpar seleção",
        width=135,
        fg_color="transparent",
        border_width=1,
        command=lambda: (selecionados.clear(), atualizar_resumo(), reconstruir()),
    ).pack(side="left")
    ctk.CTkButton(
        rodape,
        text="Usar só neste relatório",
        width=190,
        height=40,
        fg_color="transparent",
        border_width=1,
        command=lambda: aplicar(False),
    ).pack(side="right", padx=(8, 0))
    ctk.CTkButton(
        rodape,
        text="✓ Salvar como regra",
        width=180,
        height=40,
        command=lambda: aplicar(True),
    ).pack(side="right")

    pesquisa.bind("<KeyRelease>", reconstruir)
    somente_relacionados.trace_add("write", lambda *_: reconstruir())
    atualizar_resumo()
    reconstruir()


# ============================================================
# CONFERÊNCIA
# ============================================================

def abrir_conferencia_exames(app):
    """Tela principal de exames. A área de Consultas não é alterada aqui."""

    for widget in app.winfo_children():
        widget.destroy()

    caminho_siresp = ""
    caminho_global = ""
    ultimo_resultado = []
    registros_global = []
    bruto_global = {}
    mapeamentos_temporarios = {}

    # --------------------------------------------------------
    # TOPO
    # --------------------------------------------------------
    topo = ctk.CTkFrame(app, height=68, corner_radius=0)
    topo.pack(fill="x")

    ctk.CTkLabel(
        topo,
        text="🩺 Conferência de Exames",
        font=("Segoe UI", 24, "bold"),
    ).pack(side="left", padx=22, pady=14)

    ctk.CTkLabel(
        topo,
        text="SIRESP × Demonstrativo Global",
        font=("Segoe UI", 12),
    ).pack(side="left", padx=(0, 15))

    def voltar():
        from home import abrir_home
        abrir_home(app)

    ctk.CTkButton(topo, text="← Voltar", width=110, command=voltar).pack(side="right", padx=20)

    corpo = ctk.CTkFrame(app, fg_color="transparent")
    corpo.pack(fill="both", expand=True, padx=20, pady=14)

    # --------------------------------------------------------
    # ARQUIVOS
    # --------------------------------------------------------
    arquivos = ctk.CTkFrame(corpo, corner_radius=14)
    arquivos.pack(fill="x", pady=(0, 10))
    arquivos.grid_columnconfigure((0, 1), weight=1)

    def card_arquivo(coluna, titulo, icone):
        card = ctk.CTkFrame(arquivos, fg_color="transparent")
        card.grid(row=0, column=coluna, sticky="ew", padx=16, pady=14)
        ctk.CTkLabel(card, text=f"{icone} {titulo}", font=("Segoe UI", 13, "bold"), anchor="w").pack(fill="x")
        label = ctk.CTkLabel(card, text="Nenhum arquivo selecionado", anchor="w", text_color=("gray35", "gray70"))
        label.pack(fill="x", pady=(4, 8))
        return card, label

    card_siresp, lbl_siresp = card_arquivo(0, "PDF SIRESP", "📄")
    card_global, lbl_global = card_arquivo(1, "PDF GLOBAL", "📊")

    def selecionar_siresp():
        nonlocal caminho_siresp
        arquivo = filedialog.askopenfilename(title="Selecionar PDF SIRESP", filetypes=[("Arquivos PDF", "*.pdf")])
        if arquivo:
            caminho_siresp = arquivo
            lbl_siresp.configure(text=os.path.basename(arquivo), text_color=("gray10", "gray90"))
            lbl_status.configure(text="SIRESP carregado. Selecione o Global e execute a conferência.")

    def selecionar_global():
        nonlocal caminho_global, registros_global, bruto_global, mapeamentos_temporarios
        arquivo = filedialog.askopenfilename(title="Selecionar Demonstrativo Global", filetypes=[("Arquivos PDF", "*.pdf")])
        if arquivo:
            caminho_global = arquivo
            lbl_global.configure(text=os.path.basename(arquivo), text_color=("gray10", "gray90"))
            registros_global = []
            bruto_global = {}
            mapeamentos_temporarios = {}
            btn_configurar.configure(state="normal")
            lbl_status.configure(text="Global selecionado. Pronto para conferir.")

    ctk.CTkButton(card_siresp, text="Selecionar SIRESP", height=34, command=selecionar_siresp).pack(anchor="w")
    ctk.CTkButton(card_global, text="Selecionar Global", height=34, command=selecionar_global).pack(anchor="w")

    # --------------------------------------------------------
    # INDICADORES
    # --------------------------------------------------------
    indicadores = ctk.CTkFrame(corpo, fg_color="transparent")
    indicadores.pack(fill="x", pady=(0, 10))
    indicadores.grid_columnconfigure((0, 1, 2, 3), weight=1)

    cards_valores = {}

    def criar_indicador(coluna, titulo, valor="—"):
        card = ctk.CTkFrame(indicadores, corner_radius=12)
        card.grid(row=0, column=coluna, sticky="ew", padx=4)
        ctk.CTkLabel(card, text=titulo, font=("Segoe UI", 11, "bold")).pack(pady=(9, 0))
        lbl = ctk.CTkLabel(card, text=str(valor), font=("Segoe UI", 23, "bold"))
        lbl.pack(pady=(0, 9))
        cards_valores[titulo] = lbl

    criar_indicador(0, "TOTAL")
    criar_indicador(1, "OK")
    criar_indicador(2, "DIVERGÊNCIAS")
    criar_indicador(3, "REVISAR")

    # --------------------------------------------------------
    # AÇÕES/FILTROS
    # --------------------------------------------------------
    barra = ctk.CTkFrame(corpo, fg_color="transparent")
    barra.pack(fill="x", pady=(0, 8))

    tabela = TabelaExames(corpo, callback=lambda dados: _abrir_auditoria(app, dados))

    def atualizar_resumo(resultado):
        total = len(resultado)
        ok = sum(1 for item in resultado if item.get("status") in ("OK", "✅ OK"))
        revisar = sum(1 for item in resultado if item.get("status") in ("ATENCAO", "CONFIGURAR"))
        erros = sum(1 for item in resultado if item.get("status") == "ERRO")
        cards_valores["TOTAL"].configure(text=str(total))
        cards_valores["OK"].configure(text=str(ok))
        cards_valores["DIVERGÊNCIAS"].configure(text=str(erros))
        cards_valores["REVISAR"].configure(text=str(revisar))

    def executar_conferencia(silencioso=False):
        nonlocal ultimo_resultado, registros_global, bruto_global

        if not caminho_siresp:
            if not silencioso:
                messagebox.showwarning("Arquivo não selecionado", "Selecione o PDF do SIRESP.")
            return
        if not caminho_global:
            if not silencioso:
                messagebox.showwarning("Arquivo não selecionado", "Selecione o Demonstrativo Global.")
            return

        btn_conferir.configure(state="disabled", text="Conferindo...")
        lbl_status.configure(text="Lendo os PDFs e aplicando as regras...")
        app.update_idletasks()

        try:
            siresp = ler_siresp_exames(caminho_siresp)
            faturamento, registros_global, bruto_global = ler_faturamento_exames_detalhado(caminho_global)
            mapeamentos = carregar_mapeamentos()
            for grupo_temp, lista_temp in mapeamentos_temporarios.items():
                mapeamentos[grupo_temp] = list(lista_temp)

            resultado = comparar_exames(
                siresp,
                faturamento,
                mapeamentos_manuais=mapeamentos,
                faturamento_bruto=bruto_global,
            )
            resultado = _ajustar_resultado_compartilhado(resultado)

            ultimo_resultado = resultado
            tabela.preencher(resultado)
            atualizar_resumo(resultado)

            pendentes = sum(1 for item in resultado if item.get("status") == "CONFIGURAR")
            if pendentes:
                lbl_status.configure(text="Conferência concluída · há exame aguardando configuração de regra.")
            else:
                lbl_status.configure(text="Conferência concluída. Clique em uma linha para abrir a auditoria.")

        except Exception as erro:
            lbl_status.configure(text="Falha durante a conferência.")
            messagebox.showerror("Erro na conferência", f"Ocorreu um erro durante a conferência:\n\n{erro}")
        finally:
            btn_conferir.configure(state="normal", text="▶ CONFERIR EXAMES")

    def configurar_regra():
        nonlocal registros_global, bruto_global, mapeamentos_temporarios
        if not caminho_global:
            messagebox.showwarning("Global não selecionado", "Selecione primeiro o Demonstrativo Global.")
            return
        try:
            if not registros_global:
                _, registros_global, bruto_global = ler_faturamento_exames_detalhado(caminho_global)

            dados_siresp = ler_siresp_exames(caminho_siresp) if caminho_siresp else {}
            nomes = sorted({
                *(item.get("exame", "") for item in ultimo_resultado if item.get("exame")),
                *dados_siresp.keys(),
            })
            if not nomes:
                messagebox.showwarning(
                    "Sem exames",
                    "Selecione o SIRESP ou faça uma conferência para escolher qual exame será configurado.",
                )
                return

            seletor = ctk.CTkToplevel(app)
            seletor.title("Configurar regra de exame")
            seletor.geometry("620x250")
            seletor.resizable(False, False)
            seletor.grab_set()

            ctk.CTkLabel(
                seletor,
                text="⚙ Configurar regra",
                font=("Segoe UI", 20, "bold"),
                anchor="w",
            ).pack(fill="x", padx=22, pady=(20, 4))
            ctk.CTkLabel(
                seletor,
                text="Escolha qualquer exame. A mesma regra manual da Mastologia agora funciona para todos.",
                anchor="w",
                wraplength=560,
            ).pack(fill="x", padx=22, pady=(0, 14))

            combo = ctk.CTkOptionMenu(seletor, values=nomes, width=570, height=38)
            combo.pack(padx=22, pady=(0, 16))
            if GRUPO_MASTOLOGIA_MAIOR in nomes:
                combo.set(GRUPO_MASTOLOGIA_MAIOR)

            botoes = ctk.CTkFrame(seletor, fg_color="transparent")
            botoes.pack(fill="x", padx=22)

            def abrir_escolhido():
                grupo = combo.get().strip().upper()
                if not grupo:
                    return
                seletor.destroy()

                item_siresp = dados_siresp.get(grupo, {})
                total_siresp = None
                if item_siresp:
                    total_siresp = sum(
                        int(item_siresp.get(chave, 0) or 0)
                        for chave in ("externo", "interno", "direto")
                    )
                else:
                    item_resultado = next((x for x in ultimo_resultado if x.get("exame") == grupo), None)
                    if item_resultado:
                        total_siresp = int(item_resultado.get("siresp", 0) or 0)

                temporario_atual = mapeamentos_temporarios.get(grupo)

                def ao_aplicar(lista, salvar_regra):
                    if salvar_regra:
                        mapeamentos_temporarios.pop(grupo, None)
                    else:
                        mapeamentos_temporarios[grupo] = list(lista)
                    if caminho_siresp:
                        executar_conferencia(silencioso=True)

                _abrir_configuracao_exame(
                    app,
                    grupo,
                    registros_global,
                    total_siresp=total_siresp,
                    mapeamento_temporario=temporario_atual,
                    ao_aplicar=ao_aplicar,
                )

            ctk.CTkButton(
                botoes,
                text="Cancelar",
                width=110,
                fg_color="transparent",
                border_width=1,
                command=seletor.destroy,
            ).pack(side="right", padx=(8, 0))
            ctk.CTkButton(
                botoes,
                text="Configurar exame",
                width=160,
                command=abrir_escolhido,
            ).pack(side="right")

        except Exception as erro:
            messagebox.showerror("Erro", f"Não foi possível abrir a configuração de regras:\n\n{erro}")

    def exportar_csv():
        if not ultimo_resultado:
            messagebox.showwarning("Sem resultado", "Faça uma conferência antes de exportar.")
            return
        caminho = filedialog.asksaveasfilename(
            title="Exportar conferência",
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv")],
            initialfile="YUPI_conferencia_exames.csv",
        )
        if not caminho:
            return
        try:
            with open(caminho, "w", newline="", encoding="utf-8-sig") as arquivo:
                writer = csv.writer(arquivo, delimiter=";")
                writer.writerow(["Exame", "Externo", "Interno", "Direto", "SIRESP", "Global", "Diferença", "Status", "Observação"])
                for item in ultimo_resultado:
                    writer.writerow([
                        item.get("exame", ""), item.get("externo", 0), item.get("interno", 0),
                        item.get("direto", 0), item.get("siresp", 0), item.get("global", 0),
                        item.get("diferenca", 0), item.get("status", ""), item.get("observacao", ""),
                    ])
            messagebox.showinfo("Exportação concluída", "Arquivo CSV salvo com sucesso.")
        except OSError as erro:
            messagebox.showerror("Erro ao exportar", str(erro))

    btn_conferir = ctk.CTkButton(
        barra, text="▶ CONFERIR EXAMES", width=190, height=40,
        font=("Segoe UI", 13, "bold"), command=executar_conferencia,
    )
    btn_conferir.pack(side="left")

    btn_configurar = ctk.CTkButton(
        barra, text="⚙ Configurar Regra", width=165, height=40,
        command=configurar_regra, state="disabled",
    )
    btn_configurar.pack(side="left", padx=(8, 0))

    ctk.CTkButton(barra, text="Exportar CSV", width=110, height=40, command=exportar_csv).pack(side="left", padx=(8, 0))
    ctk.CTkButton(barra, text="Todos", width=72, height=40, command=tabela.mostrar_todos).pack(side="left", padx=(12, 0))
    ctk.CTkButton(barra, text="✅ OK", width=72, height=40, command=tabela.mostrar_ok).pack(side="left", padx=(5, 0))
    ctk.CTkButton(barra, text="🔴 Erros", width=90, height=40, command=tabela.mostrar_divergencias).pack(side="left", padx=(5, 0))

    campo_pesquisa = ctk.CTkEntry(barra, width=210, height=40, placeholder_text="Pesquisar exame...")
    campo_pesquisa.pack(side="right")
    campo_pesquisa.bind("<KeyRelease>", lambda event: tabela.filtrar(campo_pesquisa.get()))

    # --------------------------------------------------------
    # TABELA + STATUS
    # --------------------------------------------------------
    tabela.pack(fill="both", expand=True)

    lbl_status = ctk.CTkLabel(
        corpo,
        text="Selecione os dois PDFs para iniciar.",
        anchor="w",
        font=("Segoe UI", 11),
    )
    lbl_status.pack(fill="x", pady=(7, 0))
