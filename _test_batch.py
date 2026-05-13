"""
Script de validacao da Etapa 3 — batch.py
Testa: fetch_current_values, dry_run, batch real com 3 cards conhecidos.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lib import batch

# Cards reais do ADM usados nos testes anteriores
CARD_IDS  = ["1249121516", "1208415895", "1171726380"]
FIELD_ID  = "escrit_rio"
NEW_VALUE = "Teles&Costa"

print("=" * 55)
print("TESTE DA ETAPA 3 — batch.py")
print("=" * 55)

# 1. Busca valores atuais
print("\n[1] Buscando valores atuais do campo 'escrit_rio'...")
old_values = batch.fetch_current_values(CARD_IDS, FIELD_ID)
for cid, val in old_values.items():
    print(f"  Card {cid}: '{val}'")
assert len(old_values) == 3, "Esperado 3 cards"
print("  OK")

# 2. Dry-run (nao chama API de escrita)
print("\n[2] Dry-run (simula sem alterar nada)...")
progress_log = []
results = batch.run_batch(
    CARD_IDS, FIELD_ID, NEW_VALUE, old_values,
    dry_run=True,
    progress_callback=lambda done, total: progress_log.append((done, total))
)
assert all(r["status"] == "DRY-RUN" for r in results), "Todos deveriam ser DRY-RUN"
assert progress_log[-1] == (3, 3), f"Progress inesperado: {progress_log}"
print(f"  OK — {len(results)} resultados DRY-RUN, progresso: {progress_log}")

# 3. Batch real com 3 cards
print("\n[3] Batch real — atualizando 3 cards (batch de 20)...")
results_real = batch.run_batch(CARD_IDS, FIELD_ID, NEW_VALUE, old_values, dry_run=False)
ok    = [r for r in results_real if r["status"] == "OK"]
falha = [r for r in results_real if r["status"] == "FALHA"]
print(f"  OK: {len(ok)} | Falha: {len(falha)}")
for r in results_real:
    print(f"  Card {r['card_id']}: [{r['status']}] old='{r['old_value']}' -> new='{r['new_value']}'")
    if r["error"]:
        print(f"    erro: {r['error']}")

assert len(ok) == 3, f"Esperado 3 OK, obteve {len(ok)}"
print("  OK — todos atualizados com sucesso")

print(f"\n{'='*55}")
print("Etapa 3 OK.")
print("=" * 55)
