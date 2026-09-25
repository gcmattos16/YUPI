from __future__ import annotations
from pathlib import Path
import re, fitz
from datetime import datetime
from collections import defaultdict
from exames.leitor_siresp_exames import ler_siresp_exames
from exames.leitor_faturamento_exames import ler_faturamento_exames, ler_faturamento_exames_detalhado
from exames.comparador_exames import comparar_exames
from exames.configuracao_mapeamento import carregar_mapeamentos
from .report_meta import pdf_period


def _classify_pdf(path):
    try:
        d=fitz.open(path); t=d[0].get_text().upper() if len(d) else ''
    except Exception:return 'PDF'
    if 'DEMONSTRATIVO GLOBAL DE FATURAMENTO' in t or 'RELATÓRIO DE EXAMES (SINTÉTICO)' in t:return 'GLOBAL'
    if 'RELATÓRIO DE CONSULTAS MÉDICAS (ANALÍTICO)' in t:return 'ANALITICO'
    if 'RELATÓRIO OFERTADO / AGENDADO / REALIZADO - EXAME' in t:return 'SIRESP_EXAMES'
    if 'DATA AGENDA:' in t and 'ESPECIALIDADE:' in t:return 'SIRESP_AGENDA'
    return 'PDF'

def detect_files(folder):
    items=[]
    for p in sorted(Path(folder).glob('*')):
        if p.suffix.lower() not in ('.pdf','.xlsx','.xlsm'): continue
        if p.suffix.lower() in ('.xlsx','.xlsm'):
            kind='SADT'; period=('','')
        else:
            kind=_classify_pdf(str(p)); period=pdf_period(str(p))
        d=period[0] if period[0]==period[1] else (f'{period[0]}–{period[1]}' if period[0] else '')
        items.append({'file':str(p),'name':p.name,'type':kind,'date':d,'period':period})
    return items

def analyze_exam_month(folder):
    items=detect_files(folder)
    siresps=[x for x in items if x['type']=='SIRESP_EXAMES']
    globals_=[x for x in items if x['type']=='GLOBAL']
    by_period_g=defaultdict(list)
    for g in globals_: by_period_g[g['period']].append(g)
    aggregate=defaultdict(lambda:{'siresp':0,'global':0,'days':[],'missing':[]})
    pairs=0
    for s in siresps:
        gs=by_period_g.get(s['period'],[])
        if not gs:
            continue
        g=gs.pop(0); pairs+=1
        try:
            sd=ler_siresp_exames(s['file']); gd=ler_faturamento_exames(g['file']); raw=ler_faturamento_exames_detalhado(g['file'])
            rows=comparar_exames(sd,gd,carregar_mapeamentos(),raw)
        except Exception as e:
            continue
        label=s['period'][0] if s['period'][0]==s['period'][1] else (s['period'][0] or s['name'])
        for r in rows:
            a=aggregate[r['exame']]; a['siresp']+=int(r.get('siresp',0)); a['global']+=int(r.get('global',0))
            if int(r.get('diferenca',0))!=0:
                a['days'].append({'date':label,'siresp':r.get('siresp',0),'global':r.get('global',0),'diff':r.get('diferenca',0)})
    result=[]
    for exam,a in sorted(aggregate.items()):
        diff=a['siresp']-a['global']; result.append({'exame':exam,**a,'diff':diff,'status':'OK' if diff==0 else 'DIVERGENCIA'})
    unmatched_s=len(siresps)-pairs; unmatched_g=sum(len(v) for v in by_period_g.values())
    return {'files':items,'pairs':pairs,'unmatched_siresp':unmatched_s,'unmatched_global':unmatched_g,'results':result}
