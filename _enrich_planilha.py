"""
Lê a planilha da pasta input/, busca o card_id pelo CPF na API do Pipefy
e salva uma nova versão com a coluna card_id adicionada.
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from pathlib import Path
from lib import api

INPUT_FILE  = Path("input/Nova_Lista_100_atualizada.xlsx")
OUTPUT_FILE = Path("input/Nova_Lista_100_com_id.xlsx")
PIPE_ID     = api.PIPES["ADM"]["id"]   # busca no ADM — ajuste se necessário

# Campo CPF no Pipefy (ID do campo)
CPF_FIELD_ID = "cpf_do_benefici_rio_1"

FIND_QUERY = """
query($pipeId: ID!, $cpf: String!) {
  findCards(pipeId: $pipeId, search: {fieldId: "%s", fieldValue: $cpf}, first: 1) {
    edges {
      node {
        id
        title
      }
    }
  }
}
""" % CPF_FIELD_ID

# ── Leitura da planilha ──────────────────────────────────────
df = pd.read_excel(INPUT_FILE, dtype=str)
df.columns = [c.strip() for c in df.columns]

# Normaliza nome da coluna CPF
cpf_col = next((c for c in df.columns if "cpf" in c.lower() and "benefic" in c.lower()), None)
if not cpf_col:
    print("ERRO: Coluna de CPF não encontrada. Colunas:", list(df.columns))
    sys.exit(1)

print(f"Planilha carregada: {len(df)} linhas | CPF em: '{cpf_col}'")
print(f"Buscando card_ids no pipe ADM...\n")

# ── Busca por CPF ────────────────────────────────────────────
card_ids  = []
nao_encontrados = []

for idx, row in df.iterrows():
    cpf = str(row[cpf_col]).strip().replace(" ", "")
    if not cpf or cpf.lower() == "nan":
        card_ids.append("")
        continue

    try:
        result = api.execute(FIND_QUERY, {"pipeId": PIPE_ID, "cpf": cpf})
        edges  = (result.get("data") or {}).get("findCards", {}).get("edges") or []
        if edges:
            cid   = edges[0]["node"]["id"]
            nome  = edges[0]["node"]["title"]
            card_ids.append(cid)
            print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> card {cid} ({nome})")
        else:
            card_ids.append("")
            nao_encontrados.append(cpf)
            print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> NAO ENCONTRADO")
    except Exception as e:
        card_ids.append("")
        nao_encontrados.append(cpf)
        print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> ERRO: {e}")

    time.sleep(0.2)

# ── Salva com card_id ────────────────────────────────────────
df.insert(0, "card_id", card_ids)
df.to_excel(OUTPUT_FILE, index=False)

encontrados = sum(1 for c in card_ids if c)
print(f"\n{'='*55}")
print(f"Concluido:")
print(f"  Encontrados    : {encontrados}")
print(f"  Nao encontrados: {len(nao_encontrados)}")
print(f"  Arquivo salvo  : {OUTPUT_FILE}")
print(f"{'='*55}")
if nao_encontrados:
    print(f"\nCPFs nao encontrados:")
    for cpf in nao_encontrados:
        print(f"  {cpf}")
