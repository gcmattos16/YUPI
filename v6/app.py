from __future__ import annotations
import os, sys, csv, json, webbrowser
from pathlib import Path
from tkinter import filedialog, messagebox, ttk, simpledialog
import customtkinter as ctk

from exames.leitor_siresp_exames import ler_siresp_exames
from exames.leitor_faturamento_exames import ler_faturamento_exames, ler_faturamento_exames_detalhado
from exames.comparador_exames import comparar_exames
from exames.configuracao_mapeamento import carregar_mapeamentos, salvar_mapeamento, remover_mapeamento
from exames.conferencia_exames import _abrir_configuracao_exame
from .storage import load_config, save_config, append_history, load_history, BASE
from .sadt_reader import read_sadt, slice_period
from .report_meta import pdf_period
from .scope_engine import validate_scope
from .presence import read_analitico_people, read_siresp_agenda, compare_presence
from .monthly import detect_files, analyze_exam_month

ctk.set_appearance_mode('dark')
ctk.set_default_color_theme('blue')

BG='#07111F'; PANEL='#0D1A2B'; PANEL2='#101F33'; PURPLE='#7047FF'; PURPLE_DARK='#5A35E8'; TEXT='#F5F7FF'; MUTED='#91A0B7'; BORDER='#20314A'; GREEN='#35D391'; YELLOW='#FFB547'; RED='#FF5364'; BLUE='#3B82F6'; CYAN='#35D6E7'


def _resource(name):
    base=getattr(sys,'_MEIPASS',Path(__file__).resolve().parents[1])
    return os.path.join(str(base),name)

def _norm_exam(n):
    n=str(n or '').upper().strip()
    aliases={'NASO':'NASOFIBROSCOPIA','RAIO X':'RX','RAIO-X':'RX','BIÓPSIA PRÓSTATA':'BIOPSIA DE PROSTATA','PFP':'PROVA DE FUNCAO PULMONAR','PROVA DE FUNÇÃO':'PROVA DE FUNCAO PULMONAR','PROVA DE FUNCAO':'PROVA DE FUNCAO PULMONAR','COLONO':'COLONOSCOPIA','ECOCARDIO':'ECOCARDIOGRAFIA','ECG':'ELETROCARDIOGRAMA','ELETROENCEFALO':'ELETROENCEFALOGRAMA','ELETRONEURO':'ELETRONEUROMIOGRAFIA'}
    return aliases.get(n,n)

def _tree(parent, columns, widths=None, height=14):
    frame=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER)
    style=ttk.Style()
    style.theme_use('clam')
    style.configure('Yupi.Treeview', background=PANEL, fieldbackground=PANEL, foreground=TEXT, rowheight=34, borderwidth=0, font=('Segoe UI',10))
    style.configure('Yupi.Treeview.Heading', background=PANEL2, foreground='#C8D3E5', relief='flat', borderwidth=0, font=('Segoe UI',10,'bold'))
    style.map('Yupi.Treeview', background=[('selected',PURPLE_DARK)], foreground=[('selected','white')])
    tree=ttk.Treeview(frame,columns=[c[0] for c in columns],show='headings',height=height,style='Yupi.Treeview')
    for i,(key,title) in enumerate(columns):
        tree.heading(key,text=title)
        w=(widths or {}).get(key,130)
        anchor='center' if key in {'siresp','sadt','global','diff','qty','total','int','ext','days','active','use'} else 'w'
        tree.column(key,width=w,anchor=anchor)
    tree.tag_configure('ok', foreground=GREEN)
    tree.tag_configure('warn', foreground=YELLOW)
    tree.tag_configure('error', foreground='#FF7B88')
    tree.tag_configure('muted', foreground=MUTED)
    sy=ttk.Scrollbar(frame,orient='vertical',command=tree.yview); tree.configure(yscrollcommand=sy.set)
    tree.pack(side='left',fill='both',expand=True,padx=(12,0),pady=12); sy.pack(side='right',fill='y',padx=(0,8),pady=12)
    return frame,tree

class YupiV6:
    def __init__(self, root):
        self.root=root; self.config=load_config(); self.current_results=[]
        self.root.title('YUPI v6.5.0 • Conferência Inteligente')
        self.root.geometry('1500x900'); self.root.minsize(1200,720)
        try:self.root.iconbitmap(_resource('YUPI.ico'))
        except:pass
        self.root.configure(fg_color=BG)
        self.session={'exames':{'paths':{'siresp':'','global':'','sadt':''},'results':[],'manual':{},'global_records':[],'global_raw':{},'sadt':{},'last_siresp':{}},'sadt':{'path':'','data':{}},'presenca':{'paths':{'agenda':'','analitico':''},'rows':[]}}
        self._build_shell(); self.show_home()

    def _build_shell(self):
        self.top=ctk.CTkFrame(self.root,height=70,corner_radius=0,fg_color=PANEL,border_width=0)
        self.top.pack(fill='x'); self.top.pack_propagate(False)
        brand=ctk.CTkFrame(self.top,fg_color='transparent'); brand.pack(side='left',padx=(24,22),pady=12)
        ctk.CTkLabel(brand,text='YUPI',font=('Segoe UI',27,'bold'),text_color=PURPLE).pack(side='left')
        ctk.CTkLabel(brand,text='v6.5.0',font=('Segoe UI',11,'bold'),text_color='white',fg_color=PURPLE,corner_radius=8).pack(side='left',padx=8,ipadx=5,ipady=2)
        nav=ctk.CTkFrame(self.top,fg_color='transparent'); nav.pack(side='left',fill='y')
        self.nav_buttons={}
        items=[('Início',self.show_home),('Consultas',self.show_consultas),('Exames',self.show_exames),('SADT',self.show_sadt),('Mensal',self.show_monthly),('Presença',self.show_presence),('Resultados',self.show_results),('Configurações',self.show_settings)]
        for label,cmd in items:
            b=ctk.CTkButton(nav,text=label,width=84,height=36,corner_radius=9,fg_color='transparent',hover_color='#182944',text_color=TEXT,font=('Segoe UI',12,'bold'),command=cmd)
            b.pack(side='left',padx=2,pady=17); self.nav_buttons[label]=b
        
        profile=self.config.setdefault('profile', {'name':self.config.get('user','Operador'), 'unit':'Unidade demonstrativa'})
        self.profile_button=ctk.CTkButton(self.top,text=self._profile_button_text(),width=165,height=42,corner_radius=11,fg_color='#16233A',hover_color='#1D3152',text_color=TEXT,font=('Segoe UI',11,'bold'),command=self._edit_profile)
        self.profile_button.pack(side='right',padx=18,pady=13)

        self.content=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0); self.content.pack(fill='both',expand=True)
        self.footer=ctk.CTkFrame(self.root,height=32,corner_radius=0,fg_color=PANEL); self.footer.pack(fill='x'); self.footer.pack_propagate(False)
        ctk.CTkLabel(self.footer,text='YUPI v6.5.0  •  Dados e regras em '+str(BASE),font=('Segoe UI',10),text_color=MUTED).pack(side='left',padx=20,pady=7)


    def _profile_initials(self):
        name=str(self.config.get('profile',{}).get('name') or self.config.get('user','Operador')).strip()
        parts=[p for p in name.split() if p]
        if not parts: return 'YU'
        return (parts[0][0] + (parts[-1][0] if len(parts)>1 else '')).upper()

    def _profile_button_text(self):
        p=self.config.get('profile',{})
        name=str(p.get('name') or self.config.get('user','Operador')).strip() or 'Gabriel'
        unit=str(p.get('unit') or 'Unidade demonstrativa').strip()
        return f"{self._profile_initials()}   {name}\n{unit}"

    def _edit_profile(self):
        p=self.config.setdefault('profile',{})
        name=simpledialog.askstring('Usuário do YUPI','Nome de quem está usando o sistema:',initialvalue=p.get('name') or self.config.get('user','Operador'),parent=self.root)
        if name is None: return
        name=name.strip()
        if not name:
            messagebox.showwarning('YUPI','Informe um nome válido.')
            return
        unit=simpledialog.askstring('Unidade','Unidade / setor exibido no topo:',initialvalue=p.get('unit','Unidade demonstrativa'),parent=self.root)
        if unit is None: unit=p.get('unit','Unidade demonstrativa')
        p['name']=name; p['unit']=unit.strip() or 'Unidade demonstrativa'
        self.config['user']=name.split()[0]
        save_config(self.config)
        if hasattr(self,'profile_button'):
            self.profile_button.configure(text=self._profile_button_text())
        messagebox.showinfo('YUPI','Usuário atualizado.')

    def _clear(self, active=''):
        for w in self.content.winfo_children(): w.destroy()
        for name,b in self.nav_buttons.items(): b.configure(fg_color='#241A4A' if name==active else 'transparent',text_color='#A98DFF' if name==active else TEXT)

    def _header(self,title,subtitle):
        f=ctk.CTkFrame(self.content,fg_color='transparent'); f.pack(fill='x',padx=28,pady=(22,12))
        ctk.CTkLabel(f,text=title,font=('Segoe UI',27,'bold'),text_color=TEXT).pack(anchor='w')
        ctk.CTkLabel(f,text=subtitle,font=('Segoe UI',12),text_color=MUTED).pack(anchor='w',pady=(3,0))
        return f

    def _card(self,parent,title,subtitle=''):
        f=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER)
        ctk.CTkLabel(f,text=title,font=('Segoe UI',16,'bold'),text_color=TEXT).pack(anchor='w',padx=18,pady=(15,2))
        if subtitle: ctk.CTkLabel(f,text=subtitle,font=('Segoe UI',11),text_color=MUTED).pack(anchor='w',padx=18,pady=(0,10))
        return f

    def show_home(self):
        self._clear('Início')
        from datetime import datetime, date
        import calendar as _cal

        wrap=ctk.CTkFrame(self.content,fg_color='transparent')
        wrap.pack(fill='both',expand=True,padx=28,pady=18)
        wrap.grid_columnconfigure(0,weight=3)
        wrap.grid_columnconfigure(1,weight=1)
        wrap.grid_rowconfigure(1,weight=1)

        # Cabeçalho enxuto: deixa o calendário respirar.
        head=ctk.CTkFrame(wrap,fg_color='transparent')
        head.grid(row=0,column=0,columnspan=2,sticky='ew',pady=(0,12))
        ctk.CTkLabel(head,text=f"Olá, {self.config.get('profile',{}).get('name','Gabriel')}! 👋",font=('Segoe UI',30,'bold'),text_color=TEXT).pack(side='left')
        ctk.CTkLabel(head,text='Acompanhe o mês e registre observações sem sair da Home.',font=('Segoe UI',11),text_color=MUTED).pack(side='left',padx=16,pady=(8,0))

        # Calendário principal (70%)
        cal=ctk.CTkFrame(wrap,fg_color=PANEL,corner_radius=18,border_width=1,border_color=BORDER)
        cal.grid(row=1,column=0,sticky='nsew',padx=(0,12))
        cal.grid_columnconfigure(0,weight=1)
        today=datetime.now(); state={'year':today.year,'month':today.month,'selected':today.date()}
        month_names=['Janeiro','Fevereiro','Março','Abril','Maio','Junho','Julho','Agosto','Setembro','Outubro','Novembro','Dezembro']
        week_names=['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']
        messages=self.config.setdefault('calendar_messages',{})

        nav=ctk.CTkFrame(cal,fg_color='transparent'); nav.pack(fill='x',padx=18,pady=(16,8))
        prev=ctk.CTkButton(nav,text='‹',width=36,height=32,fg_color=PANEL2,hover_color='#182944')
        prev.pack(side='left')
        month_label=ctk.CTkLabel(nav,text='',font=('Segoe UI',21,'bold'),text_color=TEXT); month_label.pack(side='left',expand=True)
        nxt=ctk.CTkButton(nav,text='›',width=36,height=32,fg_color=PANEL2,hover_color='#182944'); nxt.pack(side='left')
        ctk.CTkButton(nav,text='Hoje',width=70,height=32,fg_color=PANEL2,text_color='#A98DFF',command=lambda:go_today()).pack(side='left',padx=(8,0))

        grid=ctk.CTkFrame(cal,fg_color='transparent'); grid.pack(fill='both',expand=True,padx=14,pady=(0,14))
        for j,d in enumerate(week_names):
            grid.grid_columnconfigure(j,weight=1)
            ctk.CTkLabel(grid,text=d,font=('Segoe UI',10,'bold'),text_color=MUTED).grid(row=0,column=j,sticky='ew',pady=(0,6))
        day_widgets=[]

        # Painel do dia (30%)
        side=ctk.CTkFrame(wrap,fg_color=PANEL,corner_radius=18,border_width=1,border_color=BORDER)
        side.grid(row=1,column=1,sticky='nsew')
        selected_label=ctk.CTkLabel(side,text='',font=('Segoe UI',18,'bold'),text_color=TEXT); selected_label.pack(anchor='w',padx=18,pady=(18,5))
        ctk.CTkLabel(side,text='Observações do dia',font=('Segoe UI',11,'bold'),text_color='#A98DFF').pack(anchor='w',padx=18,pady=(12,5))
        msg=ctk.CTkTextbox(side,height=180,corner_radius=10,fg_color=PANEL2,border_width=1,border_color=BORDER,font=('Segoe UI',11))
        msg.pack(fill='both',expand=True,padx=18,pady=(0,10))
        actions=ctk.CTkFrame(side,fg_color='transparent'); actions.pack(fill='x',padx=18,pady=(0,18))

        def key(dt): return dt.strftime('%Y-%m-%d')
        def load_msg():
            d=state['selected']; selected_label.configure(text=f'{d.day} de {month_names[d.month-1]} de {d.year}')
            msg.delete('1.0','end'); msg.insert('1.0',messages.get(key(d),''))
        def save_msg():
            txt=msg.get('1.0','end').strip(); k=key(state['selected'])
            if txt: messages[k]=txt
            else: messages.pop(k,None)
            self.config['calendar_messages']=messages; save_config(self.config); render()
        ctk.CTkButton(actions,text='Salvar observação',height=36,fg_color=PURPLE,command=save_msg).pack(side='left',fill='x',expand=True)

        def choose(day):
            if day:
                state['selected']=date(state['year'],state['month'],day); render(); load_msg()
        def render():
            for w in day_widgets: w.destroy()
            day_widgets.clear(); month_label.configure(text=f'{month_names[state["month"]-1]} de {state["year"]}')
            weeks=_cal.Calendar(firstweekday=0).monthdayscalendar(state['year'],state['month'])
            for i,wk in enumerate(weeks,1):
                grid.grid_rowconfigure(i,weight=1)
                for j,d in enumerate(wk):
                    if not d:
                        x=ctk.CTkLabel(grid,text=''); x.grid(row=i,column=j,sticky='nsew',padx=3,pady=3); day_widgets.append(x); continue
                    dt=date(state['year'],state['month'],d); selected=dt==state['selected']; has=key(dt) in messages; is_today=dt==today.date()
                    fg=PURPLE_DARK if selected else ('#172B49' if is_today else PANEL2)
                    text=f'{d}\n●' if has else str(d)
                    b=ctk.CTkButton(grid,text=text,height=58,corner_radius=10,fg_color=fg,hover_color='#243A5D',border_width=1,border_color='#7047FF' if selected else BORDER,font=('Segoe UI',12,'bold'),command=lambda x=d:choose(x))
                    b.grid(row=i,column=j,sticky='nsew',padx=3,pady=3); day_widgets.append(b)
            load_msg()
        def shift(delta):
            m=state['month']+delta; y=state['year']
            if m<1: y-=1; m=12
            if m>12: y+=1; m=1
            state['year']=y; state['month']=m; state['selected']=date(y,m,min(state['selected'].day,_cal.monthrange(y,m)[1])); render()
        def go_today():
            state['year']=today.year; state['month']=today.month; state['selected']=today.date(); render()
        prev.configure(command=lambda:shift(-1)); nxt.configure(command=lambda:shift(1)); render()
    def show_consultas(self):
        self._clear('Consultas'); self._header('Consultas','Mantém a conferência inteligente SIRESP x Analítico da v5.2.2.')
        card=self._card(self.content,'Conferência de Consultas','A versão consolidada continua disponível sem alterar as regras já validadas.'); card.pack(fill='x',padx=28,pady=12)
        ctk.CTkButton(card,text='Abrir conferência de Consultas',height=48,fg_color=PURPLE,hover_color=PURPLE_DARK,command=lambda:self._open_legacy_consultas()).pack(anchor='w',padx=18,pady=(6,18))
        ctk.CTkLabel(card,text='Presença por paciente/código fica no módulo “Presença” para não misturar quantidade com agenda.',text_color=MUTED,font=('Segoe UI',11)).pack(anchor='w',padx=18,pady=(0,18))

    def _open_legacy_consultas(self):
        from interface.conferencia_v4 import abrir_conferencia
        abrir_conferencia(self.root)

    def show_exames(self):
        self._clear('Exames')
        self._header(
            'Exames • Conferência detalhada',
            'SIRESP + Global + SADT opcional. Veja os procedimentos do Global, códigos SIGTAP, quantidades e ajuste a regra sem sair da tela.'
        )

        state=self.session['exames']
        if state.get('results'):
            self.current_results=state['results']

        # ---------------------------- arquivos ----------------------------
        top=ctk.CTkFrame(self.content,fg_color='transparent')
        top.pack(fill='x',padx=28,pady=(0,10))
        labels={}
        for key,label,sub in [
            ('siresp','SIRESP PDF','Quantidade agendada / realizada'),
            ('global','Global PDF','Procedimentos faturados + SIGTAP'),
            ('sadt','SADT Excel (opcional)','Apoio para escopos interno/externo'),
        ]:
            f=ctk.CTkFrame(top,fg_color=PANEL,corner_radius=14,border_width=1,border_color=BORDER)
            f.pack(side='left',fill='x',expand=True,padx=5)
            ctk.CTkLabel(f,text=label,font=('Segoe UI',12,'bold'),text_color=TEXT).pack(anchor='w',padx=14,pady=(12,1))
            ctk.CTkLabel(f,text=sub,font=('Segoe UI',9),text_color=MUTED).pack(anchor='w',padx=14)
            labels[key]=ctk.CTkLabel(f,text='Nenhum arquivo',font=('Segoe UI',10),text_color=MUTED)
            labels[key].pack(anchor='w',padx=14,pady=(8,2))
            if state['paths'].get(key): labels[key].configure(text=Path(state['paths'][key]).name,text_color=TEXT)
            def choose(k=key):
                ft=[('Excel','*.xlsx *.xlsm')] if k=='sadt' else [('PDF','*.pdf')]
                pp=filedialog.askopenfilename(filetypes=ft)
                if pp:
                    state['paths'][k]=pp
                    state['results']=[]; self.current_results=[]
                    labels[k].configure(text=Path(pp).name,text_color=TEXT)
            ctk.CTkButton(f,text='Selecionar',width=100,height=30,fg_color=PURPLE,command=choose).pack(anchor='e',padx=14,pady=(4,12))

        # ---------------------------- toolbar ----------------------------
        bar=ctk.CTkFrame(self.content,fg_color='transparent')
        bar.pack(fill='x',padx=28,pady=5)
        status=ctk.CTkLabel(bar,text='Selecione SIRESP e Global.',font=('Segoe UI',11),text_color=MUTED)
        status.pack(side='left')

        # tabela mais clara, com coluna de regra/origem
        frame,tree=_tree(
            self.content,
            [('exam','Exame'),('scope','Regra'),('siresp','SIRESP'),('sadt','SADT'),('global','Global'),('diff','Dif.'),('status','Status')],
            {'exam':335,'scope':170,'siresp':85,'sadt':85,'global':85,'diff':75,'status':165},18
        )
        frame.pack(fill='both',expand=True,padx=28,pady=(6,22))

        def selected_exam():
            sel=tree.selection()
            return tree.item(sel[0],'values')[0] if sel else None

        def find_result(exam):
            return next((x for x in self.current_results if x.get('exame')==exam),None)

        def build_global_details_for_exam(r):
            # detalhes da regra + códigos/quantidades reais do Global atual
            selected_names=set()
            for d in r.get('detalhes_global',[]) or []:
                n=str(d.get('exame','')).strip().upper()
                if n: selected_names.add(n)
            selected_names.update(carregar_mapeamentos().get(r.get('exame',''),[]))
            rows=[]
            for rec in state['global_records']:
                exact=str(rec.get('nome_exato','')).strip().upper()
                canon=str(rec.get('nome_normalizado','')).strip().upper()
                if exact in selected_names or canon in selected_names:
                    rows.append({
                        'nome': rec.get('nome_original') or exact,
                        'codigo': rec.get('codigo',''),
                        'quantidade': int(rec.get('quantidade',0) or 0),
                    })
            if not rows:
                # fallback para o detalhe calculado pelo comparador
                for d in r.get('detalhes_global',[]) or []:
                    rows.append({'nome':d.get('exame',''), 'codigo':d.get('codigo',''), 'quantidade':d.get('quantidade',0)})
            return rows

        def refresh_from_current():
            for x in tree.get_children(): tree.delete(x)
            for r in self.current_results:
                exam=r['exame']; v=r.get('scope_validation',{}); rule=self.config.get('exams',{}).get(exam,{})
                st=v.get('status',r.get('status','ERRO'))
                if r.get('manual_override') is not None:
                    st='MANUAL'
                icon = ('🟢 OK' if st=='OK' else '🟣 MANUAL' if st=='MANUAL' else '🟡 REQUER SADT' if st=='ESCOPO_PENDENTE' else '🟡 CONFIGURAR' if st=='CONFIGURAR' else '🔴 DIVERGÊNCIA')
                sc=rule.get('scope',{})
                sc_text=f"S:{sc.get('siresp','ambos')} → G:{sc.get('global','total')}"
                if carregar_mapeamentos().get(exam): sc_text += ' • personalizada'
                sd=r.get('sadt')
                sadt_val=(sd or {}).get('total','—')
                s_val=v.get('siresp_scope',r.get('siresp',0))
                g_val=r.get('manual_override', v.get('global',r.get('global',0)))
                try:
                    if rule.get('scope_strategy')=='bridge_sadt' and v.get('sadt_total') is not None:
                        diff=int(v.get('sadt_total',0) or 0)-int(g_val or 0)
                    elif v.get('status')=='ESCOPO_PENDENTE':
                        diff='—'
                    else:
                        diff=int(s_val or 0)-int(g_val or 0)
                except: diff='—'
                tag='ok' if st=='OK' else ('warn' if st in {'ESCOPO_PENDENTE','CONFIGURAR','MANUAL'} else 'error')
                tree.insert('', 'end',values=(exam,sc_text,s_val,sadt_val,g_val,diff,icon),tags=(tag,))

        if self.current_results:
            refresh_from_current()

        def run():
            if not state['paths']['siresp'] or not state['paths']['global']:
                messagebox.showwarning('YUPI','Selecione SIRESP e Global.')
                return
            try:
                sdata=ler_siresp_exames(state['paths']['siresp'])
                g,records,raw=ler_faturamento_exames_detalhado(state['paths']['global'])
                state['global_records']=records
                state['global_raw']=raw
                state['last_siresp']=sdata
                base=comparar_exames(sdata,g,carregar_mapeamentos(),raw)
                sadt=read_sadt(state['paths']['sadt']) if state['paths']['sadt'] else {}
                state['sadt']=sadt
                period_s=pdf_period(state['paths']['siresp']); period_g=pdf_period(state['paths']['global'])
                if period_s[0] and state['paths']['sadt']:
                    sadt=slice_period(sadt,*period_s); state['sadt']=sadt
                if period_s[0] and period_g[0] and period_s!=period_g:
                    messagebox.showwarning('YUPI',f'Períodos diferentes detectados:\nSIRESP: {period_s[0]} a {period_s[1]}\nGlobal: {period_g[0]} a {period_g[1]}')

                out=[]; cfg=self.config.get('exams',{})
                for r in base:
                    exam=_norm_exam(r['exame'])
                    rule=cfg.get(exam,{'active':True,'scope':{'siresp':'ambos','sadt':'ambos','global':'total'},'scope_strategy':'direct','sigtap':[]})
                    if not rule.get('active',True): continue
                    mult=int(r.get('multiplicador',1) or 1); sr={'externo':int(r.get('externo',0) or 0)*mult,'interno':int(r.get('interno',0) or 0)*mult,'total':(int(r.get('externo',0) or 0)+int(r.get('interno',0) or 0)+int(r.get('direto',0) or 0))*mult}
                    sd=sadt.get(exam)
                    global_value=r.get('global',0)
                    if exam in state['manual']:
                        global_value=state['manual'][exam]
                    v=validate_scope(exam,sr,global_value,sd,rule)
                    if exam not in cfg:
                        st=r.get('status','ERRO'); v={'status':st,'explanation':r.get('observacao',''),'siresp_scope':r.get('siresp',0),'global':global_value}
                    item={'exame':exam,**r,'scope_validation':v,'sadt':sd}
                    if exam in state['manual']:
                        item['manual_override']=state['manual'][exam]
                        item['scope_validation']={**v,'status':'MANUAL','global':state['manual'][exam],'explanation':'Quantidade do Global informada manualmente nesta conferência.'}
                    out.append(item)
                self.current_results=out
                state['results']=out
                refresh_from_current()
                append_history('Exames','Concluído',{'itens':len(out),'sadt':bool(sadt)})
                status.configure(text=f'Concluído • {len(out)} exames • clique duas vezes para detalhes',text_color=GREEN)
            except Exception as e:
                messagebox.showerror('YUPI',f'Erro na conferência:\n\n{e}')

        def manual_qty():
            exam=selected_exam()
            if not exam:
                messagebox.showinfo('YUPI','Selecione um exame na tabela.')
                return
            r=find_result(exam)
            atual = int((r or {}).get('manual_override', (r or {}).get('global',0)) or 0)
            q=simpledialog.askinteger('Quantidade manual',f'{exam}\n\nInforme a quantidade correta do Global para ESTA conferência:',initialvalue=atual,minvalue=0)
            if q is None: return
            state['manual'][exam]=q
            if r:
                r['manual_override']=q
                sv=r.setdefault('scope_validation',{})
                sv['status']='MANUAL'; sv['global']=q; sv['explanation']='Quantidade do Global informada manualmente nesta conferência.'
            refresh_from_current()
            status.configure(text=f'{exam}: quantidade manual = {q}',text_color='#A98DFF')

        def edit_procedures():
            exam=selected_exam()
            if not exam:
                messagebox.showinfo('YUPI','Selecione um exame na tabela.')
                return
            if not state['global_records']:
                messagebox.showwarning('YUPI','Confira os arquivos primeiro para carregar os procedimentos do Global.')
                return
            r=find_result(exam)
            total_siresp=None
            if r:
                total_siresp=(r.get('scope_validation') or {}).get('siresp_scope',r.get('siresp',0))
            def applied(lista,salvou):
                # Reprocessa usando a nova seleção, mantendo arquivos atuais.
                run()
            _abrir_configuracao_exame(
                self.root, exam, state['global_records'], total_siresp=total_siresp,
                mapeamento_temporario=carregar_mapeamentos().get(exam,[]), ao_aplicar=applied
            )

        def clear_mapping():
            exam=selected_exam()
            if not exam:
                messagebox.showinfo('YUPI','Selecione um exame na tabela.')
                return
            if not carregar_mapeamentos().get(exam):
                messagebox.showinfo('YUPI','Esse exame não possui procedimentos personalizados salvos.')
                return
            if messagebox.askyesno('Remover regra',f'Remover todos os procedimentos personalizados de {exam}?'):
                remover_mapeamento(exam)
                run()

        def composition(event=None):
            exam=selected_exam()
            if not exam:return
            r=find_result(exam)
            if not r:return
            w=ctk.CTkToplevel(self.root)
            w.title('Auditoria do exame • '+exam); w.geometry('1380x820'); w.minsize(1120,700); w.grab_set(); w.configure(fg_color=BG)
            head=ctk.CTkFrame(w,fg_color='transparent'); head.pack(fill='x',padx=28,pady=(20,8))
            ctk.CTkLabel(head,text='←',font=('Segoe UI',26,'bold'),text_color=MUTED).pack(side='left',padx=(0,12))
            ctk.CTkLabel(head,text=exam.title(),font=('Segoe UI',27,'bold'),text_color=TEXT).pack(side='left')
            st=(r.get('scope_validation') or {}).get('status',r.get('status',''))
            badge='✓ OK' if st=='OK' else '⚠ VERIFICAR' if st in {'ESCOPO_PENDENTE','CONFIGURAR','MANUAL'} else '✕ DIVERGÊNCIA'
            badge_color=GREEN if st=='OK' else YELLOW if st in {'ESCOPO_PENDENTE','CONFIGURAR','MANUAL'} else RED
            ctk.CTkLabel(head,text=badge,font=('Segoe UI',12,'bold'),text_color='white',fg_color=badge_color,corner_radius=9).pack(side='right',ipadx=14,ipady=7)

            sv=r.get('scope_validation',{}); sd=r.get('sadt') or {}
            s_val=sv.get('siresp_scope',r.get('siresp',0)); g_val=r.get('manual_override',sv.get('global',r.get('global',0)))
            if sv.get('sadt_total') is not None and self.config.get('exams',{}).get(exam,{}).get('scope_strategy')=='bridge_sadt':
                diff=int(sv.get('sadt_total',0) or 0)-int(g_val or 0)
            else:
                try: diff=int(s_val or 0)-int(g_val or 0)
                except: diff='—'

            tabs=ctk.CTkTabview(w,fg_color=PANEL,segmented_button_selected_color=PURPLE,segmented_button_selected_hover_color=PURPLE_DARK)
            tabs.pack(fill='both',expand=True,padx=24,pady=(0,18))
            resumo=tabs.add('Resumo'); proc=tabs.add('Procedimentos'); dia=tabs.add('Por dia'); comp=tabs.add('Comparativo'); regras=tabs.add('Regras'); aud=tabs.add('Auditoria')

            # RESUMO
            cards=ctk.CTkFrame(resumo,fg_color='transparent'); cards.pack(fill='x',padx=14,pady=(14,8))
            for title,val,color,sub in [('SIRESP',s_val,BLUE,'Procedimentos realizados'),('SADT',sd.get('total','—'),GREEN,'Procedimentos faturáveis'),('Global',g_val,YELLOW,'Procedimentos no Global'),('Diferença',diff,PURPLE,'Resultado da regra')]:
                c=ctk.CTkFrame(cards,fg_color=PANEL2,corner_radius=14,border_width=1,border_color=BORDER); c.pack(side='left',fill='x',expand=True,padx=5)
                ctk.CTkLabel(c,text=str(val),font=('Segoe UI',29,'bold'),text_color=TEXT).pack(anchor='w',padx=18,pady=(15,0))
                ctk.CTkLabel(c,text=title,font=('Segoe UI',12,'bold'),text_color=color).pack(anchor='w',padx=18)
                ctk.CTkLabel(c,text=sub,font=('Segoe UI',10),text_color=MUTED).pack(anchor='w',padx=18,pady=(2,15))
            body=ctk.CTkFrame(resumo,fg_color='transparent'); body.pack(fill='both',expand=True,padx=14,pady=8); body.grid_columnconfigure(0,weight=3); body.grid_columnconfigure(1,weight=1); body.grid_rowconfigure(0,weight=1)
            left=ctk.CTkFrame(body,fg_color=PANEL2,corner_radius=14,border_width=1,border_color=BORDER); left.grid(row=0,column=0,sticky='nsew',padx=(0,8))
            right=ctk.CTkFrame(body,fg_color=PANEL2,corner_radius=14,border_width=1,border_color=BORDER); right.grid(row=0,column=1,sticky='nsew',padx=(8,0))
            ctk.CTkLabel(left,text=f'Movimento por dia • {exam.title()}',font=('Segoe UI',15,'bold'),text_color=TEXT).pack(anchor='w',padx=16,pady=(14,8))
            fd,td=_tree(left,[('day','Dia'),('sadt','SADT')],{'day':160,'sadt':120},10); fd.pack(fill='both',expand=True,padx=6,pady=(0,8))
            for ds,v in sorted(sd.get('daily',{}).items()): td.insert('', 'end',values=(ds,v.get('total',0)),tags=('ok',))
            if not sd.get('daily'): td.insert('', 'end',values=('Sem SADT diário','—'),tags=('muted',))
            ctk.CTkLabel(right,text='Ações rápidas',font=('Segoe UI',15,'bold'),text_color=TEXT).pack(anchor='w',padx=16,pady=(14,10))
            ctk.CTkButton(right,text='+ Adicionar procedimento',height=42,fg_color=PURPLE,command=edit_procedures).pack(fill='x',padx=14,pady=5)
            ctk.CTkButton(right,text='− Remover procedimento',height=42,fg_color='#812A35',hover_color='#9A3341',command=lambda:tabs.set('Procedimentos')).pack(fill='x',padx=14,pady=5)
            ctk.CTkButton(right,text='✏ Editar quantidade',height=40,fg_color=PANEL,command=manual_qty).pack(fill='x',padx=14,pady=5)
            ctk.CTkButton(right,text='⚙ Editar regra',height=40,fg_color=PANEL,command=self.show_settings).pack(fill='x',padx=14,pady=5)
            ctk.CTkLabel(right,text=(sv.get('explanation','') or 'Comparação conforme regra configurada.'),wraplength=300,justify='left',text_color=MUTED).pack(anchor='w',padx=16,pady=(16,8))

            # PROCEDIMENTOS
            ptop=ctk.CTkFrame(proc,fg_color='transparent'); ptop.pack(fill='x',padx=12,pady=(12,4))
            ctk.CTkButton(ptop,text='+ Adicionar procedimento',fg_color=PURPLE,command=edit_procedures).pack(side='left',padx=4)
            pf,ptree=_tree(proc,[('name','Procedimento do Global'),('code','Código SIGTAP'),('qty','Quantidade')],{'name':650,'code':200,'qty':120},13); pf.pack(fill='both',expand=True,padx=8,pady=8)
            def fill_proc():
                for x in ptree.get_children(): ptree.delete(x)
                for d in build_global_details_for_exam(r): ptree.insert('', 'end',values=(d.get('nome',''),d.get('codigo','') or '—',d.get('quantidade',0)),tags=('ok',))
            fill_proc()
            def remove_selected_proc():
                sel=ptree.selection()
                if not sel: messagebox.showinfo('YUPI','Selecione um procedimento para retirar.'); return
                nome=str(ptree.item(sel[0],'values')[0]).strip().upper()
                atual=carregar_mapeamentos().get(exam,[])
                if not atual:
                    messagebox.showinfo('YUPI','Esse exame ainda usa a composição automática. Clique em “Adicionar procedimento” para criar uma regra personalizada.')
                    return
                novo=[x for x in atual if str(x).strip().upper()!=nome]
                if len(novo)==len(atual):
                    messagebox.showwarning('YUPI','O procedimento selecionado não pertence à regra personalizada salva.')
                    return
                salvar_mapeamento(exam,novo); run(); w.destroy(); composition()
            ctk.CTkButton(ptop,text='− Remover selecionado',fg_color='#812A35',hover_color='#9A3341',command=remove_selected_proc).pack(side='left',padx=4)
            ctk.CTkButton(ptop,text='Editar seleção completa',fg_color=PANEL2,text_color='#A98DFF',command=edit_procedures).pack(side='left',padx=4)

            # POR DIA
            ctk.CTkLabel(dia,text='Movimento diário do SADT',font=('Segoe UI',16,'bold'),text_color=TEXT).pack(anchor='w',padx=18,pady=(14,4))
            df,dt=_tree(dia,[('day','Dia'),('int','Interno'),('ext','Externo'),('total','Total')],{'day':160,'int':130,'ext':130,'total':130},15); df.pack(fill='both',expand=True,padx=10,pady=10)
            for ds,v in sorted(sd.get('daily',{}).items()): dt.insert('', 'end',values=(ds,v.get('interno',0),v.get('externo',0),v.get('total',0)),tags=('ok',))

            # COMPARATIVO
            ctk.CTkLabel(comp,text='Comparativo das fontes',font=('Segoe UI',16,'bold'),text_color=TEXT).pack(anchor='w',padx=18,pady=(14,8))
            cf,ct=_tree(comp,[('src','Fonte'),('value','Quantidade'),('detail','Leitura')],{'src':190,'value':140,'detail':650},10); cf.pack(fill='both',expand=True,padx=10,pady=10)
            for src,val,detail in [('SIRESP',s_val,'Escopo usado pela regra atual'),('SADT',sd.get('total','—'),f"Aba: {sd.get('sheet','—')}"),('GLOBAL',g_val,'Soma dos procedimentos vinculados'),('DIFERENÇA',diff,'Resultado final da comparação')]: ct.insert('', 'end',values=(src,val,detail),tags=('ok' if src!='DIFERENÇA' or diff==0 else 'error',))

            # REGRAS
            rule=self.config.get('exams',{}).get(exam,{})
            rb=ctk.CTkTextbox(regras,fg_color=PANEL2,border_width=1,border_color=BORDER,corner_radius=12,font=('Consolas',12)); rb.pack(fill='both',expand=True,padx=14,pady=14)
            rb.insert('1.0',json.dumps(rule,ensure_ascii=False,indent=2)); rb.configure(state='disabled')
            ctk.CTkButton(regras,text='Abrir Configurações',fg_color=PURPLE,command=self.show_settings).pack(anchor='e',padx=18,pady=(0,14))

            # AUDITORIA
            ab=ctk.CTkTextbox(aud,fg_color=PANEL2,border_width=1,border_color=BORDER,corner_radius=12,font=('Segoe UI',12)); ab.pack(fill='both',expand=True,padx=14,pady=14)
            audit_txt=(f"Exame: {exam}\nSIRESP: {s_val}\nSADT: {sd.get('total','—')}\nGlobal: {g_val}\nDiferença: {diff}\nStatus: {st}\n\n{sv.get('explanation','Sem explicação adicional.')}")
            ab.insert('1.0',audit_txt); ab.configure(state='disabled')

        tree.bind('<Double-1>',composition)
        ctk.CTkButton(bar,text='▶ Conferir',width=120,fg_color=PURPLE,hover_color=PURPLE_DARK,command=run).pack(side='right')
        ctk.CTkButton(bar,text='✏ Quantidade',width=115,fg_color=PANEL2,text_color='#A98DFF',command=manual_qty).pack(side='right',padx=4)
        ctk.CTkButton(bar,text='🗑 Tirar regra',width=105,fg_color=PANEL2,text_color=RED,command=clear_mapping).pack(side='right',padx=4)
        ctk.CTkButton(bar,text='🧩 Procedimentos',width=135,fg_color=PANEL2,text_color='#A98DFF',command=edit_procedures).pack(side='right',padx=4)
        ctk.CTkButton(bar,text='👁 Detalhes',width=105,fg_color=PANEL2,text_color='#A98DFF',command=composition).pack(side='right',padx=4)
        ctk.CTkButton(bar,text='⚙ Escopos',width=105,fg_color=PANEL2,text_color='#A98DFF',command=self.show_settings).pack(side='right',padx=4)

    def show_sadt(self):
        self._clear('SADT'); self._header('Planilha SADT','Leitura completa das abas. Explore Interno, Externo, total e movimento por dia.')
        sess=self.session['sadt']; data=sess.get('data',{})
        filebar=ctk.CTkFrame(self.content,fg_color=PANEL,corner_radius=14,border_width=1,border_color=BORDER)
        filebar.pack(fill='x',padx=28,pady=(0,10))
        lbl=ctk.CTkLabel(filebar,text=Path(sess['path']).name if sess.get('path') else 'Nenhum arquivo carregado',font=('Segoe UI',11,'bold'),text_color=TEXT if sess.get('path') else MUTED)
        lbl.pack(side='left',padx=16,pady=12)

        body=ctk.CTkFrame(self.content,fg_color='transparent'); body.pack(fill='both',expand=True,padx=28,pady=(0,22)); body.grid_columnconfigure(0,weight=3); body.grid_columnconfigure(1,weight=2); body.grid_rowconfigure(0,weight=1)
        left=ctk.CTkFrame(body,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER); left.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        right=ctk.CTkFrame(body,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER); right.grid(row=0,column=1,sticky='nsew',padx=(8,0))
        search=ctk.StringVar(value='')
        sf=ctk.CTkFrame(left,fg_color='transparent'); sf.pack(fill='x',padx=12,pady=(12,4))
        ent=ctk.CTkEntry(sf,textvariable=search,placeholder_text='Pesquisar exame ou aba...'); ent.pack(side='left',fill='x',expand=True)
        frame,tree=_tree(left,[('sheet','Aba / Exame'),('int','Interno'),('ext','Externo'),('total','Total'),('days','Dias')],{'sheet':270,'int':80,'ext':80,'total':80,'days':55},16); frame.pack(fill='both',expand=True,padx=0,pady=(0,8))
        selected={'exam':None}

        title=ctk.CTkLabel(right,text='Detalhes da aba',font=('Segoe UI',18,'bold'),text_color=TEXT); title.pack(anchor='w',padx=18,pady=(16,2))
        subtitle=ctk.CTkLabel(right,text='Selecione uma aba para visualizar.',font=('Segoe UI',10),text_color=MUTED); subtitle.pack(anchor='w',padx=18,pady=(0,8))
        totals=ctk.CTkFrame(right,fg_color='transparent'); totals.pack(fill='x',padx=12,pady=4)
        total_labels={}
        for k,name,color in [('interno','Internos',BLUE),('externo','Externos',YELLOW),('total','Total',PURPLE)]:
            c=ctk.CTkFrame(totals,fg_color=PANEL2,corner_radius=12,border_width=1,border_color=BORDER); c.pack(side='left',fill='x',expand=True,padx=4)
            total_labels[k]=ctk.CTkLabel(c,text='—',font=('Segoe UI',22,'bold'),text_color=color); total_labels[k].pack(pady=(12,0))
            ctk.CTkLabel(c,text=name,font=('Segoe UI',9),text_color=MUTED).pack(pady=(0,12))
        ctk.CTkLabel(right,text='Movimento por dia',font=('Segoe UI',12,'bold'),text_color=TEXT).pack(anchor='w',padx=18,pady=(12,4))
        df,daily_tree=_tree(right,[('day','Dia'),('int','Interno'),('ext','Externo'),('total','Total')],{'day':105,'int':80,'ext':80,'total':80},13); df.pack(fill='both',expand=True,padx=8,pady=(0,8))
        toggle_btn=ctk.CTkButton(right,text='Ativar / Ignorar esta aba',fg_color=PANEL2,text_color='#A98DFF')
        toggle_btn.pack(fill='x',padx=18,pady=(0,16))

        def render_list(*_):
            q=search.get().strip().upper()
            for x in tree.get_children(): tree.delete(x)
            ign=set(self.config.get('ignored_sadt_sheets',[]))
            for exam,r in sorted(data.items()):
                if q and q not in exam.upper() and q not in str(r.get('sheet','')).upper(): continue
                status=' • ignorada' if r.get('sheet') in ign else ''
                tree.insert('', 'end',values=(f"{exam}{status}",r.get('interno',0),r.get('externo',0),r.get('total',0),len(r.get('daily',{}))),tags=('muted' if r.get('sheet') in ign else 'ok',),iid=exam)
        def show_detail(_=None):
            sel=tree.selection()
            if not sel:return
            exam=sel[0]; selected['exam']=exam; r=data.get(exam,{})
            title.configure(text=exam); subtitle.configure(text=f"Aba: {r.get('sheet','—')}")
            for k in total_labels: total_labels[k].configure(text=str(r.get(k,0)))
            for x in daily_tree.get_children(): daily_tree.delete(x)
            for ds,v in sorted(r.get('daily',{}).items(), key=lambda kv: tuple(reversed(kv[0].split('/')))):
                daily_tree.insert('', 'end',values=(ds,v.get('interno',0),v.get('externo',0),v.get('total',0)),tags=('ok',))
            ign=set(self.config.get('ignored_sadt_sheets',[])); toggle_btn.configure(text='Ativar esta aba' if r.get('sheet') in ign else 'Ignorar esta aba')
        def toggle():
            exam=selected.get('exam')
            if not exam:return
            sheet=data[exam].get('sheet'); ign=set(self.config.get('ignored_sadt_sheets',[]))
            if sheet in ign: ign.remove(sheet)
            else: ign.add(sheet)
            self.config['ignored_sadt_sheets']=sorted(ign); save_config(self.config); render_list(); show_detail()
        toggle_btn.configure(command=toggle); tree.bind('<<TreeviewSelect>>',show_detail); search.trace_add('write',render_list)

        def load():
            p=filedialog.askopenfilename(filetypes=[('Excel','*.xlsx *.xlsm')])
            if not p:return
            try:
                d=read_sadt(p); sess['path']=p; sess['data']=d; data.clear(); data.update(d); lbl.configure(text=Path(p).name,text_color=TEXT); render_list(); append_history('SADT','Lida',{'abas':len(d),'arquivo':Path(p).name})
            except Exception as e: messagebox.showerror('YUPI',str(e))
        ctk.CTkButton(filebar,text='Carregar Excel',fg_color=PURPLE,command=load).pack(side='right',padx=12,pady=8)
        render_list()
        if data:
            first=next(iter(sorted(data))); tree.selection_set(first); tree.focus(first); show_detail()
    def show_monthly(self):
        self._clear('Mensal'); self._header('Conferência Mensal','Organiza relatórios por período, fecha o TOTAL primeiro e usa os dias somente para localizar a provável origem da divergência.')
        bar=ctk.CTkFrame(self.content,fg_color='transparent'); bar.pack(fill='x',padx=28,pady=(0,8)); info=ctk.CTkLabel(bar,text='Nenhuma pasta selecionada',text_color=MUTED);info.pack(side='left')
        tabs=ctk.CTkTabview(self.content,fg_color=PANEL,segmented_button_selected_color=PURPLE);tabs.pack(fill='both',expand=True,padx=28,pady=(4,22)); tf=tabs.add('Arquivos detectados'); tr=tabs.add('Fechamento do período')
        ff,files_tree=_tree(tf,[('date','Período'),('type','Fonte'),('name','Arquivo'),('status','Status')],{'date':180,'type':140,'name':650,'status':160},17);ff.pack(fill='both',expand=True,padx=5,pady=5)
        fr,res_tree=_tree(tr,[('exam','Exame'),('siresp','SIRESP'),('global','Global'),('diff','Dif.'),('status','Status'),('days','Investigar')],{'exam':360,'siresp':100,'global':100,'diff':80,'status':150,'days':330},17);fr.pack(fill='both',expand=True,padx=5,pady=5)
        folder={'path':''}
        def select_folder():
            p=filedialog.askdirectory()
            if not p:return
            folder['path']=p; items=detect_files(p);info.configure(text=f'{p} • {len(items)} arquivo(s)',text_color=TEXT)
            for x in files_tree.get_children():files_tree.delete(x)
            for r in items:files_tree.insert('', 'end',values=(r['date'] or '—',r['type'],r['name'],'Detectado'))
        def analyze():
            if not folder['path']:messagebox.showwarning('YUPI','Selecione uma pasta.');return
            data=analyze_exam_month(folder['path'])
            for x in res_tree.get_children():res_tree.delete(x)
            for r in data['results']:
                days=', '.join(x['date'] for x in r['days'][:5]) if r['diff'] else '—'
                if len(r['days'])>5:days+=f' +{len(r["days"])-5}'
                res_tree.insert('', 'end',values=(r['exame'],r['siresp'],r['global'],r['diff'],'🟢 OK' if r['status']=='OK' else '🔴 DIVERGÊNCIA',days),tags=('ok' if r['status']=='OK' else 'error',))
            append_history('Mensal','Concluída',{'pares':data['pairs'],'sem_global':data['unmatched_siresp'],'sem_siresp':data['unmatched_global'],'exames':len(data['results'])})
            tabs.set('Fechamento do período'); info.configure(text=f"{data['pairs']} par(es) processados • {data['unmatched_siresp']} SIRESP sem Global • {data['unmatched_global']} Global sem SIRESP")
        ctk.CTkButton(bar,text='📁 Selecionar pasta',fg_color=PANEL2,text_color='#A98DFF',command=select_folder).pack(side='right',padx=6)
        ctk.CTkButton(bar,text='▶ Analisar período',fg_color=PURPLE,command=analyze).pack(side='right',padx=6)
        ctk.CTkLabel(self.content,text='Regra v6: diferença diária sozinha NÃO é erro. Os dias aparecem somente quando o total acumulado do período não fecha.',font=('Segoe UI',11,'bold'),text_color='#A98DFF').pack(anchor='w',padx=34,pady=(0,6))

    def show_presence(self):
        self._clear('Presença'); self._header('Controle de Presença','Agenda SIRESP x Analítico. Prontuário é a chave principal; nome é usado apenas como fallback seguro.')
        sess=self.session['presenca']; files=sess['paths']; allrows=sess.get('rows',[])
        top=ctk.CTkFrame(self.content,fg_color='transparent'); top.pack(fill='x',padx=28,pady=(0,8))
        labels={}; spec=ctk.StringVar(value='Todas')
        def choose(k):
            p=filedialog.askopenfilename(filetypes=[('PDF','*.pdf')])
            if p:
                files[k]=p; labels[k].configure(text=Path(p).name,text_color=TEXT); sess['rows']=[]
        for k,t in [('agenda','Agenda SIRESP'),('analitico','Analítico')]:
            f=ctk.CTkFrame(top,fg_color=PANEL,corner_radius=12,border_width=1,border_color=BORDER); f.pack(side='left',fill='x',expand=True,padx=4)
            ctk.CTkLabel(f,text=t,font=('Segoe UI',11,'bold')).pack(anchor='w',padx=12,pady=(10,2))
            labels[k]=ctk.CTkLabel(f,text=Path(files[k]).name if files.get(k) else 'Nenhum arquivo',text_color=TEXT if files.get(k) else MUTED); labels[k].pack(anchor='w',padx=12)
            ctk.CTkButton(f,text='Selecionar',width=90,height=28,fg_color=PANEL2,text_color='#A98DFF',command=lambda x=k:choose(x)).pack(anchor='e',padx=12,pady=(2,10))
        runbtn=ctk.CTkButton(top,text='▶ Conferir',width=130,height=48,fg_color=PURPLE); runbtn.pack(side='right',padx=(8,0))

        body=ctk.CTkFrame(self.content,fg_color='transparent'); body.pack(fill='both',expand=True,padx=28,pady=(0,22)); body.grid_columnconfigure(0,weight=3); body.grid_columnconfigure(1,weight=1); body.grid_rowconfigure(0,weight=1)
        left=ctk.CTkFrame(body,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER); left.grid(row=0,column=0,sticky='nsew',padx=(0,8))
        right=ctk.CTkFrame(body,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER); right.grid(row=0,column=1,sticky='nsew',padx=(8,0))
        tools=ctk.CTkFrame(left,fg_color='transparent'); tools.pack(fill='x',padx=12,pady=(12,2))
        search=ctk.StringVar(value=''); ctk.CTkEntry(tools,textvariable=search,placeholder_text='Nome, prontuário ou código...').pack(side='left',fill='x',expand=True,padx=(0,8))
        combo=ctk.CTkComboBox(tools,variable=spec,values=['Todas'],width=220); combo.pack(side='left')
        frame,tree=_tree(left,[('patient','Paciente'),('pront','Prontuário'),('spec','Especialidade'),('code','Código'),('qty','Qtd.'),('result','Situação')],{'patient':250,'pront':100,'spec':210,'code':130,'qty':60,'result':180},14); frame.pack(fill='both',expand=True,padx=0,pady=(0,8))
        rtitle=ctk.CTkLabel(right,text='Detalhes do paciente',font=('Segoe UI',18,'bold'),text_color=TEXT); rtitle.pack(anchor='w',padx=18,pady=(16,6))
        rbox=ctk.CTkTextbox(right,fg_color=PANEL2,border_width=1,border_color=BORDER,corner_radius=10,font=('Segoe UI',11)); rbox.pack(fill='both',expand=True,padx=18,pady=(0,18)); rbox.configure(state='disabled')

        def status_text(code):
            return {'COMPARECEU':'🟢 Compareceu','NAO_ENCONTRADO':'🔴 Não encontrado','CODIGO_NAO_MAPEADO':'🟡 Código não mapeado','DUPLICIDADE':'🔴 Duplicidade','ACIMA_PERMITIDO':'🔴 Acima do permitido','ENCAIXE_EXTRA':'🟠 Encaixe / Extra'}.get(code,code)
        def paint(*_):
            q=search.get().strip().upper(); chosen=spec.get()
            for x in tree.get_children(): tree.delete(x)
            for i,r in enumerate(allrows):
                if chosen!='Todas' and r.get('especialidade')!=chosen: continue
                hay=f"{r.get('paciente','')} {r.get('prontuario','')} {r.get('codigo','')}".upper()
                if q and q not in hay: continue
                st=r.get('resultado',''); tag='ok' if st=='COMPARECEU' else ('warn' if st in {'CODIGO_NAO_MAPEADO','ENCAIXE_EXTRA'} else 'error')
                tree.insert('', 'end',iid=str(i),values=(r.get('paciente','') or '—',r.get('prontuario',''),r.get('especialidade',''),r.get('codigo',''),r.get('qtde',0),status_text(st)),tags=(tag,))
        def detail(_=None):
            sel=tree.selection()
            if not sel:return
            r=allrows[int(sel[0])]; rtitle.configure(text=r.get('paciente') or f"Prontuário {r.get('prontuario','')}")
            txt=(f"Prontuário: {r.get('prontuario','—')}\n"
                 f"Registro: {r.get('registro','—')}\n"
                 f"Especialidade: {r.get('especialidade','—')}\n"
                 f"Data: {r.get('data','—')}\n"
                 f"Código(s): {r.get('codigo','—')}\n"
                 f"Quantidade: {r.get('qtde',0)}\n\n"
                 f"Situação: {status_text(r.get('resultado',''))}\n"
                 f"{r.get('detalhe','')}\n\n"
                 f"Correspondência: {r.get('match_mode','—')}")
            rbox.configure(state='normal'); rbox.delete('1.0','end'); rbox.insert('1.0',txt); rbox.configure(state='disabled')
        tree.bind('<<TreeviewSelect>>',detail); search.trace_add('write',paint); combo.configure(command=lambda _:paint())

        def run():
            nonlocal allrows
            if not files.get('agenda') or not files.get('analitico'): messagebox.showwarning('YUPI','Selecione os dois PDFs.'); return
            try:
                pa=pdf_period(files['agenda']); pn=pdf_period(files['analitico'])
                if pa[0] and pn[0] and pa!=pn:
                    messagebox.showwarning('YUPI',f'Arquivos de períodos diferentes.\n\nAgenda: {pa[0]} a {pa[1]}\nAnalítico: {pn[0]} a {pn[1]}\n\nA conferência foi bloqueada para evitar falsos ausentes.')
                    return
                a=read_siresp_agenda(files['agenda']); n=read_analitico_people(files['analitico']); allrows=compare_presence(a,n,self.config.get('specialties',{})); sess['rows']=allrows
                specs=sorted({r.get('especialidade','') for r in allrows if r.get('especialidade')}); combo.configure(values=['Todas']+specs); spec.set('Todas'); paint()
                counts={k:sum(1 for r in allrows if r.get('resultado')==k) for k in ['COMPARECEU','NAO_ENCONTRADO','ENCAIXE_EXTRA','CODIGO_NAO_MAPEADO','DUPLICIDADE','ACIMA_PERMITIDO']}
                append_history('Presença','Concluída',{'agenda':len(a),'analitico':len(n),'comparacoes':len(allrows),**counts})
            except Exception as e: messagebox.showerror('YUPI',str(e))
        runbtn.configure(command=run); paint()

    def show_results(self):
        self._clear('Resultados'); self._header('Resultados e Histórico','Todas as execuções da v6 ficam registradas localmente.')
        bar=ctk.CTkFrame(self.content,fg_color='transparent');bar.pack(fill='x',padx=28,pady=(0,8))
        frame,tree=_tree(self.content,[('at','Data/Hora'),('module','Módulo'),('result','Resultado'),('detail','Detalhes')],{'at':180,'module':140,'result':140,'detail':700},20);frame.pack(fill='both',expand=True,padx=28,pady=(4,22))
        for h in load_history(): tree.insert('', 'end',values=(h.get('at','').replace('T',' '),h.get('module',''),h.get('result',''),str(h.get('details',{}))))
        def export():
            p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='YUPI_v6_historico.csv');
            if not p:return
            with open(p,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f,delimiter=';');w.writerow(['Data/Hora','Módulo','Resultado','Detalhes'])
                for h in load_history():w.writerow([h.get('at'),h.get('module'),h.get('result'),h.get('details')])
            messagebox.showinfo('YUPI','Histórico exportado.')
        ctk.CTkButton(bar,text='Exportar CSV',fg_color=PURPLE,command=export).pack(side='right')

    def show_settings(self):
        self._clear('Configurações'); self._header('Configurações','Escopo em todos os exames + códigos SIGTAP + quantidade permitida. As regras ficam salvas para as próximas conferências.')
        tabs=ctk.CTkTabview(self.content,fg_color=PANEL,segmented_button_selected_color=PURPLE,segmented_button_selected_hover_color=PURPLE_DARK);tabs.pack(fill='both',expand=True,padx=28,pady=(0,24))
        te=tabs.add('Exames e Escopo'); ts=tabs.add('Códigos por Especialidade')
        self._settings_exams(te); self._settings_specialties(ts)

    def _settings_exams(self,parent):
        left=ctk.CTkFrame(parent,fg_color='transparent')
        left.pack(side='left',fill='both',expand=True,padx=8,pady=8)
        frame,tree=_tree(
            left,
            [('exam','Exame'),('active','Status'),('ss','SIRESP'),('sa','SADT'),('sg','Global'),('strategy','Comparação'),('sig','Limite')],
            {'exam':260,'active':75,'ss':80,'sa':80,'sg':80,'strategy':150,'sig':70},17
        )
        frame.pack(fill='both',expand=True)

        def friendly_strategy(v):
            return 'Direta' if v=='direct' else 'Ponte SADT'

        def refresh():
            for x in tree.get_children():tree.delete(x)
            for name,r in sorted(self.config.get('exams',{}).items()):
                sc=r.get('scope',{})
                limit=(r.get('sigtap') or [{}])[0].get('max_qty','—') if r.get('sigtap') else '—'
                tree.insert('', 'end',values=(name,'Ativo' if r.get('active',True) else 'Ignorado',sc.get('siresp','ambos'),sc.get('sadt','ambos'),sc.get('global','total'),friendly_strategy(r.get('scope_strategy','direct')),limit),tags=('ok' if r.get('active',True) else 'muted',))
        refresh()

        actions=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=14,border_width=1,border_color=BORDER,width=360)
        actions.pack(side='right',fill='y',padx=10,pady=8); actions.pack_propagate(False)
        ctk.CTkLabel(actions,text='Regra do exame',font=('Segoe UI',17,'bold'),text_color=TEXT).pack(anchor='w',padx=18,pady=(18,4))
        ctk.CTkLabel(actions,text='Configure fontes, método de comparação e limite por paciente. Os nomes técnicos ficam escondidos.',wraplength=320,justify='left',text_color=MUTED).pack(anchor='w',padx=18,pady=(0,14))

        def edit():
            sel=tree.selection()
            if not sel:
                messagebox.showinfo('YUPI','Selecione um exame.')
                return
            exam=tree.item(sel[0],'values')[0]; r=self.config['exams'][exam]; sc=r.setdefault('scope',{})
            win=ctk.CTkToplevel(self.root); win.title('Configurar • '+exam); win.geometry('760x480'); win.resizable(False,False); win.grab_set()
            header=ctk.CTkFrame(win,fg_color='transparent'); header.pack(fill='x',padx=24,pady=(20,8))
            ctk.CTkLabel(header,text=exam,font=('Segoe UI',22,'bold')).pack(anchor='w')
            ctk.CTkLabel(header,text='Defina como o YUPI deve comparar este exame.',font=('Segoe UI',11),text_color=MUTED).pack(anchor='w',pady=(2,0))
            active=ctk.BooleanVar(value=r.get('active',True))
            ctk.CTkSwitch(header,text='Exame ativo',variable=active).pack(anchor='w',pady=(10,0))

            source=ctk.CTkFrame(win,fg_color=PANEL,corner_radius=12,border_width=1,border_color=BORDER); source.pack(fill='x',padx=24,pady=8)
            ctk.CTkLabel(source,text='Fontes utilizadas',font=('Segoe UI',13,'bold')).grid(row=0,column=0,columnspan=3,sticky='w',padx=14,pady=(12,4))
            vars={}
            specs=[('siresp','SIRESP',['interno','externo','ambos']),('sadt','SADT',['interno','externo','ambos']),('global','GLOBAL',['interno','externo','total'])]
            for col,(key,label,vals) in enumerate(specs):
                ctk.CTkLabel(source,text=label,font=('Segoe UI',10,'bold'),text_color=MUTED).grid(row=1,column=col,sticky='w',padx=14)
                vars[key]=ctk.StringVar(value=sc.get(key,vals[-1]))
                ctk.CTkComboBox(source,variable=vars[key],values=vals,width=205).grid(row=2,column=col,padx=14,pady=(3,14),sticky='ew')
                source.grid_columnconfigure(col,weight=1)

            rulebox=ctk.CTkFrame(win,fg_color='transparent'); rulebox.pack(fill='x',padx=24,pady=8)
            leftbox=ctk.CTkFrame(rulebox,fg_color=PANEL,corner_radius=12,border_width=1,border_color=BORDER); leftbox.pack(side='left',fill='both',expand=True,padx=(0,5))
            ctk.CTkLabel(leftbox,text='Como comparar',font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,4))
            strat=ctk.StringVar(value='Comparação direta' if r.get('scope_strategy','direct')=='direct' else 'Usar SADT como ponte')
            ctk.CTkComboBox(leftbox,variable=strat,values=['Comparação direta','Usar SADT como ponte']).pack(fill='x',padx=14,pady=(0,12))
            rightbox=ctk.CTkFrame(rulebox,fg_color=PANEL,corner_radius=12,border_width=1,border_color=BORDER); rightbox.pack(side='left',fill='both',expand=True,padx=(5,0))
            ctk.CTkLabel(rightbox,text='Quantidade permitida por paciente',font=('Segoe UI',11,'bold')).pack(anchor='w',padx=14,pady=(12,4))
            qty=ctk.StringVar(value=str((r.get('sigtap') or [{}])[0].get('max_qty',1)))
            ctk.CTkEntry(rightbox,textvariable=qty).pack(fill='x',padx=14,pady=(0,12))

            summary=ctk.CTkLabel(win,text='',font=('Segoe UI',10),text_color='#A98DFF')
            summary.pack(anchor='w',padx=26,pady=(4,0))
            def update_summary(*_):
                summary.configure(text=f"Resumo: SIRESP {vars['siresp'].get()} → Global {vars['global'].get()} • SADT {vars['sadt'].get()} • {strat.get()}")
            for vv in vars.values(): vv.trace_add('write',update_summary)
            strat.trace_add('write',update_summary); update_summary()

            footer=ctk.CTkFrame(win,fg_color='transparent'); footer.pack(fill='x',padx=24,pady=18)
            def save():
                r['active']=active.get(); r['scope']={k:v.get() for k,v in vars.items()}; r['scope_strategy']='direct' if strat.get()=='Comparação direta' else 'bridge_sadt'
                if not r.get('sigtap'):r['sigtap']=[{'code':'','name':exam,'max_qty':1,'unit':'atendimento','active':True}]
                try:r['sigtap'][0]['max_qty']=max(1,int(qty.get()))
                except:r['sigtap'][0]['max_qty']=1
                save_config(self.config); append_history('Configuração','Regra alterada',{'exame':exam}); refresh(); win.destroy()
            ctk.CTkButton(footer,text='Cancelar',width=110,fg_color=PANEL2,text_color=TEXT,command=win.destroy).pack(side='right',padx=5)
            ctk.CTkButton(footer,text='Salvar alterações',width=160,fg_color=PURPLE,command=save).pack(side='right',padx=5)

        ctk.CTkButton(actions,text='⚙ Editar regra',height=40,fg_color=PURPLE,command=edit).pack(fill='x',padx=18,pady=(6,8))
        def add():
            name=simpledialog.askstring('YUPI','Nome do exame:')
            if not name:return
            name=_norm_exam(name); self.config.setdefault('exams',{})[name]={'active':True,'scope':{'siresp':'ambos','sadt':'ambos','global':'total'},'scope_strategy':'direct','sigtap':[]}; save_config(self.config); refresh()
        ctk.CTkButton(actions,text='+ Adicionar exame',height=36,fg_color=PANEL2,text_color='#A98DFF',command=add).pack(fill='x',padx=18,pady=5)
        ctk.CTkLabel(actions,text='Dica: os procedimentos reais do Global (nome + código + quantidade) agora são editados diretamente na tela Exames.',wraplength=320,justify='left',text_color=MUTED).pack(anchor='w',padx=18,pady=(18,0))

    def _settings_specialties(self,parent):
        cols=ctk.CTkFrame(parent,fg_color='transparent');cols.pack(fill='both',expand=True,padx=8,pady=8);cols.grid_columnconfigure((0,1),weight=1);cols.grid_rowconfigure(0,weight=1)
        lf=self._card(cols,'Especialidades');lf.grid(row=0,column=0,sticky='nsew',padx=(0,6));rf=self._card(cols,'Códigos SIGTAP permitidos');rf.grid(row=0,column=1,sticky='nsew',padx=(6,0))
        specs=ctk.CTkScrollableFrame(lf,fg_color='transparent');specs.pack(fill='both',expand=True,padx=10,pady=10);selected=ctk.StringVar(value='')
        codes=ctk.CTkScrollableFrame(rf,fg_color='transparent');codes.pack(fill='both',expand=True,padx=10,pady=10)
        def render_codes(name):
            selected.set(name)
            for w in codes.winfo_children():w.destroy()
            ctk.CTkLabel(codes,text=name,font=('Segoe UI',15,'bold'),text_color='#A98DFF').pack(anchor='w',pady=(2,8))
            for idx,r in enumerate(self.config.get('specialties',{}).get(name,[])):
                f=ctk.CTkFrame(codes,fg_color=PANEL2,corner_radius=10);f.pack(fill='x',pady=4)
                ctk.CTkLabel(f,text=f"{r.get('code','')}  •  {r.get('type','Procedimento')}\n{r.get('name','')}\nPermitido: {r.get('max_qty',1)} por {r.get('unit','atendimento')}",justify='left',anchor='w',text_color=TEXT).pack(side='left',fill='x',expand=True,padx=10,pady=9)
                def delete(i=idx):
                    self.config['specialties'][name].pop(i);save_config(self.config);render_codes(name)
                ctk.CTkButton(f,text='Excluir',width=60,fg_color='#FBEAEA',text_color=RED,command=delete).pack(side='right',padx=8)
            def addcode():
                code=simpledialog.askstring('Código SIGTAP','Código:');
                if not code:return
                pname=simpledialog.askstring('Procedimento','Nome do procedimento:') or ''
                typ=simpledialog.askstring('Tipo','Tipo (Consulta/Sessão/Procedimento):') or 'Procedimento'
                q=simpledialog.askinteger('Quantidade permitida','Quantidade máxima por atendimento:',initialvalue=1,minvalue=1) or 1
                self.config['specialties'].setdefault(name,[]).append({'code':code.strip(),'name':pname.strip(),'type':typ.strip(),'max_qty':q,'unit':'atendimento','active':True});save_config(self.config);render_codes(name)
            ctk.CTkButton(codes,text='+ Adicionar código',fg_color=PURPLE,command=addcode).pack(anchor='w',pady=10)
        for name in sorted(self.config.get('specialties',{})):
            ctk.CTkButton(specs,text=name,anchor='w',fg_color=PANEL2,hover_color='#182944',text_color=TEXT,command=lambda n=name:render_codes(n)).pack(fill='x',pady=3)
        def addspec():
            name=simpledialog.askstring('Especialidade','Nome da especialidade:')
            if name:
                name=name.upper().strip();self.config.setdefault('specialties',{}).setdefault(name,[]);save_config(self.config);self.show_settings()
        ctk.CTkButton(lf,text='+ Especialidade',fg_color=PURPLE,command=addspec).pack(anchor='w',padx=12,pady=(0,12))
        if self.config.get('specialties'):render_codes(sorted(self.config['specialties'])[0])

def abrir_yupi_v6(app=None):
    own=False
    if app is None:app=ctk.CTk();own=True
    else:
        for w in app.winfo_children():w.destroy()
    YupiV6(app)
    if own:app.mainloop()
