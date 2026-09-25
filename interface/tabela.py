import customtkinter as ctk

from interface.linha_tabela import LinhaTabela


class TabelaConsultas(ctk.CTkFrame):

    def __init__(self, master, callback=None):

        super().__init__(
            master,
            fg_color="transparent"
        )

        self.callback = callback

        self.todos_dados = []

        self.linhas = []

        self.pack(
            fill="both",
            expand=True
        )

        self._criar_cabecalho()

        self._criar_scroll()

    # ==========================================
    # CABEÇALHO
    # ==========================================

    def _criar_cabecalho(self):

        cabecalho = ctk.CTkFrame(
            self,
            height=38,
            corner_radius=8
        )

        cabecalho.pack(
            fill="x",
            pady=(0,5)
        )

        colunas = [

            ("Especialidade",320),

            ("SIRESP",80),

            ("Analítico",80),

            ("Dif.",70),

            ("Status",120)

        ]

        for texto, largura in colunas:

            lbl = ctk.CTkLabel(

                cabecalho,

                text=texto,

                width=largura,

                font=(
                    "Segoe UI",
                    14,
                    "bold"
                )

            )

            lbl.pack(
                side="left",
                padx=2,
                pady=5
            )
                # ==========================================
    # ÁREA DE SCROLL
    # ==========================================

    def _criar_scroll(self):

        self.scroll = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent"
        )

        self.scroll.pack(
            fill="both",
            expand=True
        )

    # ==========================================
    # LIMPAR TABELA
    # ==========================================

    def limpar(self):

        for linha in self.linhas:

            linha.destroy()

        self.linhas.clear()

    # ==========================================
    # ADICIONAR UMA LINHA
    # ==========================================

    def adicionar(self, dados):

        linha = LinhaTabela(
            self.scroll,
            dados,
            callback=self._clicou_linha
        )

        linha.pack(
            fill="x",
            pady=2
        )

        self.linhas.append(linha)

    # ==========================================
    # CLIQUE NA LINHA
    # ==========================================

    def _clicou_linha(self, dados):

        if self.callback:

            self.callback(
                dados["especialidade"]
            )
                # ==========================================
    # PREENCHER TABELA
    # ==========================================

    def preencher(self, dados):

        self.todos_dados = dados

        self.limpar()

        for item in dados:

            self.adicionar(item)

    # ==========================================
    # FILTRAR POR NOME
    # ==========================================

    def filtrar(self, texto):

        texto = texto.upper().strip()

        self.limpar()

        for item in self.todos_dados:

            if texto in item["especialidade"].upper():

                self.adicionar(item)

    # ==========================================
    # MOSTRAR SOMENTE OK
    # ==========================================

    def mostrar_ok(self):

        self.limpar()

        for item in self.todos_dados:

            if item["status"] == "✅ OK":

                self.adicionar(item)

    # ==========================================
    # MOSTRAR SOMENTE DIVERGÊNCIAS
    # ==========================================

    def mostrar_divergencias(self):

        self.limpar()

        for item in self.todos_dados:

            if item["status"] != "✅ OK":

                self.adicionar(item)

    # ==========================================
    # MOSTRAR TODOS
    # ==========================================

    def mostrar_todos(self):

        self.preencher(
            self.todos_dados
        )
            # ==========================================
    # QUANTIDADE DE LINHAS
    # ==========================================

    def quantidade(self):

        return len(self.linhas)

    # ==========================================
    # RETORNAR TODOS OS DADOS
    # ==========================================

    def dados(self):

        return self.todos_dados

    # ==========================================
    # ATUALIZAR UMA LINHA
    # ==========================================

    def atualizar(self, especialidade, novos_dados):

        for indice, item in enumerate(self.todos_dados):

            if item["especialidade"] == especialidade:

                self.todos_dados[indice] = novos_dados
                break

        self.preencher(self.todos_dados)

    # ==========================================
    # REMOVER UMA LINHA
    # ==========================================

    def remover(self, especialidade):

        self.todos_dados = [

            item

            for item in self.todos_dados

            if item["especialidade"] != especialidade

        ]

        self.preencher(self.todos_dados)

    # ==========================================
    # SELECIONAR UMA ESPECIALIDADE
    # ==========================================

    def selecionar(self, especialidade):

        for linha in self.linhas:

            if linha.dados["especialidade"] == especialidade:

                linha.clicar(None)

                break