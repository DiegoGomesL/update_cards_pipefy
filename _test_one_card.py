# -*- coding: utf-8 -*-
import requests, json, sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def run(q, v=None):
    r = requests.post(PIPEFY_URL, json={"query": q, "variables": v or {}}, headers=HEADERS, timeout=30)
    return r.json()

# 1. Busca 1 card do ADM com todos os campos
fetch = run("""
query {
  allCards(pipeId: "305726681", first: 1) {
    edges {
      node {
        id
        title
        fields {
          field { id label }
          value
        }
      }
    }
  }
}
""")

if "errors" in fetch:
    print("ERRO na busca:", fetch["errors"])
    sys.exit(1)

node    = fetch["data"]["allCards"]["edges"][0]["node"]
card_id = node["id"]
print(f"Card: id={card_id} | titulo={node['title']}")
print("\nTodos os campos:")
escritorio_value = ""
for f in node["fields"]:
    fid   = f["field"]["id"]
    label = f["field"]["label"]
    value = f.get("value") or ""
    print(f"  [{fid}] {label}: {value[:80]}")
    if fid == "field_151_string":
        escritorio_value = value

print(f"\nValor atual do campo 'field_151_string' (Escritório): '{escritorio_value}'")

# 2. Testa mutation
print(f"\nAtualizando campo 'escrit_rio' → 'Teles&Costa' no card {card_id}...")
mut = run("""
mutation($cardId: ID!) {
  updateCardField(input: {
    card_id:   $cardId
    field_id:  "escrit_rio"
    new_value: "Teles&Costa"
  }) {
    success
  }
}
""", {"cardId": card_id})

if "errors" in mut:
    print("ERRO na mutation:", mut["errors"])
else:
    success = mut["data"]["updateCardField"]["success"]
    print(f"Mutation resultado: {'OK - campo atualizado!' if success else 'FALHOU (success=false)'}")
