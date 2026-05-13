import requests, json

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

PIPES = [
    {"label": "ADM", "pipe_id": 305726681, "uuid": "f02111d4-176b-4630-8f17-1e976f65feb6", "report_id": "301050527"},
    {"label": "JUD", "pipe_id": 305859312, "uuid": "4664be35-c3ad-422a-849f-1fedefb2d357", "report_id": "301050530"},
    {"label": "FIN", "pipe_id": 305859195, "uuid": "1a156047-bfe4-4a1e-b45e-ab6ee3128731", "report_id": "301050531"},
]

def run(query, variables=None):
    r = requests.post(PIPEFY_URL, json={"query": query, "variables": variables or {}}, headers=HEADERS, timeout=30)
    return r.json()

REPORT_QUERY = """
query($uuid: String!, $reportId: ID) {
  pipeReports(pipeUuid: $uuid, reportId: $reportId, first: 1) {
    edges {
      node {
        id
        name
        cardCount
        filter
      }
    }
  }
}
"""

for p in PIPES:
    result = run(REPORT_QUERY, {"uuid": p["uuid"], "reportId": p["report_id"]})
    if "errors" in result:
        print(f"[{p['label']}] ERRO: {result['errors']}")
        continue
    edges = result["data"]["pipeReports"]["edges"]
    if not edges:
        print(f"[{p['label']}] Nenhum relatório retornado")
        continue
    node = edges[0]["node"]
    print(f"\n[{p['label']}] Report: {node['name']} (id={node['id']}, {node['cardCount']} cards)")
    print(f"  filter JSON: {json.dumps(node['filter'], ensure_ascii=False, indent=2)}")
