import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib import batch, reporter

CARD_IDS  = ["1249121516", "1208415895", "1171726380"]
FIELD_ID  = "escrit_rio"
NEW_VALUE = "Teles&Costa"

print("Buscando valores atuais + nome do beneficiario...")
old_values = batch.fetch_current_values(CARD_IDS, FIELD_ID)
for cid, info in old_values.items():
    nome  = info["nome"]
    valor = info["value"]
    print(f"  {cid} | nome={nome} | valor={valor}")

print()
print("Rodando batch (dry-run)...")
results = batch.run_batch(CARD_IDS, FIELD_ID, NEW_VALUE, old_values, dry_run=True)
for r in results:
    print(f"  {r['card_id']} | {r['nome']} | {r['old_value']} -> {r['new_value']} | {r['status']}")

print()
path = reporter.save(results, "ADM", FIELD_ID, dry_run=True)
print(f"Log salvo: {path}")

with open(path, encoding="utf-8-sig") as f:
    print()
    print("Conteudo do CSV:")
    print(f.read())
