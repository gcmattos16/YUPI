from __future__ import annotations
import csv, calendar, os, json, webbrowser
from pathlib import Path
from datetime import datetime, date
from tkinter import filedialog, messagebox, ttk, simpledialog
import customtkinter as ctk

from .app import (
    YupiV6, BG, PANEL, PANEL2, PURPLE, PURPLE_DARK, TEXT, MUTED, BORDER,
    GREEN, YELLOW, RED, BLUE, CYAN, _tree, _norm_exam, _resource
)
from .storage import load_config, save_config, append_history, load_history, BASE
from .sadt_reader import read_sadt, slice_period
from .report_meta import pdf_period
from .scope_engine import validate_scope
from .presence import read_analitico_people, read_siresp_agenda, compare_presence
from .monthly import detect_files, analyze_exam_month
from exames.leitor_siresp_exames import ler_siresp_exames
from exames.leitor_faturamento_exames import ler_faturamento_exames_detalhado
from exames.comparador_exames import comparar_exames
from exames.configuracao_mapeamento import carregar_mapeamentos, salvar_mapeamento, remover_mapeamento
from exames.conferencia_exames import _abrir_configuracao_exame
from logica.leitor_siresp import ler_siresp
from logica.leitor_analitico import ler_analitico
from logica.comparador import comparar

ACCENT2='#1787FF'; TEAL='#00D8A0'; ORANGE='#FF9F43'; SLATE='#6C7A96'

class YupiV654(YupiV6):
    def __init__(self, root):
        self.session_files={}
        # Estado de sessão: mantém arquivos, resultados e ajustes ao trocar de tela.
        # O estado dura enquanto o YUPI estiver aberto; não é necessário selecionar os PDFs novamente.
        self.module_state={
            'consultas': {'siresp':'','analitico':'','results':[],'resolved':set()},
            'exames': {'siresp':'','global':'','sadt':'','global_records':[],'global_raw':{},'sadt_data':{},'results':[],'manual':{},'resolved':set()},
            'sadt': {'data':{},'path':''},
            'monthly': {'folder':'','files':[],'selected':date(2026,8,1),'month':date(2026,8,1)},
            'presence': {'agenda':'','analitico':'','rows':[],'agenda_rows':[],'analitico_rows':[]},
        }
        self.home_month=date.today().replace(day=1)
        self.selected_home_day=date.today()
        super().__init__(root)
        self.root.title('YUPI v6.5.4 • Conferência Inteligente')

    _MESES_PT={1:'Janeiro',2:'Fevereiro',3:'Março',4:'Abril',5:'Maio',6:'Junho',7:'Julho',8:'Agosto',9:'Setembro',10:'Outubro',11:'Novembro',12:'Dezembro'}

    def _mes_ano_pt(self, dt, sep=' de '):
        return f"{self._MESES_PT.get(dt.month, str(dt.month))}{sep}{dt.year}"

    def _data_extenso_pt(self, dt):
        return f"{dt.day:02d} de {self._MESES_PT.get(dt.month, str(dt.month))} de {dt.year}"

    def _safe_name(self, path):
        return Path(path).name if path else 'Nenhum arquivo'

    # ---------- shell ----------
    def _build_shell(self):
        self.top=ctk.CTkFrame(self.root,height=74,corner_radius=0,fg_color='#081525')
        self.top.pack(fill='x'); self.top.pack_propagate(False)
        brand=ctk.CTkFrame(self.top,fg_color='transparent');brand.pack(side='left',padx=(26,26),pady=10)
        ctk.CTkLabel(brand,text='YUPI',font=('Segoe UI',29,'bold'),text_color=TEXT).pack(side='left')
        ctk.CTkLabel(brand,text='v6.5.4',font=('Segoe UI',10,'bold'),text_color='white',fg_color=PURPLE,corner_radius=8).pack(side='left',padx=8,ipadx=5,ipady=2)
        nav=ctk.CTkFrame(self.top,fg_color='transparent');nav.pack(side='left',fill='y')
        self.nav_buttons={}
        items=[('Início',self.show_home),('Consultas',self.show_consultas),('Exames',self.show_exames),('SADT',self.show_sadt),('Mensal',self.show_monthly),('Presença',self.show_presence),('Resultados',self.show_results),('Configurações',self.show_settings)]
        for label,cmd in items:
            b=ctk.CTkButton(nav,text=label,width=88,height=42,corner_radius=10,fg_color='transparent',hover_color='#152745',text_color='#DCE7F7',font=('Segoe UI',11,'bold'),command=cmd)
            b.pack(side='left',padx=2,pady=16);self.nav_buttons[label]=b
        right=ctk.CTkFrame(self.top,fg_color='transparent');right.pack(side='right',padx=20,pady=10)
        ctk.CTkEntry(right,width=220,height=36,placeholder_text='Buscar no sistema...').pack(side='left',padx=(0,14))
        user=ctk.CTkFrame(right,fg_color='#11223A',corner_radius=12)
        user.pack(side='left')
        self.operator_name=self.config.get('operator_name','Operador')
        self.operator_unit=self.config.get('operator_unit','Unidade demonstrativa')
        initials=''.join(x[0] for x in self.operator_name.split()[:2]).upper() or 'YU'
        self.operator_initials=ctk.CTkLabel(user,text=initials,width=34,height=34,fg_color=PURPLE,corner_radius=17,font=('Segoe UI',11,'bold'))
        self.operator_initials.pack(side='left',padx=7,pady=5)
        self.operator_label=ctk.CTkLabel(user,text=f'{self.operator_name}\n{self.operator_unit}',justify='left',font=('Segoe UI',9,'bold'),text_color='#DDE7F5')
        self.operator_label.pack(side='left',padx=(0,10))
        for w in (user,self.operator_initials,self.operator_label):
            w.bind('<Button-1>',lambda e:self._edit_operator())
        self.content=ctk.CTkFrame(self.root,fg_color=BG,corner_radius=0);self.content.pack(fill='both',expand=True)
        self.footer=ctk.CTkFrame(self.root,height=30,corner_radius=0,fg_color='#071321');self.footer.pack(fill='x');self.footer.pack_propagate(False)
        ctk.CTkLabel(self.footer,text='YUPI v6.5.4   |   Unidade demonstrativa',font=('Segoe UI',9),text_color=MUTED).pack(side='left',padx=20,pady=6)
        ctk.CTkLabel(self.footer,text='Conferência inteligente • mais controle, menos retrabalho.',font=('Segoe UI',9,'italic'),text_color='#72849F').pack(side='right',padx=20,pady=6)

    def _clear(self, active=''):
        for w in self.content.winfo_children(): w.destroy()
        for name,b in self.nav_buttons.items():
            b.configure(fg_color='#271A59' if name==active else 'transparent',text_color='#B99DFF' if name==active else '#DCE7F7')

    def _page_header(self,title,subtitle,icon=''):
        f=ctk.CTkFrame(self.content,fg_color='transparent');f.pack(fill='x',padx=28,pady=(20,10))
        left=ctk.CTkFrame(f,fg_color='transparent');left.pack(side='left')
        if icon:
            ctk.CTkLabel(left,text=icon,width=56,height=56,fg_color='#14254A',corner_radius=14,font=('Segoe UI Emoji',28)).pack(side='left',padx=(0,16))
        tx=ctk.CTkFrame(left,fg_color='transparent');tx.pack(side='left')
        ctk.CTkLabel(tx,text=title,font=('Segoe UI',26,'bold'),text_color=TEXT).pack(anchor='w')
        ctk.CTkLabel(tx,text=subtitle,font=('Segoe UI',11),text_color=MUTED).pack(anchor='w',pady=(3,0))
        return f

    def _metric(self,parent,value,label,color=PURPLE,sub=''):
        f=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=14,border_width=1,border_color=BORDER)
        ctk.CTkLabel(f,text=str(value),font=('Segoe UI',24,'bold'),text_color=TEXT).pack(anchor='w',padx=15,pady=(12,0))
        ctk.CTkLabel(f,text=label,font=('Segoe UI',10,'bold'),text_color=color).pack(anchor='w',padx=15,pady=(1,0))
        if sub: ctk.CTkLabel(f,text=sub,font=('Segoe UI',8),text_color=MUTED).pack(anchor='w',padx=15,pady=(2,10))
        else: ctk.CTkLabel(f,text=' ',font=('Segoe UI',8),text_color=MUTED).pack(anchor='w',padx=15,pady=(2,10))
        return f

    def _section(self,parent,title=''):
        f=ctk.CTkFrame(parent,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER)
        if title: ctk.CTkLabel(f,text=title,font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',padx=16,pady=(13,7))
        return f

    # ---------- HOME ----------
    def show_home(self):
        return YupiV6.show_home(self)

    # ---------- CONSULTAS ----------
    def show_consultas(self):
        self._clear('Consultas');self._page_header('Conferência de Consultas','Compare SIRESP e Analítico. Identifique divergências, composição, códigos e auditoria.','🩺')
        state=self.module_state['consultas']
        top=ctk.CTkFrame(self.content,fg_color='transparent');top.pack(fill='x',padx=28,pady=(0,10))
        labels={}
        for key,title in [('siresp','SIRESP'),('analitico','Analítico')]:
            f=self._section(top);f.pack(side='left',fill='x',expand=True,padx=5)
            ctk.CTkLabel(f,text=title,font=('Segoe UI',11,'bold'),text_color='#A98DFF').pack(anchor='w',padx=13,pady=(10,0));labels[key]=ctk.CTkLabel(f,text=self._safe_name(state.get(key,'')),font=('Segoe UI',9),text_color=TEXT if state.get(key) else MUTED);labels[key].pack(anchor='w',padx=13,pady=(3,8))
            def choose(k=key,t=title):
                pp=filedialog.askopenfilename(filetypes=[('PDF','*.pdf')])
                if pp:
                    state[k]=pp; self.session_files['Consultas '+t]=pp
                    labels[k].configure(text=Path(pp).name,text_color=TEXT)
            ctk.CTkButton(f,text='Selecionar',height=28,fg_color=PANEL2,text_color='#B99DFF',command=choose).pack(anchor='e',padx=13,pady=(0,10))
        ctk.CTkButton(top,text='▶ Conferir',height=74,width=150,fg_color=PURPLE,command=lambda:run()).pack(side='left',padx=8)

        kpis=ctk.CTkFrame(self.content,fg_color='transparent');kpis.pack(fill='x',padx=28,pady=(0,10));metric_labels=[]
        for v,l,c in [('0','Especialidades',PURPLE),('0','OK',GREEN),('0','Divergências',RED),('0','Resolvidas',ORANGE),('0%','Conformidade',ACCENT2)]:
            card=self._metric(kpis,v,l,c);card.pack(side='left',fill='x',expand=True,padx=4);metric_labels.append(card.winfo_children()[0])

        body=ctk.CTkFrame(self.content,fg_color='transparent');body.pack(fill='both',expand=True,padx=28,pady=(0,20));body.grid_columnconfigure(0,weight=7);body.grid_columnconfigure(1,weight=5);body.grid_rowconfigure(0,weight=1)
        left=self._section(body);left.grid(row=0,column=0,sticky='nsew',padx=(0,7));right=self._section(body);right.grid(row=0,column=1,sticky='nsew',padx=(7,0))
        tools=ctk.CTkFrame(left,fg_color='transparent');tools.pack(fill='x',padx=12,pady=(12,6))
        search=ctk.CTkEntry(tools,placeholder_text='Pesquisar especialidade...');search.pack(side='left',fill='x',expand=True)
        filt=ctk.StringVar(value='Todas');ctk.CTkComboBox(tools,variable=filt,values=['Todas','OK','Divergência','Resolvidas'],width=150,command=lambda _:paint()).pack(side='left',padx=(6,0))
        ff,tree=_tree(left,[('spec','Especialidade'),('s','SIRESP'),('a','Analítico'),('d','Dif.'),('st','Status')],{'spec':280,'s':90,'a':90,'d':70,'st':160},16);ff.pack(fill='both',expand=True,padx=4,pady=(0,8))
        detail=ctk.CTkFrame(right,fg_color='transparent');detail.pack(fill='both',expand=True,padx=8,pady=8)

        def current_result(spec):
            return next((x for x in state['results'] if (x.get('especialidade') or x.get('nome') or x.get('especialidade_normalizada'))==spec),{})

        def render_detail(_=None):
            for w in detail.winfo_children():w.destroy()
            sel=tree.selection()
            if not sel:
                ctk.CTkLabel(detail,text='Selecione uma especialidade para abrir a auditoria.',text_color=MUTED).pack(anchor='w');return
            vals=tree.item(sel[0],'values');spec,sval,aval,dval,st=vals;r=current_result(spec);dnum=int(dval)
            head=ctk.CTkFrame(detail,fg_color='transparent');head.pack(fill='x')
            ctk.CTkLabel(head,text=spec,font=('Segoe UI',19,'bold'),text_color=TEXT).pack(side='left')
            badge='RESOLVIDA' if spec in state['resolved'] else ('OK' if dnum==0 else 'DIVERGÊNCIA')
            ctk.CTkLabel(head,text=badge,font=('Segoe UI',9,'bold'),text_color=GREEN if badge in ('OK','RESOLVIDA') else RED,fg_color='#10243A',corner_radius=8).pack(side='right',ipadx=8,ipady=4)
            tabs=ctk.CTkTabview(detail,fg_color=PANEL2,segmented_button_selected_color=PURPLE,segmented_button_selected_hover_color=PURPLE_DARK)
            tabs.pack(fill='both',expand=True,pady=(10,0))
            t_sum=tabs.add('Resumo');t_comp=tabs.add('Composição');t_day=tabs.add('Por dia');t_cod=tabs.add('Códigos');t_aud=tabs.add('Auditoria')
            # resumo
            row=ctk.CTkFrame(t_sum,fg_color='transparent');row.pack(fill='x',padx=8,pady=8)
            for val,lab,col in [(sval,'SIRESP',ACCENT2),(aval,'Analítico',PURPLE),(dval,'Diferença',RED if dnum else GREEN)]:self._metric(row,val,lab,col).pack(side='left',fill='x',expand=True,padx=2)
            msg=r.get('explicacao') or ('Valores conferem.' if dnum==0 else f'Existe diferença de {abs(dnum)} lançamento(s) entre as fontes.')
            ctk.CTkLabel(t_sum,text='Situação da conferência',font=('Segoe UI',11,'bold'),text_color=TEXT).pack(anchor='w',padx=10,pady=(8,3))
            ctk.CTkLabel(t_sum,text=msg,wraplength=430,justify='left',font=('Segoe UI',9),text_color=GREEN if dnum==0 else '#FF8A98').pack(anchor='w',padx=10)
            # composição real do comparador
            for title,key,col in [('Composição SIRESP','detalhes_siresp',ACCENT2),('Composição Analítico','detalhes_analitico',PURPLE)]:
                ctk.CTkLabel(t_comp,text=title,font=('Segoe UI',11,'bold'),text_color=col).pack(anchor='w',padx=10,pady=(8,3))
                items=r.get(key,[]) or []
                if not items: ctk.CTkLabel(t_comp,text='Nenhum detalhe disponível.',text_color=MUTED).pack(anchor='w',padx=10)
                for it in items:
                    rr=ctk.CTkFrame(t_comp,fg_color='#0A1727',corner_radius=8);rr.pack(fill='x',padx=10,pady=2)
                    ctk.CTkLabel(rr,text=str(it.get('especialidade','')),font=('Segoe UI',9),text_color=TEXT).pack(side='left',padx=8,pady=5)
                    ctk.CTkLabel(rr,text=str(it.get('quantidade',0)),font=('Segoe UI',9,'bold'),text_color=col).pack(side='right',padx=8)
            # por dia: auditoria clássica contém investigação detalhada validada
            ctk.CTkLabel(t_day,text='Investigação diária',font=('Segoe UI',12,'bold'),text_color=TEXT).pack(anchor='w',padx=10,pady=(10,3))
            ctk.CTkLabel(t_day,text='A investigação por dia é usada apenas quando o total diverge. Abra a auditoria clássica para localizar o dia e os lançamentos responsáveis.',wraplength=430,justify='left',text_color=MUTED).pack(anchor='w',padx=10,pady=(0,10))
            ctk.CTkButton(t_day,text='👥 Investigar pacientes na Presença',fg_color=PURPLE,command=self.show_presence).pack(fill='x',padx=10,pady=5)
            # códigos configurados
            ctk.CTkLabel(t_cod,text='Códigos permitidos para a especialidade',font=('Segoe UI',11,'bold'),text_color=TEXT).pack(anchor='w',padx=10,pady=(10,4))
            codes=self.config.get('specialties',{}).get(spec,[]) or []
            if not codes: ctk.CTkLabel(t_cod,text='Nenhum código cadastrado. Use Configurações para adicionar.',text_color=YELLOW,wraplength=420,justify='left').pack(anchor='w',padx=10,pady=4)
            for cr in codes:
                rr=ctk.CTkFrame(t_cod,fg_color='#0A1727',corner_radius=8);rr.pack(fill='x',padx=10,pady=2)
                ctk.CTkLabel(rr,text=f"{cr.get('code','')}  •  {cr.get('name','')}",font=('Segoe UI',9),text_color=TEXT,anchor='w').pack(side='left',fill='x',expand=True,padx=8,pady=6)
                ctk.CTkLabel(rr,text=f"máx. {cr.get('max_qty',1)}",font=('Segoe UI',8,'bold'),text_color=TEAL).pack(side='right',padx=8)
            ctk.CTkButton(t_cod,text='⚙ Editar códigos',fg_color=PANEL,command=self.show_settings).pack(fill='x',padx=10,pady=8)
            # auditoria
            ctk.CTkLabel(t_aud,text='Auditoria da divergência',font=('Segoe UI',12,'bold'),text_color=TEXT).pack(anchor='w',padx=10,pady=(10,4))
            audmsg='Nenhuma divergência encontrada.' if dnum==0 else f'SIRESP: {sval} | Analítico: {aval}\nDiferença: {dval}\nUse \"Investigar pacientes\" para seguir para Presença ou abra a auditoria clássica.'
            ctk.CTkLabel(t_aud,text=audmsg,wraplength=430,justify='left',text_color=GREEN if dnum==0 else '#FF8A98').pack(anchor='w',padx=10,pady=4)
            obs=ctk.CTkTextbox(t_aud,height=78,fg_color='#071525',border_width=1,border_color=BORDER);obs.pack(fill='x',padx=10,pady=6)
            obs.insert('1.0','')
            actions=ctk.CTkFrame(t_aud,fg_color='transparent');actions.pack(fill='x',padx=10,pady=6)
            ctk.CTkButton(actions,text='👥 Investigar pacientes',fg_color='#9E2944',command=self.show_presence).pack(side='left',fill='x',expand=True,padx=(0,3))
            def resolve():
                state['resolved'].add(spec);append_history('Consultas','Divergência resolvida',{'especialidade':spec,'observacao':obs.get('1.0','end').strip()});paint();render_detail()
            ctk.CTkButton(actions,text='✓ Marcar resolvido',fg_color=PURPLE,command=resolve).pack(side='left',fill='x',expand=True,padx=(3,0))
            ctk.CTkLabel(t_aud,text='Auditoria integrada nesta tela — nenhuma janela antiga será aberta.',text_color=MUTED,font=('Segoe UI',8)).pack(anchor='w',padx=10,pady=(2,10))

        tree.bind('<<TreeviewSelect>>',render_detail)
        def paint():
            q=search.get().upper().strip();f=filt.get()
            for x in tree.get_children():tree.delete(x)
            for r in state['results']:
                spec=r.get('especialidade') or r.get('nome') or r.get('especialidade_normalizada') or ''
                if q and q not in str(spec).upper():continue
                s=int(r.get('siresp',r.get('qtd_siresp',0)) or 0);a=int(r.get('analitico',r.get('qtd_analitico',0)) or 0);d=s-a
                resolved=spec in state['resolved'];status_txt='RESOLVIDA' if resolved else ('OK' if d==0 else 'DIVERGÊNCIA')
                if f=='OK' and d!=0:continue
                if f=='Divergência' and (d==0 or resolved):continue
                if f=='Resolvidas' and not resolved:continue
                st=('🟣 RESOLVIDA' if resolved else ('🟢 OK' if d==0 else '🔴 DIVERGÊNCIA'))
                tree.insert('', 'end',values=(spec,s,a,d,st),tags=('ok' if d==0 or resolved else 'error',))
        search.bind('<KeyRelease>',lambda e:paint())
        def run():
            if not state['siresp'] or not state['analitico']:messagebox.showwarning('YUPI','Selecione os dois PDFs.');return
            try:
                ss=ler_siresp(state['siresp']);aa=ler_analitico(state['analitico']);state['results']=comparar(ss,aa);paint()
                total=len(state['results']);ok=sum(1 for r in state['results'] if int(r.get('diferenca',0) or 0)==0);div=total-ok;conf=round((ok/total*100),1) if total else 0
                for lbl,val in zip(metric_labels,[total,ok,div,len(state['resolved']),f'{conf}%']):lbl.configure(text=str(val))
                append_history('Consultas','Concluída',{'especialidades':total,'divergencias':div})
            except Exception as e:messagebox.showerror('YUPI',str(e))

        # Restaura a conferência ao voltar para a tela, sem exigir nova seleção dos PDFs.
        if state.get('results'):
            paint()
            total=len(state['results']); ok=sum(1 for r in state['results'] if int(r.get('diferenca',0) or 0)==0)
            div=total-ok; conf=round((ok/total*100),1) if total else 0
            for lbl,val in zip(metric_labels,[total,ok,div,len(state['resolved']),f'{conf}%']): lbl.configure(text=str(val))
            if tree.get_children(): tree.selection_set(tree.get_children()[0]); render_detail()

    # ---------- EXAMES ----------
    def show_exames(self):
        self._clear('Exames');self._page_header('Conferência de Exames','Compare SIRESP, Global e SADT. Audite composição, procedimentos, dias e regras em uma única tela.','🗂')
        state=self.module_state['exames']
        if not state.get('sadt') and self.session.get('sadt',{}).get('path'):
            state['sadt']=self.session['sadt']['path']
        files=ctk.CTkFrame(self.content,fg_color='transparent');files.pack(fill='x',padx=28,pady=(0,10));lbls={}
        for k,t in [('siresp','SIRESP PDF'),('global','Global PDF'),('sadt','SADT Excel')]:
            f=self._section(files);f.pack(side='left',fill='x',expand=True,padx=4);ctk.CTkLabel(f,text=t,font=('Segoe UI',10,'bold'),text_color='#B99DFF').pack(anchor='w',padx=12,pady=(10,0));lbls[k]=ctk.CTkLabel(f,text=self._safe_name(state.get(k,'')),font=('Segoe UI',8),text_color=TEXT if state.get(k) else MUTED);lbls[k].pack(anchor='w',padx=12,pady=(3,8))
            def ch(x=k,tit=t):
                pp=filedialog.askopenfilename(filetypes=[('Excel','*.xlsx *.xlsm')] if x=='sadt' else [('PDF','*.pdf')])
                if pp:
                    state[x]=pp; self.session_files[tit]=pp; lbls[x].configure(text=Path(pp).name,text_color=TEXT)
                    state['results']=[]; state['resolved'].clear()
                    if x!='global': state['manual'].clear()
            ctk.CTkButton(f,text='Selecionar',height=27,fg_color=PANEL2,text_color='#B99DFF',command=ch).pack(anchor='e',padx=12,pady=(0,9))
        ctk.CTkButton(files,text='▶ Conferir',width=145,height=69,fg_color=PURPLE,command=lambda:run()).pack(side='left',padx=6)
        metrics=ctk.CTkFrame(self.content,fg_color='transparent');metrics.pack(fill='x',padx=28,pady=(0,10));ml=[]
        for v,l,c in [('0','Exames',PURPLE),('0','OK',GREEN),('0','Divergências',RED),('0','Resolvidos',ORANGE),('0','Zerados',SLATE),('0%','Conformidade',ACCENT2)]:
            ca=self._metric(metrics,v,l,c);ca.pack(side='left',fill='x',expand=True,padx=3);ml.append(ca.winfo_children()[0])
        body=ctk.CTkFrame(self.content,fg_color='transparent');body.pack(fill='both',expand=True,padx=28,pady=(0,18));body.grid_columnconfigure(0,weight=7);body.grid_columnconfigure(1,weight=5);body.grid_rowconfigure(0,weight=1)
        left=self._section(body);left.grid(row=0,column=0,sticky='nsew',padx=(0,7));right=self._section(body);right.grid(row=0,column=1,sticky='nsew',padx=(7,0))
        toolbar=ctk.CTkFrame(left,fg_color='transparent');toolbar.pack(fill='x',padx=12,pady=(12,4));search=ctk.CTkEntry(toolbar,placeholder_text='Pesquisar exame...');search.pack(side='left',fill='x',expand=True);status=ctk.StringVar(value='Todos');ctk.CTkComboBox(toolbar,variable=status,values=['Todos','OK','Divergência','Resolvidos','Zerado'],width=145,command=lambda _:paint()).pack(side='left',padx=6)
        ff,tree=_tree(left,[('exam','Exame'),('s','SIRESP'),('sa','SADT'),('g','Global'),('d','Dif.'),('st','Status')],{'exam':270,'s':75,'sa':75,'g':75,'d':65,'st':145},16);ff.pack(fill='both',expand=True,padx=4,pady=(0,8))
        detail=ctk.CTkFrame(right,fg_color='transparent');detail.pack(fill='both',expand=True,padx=8,pady=8)
        def findr(ex):return next((r for r in state['results'] if r.get('exame')==ex),None)
        def selected_global_rows(ex,r):
            selected=set(str(x).strip().upper() for x in carregar_mapeamentos().get(ex,[]))
            for d in r.get('detalhes_global',[]) or []:
                n=str(d.get('exame','')).strip().upper()
                if n:selected.add(n)
            rows=[]
            for rec in state['global_records']:
                exact=str(rec.get('nome_exato','')).strip().upper();canon=str(rec.get('nome_normalizado','')).strip().upper()
                if exact in selected or canon in selected:
                    rows.append((rec.get('nome_original') or exact,rec.get('codigo','') or '—',int(rec.get('quantidade',0) or 0)))
            return rows
        def render_detail(_=None):
            for w in detail.winfo_children():w.destroy()
            sel=tree.selection()
            if not sel:ctk.CTkLabel(detail,text='Selecione um exame para abrir a auditoria.',text_color=MUTED).pack(anchor='w');return
            ex=tree.item(sel[0],'values')[0];r=findr(ex) or {};v=r.get('scope_validation',{});sd=r.get('sadt') or {};sval=int(v.get('siresp_scope',r.get('siresp',0)) or 0);gval=int(state['manual'].get(ex,v.get('global',r.get('global',0))) or 0);dval=v.get('difference');dval=(sval-gval if dval is None and v.get('status')!='ESCOPO_PENDENTE' else dval)
            head=ctk.CTkFrame(detail,fg_color='transparent');head.pack(fill='x');ctk.CTkLabel(head,text=ex,font=('Segoe UI',18,'bold'),text_color=TEXT).pack(side='left')
            badge='RESOLVIDO' if ex in state['resolved'] else ('REQUER SADT' if v.get('status')=='ESCOPO_PENDENTE' else ('OK' if v.get('status')=='OK' else 'DIVERGÊNCIA'));ctk.CTkLabel(head,text=badge,font=('Segoe UI',9,'bold'),text_color=GREEN if badge in ('OK','RESOLVIDO') else RED,fg_color='#10243A',corner_radius=8).pack(side='right',ipadx=8,ipady=4)
            tabs=ctk.CTkTabview(detail,fg_color=PANEL2,segmented_button_selected_color=PURPLE,segmented_button_selected_hover_color=PURPLE_DARK)
            tabs.pack(fill='both',expand=True,pady=(10,0))
            t_sum=tabs.add('Resumo');t_proc=tabs.add('Procedimentos');t_day=tabs.add('Por dia');t_comp=tabs.add('Comparativo');t_rule=tabs.add('Regras');t_aud=tabs.add('Auditoria')
            # resumo
            row=ctk.CTkFrame(t_sum,fg_color='transparent');row.pack(fill='x',padx=6,pady=7)
            for val,lab,col in [(sval,'SIRESP',ACCENT2),(sd.get('total','—'),'SADT',TEAL),(gval,'Global',ORANGE),(dval if dval is not None else '—','Diferença',RED if dval not in (0,None) else GREEN)]:self._metric(row,val,lab,col).pack(side='left',fill='x',expand=True,padx=2)
            info=[('Aba no SADT',sd.get('sheet','—')),('Interno SADT',sd.get('interno','—')),('Externo SADT',sd.get('externo','—')),('Status','Conferido' if v.get('status')=='OK' else ('Requer SADT' if v.get('status')=='ESCOPO_PENDENTE' else 'Revisar'))]
            for a,b in info:
                rr=ctk.CTkFrame(t_sum,fg_color='#0A1727',corner_radius=8);rr.pack(fill='x',padx=8,pady=2);ctk.CTkLabel(rr,text=a,text_color=MUTED,font=('Segoe UI',8)).pack(side='left',padx=8,pady=5);ctk.CTkLabel(rr,text=str(b),text_color=TEXT,font=('Segoe UI',8,'bold')).pack(side='right',padx=8)
            # procedimentos
            grows=selected_global_rows(ex,r)
            ctk.CTkLabel(t_proc,text='Composição do Global',font=('Segoe UI',12,'bold'),text_color=TEXT).pack(anchor='w',padx=9,pady=(8,4))
            ctk.CTkLabel(t_proc,text='Nome do procedimento, código SIGTAP e quantidade. Selecione uma linha para retirar.',font=('Segoe UI',8),text_color=MUTED).pack(anchor='w',padx=9,pady=(0,5))
            pf,ptree=_tree(t_proc,[('nome','Procedimento'),('codigo','SIGTAP'),('qtd','Qtd.')],{'nome':300,'codigo':120,'qtd':65},7);pf.pack(fill='both',expand=True,padx=8,pady=4)
            for nome,codigo,qtd in grows: ptree.insert('', 'end',values=(nome,codigo,qtd),tags=('ok',))
            def edit_procs():
                if not state['global_records']:messagebox.showwarning('YUPI','Faça a conferência para carregar os procedimentos do Global.');return
                _abrir_configuracao_exame(self.root,ex,state['global_records'],total_siresp=sval,mapeamento_temporario=carregar_mapeamentos().get(ex,[]),ao_aplicar=lambda *_:run())
            def remove_selected_proc():
                selp=ptree.selection()
                if not selp: messagebox.showinfo('YUPI','Selecione um procedimento na tabela para retirar.'); return
                nome=str(ptree.item(selp[0],'values')[0]).strip().upper()
                atual=carregar_mapeamentos().get(ex,[])
                if not atual:
                    atual=[str(n).strip().upper() for n,_,_ in grows]
                novo=[x for x in atual if str(x).strip().upper()!=nome]
                salvar_mapeamento(ex,novo); run()
            def remove_rule():
                if not carregar_mapeamentos().get(ex):messagebox.showinfo('YUPI','Este exame não possui regra personalizada.');return
                if messagebox.askyesno('YUPI',f'Remover a composição personalizada de {ex}?'):remover_mapeamento(ex);run()
            actions_p=ctk.CTkFrame(t_proc,fg_color='transparent');actions_p.pack(fill='x',padx=8,pady=4)
            ctk.CTkButton(actions_p,text='+ Adicionar procedimento',fg_color=PURPLE,command=edit_procs).pack(side='left',fill='x',expand=True,padx=(0,3))
            ctk.CTkButton(actions_p,text='− Remover selecionado',fg_color='#812A35',hover_color='#9A3341',command=remove_selected_proc).pack(side='left',fill='x',expand=True,padx=(3,0))
            ctk.CTkButton(t_proc,text='Restaurar composição automática',fg_color=PANEL,text_color='#B99DFF',command=remove_rule).pack(fill='x',padx=8,pady=(1,8))
            # por dia - dados SADT reais
            ctk.CTkLabel(t_day,text='Distribuição SADT por dia',font=('Segoe UI',11,'bold'),text_color=TEXT).pack(anchor='w',padx=9,pady=(8,4))
            daily=sd.get('daily') or {}
            ff2,tr2=_tree(t_day,[('d','Dia'),('i','Interno'),('e','Externo'),('t','Total')],{'d':110,'i':75,'e':75,'t':75},8);ff2.pack(fill='both',expand=True,padx=8,pady=4)
            for day,val in sorted(daily.items()):tr2.insert('', 'end',values=(day,val.get('interno',0),val.get('externo',0),val.get('total',val.get('interno',0)+val.get('externo',0))))
            if not daily:ctk.CTkLabel(t_day,text='Sem detalhamento diário no SADT carregado.',text_color=MUTED).pack(anchor='w',padx=9,pady=5)
            # comparativo
            ctk.CTkLabel(t_comp,text='Como o YUPI chegou neste resultado',font=('Segoe UI',11,'bold'),text_color=TEXT).pack(anchor='w',padx=9,pady=(8,5))
            for title,items,col in [('SIRESP',r.get('detalhes_siresp',[]) or [],ACCENT2),('GLOBAL',r.get('detalhes_global',[]) or [],ORANGE)]:
                ctk.CTkLabel(t_comp,text=title,font=('Segoe UI',9,'bold'),text_color=col).pack(anchor='w',padx=9,pady=(5,2))
                for it in items:
                    txt=(f"{it.get('exame','')} • ext {it.get('externo',0)} • int {it.get('interno',0)} • direto {it.get('direto',0)}" if title=='SIRESP' else f"{it.get('exame','')} • qtd {it.get('quantidade',0)}")
                    ctk.CTkLabel(t_comp,text=txt,justify='left',text_color=TEXT,font=('Segoe UI',8)).pack(anchor='w',padx=14,pady=1)
            # regras
            rule=self.config.get('exams',{}).get(ex,{});sc=rule.get('scope',{});limit=((rule.get('sigtap') or [{}])[0].get('max_qty',1) if rule.get('sigtap') else 1)
            for a,b in [('SIRESP',sc.get('siresp','ambos')),('SADT',sc.get('sadt','ambos')),('Global',sc.get('global','total')),('Estratégia',rule.get('scope_strategy','direct')),('Quantidade permitida',limit)]:
                rr=ctk.CTkFrame(t_rule,fg_color='#0A1727',corner_radius=8);rr.pack(fill='x',padx=8,pady=3);ctk.CTkLabel(rr,text=a,text_color=MUTED,font=('Segoe UI',8)).pack(side='left',padx=8,pady=6);ctk.CTkLabel(rr,text=str(b),text_color=TEXT,font=('Segoe UI',8,'bold')).pack(side='right',padx=8)
            ctk.CTkButton(t_rule,text='⚙ Editar regra / escopo',fg_color=PURPLE,command=self.show_settings).pack(fill='x',padx=8,pady=8)
            # auditoria e manual
            ctk.CTkLabel(t_aud,text='Auditoria do exame',font=('Segoe UI',11,'bold'),text_color=TEXT).pack(anchor='w',padx=9,pady=(8,4))
            audmsg=('Valores conferem.' if v.get('status')=='OK' else (v.get('explanation') or ('Existe divergência de escopo/total.' if dval is None else f'Existe diferença de {abs(dval)}. Revise os procedimentos, o escopo e o detalhe por dia.')))
            ctk.CTkLabel(t_aud,text=audmsg,wraplength=430,justify='left',text_color=GREEN if v.get('status')=='OK' else '#FF8A98').pack(anchor='w',padx=9,pady=4)
            def manual_qty():
                q=simpledialog.askinteger('Quantidade manual',f'{ex}\nInforme a quantidade do Global para esta conferência:',initialvalue=gval,minvalue=0)
                if q is None:return
                state['manual'][ex]=q;paint();render_detail()
            ctk.CTkButton(t_aud,text='✏ Informar quantidade manual',fg_color=PANEL,text_color='#B99DFF',command=manual_qty).pack(fill='x',padx=9,pady=3)
            obs=ctk.CTkTextbox(t_aud,height=70,fg_color='#071525',border_width=1,border_color=BORDER);obs.pack(fill='x',padx=9,pady=5)
            def resolve():state['resolved'].add(ex);append_history('Exames','Divergência resolvida',{'exame':ex,'observacao':obs.get('1.0','end').strip()});paint();render_detail()
            ctk.CTkButton(t_aud,text='✓ Marcar como resolvido',fg_color=PURPLE,command=resolve).pack(fill='x',padx=9,pady=(2,8))
        tree.bind('<<TreeviewSelect>>',render_detail)
        def paint():
            q=search.get().upper().strip();filt=status.get()
            for x in tree.get_children():tree.delete(x)
            for r in state['results']:
                ex=r['exame'];v=r.get('scope_validation',{});sd=r.get('sadt') or {};ss=int(v.get('siresp_scope',r.get('siresp',0)) or 0);gg=int(state['manual'].get(ex,v.get('global',r.get('global',0))) or 0)
                dd=v.get('difference')
                if dd is None and v.get('status')!='ESCOPO_PENDENTE': dd=ss-gg
                if ss==0 and gg==0 and v.get('status')!='ESCOPO_PENDENTE': raw='ZERADO'
                elif v.get('status')=='OK': raw='OK'
                elif v.get('status')=='ESCOPO_PENDENTE': raw='REQUER SADT'
                else: raw='DIVERGÊNCIA'
                resolved=ex in state['resolved'];st='RESOLVIDO' if resolved else raw
                if q and q not in ex.upper():continue
                if filt=='OK' and raw!='OK':continue
                if filt=='Divergência' and (raw not in ('DIVERGÊNCIA','REQUER SADT') or resolved):continue
                if filt=='Resolvidos' and not resolved:continue
                if filt=='Zerado' and raw!='ZERADO':continue
                label='🟣 RESOLVIDO' if resolved else ('🟢 OK' if raw=='OK' else '⚪ ZERADO' if raw=='ZERADO' else '🟡 REQUER SADT' if raw=='REQUER SADT' else '🔴 DIVERGÊNCIA')
                tree.insert('', 'end',values=(ex,ss,sd.get('total','—'),gg,dd if dd is not None else '—',label),tags=('ok' if raw=='OK' or resolved else 'muted' if raw=='ZERADO' else 'error',))
        search.bind('<KeyRelease>',lambda e:paint())
        def run():
            if not state['siresp'] or not state['global']:messagebox.showwarning('YUPI','Selecione SIRESP e Global.');return
            try:
                sdata=ler_siresp_exames(state['siresp']);g,records,raw=ler_faturamento_exames_detalhado(state['global']);state['global_records']=records;state['global_raw']=raw;base=comparar_exames(sdata,g,carregar_mapeamentos(),raw);sadt=read_sadt(state['sadt']) if state['sadt'] else {}
                # Mantém SIRESP/Global/SADT no mesmo período quando a informação está disponível.
                ps=pdf_period(state['siresp']); pg=pdf_period(state['global'])
                if ps[0] and state['sadt']:
                    sadt=slice_period(sadt,*ps)
                state['sadt_data']=sadt
                if ps[0] and pg[0] and ps!=pg:
                    messagebox.showwarning('YUPI',f'Períodos diferentes detectados:\nSIRESP: {ps[0]} a {ps[1]}\nGlobal: {pg[0]} a {pg[1]}\n\nA conferência foi interrompida para evitar um resultado incorreto.')
                    return
                out=[];cfg=self.config.get('exams',{})
                for rr in base:
                    ex=_norm_exam(rr['exame']);rule=cfg.get(ex,{'active':True,'scope':{'siresp':'ambos','sadt':'ambos','global':'total'},'scope_strategy':'direct','sigtap':[]})
                    if not rule.get('active',True):continue
                    sd=sadt.get(ex) or next((vv for kk,vv in sadt.items() if _norm_exam(kk)==ex),None)
                    rr['sadt']=sd
                    mult=int(rr.get('multiplicador',1) or 1); sr={'externo':int(rr.get('externo',0) or 0)*mult,'interno':int(rr.get('interno',0) or 0)*mult,'total':(int(rr.get('externo',0) or 0)+int(rr.get('interno',0) or 0)+int(rr.get('direto',0) or 0))*mult}
                    global_value=state['manual'].get(ex, rr.get('global',0))
                    rr['scope_validation']=validate_scope(ex,sr,global_value,sd,rule)
                    if ex in state['manual']:
                        rr['manual_override']=state['manual'][ex]
                        rr['scope_validation']={**rr['scope_validation'],'status':'MANUAL','global':state['manual'][ex],'explanation':'Quantidade do Global informada manualmente nesta conferência.'}
                    out.append(rr)
                state['results']=out;paint();total=len(out)
                zero=sum(1 for rr in out if int((rr.get('scope_validation') or {}).get('siresp_scope',rr.get('siresp',0)) or 0)==0 and int((rr.get('scope_validation') or {}).get('global',rr.get('global',0)) or 0)==0)
                ok=sum(1 for rr in out if (rr.get('scope_validation') or {}).get('status')=='OK' and not (int((rr.get('scope_validation') or {}).get('siresp_scope',0) or 0)==0 and int((rr.get('scope_validation') or {}).get('global',0) or 0)==0))
                div=max(0,total-ok-zero);conf=round(ok/total*100,1) if total else 0
                for lbl,val in zip(ml,[total,ok,div,len(state['resolved']),zero,f'{conf}%']):lbl.configure(text=str(val))
                append_history('Exames','Concluída',{'exames':total,'divergencias':div})
                if tree.get_children():tree.selection_set(tree.get_children()[0]);render_detail()
            except Exception as e:messagebox.showerror('YUPI',str(e))

        if state.get('results'):
            paint()
            total=len(state['results'])
            ok=zero=0
            for rr in state['results']:
                v=rr.get('scope_validation') or {}; ss=int(v.get('siresp_scope',rr.get('siresp',0)) or 0); gg=int(state['manual'].get(rr.get('exame'),v.get('global',rr.get('global',0))) or 0)
                if ss==0 and gg==0 and v.get('status')!='ESCOPO_PENDENTE': zero+=1
                elif v.get('status')=='OK': ok+=1
            div=max(0,total-ok-zero); conf=round(ok/total*100,1) if total else 0
            for lbl,val in zip(ml,[total,ok,div,len(state['resolved']),zero,f'{conf}%']): lbl.configure(text=str(val))
            if tree.get_children(): tree.selection_set(tree.get_children()[0]); render_detail()

    # ---------- SADT ----------
    def show_sadt(self):
        # Usa o layout SADT revisado (tabela + detalhes + movimento por dia).
        ms=self.module_state.get('sadt',{})
        ss=self.session.setdefault('sadt',{'path':'','data':{}})
        if ms.get('path') and not ss.get('path'):
            ss['path']=ms.get('path'); ss['data']=ms.get('data',{})
        result=YupiV6.show_sadt(self)
        # O objeto é compartilhado durante a sessão; ao voltar para a tela os dados permanecem.
        self.module_state['sadt']=self.session['sadt']
        if self.session['sadt'].get('path'):
            self.session_files['SADT Excel']=self.session['sadt']['path']
        return result

    # ---------- MENSAL ----------
    def show_monthly(self):
        self._clear('Mensal');self._page_header('Conferência Mensal','Acompanhe o mês por dia. Clique em uma data para ver arquivos, status e resultados.','📅')
        state=self.module_state['monthly']
        top=ctk.CTkFrame(self.content,fg_color='transparent');top.pack(fill='x',padx=28,pady=(0,10));info=ctk.CTkLabel(top,text=(f"{state['folder']} • {len(state['files'])} arquivo(s)" if state.get('folder') else 'Nenhuma pasta selecionada'),font=('Segoe UI',9),text_color=TEXT if state.get('folder') else MUTED);info.pack(side='left')
        body=ctk.CTkFrame(self.content,fg_color='transparent');body.pack(fill='both',expand=True,padx=28,pady=(0,18));body.grid_columnconfigure(0,weight=3);body.grid_columnconfigure(1,weight=1);body.grid_rowconfigure(0,weight=1)
        cal=self._section(body);cal.grid(row=0,column=0,sticky='nsew',padx=(0,7));detail=self._section(body);detail.grid(row=0,column=1,sticky='nsew',padx=(7,0));dframe=ctk.CTkFrame(detail,fg_color='transparent');dframe.pack(fill='both',expand=True,padx=14,pady=14)
        def render_detail(dt):
            state['selected']=dt
            for w in dframe.winfo_children():w.destroy();
            ctk.CTkLabel(dframe,text=self._data_extenso_pt(dt),font=('Segoe UI',17,'bold'),text_color=TEXT).pack(anchor='w')
            dayfiles=[f for f in state['files'] if str(f.get('date','')).startswith(dt.strftime('%Y-%m-%d')) or str(f.get('date','')).startswith(dt.strftime('%d/%m/%Y'))]
            ctk.CTkLabel(dframe,text=f'{len(dayfiles)} arquivo(s) detectado(s)',font=('Segoe UI',9),text_color=MUTED).pack(anchor='w',pady=(3,10))
            for f in dayfiles[:10]:
                r=ctk.CTkFrame(dframe,fg_color=PANEL2,corner_radius=9);r.pack(fill='x',pady=3);ctk.CTkLabel(r,text=f"{f.get('type','')} • {f.get('name','')}",font=('Segoe UI',8),text_color=TEXT).pack(anchor='w',padx=9,pady=7)
            ctk.CTkButton(dframe,text='Analisar período completo',fg_color=PURPLE,command=analyze).pack(fill='x',pady=(16,0))
        def render_cal():
            for w in cal.winfo_children():w.destroy();m=state['month'];h=ctk.CTkFrame(cal,fg_color='transparent');h.pack(fill='x',padx=14,pady=(12,6));ctk.CTkLabel(h,text=f"{self._MESES_PT.get(m.month)}/{m.year}",font=('Segoe UI',18,'bold'),text_color=TEXT).pack(side='left')
            g=ctk.CTkFrame(cal,fg_color='transparent');g.pack(fill='both',expand=True,padx=12,pady=(4,12));
            for j,d in enumerate(['Seg','Ter','Qua','Qui','Sex','Sáb','Dom']):ctk.CTkLabel(g,text=d,font=('Segoe UI',9,'bold'),text_color=MUTED).grid(row=0,column=j,sticky='ew');g.grid_columnconfigure(j,weight=1)
            for i,wk in enumerate(calendar.monthcalendar(m.year,m.month),1):
                for j,d in enumerate(wk):
                    if not d:continue
                    dt=date(m.year,m.month,d);cnt=sum(1 for f in state['files'] if str(f.get('date','')).startswith(dt.strftime('%Y-%m-%d')) or str(f.get('date','')).startswith(dt.strftime('%d/%m/%Y')));col=TEAL if cnt>=2 else ORANGE if cnt==1 else SLATE
                    ctk.CTkButton(g,text=f'{d}\n{cnt} arq.',height=65,fg_color='#0C1A2D',hover_color='#182C49',border_width=1,border_color=PURPLE if dt==state['selected'] else BORDER,text_color=TEXT,command=lambda x=dt:(render_detail(x),render_cal())).grid(row=i,column=j,sticky='nsew',padx=2,pady=2)
        def choose_folder():
            p=filedialog.askdirectory();
            if not p:return
            state['folder']=p;state['files']=detect_files(p);info.configure(text=f'{p} • {len(state["files"])} arquivo(s)',text_color=TEXT);render_cal();render_detail(state['selected'])
        def analyze():
            if not state['folder']:messagebox.showwarning('YUPI','Selecione uma pasta.');return
            try:
                data=analyze_exam_month(state['folder']);messagebox.showinfo('YUPI',f"Fechamento concluído.\nPares processados: {data['pairs']}\nExames: {len(data['results'])}\nSem Global: {data['unmatched_siresp']}\nSem SIRESP: {data['unmatched_global']}")
                append_history('Mensal','Concluída',{'pares':data['pairs'],'exames':len(data['results'])})
            except Exception as e:messagebox.showerror('YUPI',str(e))
        ctk.CTkButton(top,text='Selecionar pasta',fg_color=PANEL2,text_color='#B99DFF',command=choose_folder).pack(side='right',padx=5);ctk.CTkButton(top,text='Analisar mês',fg_color=PURPLE,command=analyze).pack(side='right',padx=5);render_cal();render_detail(state['selected'])

    # ---------- PRESENÇA ----------
    def show_presence(self):
        self._clear('Presença');self._page_header('Controle de Presença','Compare a Agenda SIRESP com o realizado no Analítico. Identifique faltas, extras e divergências.','👥')
        state=self.module_state['presence'];top=ctk.CTkFrame(self.content,fg_color='transparent');top.pack(fill='x',padx=28,pady=(0,8));labels={}
        for k,t in [('agenda','Agenda SIRESP'),('analitico','Analítico')]:
            f=self._section(top);f.pack(side='left',fill='x',expand=True,padx=4);ctk.CTkLabel(f,text=t,font=('Segoe UI',10,'bold'),text_color='#B99DFF').pack(anchor='w',padx=12,pady=(10,0));labels[k]=ctk.CTkLabel(f,text=self._safe_name(state.get(k,'')),font=('Segoe UI',8),text_color=TEXT if state.get(k) else MUTED);labels[k].pack(anchor='w',padx=12,pady=(3,8))
            def ch(x=k,title=t):
                p=filedialog.askopenfilename(filetypes=[('PDF','*.pdf')])
                if p:
                    state[x]=p; self.session_files[title]=p
                    labels[x].configure(text=Path(p).name,text_color=TEXT)
            ctk.CTkButton(f,text='Selecionar',height=27,fg_color=PANEL2,text_color='#B99DFF',command=ch).pack(anchor='e',padx=12,pady=(0,9))
        ctk.CTkButton(top,text='▶ Conferir',width=145,height=66,fg_color=PURPLE,command=lambda:run()).pack(side='left',padx=6)
        kpis=ctk.CTkFrame(self.content,fg_color='transparent');kpis.pack(fill='x',padx=28,pady=(0,9));kl=[]
        for v,l,c in [('0','Agendados',ACCENT2),('0','Compareceram',GREEN),('0','Não encontrados',RED),('0','Divergências',ORANGE),('0','Especialidades',PURPLE)]:ca=self._metric(kpis,v,l,c);ca.pack(side='left',fill='x',expand=True,padx=4);kl.append(ca.winfo_children()[0])
        body=ctk.CTkFrame(self.content,fg_color='transparent');body.pack(fill='both',expand=True,padx=28,pady=(0,18));body.grid_columnconfigure(0,weight=3);body.grid_columnconfigure(1,weight=1);body.grid_rowconfigure(0,weight=1)
        left=self._section(body);left.grid(row=0,column=0,sticky='nsew',padx=(0,7));right=self._section(body);right.grid(row=0,column=1,sticky='nsew',padx=(7,0))
        tools=ctk.CTkFrame(left,fg_color='transparent');tools.pack(fill='x',padx=12,pady=(12,4));search=ctk.CTkEntry(tools,placeholder_text='Nome, prontuário ou código...');search.pack(side='left',fill='x',expand=True);spec=ctk.StringVar(value='Todas');combo=ctk.CTkComboBox(tools,variable=spec,values=['Todas'],width=190,command=lambda _:paint());combo.pack(side='left',padx=6)
        ff,tree=_tree(left,[('p','Paciente'),('pr','Prontuário'),('sp','Especialidade'),('c','Código'),('q','Qtd.'),('st','Situação')],{'p':250,'pr':100,'sp':180,'c':110,'q':55,'st':150},15);ff.pack(fill='both',expand=True,padx=4,pady=(0,8))
        detail=ctk.CTkFrame(right,fg_color='transparent');detail.pack(fill='both',expand=True,padx=14,pady=14)
        def render_detail(_=None):
            for w in detail.winfo_children():w.destroy();sel=tree.selection();
            if not sel:ctk.CTkLabel(detail,text='Selecione um paciente',text_color=MUTED).pack(anchor='w');return
            vals=tree.item(sel[0],'values');p,pr,sp,c,q,st=vals;ctk.CTkLabel(detail,text=p or 'Paciente',font=('Segoe UI',18,'bold'),text_color=TEXT).pack(anchor='w');ctk.CTkLabel(detail,text='Prontuário: '+str(pr),font=('Segoe UI',9),text_color=MUTED).pack(anchor='w')
            for a,b in [('Especialidade',sp),('Código',c or '—'),('Quantidade',q),('Situação',st)]:r=ctk.CTkFrame(detail,fg_color=PANEL2,corner_radius=9);r.pack(fill='x',pady=3);ctk.CTkLabel(r,text=a,font=('Segoe UI',9),text_color=MUTED).pack(side='left',padx=9,pady=7);ctk.CTkLabel(r,text=str(b),font=('Segoe UI',9,'bold'),text_color=TEXT).pack(side='right',padx=9)
            ctk.CTkLabel(detail,text='Observações',font=('Segoe UI',11,'bold'),text_color=TEXT).pack(anchor='w',pady=(12,4));ctk.CTkTextbox(detail,height=95,fg_color='#0A1727',border_width=1,border_color=BORDER).pack(fill='x')
        tree.bind('<<TreeviewSelect>>',render_detail)
        def paint():
            q=search.get().upper().strip();sfilter=spec.get();
            for x in tree.get_children():tree.delete(x)
            for r in state['rows']:
                if sfilter!='Todas' and r.get('especialidade')!=sfilter:continue
                blob=f"{r.get('paciente','')} {r.get('prontuario','')} {r.get('codigo','')}".upper();
                if q and q not in blob:continue
                st={'OK':'🟢 Compareceu','COMPARECEU':'🟢 Compareceu','NAO_ENCONTRADO':'🔴 Não encontrado','CODIGO_NAO_MAPEADO':'🟡 Código não mapeado','CODIGO_DIFERENTE':'🟡 Código diferente','DUPLICIDADE':'🟠 Duplicidade','ACIMA_PERMITIDO':'🔴 Acima do permitido','ENCAIXE_EXTRA':'🔵 Encaixe / Extra'}.get(r.get('resultado'),r.get('resultado'))
                tree.insert('', 'end',values=(r.get('paciente',''),r.get('prontuario',''),r.get('especialidade',''),r.get('codigo',''),r.get('qtde',0),st),tags=('ok' if r.get('resultado') in ('OK','COMPARECEU') else 'warn' if r.get('resultado') in ('CODIGO_NAO_MAPEADO','CODIGO_DIFERENTE','ENCAIXE_EXTRA','DUPLICIDADE') else 'error',))
        search.bind('<KeyRelease>',lambda e:paint())
        def run():
            if not state['agenda'] or not state['analitico']:
                messagebox.showwarning('YUPI','Selecione os dois PDFs.'); return
            try:
                pa=pdf_period(state['agenda']); pn=pdf_period(state['analitico'])
                if pa[0] and pn[0] and pa!=pn:
                    messagebox.showwarning('YUPI',
                        f'Os arquivos são de períodos diferentes.\n\nAgenda SIRESP: {pa[0]} a {pa[1]}\nAnalítico: {pn[0]} a {pn[1]}\n\nSelecione arquivos do mesmo dia/período para não marcar pacientes incorretamente como ausentes.')
                    return
                a=read_siresp_agenda(state['agenda']); n=read_analitico_people(state['analitico'])
                state['agenda_rows']=a; state['analitico_rows']=n
                if not a:
                    messagebox.showwarning('YUPI','Nenhum paciente foi identificado na Agenda SIRESP.'); return
                if not n:
                    messagebox.showwarning('YUPI','Nenhum lançamento foi identificado no Analítico.'); return
                state['rows']=compare_presence(a,n,self.config.get('specialties',{}))
                specs=sorted({r.get('especialidade','') for r in state['rows'] if r.get('especialidade')})
                combo.configure(values=['Todas']+specs); paint()
                ok=sum(1 for r in state['rows'] if r.get('resultado') in ('OK','COMPARECEU'))
                miss=sum(1 for r in state['rows'] if r.get('resultado')=='NAO_ENCONTRADO')
                extras=sum(1 for r in state['rows'] if r.get('resultado')=='ENCAIXE_EXTRA')
                div=sum(1 for r in state['rows'] if r.get('resultado') not in ('OK','COMPARECEU','NAO_ENCONTRADO','ENCAIXE_EXTRA'))
                agendados=len(a)
                for lbl,val in zip(kl,[agendados,ok,miss,div,len(specs)]): lbl.configure(text=str(val))
                append_history('Presença','Concluída',{'agenda':agendados,'compareceram':ok,'nao_encontrados':miss,'extras':extras,'divergencias':div})
                if tree.get_children():
                    tree.selection_set(tree.get_children()[0]); render_detail()
            except Exception as e:
                messagebox.showerror('YUPI',f'Erro na conferência de presença:\n\n{e}')

        if state.get('rows'):
            specs=sorted({r.get('especialidade','') for r in state['rows'] if r.get('especialidade')}); combo.configure(values=['Todas']+specs); paint()
            ok=sum(1 for r in state['rows'] if r.get('resultado') in ('OK','COMPARECEU')); miss=sum(1 for r in state['rows'] if r.get('resultado')=='NAO_ENCONTRADO'); div=sum(1 for r in state['rows'] if r.get('resultado') not in ('OK','COMPARECEU','NAO_ENCONTRADO','ENCAIXE_EXTRA'))
            agendados=len(state.get('agenda_rows') or []); 
            for lbl,val in zip(kl,[agendados,ok,miss,div,len(specs)]): lbl.configure(text=str(val))
            if tree.get_children(): tree.selection_set(tree.get_children()[0]); render_detail()

    # ---------- PERFIL / MOTOR SALUTEM ----------
    def _edit_operator(self):
        name=simpledialog.askstring('Operador YUPI','Nome de quem está usando o sistema:',initialvalue=self.config.get('operator_name','Operador'),parent=self.root)
        if not name:return
        unit=simpledialog.askstring('Operador YUPI','Unidade / setor:',initialvalue=self.config.get('operator_unit','Unidade demonstrativa'),parent=self.root)
        if unit is None:return
        self.config['operator_name']=name.strip(); self.config['operator_unit']=unit.strip(); save_config(self.config)
        initials=''.join(x[0] for x in name.split()[:2]).upper() or 'YU'
        self.operator_initials.configure(text=initials); self.operator_label.configure(text=f'{name.strip()}\n{unit.strip()}')

    def show_results(self):
        self._clear('Resultados');self._page_header('Resultados e Histórico','Consulte todas as execuções registradas, filtre por módulo e exporte quando precisar.','📊')
        data=load_history();top=ctk.CTkFrame(self.content,fg_color='transparent');top.pack(fill='x',padx=28,pady=(0,8));module=ctk.StringVar(value='Todos');mods=['Todos']+sorted({h.get('module','') for h in data if h.get('module')});ctk.CTkComboBox(top,variable=module,values=mods,width=180,command=lambda _:paint()).pack(side='left');search=ctk.CTkEntry(top,placeholder_text='Pesquisar...');search.pack(side='left',fill='x',expand=True,padx=8)
        ff,tree=_tree(self.content,[('at','Data/Hora'),('m','Módulo'),('r','Resultado'),('d','Detalhes')],{'at':180,'m':150,'r':160,'d':800},19);ff.pack(fill='both',expand=True,padx=28,pady=(4,18))
        def paint():
            q=search.get().upper().strip();m=module.get();
            for x in tree.get_children():tree.delete(x)
            for h in data:
                if m!='Todos' and h.get('module')!=m:continue
                blob=str(h).upper();
                if q and q not in blob:continue
                tree.insert('', 'end',values=(h.get('at','').replace('T',' '),h.get('module',''),h.get('result',''),str(h.get('details',{}))))
        search.bind('<KeyRelease>',lambda e:paint());paint()
        def export():
            p=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV','*.csv')],initialfile='YUPI_v654_historico.csv');
            if not p:return
            with open(p,'w',newline='',encoding='utf-8-sig') as f:
                w=csv.writer(f,delimiter=';');w.writerow(['Data/Hora','Módulo','Resultado','Detalhes']);
                for h in data:w.writerow([h.get('at'),h.get('module'),h.get('result'),h.get('details')])
            messagebox.showinfo('YUPI','Histórico exportado.')
        ctk.CTkButton(top,text='Exportar CSV',fg_color=PURPLE,command=export).pack(side='right')

    # ---------- CONFIGURAÇÕES ----------
    def show_settings(self):
        self._clear('Configurações');self._page_header('Configurações','Gerencie escopos, regras de exames e códigos permitidos por especialidade.','⚙')
        tabs=ctk.CTkTabview(self.content,fg_color=PANEL,segmented_button_selected_color=PURPLE,segmented_button_selected_hover_color=PURPLE_DARK);tabs.pack(fill='both',expand=True,padx=28,pady=(0,20));te=tabs.add('Exames e Escopo');ts=tabs.add('Códigos por Especialidade');self._settings_exams(te);self._settings_specialties(ts)



    # ---------- PROTEÇÃO CONTRA INTERFACE LEGADA ----------
    def _open_legacy_consultas(self):
        """Compatibilidade: qualquer atalho antigo passa a abrir a tela integrada."""
        self.show_consultas()

    def _exam_find_result(self, exam):
        state=self.module_state['exames']
        return next((r for r in state.get('results',[]) if r.get('exame')==exam),None)

    def _exam_selected_global_rows(self, exam, result):
        state=self.module_state['exames']
        selected=set(str(x).strip().upper() for x in carregar_mapeamentos().get(exam,[]))
        if not selected:
            for d in result.get('detalhes_global',[]) or []:
                n=str(d.get('exame','')).strip().upper()
                if n:selected.add(n)
        rows=[]
        seen=set()
        for rec in state.get('global_records',[]):
            exact=str(rec.get('nome_exato','')).strip().upper()
            canon=str(rec.get('nome_normalizado','')).strip().upper()
            original=str(rec.get('nome_original') or exact).strip()
            if exact in selected or canon in selected or original.upper() in selected:
                key=(original.upper(),str(rec.get('codigo','')).strip())
                if key in seen: continue
                seen.add(key)
                rows.append((original,rec.get('codigo','') or '—',int(rec.get('quantidade',0) or 0),exact or original.upper()))
        return rows

    def _compute_exames_results(self, state):
        if not state.get('siresp') or not state.get('global'):
            messagebox.showwarning('YUPI','Selecione SIRESP e Global.')
            return False
        try:
            sdata=ler_siresp_exames(state['siresp'])
            g,records,raw=ler_faturamento_exames_detalhado(state['global'])
            state['global_records']=records; state['global_raw']=raw
            base=comparar_exames(sdata,g,carregar_mapeamentos(),raw)
            sadt=read_sadt(state['sadt']) if state.get('sadt') else {}
            ps=pdf_period(state['siresp']); pg=pdf_period(state['global'])
            if ps[0] and state.get('sadt'):
                sadt=slice_period(sadt,*ps)
            state['sadt_data']=sadt
            if ps[0] and pg[0] and ps!=pg:
                messagebox.showwarning('YUPI',f'Períodos diferentes detectados:\nSIRESP: {ps[0]} a {ps[1]}\nGlobal: {pg[0]} a {pg[1]}\n\nA conferência foi interrompida para evitar um resultado incorreto.')
                return False
            out=[];cfg=self.config.get('exams',{})
            for rr in base:
                ex=_norm_exam(rr['exame'])
                rule=cfg.get(ex,{'active':True,'scope':{'siresp':'ambos','sadt':'ambos','global':'total'},'scope_strategy':'direct','sigtap':[]})
                if not rule.get('active',True):continue
                sd=sadt.get(ex) or next((vv for kk,vv in sadt.items() if _norm_exam(kk)==ex),None)
                rr['sadt']=sd
                mult=int(rr.get('multiplicador',1) or 1)
                sr={'externo':int(rr.get('externo',0) or 0)*mult,'interno':int(rr.get('interno',0) or 0)*mult,'total':(int(rr.get('externo',0) or 0)+int(rr.get('interno',0) or 0)+int(rr.get('direto',0) or 0))*mult}
                global_value=state.get('manual',{}).get(ex, rr.get('global',0))
                rr['scope_validation']=validate_scope(ex,sr,global_value,sd,rule)
                if ex in state.get('manual',{}):
                    rr['manual_override']=state['manual'][ex]
                    rr['scope_validation']={**rr['scope_validation'],'status':'MANUAL','global':state['manual'][ex],'explanation':'Quantidade do Global informada manualmente nesta conferência.'}
                out.append(rr)
            state['results']=out
            append_history('Exames','Concluída',{'exames':len(out),'divergencias':sum(1 for r in out if (r.get('scope_validation') or {}).get('status') not in ('OK',))})
            return True
        except Exception as e:
            messagebox.showerror('YUPI',f'Erro na conferência de exames:\n\n{e}')
            return False

    # ---------- EXAMES v6.5.4: LISTA LIMPA + ANÁLISE COMPLETA ----------
    def show_exames(self):
        self._clear('Exames')
        self._page_header('Conferência de Exames','Compare SIRESP, Global e SADT. Selecione um exame e abra a análise completa.','🗂')
        state=self.module_state['exames']
        if not state.get('sadt') and self.session.get('sadt',{}).get('path'):
            state['sadt']=self.session['sadt']['path']
        files=ctk.CTkFrame(self.content,fg_color='transparent');files.pack(fill='x',padx=28,pady=(0,10));lbls={}
        for k,t in [('siresp','SIRESP PDF'),('global','Global PDF'),('sadt','SADT Excel')]:
            f=self._section(files);f.pack(side='left',fill='x',expand=True,padx=4)
            ctk.CTkLabel(f,text=t,font=('Segoe UI',10,'bold'),text_color='#B99DFF').pack(anchor='w',padx=12,pady=(10,0))
            lbls[k]=ctk.CTkLabel(f,text=self._safe_name(state.get(k,'')),font=('Segoe UI',8),text_color=TEXT if state.get(k) else MUTED);lbls[k].pack(anchor='w',padx=12,pady=(3,8))
            def ch(x=k,tit=t):
                pp=filedialog.askopenfilename(filetypes=[('Excel','*.xlsx *.xlsm')] if x=='sadt' else [('PDF','*.pdf')])
                if pp:
                    state[x]=pp;self.session_files[tit]=pp;lbls[x].configure(text=Path(pp).name,text_color=TEXT)
                    state['results']=[];state['resolved'].clear()
                    if x!='global':state['manual'].clear()
                    paint()
            ctk.CTkButton(f,text='Selecionar',height=27,fg_color=PANEL2,text_color='#B99DFF',command=ch).pack(anchor='e',padx=12,pady=(0,9))
        ctk.CTkButton(files,text='▶ Conferir',width=145,height=69,fg_color=PURPLE,command=lambda:(self._compute_exames_results(state) and paint())).pack(side='left',padx=6)

        metrics=ctk.CTkFrame(self.content,fg_color='transparent');metrics.pack(fill='x',padx=28,pady=(0,10));ml=[]
        for v,l,c in [('0','Exames',PURPLE),('0','OK',GREEN),('0','Divergências',RED),('0','Resolvidos',ORANGE),('0','Zerados',SLATE),('0%','Conformidade',ACCENT2)]:
            ca=self._metric(metrics,v,l,c);ca.pack(side='left',fill='x',expand=True,padx=3);ml.append(ca.winfo_children()[0])

        body=ctk.CTkFrame(self.content,fg_color='transparent');body.pack(fill='both',expand=True,padx=28,pady=(0,18));body.grid_columnconfigure(0,weight=8);body.grid_columnconfigure(1,weight=4);body.grid_rowconfigure(0,weight=1)
        left=self._section(body);left.grid(row=0,column=0,sticky='nsew',padx=(0,7));right=self._section(body);right.grid(row=0,column=1,sticky='nsew',padx=(7,0))
        toolbar=ctk.CTkFrame(left,fg_color='transparent');toolbar.pack(fill='x',padx=12,pady=(12,4))
        search=ctk.CTkEntry(toolbar,placeholder_text='Pesquisar exame...');search.pack(side='left',fill='x',expand=True)
        status=ctk.StringVar(value='Todos');ctk.CTkComboBox(toolbar,variable=status,values=['Todos','OK','Divergência','Resolvidos','Zerado'],width=145,command=lambda _:paint()).pack(side='left',padx=6)
        ff,tree=_tree(left,[('exam','Exame'),('s','SIRESP'),('sa','SADT'),('g','Global'),('d','Dif.'),('st','Status')],{'exam':300,'s':80,'sa':80,'g':80,'d':70,'st':155},17);ff.pack(fill='both',expand=True,padx=4,pady=(0,8))
        preview=ctk.CTkFrame(right,fg_color='transparent');preview.pack(fill='both',expand=True,padx=14,pady=14)

        def row_data(r):
            ex=r['exame'];v=r.get('scope_validation',{});sd=r.get('sadt') or {};ss=int(v.get('siresp_scope',r.get('siresp',0)) or 0);gg=int(state.get('manual',{}).get(ex,v.get('global',r.get('global',0))) or 0)
            dd=v.get('difference')
            if dd is None and v.get('status')!='ESCOPO_PENDENTE':dd=ss-gg
            if ss==0 and gg==0 and v.get('status')!='ESCOPO_PENDENTE':raw='ZERADO'
            elif v.get('status')=='OK':raw='OK'
            elif v.get('status')=='ESCOPO_PENDENTE':raw='REQUER SADT'
            else:raw='DIVERGÊNCIA'
            return ex,v,sd,ss,gg,dd,raw

        def render_preview(_=None):
            for w in preview.winfo_children():w.destroy()
            sel=tree.selection()
            if not sel:
                ctk.CTkLabel(preview,text='Selecione um exame.',font=('Segoe UI',14,'bold'),text_color=MUTED).pack(anchor='w');return
            ex=tree.item(sel[0],'values')[0];r=self._exam_find_result(ex) or {};ex,v,sd,ss,gg,dd,raw=row_data(r)
            ctk.CTkLabel(preview,text=ex,font=('Segoe UI',20,'bold'),text_color=TEXT,wraplength=380,justify='left').pack(anchor='w')
            badge='RESOLVIDO' if ex in state['resolved'] else raw
            ctk.CTkLabel(preview,text=badge,font=('Segoe UI',9,'bold'),text_color=GREEN if badge in ('OK','RESOLVIDO') else (YELLOW if badge=='REQUER SADT' else RED),fg_color='#10243A',corner_radius=8).pack(anchor='w',pady=(6,12),ipadx=8,ipady=4)
            grid=ctk.CTkFrame(preview,fg_color='transparent');grid.pack(fill='x')
            for val,lab,col in [(ss,'SIRESP',ACCENT2),(sd.get('total','—'),'SADT',TEAL),(gg,'Global',ORANGE),(dd if dd is not None else '—','Diferença',GREEN if dd in (0,None) else RED)]:
                c=self._metric(grid,val,lab,col);c.pack(side='left',fill='x',expand=True,padx=2)
            ctk.CTkLabel(preview,text='A análise completa abre nesta mesma tela, sem janelas antigas.',wraplength=380,justify='left',font=('Segoe UI',9),text_color=MUTED).pack(anchor='w',pady=(16,8))
            ctk.CTkButton(preview,text='Abrir análise completa →',height=44,fg_color=PURPLE,command=lambda e=ex:self._show_exam_workspace(e)).pack(fill='x',pady=4)
            ctk.CTkButton(preview,text='Procedimentos / SIGTAP',height=38,fg_color=PANEL2,text_color='#B99DFF',command=lambda e=ex:self._show_exam_workspace(e,'Procedimentos')).pack(fill='x',pady=4)

        def paint():
            q=search.get().upper().strip();flt=status.get()
            for x in tree.get_children():tree.delete(x)
            total=ok=zero=div=0
            for r in state.get('results',[]):
                ex,v,sd,ss,gg,dd,raw=row_data(r);resolved=ex in state['resolved']
                total+=1
                if raw=='ZERADO':zero+=1
                elif raw=='OK':ok+=1
                else:div+=1
                if q and q not in ex.upper():continue
                if flt=='OK' and raw!='OK':continue
                if flt=='Divergência' and (raw not in ('DIVERGÊNCIA','REQUER SADT') or resolved):continue
                if flt=='Resolvidos' and not resolved:continue
                if flt=='Zerado' and raw!='ZERADO':continue
                label='🟣 RESOLVIDO' if resolved else ('🟢 OK' if raw=='OK' else '⚪ ZERADO' if raw=='ZERADO' else '🟡 REQUER SADT' if raw=='REQUER SADT' else '🔴 DIVERGÊNCIA')
                tree.insert('', 'end',values=(ex,ss,sd.get('total','—'),gg,dd if dd is not None else '—',label),tags=('ok' if raw=='OK' or resolved else 'muted' if raw=='ZERADO' else 'error',))
            conf=round(ok/total*100,1) if total else 0
            for lbl,val in zip(ml,[total,ok,div,len(state['resolved']),zero,f'{conf}%']):lbl.configure(text=str(val))
            if tree.get_children():
                tree.selection_set(tree.get_children()[0]);render_preview()
            else:render_preview()
        search.bind('<KeyRelease>',lambda e:paint());tree.bind('<<TreeviewSelect>>',render_preview);tree.bind('<Double-1>',lambda e:(tree.selection() and self._show_exam_workspace(tree.item(tree.selection()[0],'values')[0])))
        paint()

    def _show_exam_workspace(self, exam, initial_tab='Resumo'):
        """Análise completa do exame em uma única tela, sem painel espremido ou popup legado."""
        state=self.module_state['exames'];r=self._exam_find_result(exam)
        if not r:
            messagebox.showwarning('YUPI','Faça a conferência antes de abrir a análise completa.');return
        self._clear('Exames')
        v=r.get('scope_validation',{});sd=r.get('sadt') or {};sval=int(v.get('siresp_scope',r.get('siresp',0)) or 0);gval=int(state.get('manual',{}).get(exam,v.get('global',r.get('global',0))) or 0);dval=v.get('difference')
        if dval is None and v.get('status')!='ESCOPO_PENDENTE':dval=sval-gval
        top=self._page_header(exam,'Análise completa do exame • composição, movimento diário, regras e auditoria.','🔎')
        ctk.CTkButton(top,text='← Voltar para Exames',width=160,fg_color=PANEL2,text_color='#B99DFF',command=self.show_exames).pack(side='right',padx=8,pady=8)
        badge='RESOLVIDO' if exam in state['resolved'] else ('REQUER SADT' if v.get('status')=='ESCOPO_PENDENTE' else ('OK' if v.get('status')=='OK' else 'DIVERGÊNCIA'))
        ctk.CTkLabel(top,text=badge,font=('Segoe UI',10,'bold'),text_color=GREEN if badge in ('OK','RESOLVIDO') else (YELLOW if badge=='REQUER SADT' else RED),fg_color='#10243A',corner_radius=9).pack(side='right',padx=4,ipadx=10,ipady=5)
        cards=ctk.CTkFrame(self.content,fg_color='transparent');cards.pack(fill='x',padx=28,pady=(0,10))
        for val,lab,col,sub in [(sval,'SIRESP',ACCENT2,'Quantidade no recorte configurado'),(sd.get('total','—'),'SADT',TEAL,'Quantidade na planilha SADT'),(gval,'Global',ORANGE,'Quantidade da composição Global'),(dval if dval is not None else '—','Diferença',GREEN if dval in (0,None) else RED,'Resultado da regra atual')]:
            c=self._metric(cards,val,lab,col,sub);c.pack(side='left',fill='x',expand=True,padx=4)
        tabs=ctk.CTkTabview(self.content,fg_color=PANEL,corner_radius=16,border_width=1,border_color=BORDER,segmented_button_selected_color=PURPLE,segmented_button_selected_hover_color=PURPLE_DARK)
        tabs.pack(fill='both',expand=True,padx=28,pady=(0,18))
        tabnames=['Resumo','Procedimentos','Por dia','Comparativo','Regras','Auditoria']
        pages={name:tabs.add(name) for name in tabnames}
        try:tabs.set(initial_tab if initial_tab in tabnames else 'Resumo')
        except Exception:pass
        # Resumo
        t=pages['Resumo'];left=ctk.CTkFrame(t,fg_color='transparent');left.pack(side='left',fill='both',expand=True,padx=(12,6),pady=12);right=ctk.CTkFrame(t,fg_color=PANEL2,corner_radius=12);right.pack(side='right',fill='y',padx=(6,12),pady=12)
        ctk.CTkLabel(left,text='Resumo do período',font=('Segoe UI',16,'bold'),text_color=TEXT).pack(anchor='w',pady=(0,8))
        for a,b in [('Aba no SADT',sd.get('sheet','—')),('Interno SADT',sd.get('interno','—')),('Externo SADT',sd.get('externo','—')),('Status da regra',badge),('Quantidade permitida',((self.config.get('exams',{}).get(exam,{}).get('sigtap') or [{}])[0].get('max_qty',1) if self.config.get('exams',{}).get(exam,{}).get('sigtap') else 1))]:
            rr=ctk.CTkFrame(left,fg_color='#0A1727',corner_radius=9);rr.pack(fill='x',pady=3);ctk.CTkLabel(rr,text=a,text_color=MUTED,font=('Segoe UI',9)).pack(side='left',padx=10,pady=8);ctk.CTkLabel(rr,text=str(b),text_color=TEXT,font=('Segoe UI',9,'bold')).pack(side='right',padx=10)
        ctk.CTkLabel(right,text='Ações rápidas',font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',padx=14,pady=(14,8))
        ctk.CTkButton(right,text='+ Adicionar procedimento',width=220,fg_color=PURPLE,command=lambda:tabs.set('Procedimentos')).pack(padx=14,pady=4)
        ctk.CTkButton(right,text='Editar quantidade manual',width=220,fg_color=PANEL,text_color='#B99DFF',command=lambda:manual_qty()).pack(padx=14,pady=4)
        ctk.CTkButton(right,text='Abrir regras',width=220,fg_color=PANEL,text_color='#B99DFF',command=lambda:tabs.set('Regras')).pack(padx=14,pady=4)
        # Procedimentos
        tp=pages['Procedimentos']; tp.grid_columnconfigure(0,weight=3);tp.grid_columnconfigure(1,weight=2);tp.grid_rowconfigure(0,weight=1)
        pleft=ctk.CTkFrame(tp,fg_color='transparent');pleft.grid(row=0,column=0,sticky='nsew',padx=(12,6),pady=12);pright=ctk.CTkFrame(tp,fg_color=PANEL2,corner_radius=12);pright.grid(row=0,column=1,sticky='nsew',padx=(6,12),pady=12)
        ctk.CTkLabel(pleft,text='Procedimentos usados neste exame',font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',pady=(0,4));ctk.CTkLabel(pleft,text='Nome, código SIGTAP e quantidade lida do Global.',font=('Segoe UI',9),text_color=MUTED).pack(anchor='w',pady=(0,7))
        pf,ptree=_tree(pleft,[('nome','Procedimento'),('codigo','SIGTAP'),('qtd','Qtd.')],{'nome':430,'codigo':145,'qtd':80},12);pf.pack(fill='both',expand=True)
        def refresh_proc_tree():
            for x in ptree.get_children():ptree.delete(x)
            for nome,codigo,qtd,_ in self._exam_selected_global_rows(exam,r):ptree.insert('', 'end',values=(nome,codigo,qtd),tags=('ok',))
        refresh_proc_tree()
        ctk.CTkLabel(pright,text='Adicionar procedimento',font=('Segoe UI',13,'bold'),text_color=TEXT).pack(anchor='w',padx=12,pady=(12,4))
        proc_search=ctk.CTkEntry(pright,placeholder_text='Buscar nome ou SIGTAP...');proc_search.pack(fill='x',padx=12,pady=(0,6))
        af,atree=_tree(pright,[('nome','Procedimento'),('codigo','SIGTAP'),('qtd','Qtd.')],{'nome':260,'codigo':110,'qtd':55},9);af.pack(fill='both',expand=True,padx=12,pady=(0,6))
        def paint_available(*_):
            q=proc_search.get().strip().upper()
            for x in atree.get_children():atree.delete(x)
            selected={str(x).strip().upper() for x in carregar_mapeamentos().get(exam,[])}
            for idx,rec in enumerate(state.get('global_records',[])):
                name=str(rec.get('nome_original') or rec.get('nome_exato') or '').strip();code=str(rec.get('codigo','') or '—');qty=int(rec.get('quantidade',0) or 0)
                if q and q not in name.upper() and q not in code.upper():continue
                if name.upper() in selected or str(rec.get('nome_exato','')).upper() in selected:continue
                atree.insert('', 'end',iid=str(idx),values=(name,code,qty))
        proc_search.bind('<KeyRelease>',paint_available);paint_available()
        def add_selected():
            sels=atree.selection()
            if not sels:messagebox.showinfo('YUPI','Selecione um procedimento para adicionar.');return
            current=carregar_mapeamentos().get(exam,[])
            if not current:current=[row[3] for row in self._exam_selected_global_rows(exam,r)]
            for iid in sels:
                rec=state['global_records'][int(iid)];name=str(rec.get('nome_exato') or rec.get('nome_original') or '').strip().upper()
                if name and name not in current:current.append(name)
            salvar_mapeamento(exam,current)
            if self._compute_exames_results(state):
                r2=self._exam_find_result(exam)
                if r2:r.clear();r.update(r2)
                refresh_proc_tree();paint_available()
        def remove_selected():
            sels=ptree.selection()
            if not sels:messagebox.showinfo('YUPI','Selecione um procedimento para remover.');return
            remove_names={str(ptree.item(i,'values')[0]).strip().upper() for i in sels}
            current=carregar_mapeamentos().get(exam,[])
            if not current:current=[row[3] for row in self._exam_selected_global_rows(exam,r)]
            # compara tanto nome original quanto nome normalizado
            new=[]
            for x in current:
                xu=str(x).strip().upper();rec=next((z for z in state.get('global_records',[]) if str(z.get('nome_exato','')).upper()==xu or str(z.get('nome_original','')).upper()==xu),None)
                orig=str((rec or {}).get('nome_original','')).upper()
                if xu not in remove_names and orig not in remove_names:new.append(x)
            salvar_mapeamento(exam,new)
            if self._compute_exames_results(state):
                r2=self._exam_find_result(exam)
                if r2:r.clear();r.update(r2)
                refresh_proc_tree();paint_available()
        def restore_auto():
            if messagebox.askyesno('YUPI',f'Restaurar composição automática de {exam}?'):
                remover_mapeamento(exam)
                if self._compute_exames_results(state):
                    r2=self._exam_find_result(exam)
                    if r2:r.clear();r.update(r2)
                    refresh_proc_tree();paint_available()
        btns=ctk.CTkFrame(pleft,fg_color='transparent');btns.pack(fill='x',pady=(7,0))
        ctk.CTkButton(btns,text='− Remover selecionado',fg_color='#8C2F3D',command=remove_selected).pack(side='left',fill='x',expand=True,padx=(0,4))
        ctk.CTkButton(btns,text='Restaurar automático',fg_color=PANEL2,text_color='#B99DFF',command=restore_auto).pack(side='left',fill='x',expand=True,padx=(4,0))
        ctk.CTkButton(pright,text='+ Adicionar selecionado',fg_color=PURPLE,command=add_selected).pack(fill='x',padx=12,pady=(2,12))
        # Por dia
        td=pages['Por dia'];ctk.CTkLabel(td,text='Movimento por dia',font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',padx=12,pady=(12,5));daily=sd.get('daily') or {};df,dtree=_tree(td,[('d','Dia'),('i','Interno'),('e','Externo'),('t','Total')],{'d':150,'i':120,'e':120,'t':120},14);df.pack(fill='both',expand=True,padx=12,pady=(0,12));
        for day,val in sorted(daily.items()):dtree.insert('', 'end',values=(day,val.get('interno',0),val.get('externo',0),val.get('total',val.get('interno',0)+val.get('externo',0))))
        if not daily:ctk.CTkLabel(td,text='Sem detalhamento diário no SADT carregado.',text_color=MUTED).pack(anchor='w',padx=12,pady=8)
        # Comparativo
        tc=pages['Comparativo'];compwrap=ctk.CTkScrollableFrame(tc,fg_color='transparent');compwrap.pack(fill='both',expand=True,padx=12,pady=12)
        ctk.CTkLabel(compwrap,text='Como o YUPI chegou neste resultado',font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',pady=(0,8))
        for title,items,col in [('SIRESP',r.get('detalhes_siresp',[]) or [],ACCENT2),('GLOBAL',r.get('detalhes_global',[]) or [],ORANGE)]:
            ctk.CTkLabel(compwrap,text=title,font=('Segoe UI',11,'bold'),text_color=col).pack(anchor='w',pady=(7,3))
            if not items:ctk.CTkLabel(compwrap,text='Nenhum detalhe disponível.',text_color=MUTED).pack(anchor='w',padx=8)
            for it in items:
                txt=(f"{it.get('exame','')} • ext {it.get('externo',0)} • int {it.get('interno',0)} • direto {it.get('direto',0)}" if title=='SIRESP' else f"{it.get('exame','')} • qtd {it.get('quantidade',0)}")
                rr=ctk.CTkFrame(compwrap,fg_color='#0A1727',corner_radius=8);rr.pack(fill='x',pady=2);ctk.CTkLabel(rr,text=txt,anchor='w',text_color=TEXT,font=('Segoe UI',9)).pack(fill='x',padx=10,pady=7)
        # Regras
        tr=pages['Regras'];rule=self.config.get('exams',{}).get(exam,{});sc=rule.get('scope',{});limit=((rule.get('sigtap') or [{}])[0].get('max_qty',1) if rule.get('sigtap') else 1)
        ctk.CTkLabel(tr,text='Regra atual do exame',font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',padx=12,pady=(12,6))
        for a,b in [('SIRESP',sc.get('siresp','ambos')),('SADT',sc.get('sadt','ambos')),('Global',sc.get('global','total')),('Estratégia',rule.get('scope_strategy','direct')),('Quantidade permitida',limit)]:
            rr=ctk.CTkFrame(tr,fg_color='#0A1727',corner_radius=9);rr.pack(fill='x',padx=12,pady=3);ctk.CTkLabel(rr,text=a,text_color=MUTED).pack(side='left',padx=10,pady=8);ctk.CTkLabel(rr,text=str(b),text_color=TEXT,font=('Segoe UI',10,'bold')).pack(side='right',padx=10)
        ctk.CTkButton(tr,text='⚙ Abrir Configurações',fg_color=PURPLE,command=self.show_settings).pack(fill='x',padx=12,pady=10)
        # Auditoria
        ta=pages['Auditoria'];ctk.CTkLabel(ta,text='Auditoria do exame',font=('Segoe UI',14,'bold'),text_color=TEXT).pack(anchor='w',padx=12,pady=(12,5));audmsg=('Valores conferem.' if v.get('status')=='OK' else (v.get('explanation') or ('Existe divergência de escopo/total.' if dval is None else f'Existe diferença de {abs(dval)}. Revise procedimentos, escopo e movimento por dia.')));ctk.CTkLabel(ta,text=audmsg,wraplength=1100,justify='left',text_color=GREEN if v.get('status')=='OK' else '#FF8A98').pack(anchor='w',padx=12,pady=4)
        obs=ctk.CTkTextbox(ta,height=110,fg_color='#071525',border_width=1,border_color=BORDER);obs.pack(fill='x',padx=12,pady=8)
        def manual_qty():
            nonlocal gval
            q=simpledialog.askinteger('Quantidade manual',f'{exam}\nInforme a quantidade do Global para esta conferência:',initialvalue=gval,minvalue=0,parent=self.root)
            if q is None:return
            state['manual'][exam]=q;gval=q
            if self._compute_exames_results(state):self._show_exam_workspace(exam,'Auditoria')
        def resolve():
            state['resolved'].add(exam);append_history('Exames','Divergência resolvida',{'exame':exam,'observacao':obs.get('1.0','end').strip()});self._show_exam_workspace(exam,'Auditoria')
        acts=ctk.CTkFrame(ta,fg_color='transparent');acts.pack(fill='x',padx=12,pady=5);ctk.CTkButton(acts,text='✏ Quantidade manual',fg_color=PANEL2,text_color='#B99DFF',command=manual_qty).pack(side='left',fill='x',expand=True,padx=(0,4));ctk.CTkButton(acts,text='✓ Marcar como resolvido',fg_color=PURPLE,command=resolve).pack(side='left',fill='x',expand=True,padx=(4,0))

def abrir_yupi_v654(app=None):
    own=False
    if app is None: app=ctk.CTk();own=True
    else:
        for w in app.winfo_children():w.destroy()
    YupiV654(app)
    if own:app.mainloop()
