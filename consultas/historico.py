import hashlib
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_DADOS = os.path.join(os.getenv("APPDATA") or os.path.expanduser("~"), "YUPI", "dados_yupi")
ARQUIVO_HISTORICO = os.path.join(PASTA_DADOS, "historico_consultas.json")


def _carregar():
    if not os.path.exists(ARQUIVO_HISTORICO):
        return {"conferencias": []}
    try:
        with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if not isinstance(dados, dict):
            return {"conferencias": []}
        dados.setdefault("conferencias", [])
        return dados
    except Exception:
        return {"conferencias": []}


def _salvar(dados):
    os.makedirs(PASTA_DADOS, exist_ok=True)
    with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, ensure_ascii=False, indent=2)


def _assinatura(caminho_siresp, caminho_analitico):
    partes = []
    for caminho in (caminho_siresp, caminho_analitico):
        try:
            stat = os.stat(caminho)
            partes.append(f"{os.path.basename(caminho)}|{stat.st_size}|{int(stat.st_mtime)}")
        except OSError:
            partes.append(os.path.basename(caminho or ""))
    return hashlib.sha1("||".join(partes).encode("utf-8")).hexdigest()[:16]


def registrar_conferencia(caminho_siresp, caminho_analitico, resultados):
    dados = _carregar()
    assinatura = _assinatura(caminho_siresp, caminho_analitico)
    agora = datetime.now().isoformat(timespec="seconds")
    total = len(resultados)
    ok = sum(1 for item in resultados if item.get("diferenca", 0) == 0)
    divergencias = total - ok

    existente = next((c for c in dados["conferencias"] if c.get("id") == assinatura), None)
    novo = {
        "id": assinatura,
        "data_hora": agora,
        "siresp": os.path.basename(caminho_siresp),
        "analitico": os.path.basename(caminho_analitico),
        "total": total,
        "ok": ok,
        "divergencias": divergencias,
        "conformidade": round((ok / total * 100) if total else 0, 1),
        "resultados": resultados,
        "correcoes": (existente or {}).get("correcoes", {}),
    }

    if existente:
        dados["conferencias"].remove(existente)
    dados["conferencias"].insert(0, novo)
    dados["conferencias"] = dados["conferencias"][:120]
    _salvar(dados)
    return assinatura


def obter_correcoes(conferencia_id):
    dados = _carregar()
    conf = next((c for c in dados["conferencias"] if c.get("id") == conferencia_id), None)
    return dict((conf or {}).get("correcoes", {}))


def salvar_correcao(conferencia_id, especialidade, responsavel, observacao):
    dados = _carregar()
    conf = next((c for c in dados["conferencias"] if c.get("id") == conferencia_id), None)
    if conf is None:
        return False
    conf.setdefault("correcoes", {})[especialidade] = {
        "corrigido": True,
        "responsavel": (responsavel or "Não informado").strip(),
        "observacao": (observacao or "").strip(),
        "data_hora": datetime.now().isoformat(timespec="seconds"),
    }
    _salvar(dados)
    return True


def listar_conferencias(limite=50):
    return _carregar().get("conferencias", [])[:limite]
