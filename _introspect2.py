import requests, json

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

def run(query, variables=None):
    r = requests.post(PIPEFY_URL, json={"query": query, "variables": variables or {}}, headers=HEADERS, timeout=30)
    return r.json()

# 1. Argumentos de pipeReports
q1 = """
query {
  __type(name: "Query") {
    fields(includeDeprecated: true) {
      name
      args { name type { name kind ofType { name kind } } }
    }
  }
}
"""
data = run(q1)
fields = data["data"]["__type"]["fields"]
for f in fields:
    if f["name"] in ("pipeReports", "cards", "allCards", "pipeReportExport"):
        print(f"\n=== {f['name']} — argumentos ===")
        for a in f["args"]:
            t = a["type"]
            type_name = t.get("name") or f"{t.get('kind')}({t.get('ofType',{}).get('name','')})"
            print(f"  {a['name']}: {type_name}")

# 2. Campos do tipo PipeReport
q2 = """
query {
  __type(name: "PipeReport") {
    fields { name description type { name kind ofType { name kind } } }
  }
}
"""
data2 = run(q2)
print("\n=== Campos do tipo PipeReport ===")
if data2["data"]["__type"]:
    for f in data2["data"]["__type"]["fields"]:
        t = f["type"]
        type_name = t.get("name") or f"{t.get('kind')}({t.get('ofType',{}).get('name','')})"
        print(f"  {f['name']:<30} {type_name:<30} {f.get('description') or ''}")
else:
    print("  Tipo PipeReport nao encontrado")

# 3. Tenta query direta com pipeReports passando os IDs conhecidos
q3 = """
query {
  pipeReports(ids: [301050527]) {
    id
    name
  }
}
"""
data3 = run(q3)
print("\n=== Teste pipeReports(ids:[301050527]) ===")
print(json.dumps(data3, indent=2, ensure_ascii=False)[:1000])
