"""
Busca campos dos pipes e filtra por palavra-chave.
Uso: py _check_fields.py [palavra]   (padrao: terceiro)
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lib import api

kw = sys.argv[1].lower() if len(sys.argv) > 1 else "terceiro"

for label, info in api.PIPES.items():
    fields = api.fetch_pipe_fields(info["id"], force_refresh=True)
    matches = [f for f in fields if kw in f["id"].lower() or kw in f["label"].lower()]
    print(f"\n=== {label} ({info['id']}) — {len(fields)} campos ===")
    if matches:
        for f in matches:
            print(f"  {f['id']:45s} {f['label']}  [{f['type']}]")
    else:
        print(f"  (nenhum campo com '{kw}')")
