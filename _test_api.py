"""
Script de validação da Etapa 1.
Testa: carregamento do .env, conexão com a API, busca de campos e cache.
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from lib import api, cache

PIPE_LABEL = "ADM"
PIPE_ID    = api.PIPES[PIPE_LABEL]["id"]

print("=" * 55)
print("TESTE DA ETAPA 1 — api.py + cache.py")
print("=" * 55)

# 1. Conexão básica
print("\n[1] Testando conexão com a API do Pipefy...")
result = api.execute("{ me { id email name } }")
if "errors" in result:
    print(f"  FALHOU: {result['errors']}")
    sys.exit(1)
me = result["data"]["me"]
print(f"  OK — autenticado como: {me['name']} ({me['email']})")

# 2. Busca de campos (força refresh para testar a API, não o cache)
print(f"\n[2] Buscando campos do pipe {PIPE_LABEL} (force_refresh=True)...")
fields = api.fetch_pipe_fields(PIPE_ID, force_refresh=True)
print(f"  OK — {len(fields)} campos encontrados. Primeiros 10:")
for f in fields[:10]:
    print(f"    [{f['id']}] {f['label']} ({f['type']})")

# 3. Verifica cache gravado
print(f"\n[3] Verificando cache gravado...")
cached = cache.load(PIPE_ID)
if cached is None:
    print("  FALHOU: cache não foi gravado")
    sys.exit(1)
print(f"  OK — cache contém {len(cached)} campos para o pipe {PIPE_ID}")

# 4. Segunda leitura deve vir do cache (sem chamar a API)
print(f"\n[4] Segunda leitura (deve vir do cache, sem chamada à API)...")
fields_cached = api.fetch_pipe_fields(PIPE_ID, force_refresh=False)
print(f"  OK — {len(fields_cached)} campos retornados do cache")

# 5. Valida 1 card_id conhecido (card do teste anterior)
print(f"\n[5] Validando card_id conhecido (1249121516)...")
result_val = api.validate_card_ids(PIPE_ID, ["1249121516", "0000000000"])
print(f"  Válidos    : {result_val['valid']}")
print(f"  Não encontrados: {result_val['not_found']}")

print("\n" + "=" * 55)
print("Todos os testes passaram. Etapa 1 OK.")
print("=" * 55)
