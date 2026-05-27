"""
Adiciona card_id a NMPA_125_processos_livres.xlsx buscando por CPF.
Gera dois arquivos:
  input/NMPA_125_ADM_ids.xlsx  — cards encontrados no pipe ADM
  input/NMPA_125_JUD_ids.xlsx  — cards encontrados no pipe JUD

Uso: py _enrich_nmpa_125.py [ADM|JUD|AMBOS]   (padrão: AMBOS)
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd
from lib import api

INPUT_FILE = Path("input/NMPA_125_processos_livres.xlsx")

PIPE_CFG = {
    "ADM": {"id": api.PIPES["ADM"]["id"], "cpf_field": "cpf_do_benefici_rio_1",
            "filter_col": "TERCEIRO ADM"},
    "JUD": {"id": api.PIPES["JUD"]["id"], "cpf_field": "cpf_do_benefici_rio",
            "filter_col": "TERCEIRO JUD"},
    "FIN": {"id": api.PIPES["FIN"]["id"], "cpf_field": "cpf_do_benefici_rio",
            "filter_col": None, "terceiro_field": "terceiro_interessado"},
}

FIND_QUERY = """
query($pipeId: ID!, $cpf: String!) {
  findCards(pipeId: $pipeId, search: {fieldId: "%s", fieldValue: $cpf}, first: 1) {
    edges { node { id title } }
  }
}
"""


def buscar_ids(df: pd.DataFrame, pipe_label: str) -> pd.DataFrame:
    cfg        = PIPE_CFG[pipe_label]
    pipe_id    = cfg["id"]
    cpf_field  = cfg["cpf_field"]
    filter_col = cfg["filter_col"]
    query      = FIND_QUERY % cpf_field

    if filter_col and filter_col in df.columns:
        def tem_valor(v):
            if pd.isna(v):
                return False
            s = str(v).strip()
            return s != "" and "(n" not in s.lower()  # filtra "(nao esta)" / "(não está)"
        df_filtrado = df[df[filter_col].apply(tem_valor)].copy()
        print(f"\n[{pipe_label}] {len(df_filtrado)} linhas com '{filter_col}' preenchido de {len(df)} total")
    else:
        df_filtrado = df.copy()
        print(f"\n[{pipe_label}] {len(df_filtrado)} linhas (sem filtro de coluna)")

    card_ids = []
    nao_encontrados = []

    for idx, (orig_idx, row) in enumerate(df_filtrado.iterrows()):
        cpf_raw = str(row.get("CPF", "")).strip()
        cpf     = cpf_raw.replace(".", "").replace("-", "").replace(" ", "")

        if not cpf or cpf.lower() == "nan":
            card_ids.append("")
            continue

        found = False
        for cpf_fmt in [cpf_raw, cpf]:
            try:
                result = api.execute(query, {"pipeId": pipe_id, "cpf": cpf_fmt})
                edges  = (result.get("data") or {}).get("findCards", {}).get("edges") or []
                if edges:
                    cid  = edges[0]["node"]["id"]
                    nome = edges[0]["node"]["title"]
                    card_ids.append(cid)
                    print(f"  [{idx+1}/{len(df_filtrado)}] {cpf_raw} -> {cid} ({nome})")
                    found = True
                    break
            except Exception as e:
                print(f"  [{idx+1}/{len(df_filtrado)}] {cpf_raw} -> ERRO: {e}")
                break

        if not found:
            card_ids.append("")
            nao_encontrados.append(cpf_raw)
            print(f"  [{idx+1}/{len(df_filtrado)}] {cpf_raw} -> NAO ENCONTRADO")

        time.sleep(0.2)

    df_filtrado = df_filtrado.copy()
    df_filtrado.insert(0, "card_id", card_ids)

    encontrados = sum(1 for c in card_ids if c)
    print(f"\n  Encontrados    : {encontrados}")
    print(f"  Nao encontrados: {len(nao_encontrados)}")
    if nao_encontrados:
        for cpf in nao_encontrados:
            print(f"    {cpf}")

    return df_filtrado


def main():
    pipes_alvo = sys.argv[1].upper().split(",") if len(sys.argv) > 1 else ["ADM", "JUD"]
    if pipes_alvo == ["AMBOS"]:
        pipes_alvo = ["ADM", "JUD"]

    df = pd.read_excel(str(INPUT_FILE), dtype=str)
    df.columns = [c.strip() for c in df.columns]
    print(f"Planilha: {INPUT_FILE.name} — {len(df)} linhas")

    for pipe_label in pipes_alvo:
        if pipe_label not in PIPE_CFG:
            print(f"Pipe desconhecido: {pipe_label}  (use ADM, JUD, ou AMBOS)")
            continue

        df_saida  = buscar_ids(df, pipe_label)
        output    = INPUT_FILE.parent / f"NMPA_125_{pipe_label}_ids.xlsx"
        df_saida.to_excel(str(output), index=False)
        print(f"  Arquivo salvo  : {output}")

    print("\nConcluido.")


if __name__ == "__main__":
    main()
