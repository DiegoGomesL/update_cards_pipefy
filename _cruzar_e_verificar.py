import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
from lib import batch

# ── Carrega as duas listas ────────────────────────────────────
# NMPA_125_ADM_ids.xlsx tem todos os 125 CPFs (arquivo original foi removido)
df_nmpa = pd.read_excel("input/NMPA_125_ADM_ids.xlsx", dtype=str)
df_nmpa.columns = [c.strip() for c in df_nmpa.columns]
cpf_col_nmpa = next(c for c in df_nmpa.columns if "cpf" in c.lower())
cpf_nmpa = set(df_nmpa[cpf_col_nmpa].str.replace(r"[\s.\-]", "", regex=True).str.strip())

df_rel = pd.concat([
    pd.read_excel("input/Relatorio_125_Processos Livres.xlsx", sheet_name="Em andamento",              dtype=str),
    pd.read_excel("input/Relatorio_125_Processos Livres.xlsx", sheet_name="Encerrados + Substituição", dtype=str),
], ignore_index=True)
df_rel.columns = [c.strip() for c in df_rel.columns]
cpf_rel = set(df_rel["CPF DO BENEFICIÁRIO"].str.replace(r"[\s.\-]", "", regex=True).str.strip())

so_nmpa = cpf_nmpa - cpf_rel
so_rel  = cpf_rel - cpf_nmpa
comuns  = cpf_nmpa & cpf_rel

print("=== CRUZAMENTO DE CPFs ===")
print(f"  NMPA_125 (ADM_ids)     : {len(cpf_nmpa)} CPFs")
print(f"  Relatorio (ambas abas) : {len(cpf_rel)} CPFs")
print(f"  Em comum               : {len(comuns)}")
print(f"  So na NMPA_125         : {len(so_nmpa)}")
print(f"  So no Relatorio        : {len(so_rel)}")
if so_nmpa:
    nomes = df_nmpa[df_nmpa[cpf_col_nmpa].str.replace(r"[\s.\-]", "", regex=True).str.strip().isin(so_nmpa)]["NOME"].tolist()
    print(f"\n  CPFs apenas na NMPA_125:")
    for n in nomes: print(f"    {n}")
if so_rel:
    nomes = df_rel[df_rel["CPF DO BENEFICIÁRIO"].str.replace(r"[\s.\-]", "", regex=True).str.strip().isin(so_rel)]["NOME DO BENEFICIÁRIO"].tolist()
    print(f"\n  CPFs apenas no Relatorio:")
    for n in nomes: print(f"    {n}")

# ── Verificação na API ────────────────────────────────────────
print("\n=== VERIFICACAO NA API DO PIPEFY ===")

TAREFAS = [
    {"pipe": "ADM", "col": "CÓDIGO ADM",  "field_id": "terceiro_interessado"},
    {"pipe": "JUD", "col": "CÓDIGO JUD",  "field_id": "terceiro_interassado"},
]

total_com_valor = 0
for t in TAREFAS:
    ids = [v.strip() for v in df_rel[t["col"]].dropna() if str(v).strip() not in ("", "nan")]
    if not ids:
        print(f"\n[{t['pipe']}] Sem cards.")
        continue

    valores = batch.fetch_current_values(ids, t["field_id"])
    com_valor = [(cid, v["nome"], v["value"]) for cid, v in valores.items() if v["value"]]
    sem_valor = sum(1 for v in valores.values() if not v["value"])

    print(f"\n[{t['pipe']}] {len(ids)} cards verificados")
    print(f"  Campo vazio (OK) : {sem_valor}")
    print(f"  Ainda com valor  : {len(com_valor)}")
    for cid, nome, val in com_valor:
        print(f"    [{cid}] {nome} -> '{val}'")
    total_com_valor += len(com_valor)

print(f"\n{'='*50}")
if total_com_valor == 0:
    print("RESULTADO: Todos os campos estao limpos no Pipefy.")
else:
    print(f"ATENCAO: {total_com_valor} card(s) ainda com valor!")
