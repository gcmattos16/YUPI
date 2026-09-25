import re, fitz
from datetime import datetime

def pdf_period(path):
    try:
        doc=fitz.open(path); text='\n'.join(doc[i].get_text() for i in range(min(3,len(doc))))
    except Exception:return ('','')
    patterns=[
        r'Per[ií]odo(?:\s+de\s+An[aá]lise)?\s*:?\s*(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:à|a|ate|até|-)\s*(\d{2}[/-]\d{2}[/-]\d{4})',
        r'(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:à|a|ate|até)\s*(\d{2}[/-]\d{2}[/-]\d{4})'
    ]
    for pat in patterns:
        m=re.search(pat,text,re.I)
        if m:return tuple(x.replace('-','/') for x in m.groups())
    # agenda de um único dia
    m=re.search(r'DATA AGENDA:\s*(\d{2})-(\d{2})-(\d{4})',text,re.I)
    if m:
        d='/'.join(m.groups());return d,d
    return ('','')
