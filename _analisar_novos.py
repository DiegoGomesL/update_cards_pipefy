import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
from pathlib import Path

ARQUIVOS = [
    "input/Relatorio_171_Steinberg_Teles.xlsx",
    "input/Relatorio_171_Teles_Steinberg.xlsx",
]

for arq in ARQUIVOS:
    print(f"\n{'='*60}")
    print(f"ARQUIVO: {Path(arq).name}")
    wb_abas = pd.ExcelFile(arq).sheet_names
    for aba in wb_abas:
        df = pd.read_excel(arq, sheet_name=aba, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        col_ti = "TERCEIRO INTERESSADO"
        preenchidos = df[df[col_ti].notna() & (df[col_ti].str.strip() != "")] if col_ti in df.columns else pd.DataFrame()
        tem_cod_adm = any("CÓDIGO ADM" in c or "CODIGO ADM" in c for c in df.columns)
        tem_cod_jud = any("CÓDIGO JUD" in c or "CODIGO JUD" in c for c in df.columns)
        tem_cpf     = any("CPF" in c for c in df.columns)

        print(f"\n  Aba [{aba}]: {len(df)} linhas")
        print(f"    TERCEIRO preenchido : {len(preenchidos)}")
        print(f"    Tem CÓDIGO ADM      : {tem_cod_adm}")
        print(f"    Tem CÓDIGO JUD      : {tem_cod_jud}")
        print(f"    Tem CPF             : {tem_cpf}")
        if len(preenchidos) > 0:
            print(f"    Exemplo TERCEIRO    : {preenchidos[col_ti].iloc[0]}")
        if tem_cod_adm:
            col = next(c for c in df.columns if "CÓDIGO ADM" in c or "CODIGO ADM" in c)
            ids = df[col].dropna()
            print(f"    CÓDIGO ADM          : {len(ids)} preenchidos")
        if tem_cod_jud:
            col = next(c for c in df.columns if "CÓDIGO JUD" in c or "CODIGO JUD" in c)
            ids = df[col].dropna()
            print(f"    CÓDIGO JUD          : {len(ids)} preenchidos")
