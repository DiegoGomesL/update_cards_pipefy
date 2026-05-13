import requests, sys, time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
PIPEFY_URL = "https://api.pipefy.com/graphql"

FAILED_CARDS = [
    {"id": "1208415895", "pipe": "ADM"},
    {"id": "1171726380", "pipe": "JUD"},
    {"id": "1222682723", "pipe": "JUD"},
]

MUTATION = """
mutation($cardId: ID!) {
  updateCardField(input: {
    card_id:   $cardId
    field_id:  "escrit_rio"
    new_value: "Teles&Costa"
  }) {
    success
  }
}
"""

print(f"Re-tentando {len(FAILED_CARDS)} cards com falha...\n")
ok = 0
fail = 0
for c in FAILED_CARDS:
    print(f"  [{c['pipe']}] Card {c['id']}...", end=" ", flush=True)
    try:
        r = requests.post(PIPEFY_URL, json={"query": MUTATION, "variables": {"cardId": c["id"]}},
                          headers=HEADERS, timeout=30)
        data = r.json()
        if "errors" in data:
            print(f"ERRO — {data['errors'][0]['message']}")
            fail += 1
        elif data["data"]["updateCardField"]["success"]:
            print("OK")
            ok += 1
        else:
            print("FALHOU (success=false)")
            fail += 1
    except Exception as e:
        print(f"EXCECAO — {e}")
        fail += 1
    time.sleep(0.3)

print(f"\nResultado: {ok} atualizados | {fail} falhas")
