import customtkinter as ctk


class LinhaExames(ctk.CTkFrame):
    """Linha da tabela de exames com colunas alinhadas ao cabeçalho."""

    COLUNAS = {
        "exame": 360,
        "externo": 82,
        "interno": 82,
        "siresp": 82,
        "global": 82,
        "diferenca": 76,
        "status": 132,
    }

    def __init__(self, master, dados, callback=None):
        super().__init__(master, height=44, corner_radius=7)
        self.dados = dados
        self.callback = callback
        self.grid_propagate(False)
        self._configurar_grade()
        self._criar_conteudo()
        self._configurar_clique()

    def _configurar_grade(self):
        self.grid_columnconfigure(0, weight=0, minsize=self.COLUNAS["exame"])
        for col, chave in enumerate(
            ("externo", "interno", "siresp", "global", "diferenca", "status"), start=1
        ):
            self.grid_columnconfigure(col, weight=0, minsize=self.COLUNAS[chave])
        self.grid_rowconfigure(0, weight=1)

    def _criar_label(self, coluna, texto, anchor="center", bold=False, padx=4):
        label = ctk.CTkLabel(
            self,
            text=texto,
            anchor=anchor,
            font=("Segoe UI", 12, "bold" if bold else "normal"),
        )
        label.grid(row=0, column=coluna, sticky="nsew", padx=padx, pady=2)
        return label

    def _criar_conteudo(self):
        exame = self.dados.get("exame", "")
        siresp = self.dados.get("siresp", 0)
        global_ = self.dados.get("global", 0)
        diferenca = self.dados.get("diferenca", 0)
        status = self.dados.get("status", "ERRO")

        if status in ("OK", "✅ OK"):
            texto_status = "✓ OK"
        elif status == "CONFIGURAR":
            texto_status = "⚙ CONFIGURAR"
        elif status == "ATENCAO":
            texto_status = "⚠ REVISAR"
        else:
            texto_status = "● ERRO"

        texto_diferenca = f"+{diferenca}" if diferenca > 0 else str(diferenca)

        self.lbl_exame = self._criar_label(0, exame, anchor="w", bold=True, padx=10)
        self.lbl_externo = self._criar_label(1, str(self.dados.get("externo", 0)))
        self.lbl_interno = self._criar_label(2, str(self.dados.get("interno", 0)))
        self.lbl_siresp = self._criar_label(3, str(siresp))
        self.lbl_global = self._criar_label(4, str(global_))
        self.lbl_diferenca = self._criar_label(5, texto_diferenca, bold=True)
        self.lbl_status = self._criar_label(6, texto_status, anchor="w", bold=True, padx=8)

    def _configurar_clique(self):
        for widget in (
            self,
            self.lbl_exame,
            self.lbl_externo,
            self.lbl_interno,
            self.lbl_siresp,
            self.lbl_global,
            self.lbl_diferenca,
            self.lbl_status,
        ):
            widget.bind("<Button-1>", self.clicar)

    def clicar(self, evento=None):
        if self.callback:
            self.callback(self.dados)
