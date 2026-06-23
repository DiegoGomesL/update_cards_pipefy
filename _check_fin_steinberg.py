import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
from lib import api

ARQUIVOS = {
    "STEINBERG&TELES": "input/Relatorio_171_Steinberg_Teles.xlsx",
    "TELES&STEINBERG": "input/Relatorio_171_Teles_Steinberg.xlsx",
}
CPF_FIELD_FIN = "cpf_do_benefici_rio"
PIPE_ID_FIN   = api.PIPES["FIN"]["id"]

FIND_QUERY = """
query($pipeId: ID!, $cpf: String!) {
  findCards(pipeId: $pipeId, search: {fieldId: "cpf_do_benefici_rio", fieldValue: $cpf}, first: 1) {
    edges { node { id title } }
  }
}
"""

# Coleta todos os CPFs únicos das duas listas (ambas as abas)
todos_cpfs = {}  # cpf_limpo -> (nome, valor)
for valor, arq in ARQUIVOS.items():
    for aba in pd.ExcelFile(arq).sheet_names:
        df = pd.read_excel(arq, sheet_name=aba, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        for _, row in df.iterrows():
            cpf_raw = str(row.get("CPF DO BENEFICIÁRIO", "")).strip()
            cpf     = cpf_raw.replace(".", "").replace("-", "").replace(" ", "")
            nome    = str(row.get("NOME DO BENEFICIÁRIO", "")).strip()
            if cpf and cpf.lower() != "nan":
                todos_cpfs[cpf] = {"nome": nome, "cpf_raw": cpf_raw, "valor": valor}

print(f"Total de CPFs únicos nas duas listas: {len(todos_cpfs)}\n")
print("Buscando no pipe FIN...")

encontrados = []
nao_encontrados = 0

for i, (cpf, info) in enumerate(todos_cpfs.items()):
    for cpf_fmt in [info["cpf_raw"], cpf]:
        try:
            result = api.execute(FIND_QUERY, {"pipeId": PIPE_ID_FIN, "cpf": cpf_fmt})
            edges  = (result.get("data") or {}).get("findCards", {}).get("edges") or []
            if edges:
                cid = edges[0]["node"]["id"]
                encontrados.append({"card_id": cid, "nome": info["nome"], "cpf": info["cpf_raw"], "valor": info["valor"]})
                print(f"  [{i+1}/{len(todos_cpfs)}] {info['cpf_raw']} -> {cid} ({info['nome']}) [{info['valor']}]")
                break
        except Exception as e:
            print(f"  [{i+1}/{len(todos_cpfs)}] {info['cpf_raw']} -> ERRO: {e}")
            break
    else:
        nao_encontrados += 1
    time.sleep(0.15)

print(f"\n{'='*55}")
print(f"Encontrados no FIN : {len(encontrados)}")
print(f"Não encontrados    : {nao_encontrados}")
