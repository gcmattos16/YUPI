import customtkinter as ctk


class AuditoriaExames(ctk.CTkToplevel):

    def __init__(self, master, dados):

        super().__init__(master)

        self.dados = dados

        exame = dados.get(
            "exame",
            "Auditoria"
        )

        self.title(
            f"Auditoria - {exame}"
        )

        self.geometry(
            "900x650"
        )

        self.minsize(
            800,
            550
        )

        self._criar_interface()

    # ==========================================
    # INTERFACE
    # ==========================================

    def _criar_interface(self):

        exame = self.dados.get(
            "exame",
            ""
        )

        externo = self.dados.get(
            "externo",
            0
        )

        interno = self.dados.get(
            "interno",
            0
        )

        siresp = self.dados.get(
            "siresp",
            0
        )

        global_ = self.dados.get(
            "global",
            0
        )

        diferenca = self.dados.get(
            "diferenca",
            0
        )

        status = self.dados.get(
            "status",
            "ERRO"
        )

        # ======================================
        # TÍTULO
        # ======================================

        titulo = ctk.CTkLabel(

            self,

            text=f"🔎 Auditoria — {exame}",

            font=(
                "Segoe UI",
                22,
                "bold"
            )

        )

        titulo.pack(

            fill="x",

            padx=25,

            pady=(20, 10)

        )

        # ======================================
        # RESUMO
        # ======================================

        resumo = ctk.CTkFrame(
            self,
            corner_radius=12
        )

        resumo.pack(

            fill="x",

            padx=25,

            pady=10

        )

        self._criar_resumo(
            resumo,
            "Externo",
            externo
        )

        self._criar_resumo(
            resumo,
            "Interno",
            interno
        )

        self._criar_resumo(
            resumo,
            "SIRESP",
            siresp
        )

        self._criar_resumo(
            resumo,
            "Global",
            global_
        )

        self._criar_resumo(
            resumo,
            "Diferença",
            diferenca
        )

        self._criar_resumo(
            resumo,
            "Status",
            "✅ OK"
            if status in (
                "OK",
                "✅ OK"
            )
            else "🔴 ERRO"
        )

        # ======================================
        # ÁREA DE DETALHES
        # ======================================

        titulo_detalhes = ctk.CTkLabel(

            self,

            text="Detalhamento dos procedimentos",

            font=(
                "Segoe UI",
                17,
                "bold"
            ),

            anchor="w"

        )

        titulo_detalhes.pack(

            fill="x",

            padx=25,

            pady=(15, 5)

        )

        scroll = ctk.CTkScrollableFrame(

            self,

            corner_radius=10

        )

        scroll.pack(

            fill="both",

            expand=True,

            padx=25,

            pady=(5, 20)

        )

        detalhes_siresp = self.dados.get(

            "detalhes_siresp",

            []

        )

        detalhes_global = self.dados.get(

            "detalhes_global",

            []

        )

        # ======================================
        # SIRESP
        # ======================================

        self._criar_titulo_secao(

            scroll,

            "📄 SIRESP"

        )

        if detalhes_siresp:

            for item in detalhes_siresp:

                self._criar_detalhe_siresp(

                    scroll,

                    item

                )

        else:

            ctk.CTkLabel(

                scroll,

                text="Nenhum detalhe encontrado no SIRESP."

            ).pack(

                anchor="w",

                padx=10,

                pady=5

            )

        # ======================================
        # GLOBAL
        # ======================================

        self._criar_titulo_secao(

            scroll,

            "💰 GLOBAL / FATURAMENTO"

        )

        if detalhes_global:

            for item in detalhes_global:

                self._criar_detalhe_global(

                    scroll,

                    item

                )

        else:

            ctk.CTkLabel(

                scroll,

                text="Nenhum procedimento encontrado no Global."

            ).pack(

                anchor="w",

                padx=10,

                pady=5

            )

        # ======================================
        # BOTÃO FECHAR
        # ======================================

        ctk.CTkButton(

            self,

            text="Fechar",

            width=140,

            command=self.destroy

        ).pack(

            pady=(0, 20)

        )

        self.grab_set()

    # ==========================================
    # RESUMO
    # ==========================================

    def _criar_resumo(
        self,
        master,
        titulo,
        valor
    ):

        frame = ctk.CTkFrame(

            master,

            fg_color="transparent"

        )

        frame.pack(

            side="left",

            expand=True,

            padx=5,

            pady=12

        )

        ctk.CTkLabel(

            frame,

            text=titulo,

            font=(
                "Segoe UI",
                11
            )

        ).pack()

        ctk.CTkLabel(

            frame,

            text=str(valor),

            font=(
                "Segoe UI",
                16,
                "bold"
            )

        ).pack()

    # ==========================================
    # TÍTULO DA SEÇÃO
    # ==========================================

    def _criar_titulo_secao(
        self,
        master,
        texto
    ):

        frame = ctk.CTkFrame(

            master,

            height=38,

            corner_radius=8

        )

        frame.pack(

            fill="x",

            pady=(12, 5)

        )

        ctk.CTkLabel(

            frame,

            text=texto,

            font=(
                "Segoe UI",
                14,
                "bold"
            ),

            anchor="w"

        ).pack(

            fill="x",

            padx=12,

            pady=7

        )

    # ==========================================
    # DETALHE SIRESP
    # ==========================================

    def _criar_detalhe_siresp(
        self,
        master,
        item
    ):

        exame = item.get(
            "exame",
            ""
        )

        externo = item.get(
            "externo",
            0
        )

        interno = item.get(
            "interno",
            0
        )

        direto = item.get(
            "direto",
            0
        )

        quantidade = item.get(
            "quantidade",
            0
        )

        frame = ctk.CTkFrame(

            master,

            corner_radius=8

        )

        frame.pack(

            fill="x",

            pady=3

        )

        ctk.CTkLabel(

            frame,

            text=exame,

            width=350,

            anchor="w",

            font=(
                "Segoe UI",
                13,
                "bold"
            )

        ).pack(

            side="left",

            padx=10,

            pady=10

        )

        self._mini_valor(

            frame,

            "Externo",

            externo

        )

        self._mini_valor(

            frame,

            "Interno",

            interno

        )

        self._mini_valor(

            frame,

            "Direto",

            direto

        )

        self._mini_valor(

            frame,

            "Total",

            quantidade

        )

    # ==========================================
    # DETALHE GLOBAL
    # ==========================================

    def _criar_detalhe_global(
        self,
        master,
        item
    ):

        exame = item.get(
            "exame",
            ""
        )

        quantidade = item.get(
            "quantidade",
            0
        )

        frame = ctk.CTkFrame(

            master,

            corner_radius=8

        )

        frame.pack(

            fill="x",

            pady=3

        )

        ctk.CTkLabel(

            frame,

            text=exame,

            anchor="w",

            font=(
                "Segoe UI",
                13,
                "bold"
            )

        ).pack(

            side="left",

            fill="x",

            expand=True,

            padx=10,

            pady=10

        )

        ctk.CTkLabel(

            frame,

            text=str(quantidade),

            width=80,

            font=(
                "Segoe UI",
                13,
                "bold"
            )

        ).pack(

            side="right",

            padx=10

        )

    # ==========================================
    # MINI VALOR
    # ==========================================

    def _mini_valor(
        self,
        master,
        titulo,
        valor
    ):

        frame = ctk.CTkFrame(

            master,

            fg_color="transparent"

        )

        frame.pack(

            side="left",

            padx=5

        )

        ctk.CTkLabel(

            frame,

            text=titulo,

            font=(
                "Segoe UI",
                10
            )

        ).pack()

        ctk.CTkLabel(

            frame,

            text=str(valor),

            font=(
                "Segoe UI",
                13,
                "bold"
            )

        ).pack()