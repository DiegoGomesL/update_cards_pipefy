# -*- coding: utf-8 -*-
"""Pull ENIO cards (ADM/JUD/FIN) do Pipefy, consolida por CPF e gera:
   ../enio_casos.json  (lista de casos para o Excel)
   ../enio_metrics.json (contagens para a apresentação)
ENIO identificado por TERCEIRO INTERESSADO contendo 'ENIO'.
"""
import sys, re, os, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from collections import defaultdict, Counter
from lib import api

ADM=api.PIPES["ADM"]["id"]; JUD=api.PIPES["JUD"]["id"]; FIN=api.PIPES["FIN"]["id"]
ROOT=os.path.join(os.path.dirname(__file__),"..")

FID={
 "ADM":{"cpf":"cpf_do_benefici_rio_1","nome":"nome_do_benefici_rio","terc":"terceiro_interessado",
        "fundo_inv":"fundo_investidor","fundo_esp":"copy_of_fundo_investidor",
        "prot":"n_mero_do_processo_administrativo","data":"data_do_protocolo","res":"resultado_do_pedido"},
 "JUD":{"cpf":"cpf_do_benefici_rio","nome":"nome_do_benefici_rio","terc":"terceiro_interassado",
        "fundo_inv":"fundo_investidor","fundo_esp":"copy_of_fundo_investidor",
        "prot":"n_mero_do_processo","data":"data_do_protocolo","res":"resultado_do_processo"},
 "FIN":{"cpf":"cpf_do_benefici_rio","nome":"nome_do_benefici_rio","terc":"terceiro_interessado",
        "fundo_inv":"fundo_investidor","fundo_esp":"copy_of_fundo_investidor",
        "prot":"","data":"","res":""},
}
ADM_TERM={"ENCERRADOS","DESCARTADOS"}
JUD_TERM={"ENCERRADOS"}

def dig(v): return re.sub(r"\D","",str(v or ""))
def cpf11(v):
    d=dig(v); return d.zfill(11) if d and len(d)<=11 else d
def nz(v): return (str(v).strip() if v is not None else "")
def fmtcpf(c): return f"{c[:3]}.{c[3:6]}.{c[6:9]}-{c[9:]}" if len(c)==11 else c

Q="""query($pipeId:ID!,$after:String){ allCards(pipeId:$pipeId,first:50,after:$after){
  pageInfo{hasNextPage endCursor} edges{node{ id title current_phase{name} fields{ value field{id} } }} } }"""

def pull(pid,kind):
    out=[]; after=None
    while True:
        r=api.execute(Q,{"pipeId":pid,"after":after})
        if "errors" in r: raise RuntimeError(r["errors"])
        d=r["data"]["allCards"]
        for e in d["edges"]:
            n=e["node"]; fm={(f.get("field") or {}).get("id"):f.get("value") for f in (n.get("fields") or [])}
            fi=FID[kind]
            out.append({"kind":kind,"phase":nz((n.get("current_phase") or {}).get("name")),
                "cpf":cpf11(fm.get(fi["cpf"])),"nome":nz(fm.get(fi["nome"])),
                "terc":nz(fm.get(fi["terc"])),"fundo_inv":nz(fm.get(fi["fundo_inv"])),"fundo_esp":nz(fm.get(fi["fundo_esp"])),
                "prot":nz(fm.get(fi["prot"])) if fi["prot"] else "",
                "data":nz(fm.get(fi["data"])) if fi["data"] else "",
                "res":nz(fm.get(fi["res"])) if fi["res"] else ""})
        if not d["pageInfo"]["hasNextPage"]: break
        after=d["pageInfo"]["endCursor"]
    return out

def is_enio(c):
    blob=(c["terc"]+" "+c["fundo_inv"]+" "+c["fundo_esp"]).upper()
    return "ENIO" in blob

print("Pull ADM..."); adm=[c for c in pull(ADM,"ADM") if is_enio(c)]; print("  ENIO ADM:",len(adm))
print("Pull JUD..."); jud=[c for c in pull(JUD,"JUD") if is_enio(c)]; print("  ENIO JUD:",len(jud))
print("Pull FIN..."); fin=[c for c in pull(FIN,"FIN") if is_enio(c)]; print("  ENIO FIN:",len(fin))

adm_by=defaultdict(list); jud_by=defaultdict(list); fin_by=defaultdict(list)
for c in adm:
    if c["cpf"]: adm_by[c["cpf"]].append(c)
for c in jud:
    if c["cpf"]: jud_by[c["cpf"]].append(c)
for c in fin:
    if c["cpf"]: fin_by[c["cpf"]].append(c)

def lote_of(cpf):
    # lote = terceiro mais informativo (prioriza ADM, depois JUD, depois FIN)
    for src in (adm_by,jud_by,fin_by):
        for c in src.get(cpf,[]):
            if c["terc"]: return c["terc"]
    for src in (adm_by,jud_by,fin_by):
        for c in src.get(cpf,[]):
            if c["fundo_esp"]: return c["fundo_esp"]
    return "ENIO"

def adm_res(cpf):
    vals=[c["res"].upper() for c in adm_by.get(cpf,[]) if c["res"]]
    for pri in ["DEFERIDO","INDEFERIDO","DESISTÊNCIA","DESISTENCIA"]:
        for v in vals:
            if v==pri or v.startswith(pri): return v
    return vals[0] if vals else ""

def jud_res(cpf):
    vals=[c["res"].upper() for c in jud_by.get(cpf,[]) if c["res"]]
    for pri in ["PROCEDENTE","IMPROCEDENTE","EXTINÇÃO","DESISTÊNCIA"]:
        for v in vals:
            if pri in v: return v
    return vals[0] if vals else ""

def jud_active(cpf):
    return any(c["phase"].upper() not in JUD_TERM and c["phase"].upper()!="PROCEDENTES" for c in jud_by.get(cpf,[]))
def adm_active(cpf):
    return any(c["phase"].upper() not in ADM_TERM for c in adm_by.get(cpf,[]))

casos=[]
cpfs=set(adm_by)|set(jud_by)|set(fin_by)
for cpf in cpfs:
    ra=adm_res(cpf); rj=jud_res(cpf)
    in_fin=cpf in fin_by
    won_adm = ra=="DEFERIDO"
    won_jud = "PROCEDENTE" in rj and "IMPROCEDENTE" not in rj
    neg_jud = ("IMPROCEDENTE" in rj) or ("EXTINÇÃO" in rj)
    neg_adm = ra.startswith("DESIST")
    nome=""
    for src in (adm_by,jud_by,fin_by):
        for c in src.get(cpf,[]):
            if c["nome"]: nome=c["nome"]; break
        if nome: break
    prot_adm=""
    for c in adm_by.get(cpf,[]):
        if c["prot"]: prot_adm=c["prot"]; break

    # classificação
    if in_fin or won_adm or won_jud:
        situ="FIN"; resf = "DEFERIDO" if won_adm else ("PROCEDENTE" if won_jud else (ra or "DEFERIDO"))
    elif neg_jud:
        situ="ENCERRADO"; resf = rj
    elif neg_adm and not jud_active(cpf):
        situ="ENCERRADO"; resf = ra
    elif jud_active(cpf):
        situ="JUD"; resf = "INDEFERIDO" if ra=="INDEFERIDO" else (ra or "EM ANDAMENTO")
    elif adm_active(cpf):
        situ="ADM"; resf = "EM ANDAMENTO" if ra in ("","INDEFERIDO") else ra
    else:
        situ="ENCERRADO"; resf = ra or rj or "ENCERRADO"

    casos.append({"nome":nome,"cpf":fmtcpf(cpf),"cpf_limpo":cpf,"num_proc_adm":prot_adm or None,
                  "resultado_adm":ra or None,"resultado_jud":rj or None,
                  "lote":lote_of(cpf),"situacao":situ,"resultado_final":resf})

casos.sort(key=lambda x:str(x["nome"]))
cnt=Counter(c["situacao"] for c in casos)
print("\nTotal casos:",len(casos),"| ",dict(cnt))

json.dump(casos, open(os.path.join(ROOT,"enio_casos.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# métricas para apresentação
def n_adm_decided():
    return sum(1 for cpf in cpfs if adm_res(cpf) in ("DEFERIDO","INDEFERIDO") or adm_res(cpf).startswith("DESIST"))
def n_adm_deferido(): return sum(1 for cpf in cpfs if adm_res(cpf)=="DEFERIDO")
def n_jud_judged():
    return sum(1 for cpf in cpfs if any(k in jud_res(cpf) for k in ("PROCEDENTE","IMPROCEDENTE","EXTINÇÃO")))
def n_jud_proc(): return sum(1 for cpf in cpfs if "PROCEDENTE" in jud_res(cpf) and "IMPROCEDENTE" not in jud_res(cpf))
# pipeline
adm_aguardando=sum(1 for cpf in cpfs if adm_res(cpf)=="" and adm_active(cpf) and not jud_active(cpf) and cpf not in fin_by)
jud_aguardando=sum(1 for cpf in cpfs if jud_active(cpf) and not ("PROCEDENTE" in jud_res(cpf) or "IMPROCEDENTE" in jud_res(cpf)) and cpf not in fin_by)

metrics={
 "total":len(casos),"por_situacao":dict(cnt),
 "ganhos_adm_deferido":n_adm_deferido(),"ganhos_jud_procedente":n_jud_proc(),
 "adm_decididos":n_adm_decided(),"jud_julgados":n_jud_judged(),
 "taxa_adm": round(n_adm_deferido()/n_adm_decided(),4) if n_adm_decided() else 0,
 "taxa_jud": round(n_jud_proc()/n_jud_judged(),4) if n_jud_judged() else 0,
 "pipeline_adm_aguardando":adm_aguardando,"pipeline_jud_aguardando":jud_aguardando,
 "cpfs_enio":sorted(cpfs),
}
json.dump(metrics, open(os.path.join(ROOT,"enio_metrics.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=2)
print("\n=== MÉTRICAS ===")
for k,v in metrics.items():
    if k!="cpfs_enio": print(f"  {k}: {v}")
print(f"  (cpfs_enio: {len(cpfs)} CPFs)")
print("\nSalvos: enio_casos.json, enio_metrics.json")
