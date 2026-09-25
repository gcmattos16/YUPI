from __future__ import annotations
import json, os
from pathlib import Path
from datetime import datetime

BASE = Path(os.getenv('APPDATA') or Path.home()) / 'YUPI'
BASE.mkdir(parents=True, exist_ok=True)
CONFIG = BASE / 'v6_config.json'
HISTORY = BASE / 'v6_history.json'

DEFAULT_CONFIG = {
    'version': '6.5.0',
    'exams': {
        'NASOFIBROSCOPIA': {
            'active': True,
            'scope': {'siresp': 'externo', 'sadt': 'ambos', 'global': 'total'},
            'scope_strategy': 'bridge_sadt',
            'sigtap': [],
        },
        'RX': {
            'active': True,
            'scope': {'siresp': 'externo', 'sadt': 'ambos', 'global': 'total'},
            'scope_strategy': 'bridge_sadt',
            'sigtap': [],
        },
        'BIOMETRIA': {
            'active': True,
            'scope': {'siresp': 'interno', 'sadt': 'ambos', 'global': 'total'},
            'scope_strategy': 'direct',
            'sigtap': [{'code':'', 'name':'BIOMETRIA', 'max_qty':2, 'unit':'atendimento', 'active':True}],
        },
        'ELETRONEUROMIOGRAFIA': {
            'active': True,
            'scope': {'siresp': 'ambos', 'sadt': 'ambos', 'global': 'total'},
            'scope_strategy': 'direct',
            'sigtap': [{'code':'', 'name':'ELETRONEUROMIOGRAFIA', 'max_qty':2, 'unit':'atendimento', 'active':True}],
        },
        'TESTE DE CONTATO': {
            'active': True,
            'scope': {'siresp': 'ambos', 'sadt': 'ambos', 'global': 'total'},
            'scope_strategy': 'direct',
            'sigtap': [{'code':'', 'name':'TESTE DE CONTATO', 'max_qty':3, 'unit':'atendimento', 'active':True}],
        },
    },
    'specialties': {
        'CARDIOLOGIA': [
            {'code':'0301010072','name':'CONSULTA MEDICA EM ATENÇÃO ESPECIALIZADA','type':'Consulta','max_qty':1,'unit':'atendimento','active':True}
        ],
        'FISIOTERAPIA': [
            {'code':'0301010048','name':'CONSULTA DE PROFISSIONAIS DE NIVEL SUPERIOR NA ATENÇÃO ESPECIALIZADA','type':'Consulta','max_qty':1,'unit':'atendimento','active':True},
            {'code':'0302050027','name':'ATENDIMENTO FISIOTERAPÊUTICO','type':'Sessão','max_qty':1,'unit':'atendimento','active':True},
        ],
    },
    'ignored_sadt_sheets': [],
    'user': 'Operador',
    'profile': {'name':'Operador','unit':'Unidade demonstrativa'},
}

def _merge(default, loaded):
    if isinstance(default, dict) and isinstance(loaded, dict):
        out = dict(default)
        for k,v in loaded.items():
            out[k] = _merge(out[k], v) if k in out else v
        return out
    return loaded


def _ensure_all_exam_scopes(data):
    try:
        from exames.grupos import GRUPOS
        exams=data.setdefault('exams',{})
        for name in GRUPOS:
            exams.setdefault(name, {
                'active': True,
                'scope': {'siresp':'ambos','sadt':'ambos','global':'total'},
                'scope_strategy':'direct',
                'sigtap': [],
            })
    except Exception:
        pass
    return data

def _migrate_rules(data):
    """Aplica migrações de regras novas sem quebrar configurações existentes."""
    exams = data.setdefault('exams', {})
    old_version = str(data.get('version') or '')

    # v6.4.4: ELETRONEUROMIOGRAFIA / ELETRONEURO é x2 por atendimento.
    # Só força na migração de versões anteriores; depois continua editável pela tela.
    if old_version not in {'6.4.4','6.5.0'}:
        rule = exams.setdefault('ELETRONEUROMIOGRAFIA', {
            'active': True,
            'scope': {'siresp':'ambos','sadt':'ambos','global':'total'},
            'scope_strategy':'direct',
            'sigtap': [],
        })
        sigtap = rule.setdefault('sigtap', [])
        if sigtap:
            sigtap[0]['max_qty'] = 2
            sigtap[0].setdefault('name', 'ELETRONEUROMIOGRAFIA')
            sigtap[0].setdefault('code', '')
            sigtap[0].setdefault('unit', 'atendimento')
            sigtap[0].setdefault('active', True)
        else:
            sigtap.append({'code':'', 'name':'ELETRONEUROMIOGRAFIA', 'max_qty':2, 'unit':'atendimento', 'active':True})
        data['version'] = '6.5.0'
    return data


def load_config():
    if not CONFIG.exists():
        save_config(DEFAULT_CONFIG)
        return _migrate_rules(_ensure_all_exam_scopes(json.loads(json.dumps(DEFAULT_CONFIG))))
    try:
        data = json.loads(CONFIG.read_text(encoding='utf-8'))
        return _migrate_rules(_ensure_all_exam_scopes(_merge(DEFAULT_CONFIG, data)))
    except Exception:
        return _migrate_rules(_ensure_all_exam_scopes(json.loads(json.dumps(DEFAULT_CONFIG))))

def save_config(data):
    CONFIG.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def append_history(module, result, details=None):
    items=[]
    if HISTORY.exists():
        try: items=json.loads(HISTORY.read_text(encoding='utf-8'))
        except Exception: items=[]
    items.insert(0, {'at':datetime.now().isoformat(timespec='seconds'),'module':module,'result':result,'details':details or {}})
    HISTORY.write_text(json.dumps(items[:500], ensure_ascii=False, indent=2), encoding='utf-8')

def load_history():
    if not HISTORY.exists(): return []
    try: return json.loads(HISTORY.read_text(encoding='utf-8'))
    except Exception: return []
