import sys, json
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from lib import cache

fields = cache.load("305726681")

# Busca por "terceiro"
matches = [f for f in fields if "terceiro" in f["label"].lower() or "terceiro" in f["id"].lower()]
print(f"=== Campos contendo 'terceiro' no ADM ({len(matches)} encontrado(s)) ===")
for f in matches:
    print(f"  [{f['id']}] {f['label']} ({f['type']})")

print(f"\n=== Todos os {len(fields)} campos do ADM ===")
for f in fields:
    print(f"  [{f['id']}] {f['label']}")
