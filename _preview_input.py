import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib.input_reader import read_file

ids = read_file(r"input\Nova_Lista_100_atualizada.xlsx")
print(f"Total de card_ids carregados: {len(ids)}")
print("\nPrimeiros 10:")
for i in ids[:10]:
    print(f"  {i}")
if len(ids) > 10:
    print(f"  ... e mais {len(ids) - 10}")
