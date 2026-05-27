import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import json
from pathlib import Path

cache = json.loads(Path("cache/pipe_fields.json").read_text(encoding="utf-8"))
fin_fields = cache.get("305859195", [])
matches = [f for f in fin_fields if "terceiro" in f["id"].lower() or "terceiro" in f["label"].lower()]
print(f"FIN tem {len(fin_fields)} campos. Matches 'terceiro':")
for f in matches:
    print(f"  id={f['id']}  label={f['label']}  type={f['type']}")
