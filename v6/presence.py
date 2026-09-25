from __future__ import annotations
import re, unicodedata
from collections import defaultdict, Counter
from difflib import SequenceMatcher
import fitz


def norm(s):
    s=unicodedata.normalize('NFKD',str(s or '')).encode('ascii','ignore').decode().upper().strip()
    s=re.sub(r'[^A-Z0-9 ]+',' ',s)
    return re.sub(r'\s+',' ',s).strip()


def norm_spec(s):
    s=norm(s)
    aliases={
        'CARDIOLOGIA AVALIACAO PRE CIRURGICA':'AVALIACAO PRE CIRURGICA',
        'AVALIACAO PRE CIRURGICA':'AVALIACAO PRE CIRURGICA',
        'ENFERMAGEM CARDIOLOGIA':'ENFERMAGEM CARDIOLOGIA',
        'ENFERMAGEM CLASSIFICACAO DE RISCO':'ENFERMAGEM CLASSIFICACAO DE RISCO',
        'ENFERMAGEM PREPARO ENDOSCOPIA':'ENFERMAGEM PREPARO ENDOSCOPIA',
        'GASTROCLINICA':'GASTROENTEROLOGIA',
    }
    return aliases.get(s,s)


def _page_specialties(doc):
    """Infere a especialidade de páginas de continuação da Agenda SIRESP."""
    specs=[]
    for page in doc:
        text=page.get_text()
        m=re.search(r'ESPECIALIDADE:\s*([^\n]+)',text,re.I)
        specs.append(norm_spec(m.group(1)) if m else '')
    # propaga a última especialidade conhecida para páginas de continuação
    last=''
    for i,s in enumerate(specs):
        if s: last=s
        elif last: specs[i]=last
    # em páginas iniciais/órfãs, usa a próxima especialidade conhecida
    nxt=''
    for i in range(len(specs)-1,-1,-1):
        if specs[i]: nxt=specs[i]
        elif nxt: specs[i]=nxt
    return specs


def read_analitico_people(path):
    rows=[]
    doc=fitz.open(path)
    for page in doc:
        text=page.get_text()
        m=re.search(r'Especialidade:\s*\d+\s*-\s*([^\n]+)',text,re.I)
        spec=norm_spec(m.group(1)) if m else 'NAO IDENTIFICADA'
        pm=re.search(r'Per[ií]odo de An[aá]lise\s*:\s*(\d{2}/\d{2}/\d{4})\s*(?:à|a|-)+\s*(\d{2}/\d{2}/\d{4})',text,re.I)
        period=(pm.group(1),pm.group(2)) if pm else ('','')
        lines=[x.strip() for x in text.splitlines() if x.strip()]
        for i,line in enumerate(lines):
            if not re.fullmatch(r'\d{10}',line):
                continue
            code=line
            # Layout típico: Registro, Nome, Código, Procedimento, Prontuário, Qtde, Data
            name=lines[i-1] if i>=1 else ''
            reg=lines[i-2] if i>=2 and re.fullmatch(r'\d{4,9}',lines[i-2]) else ''
            pront=''; qty=1; proc=''; dt=''
            for j in range(i+1,min(i+10,len(lines))):
                cur=lines[j]
                if not proc and not re.fullmatch(r'\d+',cur) and not re.fullmatch(r'\d{2}/\d{2}/\d{4}',cur):
                    proc=cur
                if not pront and re.fullmatch(r'\d{4,9}',cur):
                    pront=cur
                    if j+1<len(lines) and re.fullmatch(r'\d+',lines[j+1]):
                        qty=int(lines[j+1])
                if re.fullmatch(r'\d{2}/\d{2}/\d{4}',cur):
                    dt=cur
                if pront and dt:
                    break
            if pront:
                rows.append({
                    'especialidade':spec,'prontuario':pront,'paciente':name,'paciente_norm':norm(name),
                    'codigo':code,'procedimento':proc,'qtde':qty,'registro':reg,'data':dt,
                    'periodo_inicio':period[0],'periodo_fim':period[1],
                })
    return rows


def read_siresp_agenda(path):
    rows=[]
    doc=fitz.open(path)
    specs=_page_specialties(doc)
    for pidx,page in enumerate(doc):
        text=page.get_text()
        spec=specs[pidx] or 'NAO IDENTIFICADA'
        dm=re.search(r'DATA AGENDA:\s*(\d{2})[-/](\d{2})[-/](\d{4})',text,re.I)
        agenda_date=f'{dm.group(1)}/{dm.group(2)}/{dm.group(3)}' if dm else ''
        lines=[x.strip() for x in text.splitlines() if x.strip()]
        for i,line in enumerate(lines):
            mm=re.search(r'Prontu[aá]rio:\s*(\d+)',line,re.I)
            if not mm:
                continue
            pront=mm.group(1)
            name=''
            # O PDF da agenda costuma trazer "MATRICULA + NOME" ou a matrícula e o nome em linhas separadas.
            # Procura primeiro esses padrões, que são muito mais seguros que escolher qualquer texto antes do prontuário.
            block=lines[max(0,i-24):i]
            for raw in reversed(block):
                mname=re.match(r'^\d{4,12}\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ .\'-]{4,})$',raw.strip(),re.I)
                if mname:
                    name=mname.group(1).strip(); break
            if not name:
                for j in range(i-1,max(-1,i-24),-1):
                    raw=lines[j].strip(); cand=norm(raw)
                    if not cand or re.search(r'\d',cand): continue
                    if cand in {'MATRICULA','AGENDAMENTO','PRESENCIAL','EQUIPE F','EXTERNO INTERCON','RETORNO','INTERCONSULTA','CONSULTA'}: continue
                    if cand.startswith(('TELEFONE','PRONTUARIO','ESPECIALIDADE','DATA AGENDA')): continue
                    # aceita nome isolado somente quando a linha anterior parece matrícula.
                    prev=lines[j-1].strip() if j-1>=0 else ''
                    if re.fullmatch(r'\d{4,12}',prev) and len(cand.split())>=2:
                        name=raw.strip(' \xa0'); break
            rows.append({
                'especialidade':spec,'prontuario':pront,'paciente':name,'paciente_norm':norm(name),
                'data':agenda_date,'status_agenda':'AGENDADO'
            })
    # remove repetição real do mesmo paciente no mesmo dia/especialidade
    seen=set(); out=[]
    for r in rows:
        k=(r.get('data',''),r['especialidade'],r['prontuario'])
        if k not in seen:
            seen.add(k); out.append(r)
    return out


def _name_hit(name, candidates):
    n=norm(name)
    if not n or len(n)<6:
        return []
    exact=[x for x in candidates if x.get('paciente_norm')==n]
    if exact:
        return exact
    # fallback conservador: só aceita semelhança muito alta para evitar falsos positivos.
    scored=[]
    for x in candidates:
        xn=x.get('paciente_norm') or norm(x.get('paciente'))
        if xn:
            ratio=SequenceMatcher(None,n,xn).ratio()
            if ratio>=0.94:
                scored.append((ratio,x))
    if not scored:
        return []
    best=max(r for r,_ in scored)
    return [x for r,x in scored if r==best]


def compare_presence(agenda, analitico, specialty_rules):
    by_pront=defaultdict(list)
    for r in analitico:
        by_pront[str(r.get('prontuario','')).lstrip('0') or '0'].append(r)

    used=set()
    out=[]
    for a in agenda:
        ap=str(a.get('prontuario','')).lstrip('0') or '0'
        hits=list(by_pront.get(ap,[]))
        match_mode='PRONTUARIO'
        if not hits and a.get('paciente'):
            hits=_name_hit(a.get('paciente'),analitico)
            match_mode='NOME' if hits else ''

        if not hits:
            out.append({**a,'codigo':'','qtde':0,'resultado':'NAO_ENCONTRADO','detalhe':'Não localizado no Analítico pelo prontuário ou nome'})
            continue

        # Prioriza mesma especialidade quando possível; prontuário continua sendo a chave principal.
        aspec=norm_spec(a.get('especialidade'))
        same=[h for h in hits if norm_spec(h.get('especialidade'))==aspec]
        candidates=same or hits

        # Uma linha por paciente agendado: agrega lançamentos encontrados daquele atendimento.
        rules=specialty_rules.get(a.get('especialidade'),[]) or specialty_rules.get(aspec,[]) or []
        allowed={str(x.get('code','')):x for x in rules if x.get('active',True)}
        codes=[]; total_qty=0; details=[]
        result='COMPARECEU'; detail=f'Localizado no Analítico por {match_mode.lower()}'
        for h in candidates:
            used.add(id(h)); code=str(h.get('codigo','')); q=int(h.get('qtde',1) or 1)
            codes.append(code); total_qty+=q; details.append(h)
            if allowed:
                rule=allowed.get(code)
                if not rule and result=='COMPARECEU':
                    result='CODIGO_NAO_MAPEADO'; detail='Paciente localizado, mas o código não está cadastrado para a especialidade'
                elif rule and q>int(rule.get('max_qty',1) or 1):
                    result='ACIMA_PERMITIDO'; detail=f'Quantidade {q} acima do permitido ({rule.get("max_qty",1)})'
        # Sem regra cadastrada, presença continua válida; a falta de mapeamento não vira ausência.
        primary=candidates[0]
        out.append({
            **a,
            'registro':primary.get('registro',''),
            'codigo':', '.join(dict.fromkeys(codes)),
            'qtde':total_qty,
            'resultado':result,
            'detalhe':detail,
            'match_mode':match_mode,
            'lancamentos':details,
        })

    # Duplicidade: considera número/quantidade de lançamentos para um prontuário+código.
    counts=Counter((str(r.get('prontuario','')).lstrip('0'),str(r.get('codigo',''))) for r in analitico)
    for r in out:
        if r.get('resultado')=='NAO_ENCONTRADO':
            continue
        rules=specialty_rules.get(r.get('especialidade'),[]) or specialty_rules.get(norm_spec(r.get('especialidade')),[]) or []
        for code in [c.strip() for c in str(r.get('codigo','')).split(',') if c.strip()]:
            rr=next((x for x in rules if str(x.get('code',''))==code and x.get('active',True)),None)
            maxq=int(rr.get('max_qty',1) or 1) if rr else None
            n=counts[(str(r.get('prontuario','')).lstrip('0'),code)]
            if maxq is not None and n>maxq:
                r['resultado']='DUPLICIDADE'; r['detalhe']=f'{n} lançamentos do código {code}; regra permite {maxq}'
                break

    # Lançamentos do Analítico sem paciente na agenda = encaixe/extra.
    agenda_pronts={str(a.get('prontuario','')).lstrip('0') for a in agenda}
    for h in analitico:
        hp=str(h.get('prontuario','')).lstrip('0')
        if hp and hp not in agenda_pronts and id(h) not in used:
            out.append({
                'especialidade':h.get('especialidade',''),'prontuario':h.get('prontuario',''),
                'paciente':h.get('paciente',''),'paciente_norm':h.get('paciente_norm',''),
                'data':h.get('data',''),'status_agenda':'NAO_AGENDADO','registro':h.get('registro',''),
                'codigo':h.get('codigo',''),'qtde':int(h.get('qtde',1) or 1),
                'resultado':'ENCAIXE_EXTRA','detalhe':'Lançamento encontrado no Analítico sem correspondência na Agenda SIRESP',
                'match_mode':'EXTRA','lancamentos':[h],
            })
    return out
