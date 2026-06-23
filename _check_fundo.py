import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib import api

for label, info in api.PIPES.items():
    fields = api.fetch_pipe_fields(info["id"], force_refresh=True)
    matches = [f for f in fields if "fundo" in f["id"].lower() or "fundo" in f["label"].lower()
               or "invest" in f["id"].lower() or "invest" in f["label"].lower()
               or "terceiro" in f["id"].lower() or "terceiro" in f["label"].lower()]
    print(f"\n=== {label} ({len(fields)} campos) ===")
    for f in matches:
        print(f"  {f['id']:45s} {f['label']}  [{f['type']}]")
    if not matches:
        print("  (nenhum match)")
