import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib import batch, reporter
from lib.input_reader import read_file

card_ids  = read_file("input/NMPA_125_FIN_ids.xlsx")
field_id  = "terceiro_interessado"

print(f"FIN — {len(card_ids)} cards — limpando '{field_id}'...")
old_values = batch.fetch_current_values(card_ids, field_id)

results = batch.run_batch(card_ids, field_id, "", old_values,
                          progress_callback=lambda d, t: print(f"  {d}/{t}", end="\r"))

log = reporter.save(results, "FIN", field_id)
counts = reporter.summary(results)
print()
for status, count in sorted(counts.items()):
    print(f"  {status}: {count}")
print(f"Log: {log}")
