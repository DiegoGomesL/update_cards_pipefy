import requests
import time

# =============================================================================
# CONFIGURAÇÃO — preencha estas variáveis antes de executar
# =============================================================================

API_TOKEN = "SEU_TOKEN_AQUI"          # Cole aqui seu Bearer Token do Pipefy

PIPE_IDS = [                           # IDs dos painéis (Pipes) que serão processados
    123456,
    789012,
]

FIELD_ID  = "nome_do_campo"            # ID do campo a ser atualizado (string)
NEW_VALUE = "novo_valor"               # Novo valor a ser gravado no campo

# Intervalo entre requisições (segundos) — evita rate-limit da API
REQUEST_DELAY = 0.3

# =============================================================================
# CONFIGURAÇÃO DA API
# =============================================================================

PIPEFY_URL = "https://api.pipefy.com/graphql"

HEADERS = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json",
}

# =============================================================================
# QUERIES / MUTATIONS
# =============================================================================

CARDS_QUERY = """
query GetCards($pipeId: ID!, $after: String) {
  cards(pipe_id: $pipeId, first: 50, after: $after) {
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

UPDATE_FIELD_MUTATION = """
mutation UpdateField($cardId: ID!, $fieldId: String!, $newValue: String!) {
  updateCardField(input: {
    card_id:   $cardId
    field_id:  $fieldId
    new_value: $newValue
  }) {
    success
  }
}
"""

# =============================================================================
# FUNÇÕES
# =============================================================================

def _run_query(payload: dict) -> dict:
    """Executa uma chamada à API do Pipefy e retorna o JSON de resposta."""
    response = requests.post(PIPEFY_URL, json=payload, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.json()


def fetch_all_card_ids(pipe_id: int) -> list[str]:
    """
    Busca todos os card IDs de um pipe, percorrendo todas as páginas.
    Retorna uma lista de strings com os IDs.
    """
    card_ids: list[str] = []
    cursor: str | None = None
    page = 1

    while True:
        variables = {"pipeId": str(pipe_id), "after": cursor}
        data = _run_query({"query": CARDS_QUERY, "variables": variables})

        errors = data.get("errors")
        if errors:
            print(f"  [ERRO] Falha ao buscar cards do Pipe {pipe_id}: {errors}")
            break

        cards_data   = data["data"]["cards"]
        page_info    = cards_data["pageInfo"]
        edges        = cards_data["edges"]

        batch_ids = [edge["node"]["id"] for edge in edges]
        card_ids.extend(batch_ids)
        print(f"  Página {page}: {len(batch_ids)} cards encontrados "
              f"(total até agora: {len(card_ids)})")

        if not page_info["hasNextPage"]:
            break

        cursor = page_info["endCursor"]
        page  += 1
        time.sleep(REQUEST_DELAY)

    return card_ids


def update_card_field(card_id: str) -> bool:
    """
    Atualiza o campo FIELD_ID com NEW_VALUE no card informado.
    Retorna True em caso de sucesso, False em caso de erro.
    """
    variables = {
        "cardId":   card_id,
        "fieldId":  FIELD_ID,
        "newValue": NEW_VALUE,
    }
    data = _run_query({"query": UPDATE_FIELD_MUTATION, "variables": variables})

    errors = data.get("errors")
    if errors:
        print(f"    [ERRO] Card {card_id} — {errors}")
        return False

    success = data["data"]["updateCardField"]["success"]
    if not success:
        print(f"    [AVISO] Card {card_id} — API retornou success=false")
        return False

    return True

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================

def main() -> None:
    total_updated = 0
    total_failed  = 0

    for pipe_id in PIPE_IDS:
        print(f"\n{'='*60}")
        print(f"Buscando cards do Pipe {pipe_id}...")
        print(f"{'='*60}")

        card_ids = fetch_all_card_ids(pipe_id)
        print(f"\nTotal de cards encontrados no Pipe {pipe_id}: {len(card_ids)}")

        if not card_ids:
            print("Nenhum card para processar. Pulando para o próximo pipe.\n")
            continue

        print(f"\nIniciando atualização do campo '{FIELD_ID}' → '{NEW_VALUE}'\n")

        for index, card_id in enumerate(card_ids, start=1):
            print(f"  [{index}/{len(card_ids)}] Atualizando card {card_id}...", end=" ")

            try:
                success = update_card_field(card_id)
                if success:
                    print("OK")
                    total_updated += 1
                else:
                    total_failed += 1
            except requests.exceptions.RequestException as exc:
                print(f"FALHA DE REDE — {exc}")
                total_failed += 1

            time.sleep(REQUEST_DELAY)

    print(f"\n{'='*60}")
    print("Execução concluída.")
    print(f"  Cards atualizados com sucesso : {total_updated}")
    print(f"  Cards com falha               : {total_failed}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
