from __future__ import annotations

def _val(item, mode):
    if not item: return None
    if mode=='externo': return int(item.get('externo',0) or 0)
    if mode=='interno': return int(item.get('interno',0) or 0)
    if mode in ('ambos','total'): return int(item.get('total', item.get('siresp',0)) or 0)
    return None

def validate_scope(exam, siresp_item, global_total, sadt_item, rule):
    sc=rule.get('scope',{})
    strategy=rule.get('scope_strategy','direct')
    s_mode=sc.get('siresp','ambos'); a_mode=sc.get('sadt','ambos'); g_mode=sc.get('global','total')
    s_val=_val(siresp_item,s_mode)
    g_val=int(global_total or 0)
    if strategy=='bridge_sadt' and sadt_item:
        # Valida SIRESP no mesmo recorte do SADT e total SADT contra Global.
        a_scope=_val(sadt_item,s_mode)
        a_total=_val(sadt_item,'total')
        ok_scope=(s_val==a_scope)
        ok_total=(a_total==g_val)
        return {
            'status':'OK' if ok_scope and ok_total else 'ERRO',
            'siresp_scope':s_val,'sadt_scope':a_scope,'sadt_total':a_total,'global':g_val,
            'scope_difference':(s_val or 0)-(a_scope or 0),
            'total_difference':(a_total or 0)-g_val,
            'difference':(a_total or 0)-g_val,
            'explanation':f'{s_mode.title()}: SIRESP {s_val} x SADT {a_scope}; Total: SADT {a_total} x Global {g_val}'
        }
    if strategy=='bridge_sadt' and not sadt_item:
        return {'status':'ESCOPO_PENDENTE','siresp_scope':s_val,'global':g_val,'difference':None,
                'explanation':'A regra de escopo exige a Planilha SADT para ligar o recorte do SIRESP ao total do Global.'}
    return {'status':'OK' if s_val==g_val else 'ERRO','siresp_scope':s_val,'global':g_val,'difference':(s_val or 0)-g_val,
            'explanation':f'{s_mode.title()}: SIRESP {s_val} x Global {g_val}'}
