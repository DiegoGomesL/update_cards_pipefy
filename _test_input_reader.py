"""
Script de validação da Etapa 2 — input_reader.py
Cria arquivos de teste temporários e valida todos os cenários.
"""
import sys, shutil
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from pathlib import Path
from lib.input_reader import read_file, InputError

TMP = Path("_tmp_test_files")
TMP.mkdir(exist_ok=True)

passed = 0
failed = 0

def check(label, fn):
    global passed, failed
    try:
        fn()
        print(f"  OK  {label}")
        passed += 1
    except AssertionError as e:
        print(f"  FALHOU  {label}: {e}")
        failed += 1
    except Exception as e:
        print(f"  ERRO    {label}: {e}")
        failed += 1

print("=" * 55)
print("TESTE DA ETAPA 2 — input_reader.py")
print("=" * 55)

# 1. CSV valido com colunas extras
csv_valido = TMP / "valido.csv"
pd.DataFrame({
    "card_id": ["1249121516", "1208415895", "1171726380"],
    "nome":    ["JOSE", "MARIA", "PEDRO"],
    "cpf":     ["111", "222", "333"],
}).to_csv(csv_valido, index=False)

print("\n[1] CSV valido com colunas extras:")
def t1():
    ids = read_file(str(csv_valido))
    assert ids == ["1249121516", "1208415895", "1171726380"], f"inesperado: {ids}"
check("Le 3 card_ids e ignora colunas extras", t1)

# 2. Excel valido
xlsx_valido = TMP / "valido.xlsx"
pd.DataFrame({
    "card_id": ["1111111111", "2222222222"],
    "obs":     ["a", "b"],
}).to_excel(xlsx_valido, index=False)

print("\n[2] Excel (.xlsx) valido:")
def t2():
    ids = read_file(str(xlsx_valido))
    assert ids == ["1111111111", "2222222222"], f"inesperado: {ids}"
check("Le .xlsx corretamente", t2)

# 3. CSV com duplicatas
csv_dup = TMP / "duplicatas.csv"
pd.DataFrame({"card_id": ["AAA", "BBB", "AAA", "CCC", "BBB"]}).to_csv(csv_dup, index=False)

print("\n[3] CSV com duplicatas:")
def t3():
    ids = read_file(str(csv_dup))
    assert ids == ["AAA", "BBB", "CCC"], f"inesperado: {ids}"
check("Remove duplicatas mantendo ordem", t3)

# 4. CSV com linhas vazias
csv_vazio = TMP / "vazios.csv"
pd.DataFrame({"card_id": ["X1", None, "X2", "", "X3"]}).to_csv(csv_vazio, index=False)

print("\n[4] CSV com linhas vazias:")
def t4():
    ids = read_file(str(csv_vazio))
    assert ids == ["X1", "X2", "X3"], f"inesperado: {ids}"
check("Descarta linhas vazias", t4)

# 5. Coluna CARD_ID em maiusculo
csv_upper = TMP / "upper.csv"
pd.DataFrame({"CARD_ID": ["Z1", "Z2"], "NOME": ["a", "b"]}).to_csv(csv_upper, index=False)

print("\n[5] Coluna CARD_ID em maiusculo:")
def t5():
    ids = read_file(str(csv_upper))
    assert ids == ["Z1", "Z2"], f"inesperado: {ids}"
check("Aceita card_id case-insensitive", t5)

# 6. Arquivo sem coluna card_id
csv_sem_col = TMP / "sem_coluna.csv"
pd.DataFrame({"nome": ["JOSE"], "cpf": ["111"]}).to_csv(csv_sem_col, index=False)

print("\n[6] Arquivo sem coluna card_id:")
def t6():
    try:
        read_file(str(csv_sem_col))
        assert False, "deveria ter lancado InputError"
    except InputError as e:
        assert "card_id" in str(e).lower()
check("Lanca InputError com mensagem clara", t6)

# 7. Arquivo inexistente
print("\n[7] Arquivo inexistente:")
def t7():
    try:
        read_file("nao_existe.xlsx")
        assert False, "deveria ter lancado InputError"
    except InputError as e:
        assert "encontrado" in str(e).lower()
check("Lanca InputError de arquivo nao encontrado", t7)

# 8. Formato invalido
txt_file = TMP / "arquivo.txt"
txt_file.write_text("card_id\n123\n")
print("\n[8] Formato .txt (nao suportado):")
def t8():
    try:
        read_file(str(txt_file))
        assert False, "deveria ter lancado InputError"
    except InputError as e:
        assert "formato" in str(e).lower()
check("Lanca InputError para formato invalido", t8)

# Limpeza
shutil.rmtree(TMP)

print(f"\n{'='*55}")
print(f"Resultado: {passed} passaram | {failed} falharam")
if failed == 0:
    print("Etapa 2 OK.")
print("=" * 55)
