# -*- coding: utf-8 -*-
"""Valida a lista 'Livres - Pipefy.xlsx' contra o Pipefy ao vivo.
Livre = 3 vínculos vazios (Terceiro/Fundo Inv/Fundo Esp) + NÃO no financeiro + em andamento.
Casamento por NOME (arquivo não tem CPF)."""
import sys, re, os, unicodedata
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import openpyxl
from collections import defaultdict
import _paths
from lib import api

ADM=api.PIPES["ADM"]["id"]; JUD=api.PIPES["JUD"]["id"]; FIN=api.PIPES["FIN"]["id"]
ARQ=_paths.src("Livres - Pipefy.xlsx")

FID={"ADM":{"nome":"nome_do_benefici_rio","terc":"terceiro_interessado","inv":"fundo_investidor","esp":"copy_of_fundo_investidor","cpf":"cpf_do_benefici_rio_1"},
     "JUD":{"nome":"nome_do_benefici_rio","terc":"terceiro_interassado","inv":"fundo_investidor","esp":"copy_of_fundo_investidor","cpf":"cpf_do_benefici_rio"},
     "FIN":{"nome":"nome_do_benefici_rio","terc":"terceiro_interessado","inv":"fundo_investidor","esp":"copy_of_fundo_investidor","cpf":"cpf_do_benefici_rio"}}
ADM_TERM={"ENCERRADOS","DESCARTADOS"}; JUD_TERM={"ENCERRADOS","PROCEDENTES"}

def norm(s):
    s=unicodedata.normalize("NFKD",str(s or "")).encode("ascii","ignore").decode().upper()
    return re.sub(r"\s+"," ",s).strip()
def nz(v): return (str(v).strip() if v is not None else "")

Q="""query($pipeId:ID!,$after:String){ allCards(pipeId:$pipeId,first:50,after:$after){
 pageInfo{hasNextPage endCursor} edges{node{ id current_phase{name} fields{ value field{id} } }}}}"""
def pull(pid,kind):
    out=[]; after=None
    while True:
        r=api.execute(Q,{"pipeId":pid,"after":after}); d=r["data"]["allCards"]
        for e in d["edges"]:
            n=e["node"]; fm={(f.get("field") or {}).get("id"):f.get("value") for f in (n.get("fields") or [])}
            fi=FID[kind]
            out.append({"kind":kind,"phase":nz((n.get("current_phase") or {}).get("name")),
                "nome":nz(fm.get(fi["nome"])),"terc":nz(fm.get(fi["terc"])),
                "inv":nz(fm.get(fi["inv"])),"esp":nz(fm.get(fi["esp"])),"cpf":nz(fm.get(fi["cpf"]))})
        if not d["pageInfo"]["hasNextPage"]: break
        after=d["pageInfo"]["endCursor"]
    return out

print("Buscando Pipefy (ADM/JUD/FIN)...")
cards=pull(ADM,"ADM")+pull(JUD,"JUD")+pull(FIN,"FIN")
by_nome=defaultdict(list)
for c in cards: by_nome[norm(c["nome"])].append(c)
print(f"  cards totais: {len(cards)}\n")

wb=openpyxl.load_workbook(ARQ,data_only=True); ws=wb.active
nomes=[r[1] for r in ws.iter_rows(min_row=2,values_only=True) if r[1]]

print(f"{'#':>2} {'NOME':42} {'VEREDITO':12} DETALHE")
print("-"*120)
ok=0
for i,nome in enumerate(nomes,1):
    cs=by_nome.get(norm(nome),[])
    if not cs:
        print(f"{i:2} {nome[:42]:42} {'? N/ENCONTR':12} nenhum card casou pelo nome")
        continue
    pipes=sorted(set(c["kind"] for c in cs))
    in_fin=any(c["kind"]=="FIN" for c in cs)
    vinc=[(c["kind"],c["terc"] or c["inv"] or c["esp"]) for c in cs if (c["terc"] or c["inv"] or c["esp"])]
    def active(c):
        ph=c["phase"].upper(); term=ADM_TERM if c["kind"]=="ADM" else (JUD_TERM if c["kind"]=="JUD" else set())
        return ph not in term
    tem_ativo=any(active(c) for c in cs if c["kind"] in ("ADM","JUD"))
    fases="; ".join(f"{c['kind']}:{c['phase']}" for c in cs)

    motivos=[]
    if in_fin: motivos.append("ESTÁ NO FINANCEIRO")
    if vinc:   motivos.append("VÍNCULO: "+", ".join(f"{k}={v}" for k,v in vinc))
    if not tem_ativo: motivos.append("sem card ativo (não em andamento)")
    veredito="LIVRE ✓" if not motivos else "NÃO LIVRE"
    if not motivos: ok+=1
    print(f"{i:2} {nome[:42]:42} {veredito:12} [{','.join(pipes)}] {fases}")
    if motivos: print(f"   {'':42} {'':12} -> "+" | ".join(motivos))

print("-"*120)
print(f"LIVRES confirmados: {ok}/{len(nomes)}")
