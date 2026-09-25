import customtkinter as ctk


class CardDashboard(ctk.CTkFrame):

    def __init__(self, master, titulo, icone):

        super().__init__(
            master,
            corner_radius=12,
            height=90
        )

        self.pack_propagate(False)

        topo = ctk.CTkFrame(
            self,
            fg_color="transparent"
        )

        topo.pack(
            fill="x",
            padx=12,
            pady=(10, 0)
        )

        ctk.CTkLabel(
            topo,
            text=f"{icone} {titulo}",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w")

        self.valor = ctk.CTkLabel(
            self,
            text="0",
            font=("Segoe UI", 28, "bold")
        )

        self.valor.pack(
            pady=(5, 10)
        )

    def atualizar(self, valor):

        self.valor.configure(
            text=str(valor)
        )


def criar_dashboard(master):

    frame = ctk.CTkFrame(
        master,
        fg_color="transparent"
    )

    frame.pack(
        fill="x",
        pady=(0, 12)
    )

    card1 = CardDashboard(
        frame,
        "Especialidades",
        "🏥"
    )

    card2 = CardDashboard(
        frame,
        "Divergências",
        "❌"
    )

    card3 = CardDashboard(
        frame,
        "OK",
        "✅"
    )

    card4 = CardDashboard(
        frame,
        "Conformidade",
        "📈"
    )

    card1.pack(
        side="left",
        expand=True,
        fill="x",
        padx=5
    )

    card2.pack(
        side="left",
        expand=True,
        fill="x",
        padx=5
    )

    card3.pack(
        side="left",
        expand=True,
        fill="x",
        padx=5
    )

    card4.pack(
        side="left",
        expand=True,
        fill="x",
        padx=5
    )

    return (
        card1,
        card2,
        card3,
        card4
    )


def atualizar_dashboard(cards, dados):

    total = len(dados)

    divergencias = sum(
        1
        for item in dados
        if item["diferenca"] != 0
    )

    ok = total - divergencias

    conformidade = 0

    if total > 0:

        conformidade = (
            ok / total
        ) * 100

    cards[0].atualizar(total)
    cards[1].atualizar(divergencias)
    cards[2].atualizar(ok)
    cards[3].atualizar(f"{conformidade:.1f}%")