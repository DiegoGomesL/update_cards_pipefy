import requests
import time

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"
REPORT_IDS = [301050527, 301050530, 301050531]
PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}

REPORT_QUERY = """
query GetReportCards($reportId: ID!, $after: String) {
  pipeReport(id: $reportId) {
    id
    name
    table_records(first: 50, after: $after) {
      pageInfo { hasNextPage endCursor }
      edges { node { record_id } }
    }
  }
}
"""

totals = {}
for report_id in REPORT_IDS:
    card_ids = []
    cursor = None
    page = 1
    report_name = "?"
    print(f"Consultando relatorio {report_id}...")
    try:
        while True:
            variables = {"reportId": str(report_id), "after": cursor}
            r = requests.post(PIPEFY_URL, json={"query": REPORT_QUERY, "variables": variables}, headers=HEADERS, timeout=30)
            data = r.json()
            if "errors" in data:
                print(f"  ERRO: {data['errors']}")
                break
            rd = data["data"]["pipeReport"]
            report_name = rd["name"]
            tr = rd["table_records"]
            pi = tr["pageInfo"]
            batch = [e["node"]["record_id"] for e in tr["edges"] if e["node"]["record_id"]]
            card_ids.extend(batch)
            print(f"  Pagina {page}: {len(batch)} cards coletados")
            if not pi["hasNextPage"]:
                break
            cursor = pi["endCursor"]
            page += 1
            time.sleep(0.3)
    except Exception as e:
        print(f"  EXCECAO: {e}")
    totals[report_id] = (report_name, len(card_ids))
    print(f'  => "{report_name}": {len(card_ids)} cards')
    print()

print("=" * 50)
print("RESUMO FINAL")
print("=" * 50)
grand = 0
for rid, (name, count) in totals.items():
    print(f"  [{rid}] {name}: {count} cards")
    grand += count
print(f"  TOTAL GERAL: {grand} cards")
print("=" * 50)
