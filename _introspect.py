import requests

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

# Lista todos os campos disponíveis na raiz do tipo Query
introspection = """
query {
  __type(name: "Query") {
    fields {
      name
      description
    }
  }
}
"""

r = requests.post(PIPEFY_URL, json={"query": introspection}, headers=HEADERS, timeout=30)
data = r.json()

if "errors" in data:
    print("ERRO:", data["errors"])
else:
    fields = data["data"]["__type"]["fields"]
    print(f"Campos disponíveis na Query ({len(fields)} total):\n")
    for f in sorted(fields, key=lambda x: x["name"]):
        desc = f.get("description") or ""
        print(f"  {f['name']:<35} {desc[:80]}")
