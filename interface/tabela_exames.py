import customtkinter as ctk
from interface.l_exames import LinhaExames


class TabelaExames(ctk.CTkFrame):
    """Tabela com grade fixa para impedir desalinhamento entre colunas."""

    def __init__(self, master, callback=None):
        super().__init__(master, fg_color="transparent")
        self.callback = callback
        self.todos_dados = []
        self.linhas = []
        self._criar_cabecalho()
        self._criar_scroll()

    def _configurar_grade_colunas(self, frame):
        frame.grid_columnconfigure(0, weight=0, minsize=LinhaExames.COLUNAS["exame"])
        for col, chave in enumerate(
            ("externo", "interno", "siresp", "global", "diferenca", "status"), start=1
        ):
            frame.grid_columnconfigure(col, weight=0, minsize=LinhaExames.COLUNAS[chave])

    def _criar_cabecalho(self):
        self.cabecalho = ctk.CTkFrame(self, height=40, corner_radius=8)
        self.cabecalho.pack(fill="x", pady=(0, 6))
        self.cabecalho.grid_propagate(False)
        self._configurar_grade_colunas(self.cabecalho)

        colunas = ["Exame", "Externo", "Interno", "SIRESP", "Global", "Dif.", "Status"]
        for idx, texto in enumerate(colunas):
            ctk.CTkLabel(
                self.cabecalho,
                text=texto,
                anchor="w" if idx in (0, 6) else "center",
                font=("Segoe UI", 12, "bold"),
            ).grid(
                row=0,
                column=idx,
                sticky="nsew",
                padx=10 if idx == 0 else 4,
                pady=4,
            )

    def _criar_scroll(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

    def limpar(self):
        for linha in self.linhas:
            linha.destroy()
        self.linhas.clear()

    def adicionar(self, dados):
        linha = LinhaExames(self.scroll, dados, callback=self._clicou_linha)
        linha.pack(fill="x", pady=1)
        self.linhas.append(linha)

    def _clicou_linha(self, dados):
        if self.callback:
            self.callback(dados)

    def preencher(self, dados):
        self.todos_dados = list(dados)
        self.limpar()
        for item in self.todos_dados:
            self.adicionar(item)

    def filtrar(self, texto):
        texto = texto.upper().strip()
        self.limpar()
        for item in self.todos_dados:
            if texto in item.get("exame", "").upper():
                self.adicionar(item)

    def mostrar_ok(self):
        self.limpar()
        for item in self.todos_dados:
            if item.get("status") in ("OK", "✅ OK"):
                self.adicionar(item)

    def mostrar_divergencias(self):
        self.limpar()
        for item in self.todos_dados:
            if item.get("status") not in ("OK", "✅ OK"):
                self.adicionar(item)

    def mostrar_todos(self):
        self.limpar()
        for item in self.todos_dados:
            self.adicionar(item)

    def quantidade(self):
        return len(self.linhas)

    def dados(self):
        return self.todos_dados
