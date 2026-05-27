import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib import batch, reporter

pendentes = ["1351798732", "1352862268", "1353492847", "1351797612", "1351797077"]
field_id  = "terceiro_interassado"

print(f"Limpando {len(pendentes)} cards pendentes no JUD...")
old_values = batch.fetch_current_values(pendentes, field_id)
results    = batch.run_batch(pendentes, field_id, "", old_values,
                             progress_callback=lambda d, t: print(f"  {d}/{t}", end="\r"))

log    = reporter.save(results, "JUD", field_id)
counts = reporter.summary(results)
print()
for status, count in sorted(counts.items()):
    print(f"  {status}: {count}")
print(f"Log: {log}")
