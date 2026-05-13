import requests
import time
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# =============================================================================
# VARIÁVEIS GLOBAIS
# =============================================================================

TOKEN = "eyJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJQaXBlZnkiLCJpYXQiOjE3NTcwOTYzNjIsImp0aSI6Ijg3YTE0NTY1LTg3NjQtNDg0MC1hMzg3LTYwMmQ0NDFhY2MyYiIsInN1YiI6MzA2ODkzMDM2LCJ1c2VyIjp7ImlkIjozMDY4OTMwMzYsImVtYWlsIjoibWF0ZXVzc2lsdmFAdGVsZXNlY29zdGEuYWR2LmJyIn0sInVzZXJfdHlwZSI6ImF1dGhlbnRpY2F0ZWQifQ.nAuQRuMs9xm0pYygJudYeWSm9Gjy6OawaTeFiDG36qbS-LtDAc8vk7JcBB9fex04cWRvk0KPD881yVNkgtkt0w"

FIELD_ID  = "escrit_rio"
NEW_VALUE = "Teles&Costa"

# Configuração de cada pipe.
# skip_field / skip_if_contains: pula o card se o campo contiver esse valor.
# (Replica o filtro not_contains do relatório Update_campos do ADM)
PIPES = {
    "ADM": {
        "pipe_id": "305726681",
        "skip_field": "escrit_rio",            # ID do campo Escritório retornado pela API
        "skip_if_contains": "JuanGarcia",      # Não atualizar cards desse escritório
        "expected_cards": 2619,
    },
    "JUD": {
        "pipe_id": "305859312",
        "skip_field": None,
        "skip_if_contains": None,
        "expected_cards": 1247,
    },
    "FIN": {
        "pipe_id": "305859195",
        "skip_field": None,
        "skip_if_contains": None,
        "expected_cards": 450,
    },
}

# =============================================================================
# CONFIGURAÇÃO DA API
# =============================================================================

PIPEFY_URL = "https://api.pipefy.com/graphql"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

# =============================================================================
# QUERIES / MUTATIONS
# =============================================================================

# Busca cards com o valor atual do campo Escritório (para filtrar JuanGarcia no ADM)
CARDS_WITH_FIELD_QUERY = """
query GetCards($pipeId: ID!, $after: String) {
  allCards(pipeId: $pipeId, first: 50, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        fields {
          field { id }
          value
        }
      }
    }
  }
}
"""

# Busca só os IDs (sem campo), para pipes sem filtro de exclusão
CARDS_ONLY_ID_QUERY = """
query GetCards($pipeId: ID!, $after: String) {
  allCards(pipeId: $pipeId, first: 50, after: $after) {
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
      }
    }
  }
}
"""

# field_id e new_value são literais — a API rejeita variáveis para esses argumentos
UPDATE_MUTATION = f"""
mutation UpdateField($cardId: ID!) {{
  updateCardField(input: {{
    card_id:   $cardId
    field_id:  "{FIELD_ID}"
    new_value: "{NEW_VALUE}"
  }}) {{
    success
  }}
}}
"""

# =============================================================================
# FUNÇÕES
# =============================================================================

def _execute(payload: dict) -> dict:
    r = requests.post(PIPEFY_URL, json=payload, headers=HEADERS, timeout=30)
    r.raise_for_status()
    return r.json()


def fetch_card_ids(pipe_id: str, skip_field: str | None, skip_value: str | None) -> list[str]:
    """
    Percorre todas as páginas do pipe.
    Se skip_field/skip_value definidos, lê o campo e exclui os cards que contêm o valor.
    """
    use_field_query = skip_field is not None
    query = CARDS_WITH_FIELD_QUERY if use_field_query else CARDS_ONLY_ID_QUERY

    card_ids: list[str] = []
    skipped   = 0
    cursor: str | None = None
    page = 1

    while True:
        variables = {"pipeId": pipe_id, "after": cursor}
        result = _execute({"query": query, "variables": variables})

        if "errors" in result:
            print(f"  [ERRO ao buscar cards] {result['errors']}")
            break

        data      = result["data"]["allCards"]
        page_info = data["pageInfo"]
        edges     = data["edges"]

        for edge in edges:
            node    = edge["node"]
            card_id = node["id"]

            if use_field_query:
                # Lê o valor atual do campo de filtro
                field_value = ""
                for f in node.get("fields") or []:
                    if f["field"]["id"] == skip_field:
                        field_value = f.get("value") or ""
                        break
                if skip_value and skip_value.lower() in field_value.lower():
                    skipped += 1
                    continue   # pula este card

            card_ids.append(card_id)

        print(f"  Página {page}: {len(edges)} lidos | selecionados até agora: {len(card_ids)}"
              + (f" | ignorados: {skipped}" if use_field_query else ""))

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        page  += 1
        time.sleep(0.3)

    return card_ids


def update_card(card_id: str) -> bool:
    variables = {"cardId": card_id}
    result = _execute({"query": UPDATE_MUTATION, "variables": variables})

    if "errors" in result:
        print(f"    [ERRO API] {result['errors']}")
        return False

    return result["data"]["updateCardField"]["success"]


# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def run_pipe(label: str) -> None:
    cfg = PIPES[label]
    print(f"\n{'='*60}")
    print(f"  PIPE: {label} (id={cfg['pipe_id']}) | esperado: ~{cfg['expected_cards']} cards")
    if cfg["skip_if_contains"]:
        print(f"  Ignorando cards onde '{cfg['skip_field']}' contém '{cfg['skip_if_contains']}'")
    print(f"{'='*60}")

    print(f"\nBuscando cards...")
    try:
        card_ids = fetch_card_ids(cfg["pipe_id"], cfg["skip_field"], cfg["skip_if_contains"])
    except requests.exceptions.RequestException as e:
        print(f"[FALHA DE REDE na busca] {e}")
        return

    print(f"\nTotal a atualizar: {len(card_ids)} cards")
    print(f"Iniciando atualizacao: '{FIELD_ID}' -> '{NEW_VALUE}'\n")

    updated = failed = 0
    for idx, card_id in enumerate(card_ids, 1):
        print(f"  [{idx}/{len(card_ids)}] Card {card_id}...", end=" ", flush=True)
        try:
            ok = update_card(card_id)
            if ok:
                print("OK")
                updated += 1
            else:
                print("FALHOU (success=false)")
                failed += 1
        except requests.exceptions.RequestException as e:
            print(f"FALHA DE REDE — {e}")
            failed += 1
        time.sleep(0.3)

    print(f"\n{'='*60}")
    print(f"  {label} concluído: {updated} atualizados | {failed} falhas")
    print(f"{'='*60}\n")


def main() -> None:
    # Uso: py update_cards_by_report.py ADM
    #      py update_cards_by_report.py JUD
    #      py update_cards_by_report.py FIN
    if len(sys.argv) < 2 or sys.argv[1].upper() not in PIPES:
        print(f"Uso: py update_cards_by_report.py <PIPE>")
        print(f"Pipes disponíveis: {', '.join(PIPES.keys())}")
        sys.exit(1)

    label = sys.argv[1].upper()
    run_pipe(label)


if __name__ == "__main__":
    main()
