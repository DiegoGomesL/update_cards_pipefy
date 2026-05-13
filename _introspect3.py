import requests, json

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

PIPES = {"ADM": 305726681, "JUD": 305859312, "FIN": 305859195}
TARGET_REPORTS = {301050527, 301050530, 301050531}

def run(query, variables=None):
    r = requests.post(PIPEFY_URL, json={"query": query, "variables": variables or {}}, headers=HEADERS, timeout=30)
    return r.json()

PIPE_QUERY = """
query($pipeId: ID!) {
  pipe(id: $pipeId) {
    id
    uuid
    name
    cards_count
    reports {
      id
      name
      cardCount
    }
  }
}
"""

for label, pid in PIPES.items():
    result = run(PIPE_QUERY, {"pipeId": str(pid)})
    pipe = (result.get("data") or {}).get("pipe")
    if not pipe:
        print(f"[{label}] ERRO: {result.get('errors','sem dados')}")
        continue

    print(f"\n[{label}] Pipe: {pipe['name']} (id={pipe['id']}, uuid={pipe['uuid']})")
    print(f"  Total de cards no pipe: {pipe['cards_count']}")
    print(f"  Relatórios:")
    for rep in (pipe.get("reports") or []):
        marker = " <-- TARGET" if int(rep["id"]) in TARGET_REPORTS else ""
        print(f"    id={rep['id']} | '{rep['name']}' | {rep['cardCount']} cards{marker}")
