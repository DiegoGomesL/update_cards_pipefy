import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib import api, batch
from lib.input_reader import read_file

TAREFAS = [
    {"pipe": "ADM", "arquivo": "input/NMPA_125_ADM_ids.xlsx", "field_id": "terceiro_interessado"},
    {"pipe": "JUD", "arquivo": "input/NMPA_125_JUD_ids.xlsx", "field_id": "terceiro_interassado"},
    {"pipe": "FIN", "arquivo": "input/NMPA_125_FIN_ids.xlsx", "field_id": "terceiro_interessado"},
]

for t in TAREFAS:
    card_ids = read_file(t["arquivo"])
    valores  = batch.fetch_current_values(card_ids, t["field_id"])

    nao_limpos = [(cid, v["nome"], v["value"]) for cid, v in valores.items() if v["value"]]
    limpos     = sum(1 for v in valores.values() if not v["value"])

    print(f"\n=== {t['pipe']} ({len(card_ids)} cards) ===")
    print(f"  Limpos (campo vazio) : {limpos}")
    print(f"  Ainda com valor      : {len(nao_limpos)}")
    if nao_limpos:
        for cid, nome, val in nao_limpos:
            print(f"    [{cid}] {nome} -> '{val}'")

print("\nVerificacao concluida.")
