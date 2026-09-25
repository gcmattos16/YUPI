import customtkinter as ctk


class LinhaTabela(ctk.CTkFrame):

    def __init__(
        self,
        master,
        dados,
        callback=None
    ):

        super().__init__(
            master,
            corner_radius=8,
            fg_color="transparent",
            height=36
        )

        self.pack_propagate(False)

        self.dados = dados
        self.callback = callback

        if dados["status"] == "✅ OK":
            cor = "#DFF6DD"

        else:

            diferenca = abs(
                dados["diferenca"]
            )

            if diferenca >= 10:
                cor = "#FFD6D6"

            elif diferenca >= 5:
                cor = "#FFE8B5"

            else:
                cor = "#FFF8CC"

        valores = [

            ("especialidade", 320),

            ("siresp", 80),

            ("analitico", 80),

            ("diferenca", 70),

            ("status", 120)

        ]

        for campo, largura in valores:

            lbl = ctk.CTkLabel(

                self,

                text=str(dados[campo]),

                width=largura,

                height=32,

                fg_color=cor,

                corner_radius=6

            )

            lbl.pack(
                side="left",
                padx=2,
                pady=2
            )

            lbl.bind(
                "<Button-1>",
                self.clicar
            )

        self.bind(
            "<Button-1>",
            self.clicar
        )

    def clicar(self, event):

        if self.callback:

            self.callback(
                self.dados
            )