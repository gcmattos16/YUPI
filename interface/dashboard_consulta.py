import customtkinter as ctk


class DashboardConsulta(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master, fg_color="transparent")
        self.pack(fill="x", pady=(0, 10))
        self._criar_cards()
        self.limpar()

    def _criar_cards(self):
        self.card_total = self._criar_card("📋", "TOTAL", "0")
        self.card_ok = self._criar_card("✅", "OK", "0")
        self.card_erros = self._criar_card("❌", "DIVERGÊNCIAS", "0")
        self.card_corrigidos = self._criar_card("🔧", "CORRIGIDOS", "0")
        self.card_indice = self._criar_card("📊", "CONFORMIDADE", "0%")

    def _criar_card(self, icone, titulo, valor):
        card = ctk.CTkFrame(self, corner_radius=10)
        card.pack(side="left", fill="x", expand=True, padx=4)
        ctk.CTkLabel(card, text=f"{icone} {titulo}", font=("Segoe UI", 11, "bold")).pack(pady=(7, 0))
        lbl = ctk.CTkLabel(card, text=valor, font=("Segoe UI", 20, "bold"))
        lbl.pack(pady=(0, 7))
        return lbl

    def atualizar(self, dados):
        total = len(dados)
        ok = sum(1 for item in dados if item.get("diferenca", 0) == 0)
        erros = sum(1 for item in dados if item.get("diferenca", 0) != 0)
        corrigidos = sum(1 for item in dados if item.get("corrigido", False))
        indice = (ok / total * 100) if total else 0
        self.card_total.configure(text=str(total))
        self.card_ok.configure(text=str(ok))
        self.card_erros.configure(text=str(erros))
        self.card_corrigidos.configure(text=str(corrigidos))
        self.card_indice.configure(text=f"{indice:.1f}%")

    def limpar(self):
        self.card_total.configure(text="0")
        self.card_ok.configure(text="0")
        self.card_erros.configure(text="0")
        self.card_corrigidos.configure(text="0")
        self.card_indice.configure(text="0%")
