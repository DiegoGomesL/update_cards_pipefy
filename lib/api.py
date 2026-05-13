import os
import requests
from dotenv import load_dotenv
from lib import cache

load_dotenv()

PIPEFY_URL = "https://api.pipefy.com/graphql"

PIPES = {
    "ADM": {"id": "305726681", "name": "FLUXO PREVIDENCIÁRIO ADM"},
    "JUD": {"id": "305859312", "name": "FLUXO JUDICIAL"},
    "FIN": {"id": "305859195", "name": "FINANCEIRO"},
}


def _headers() -> dict:
    token = os.getenv("PIPEFY_TOKEN")
    if not token:
        raise EnvironmentError("PIPEFY_TOKEN não encontrado. Verifique o arquivo .env")
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def execute(query: str, variables: dict | None = None) -> dict:
    """Executa uma query/mutation GraphQL e retorna o JSON completo."""
    response = requests.post(
        PIPEFY_URL,
        json={"query": query, "variables": variables or {}},
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def fetch_pipe_fields(pipe_id: str, force_refresh: bool = False) -> list[dict]:
    """
    Retorna lista de campos do pipe: [{id, label, type}].
    Usa cache local; force_refresh=True ignora o cache e grava novo.
    """
    if not force_refresh:
        cached = cache.load(pipe_id)
        if cached is not None:
            return cached

    query = """
    query($pipeId: ID!) {
      pipe(id: $pipeId) {
        start_form_fields {
          id
          label
          type
        }
        phases {
          fields {
            id
            label
            type
          }
        }
      }
    }
    """
    result = execute(query, {"pipeId": pipe_id})

    if "errors" in result:
        raise RuntimeError(f"Erro ao buscar campos: {result['errors']}")

    pipe_data = result["data"]["pipe"]
    seen: set[str] = set()
    fields: list[dict] = []

    for f in pipe_data.get("start_form_fields") or []:
        if f["id"] not in seen:
            seen.add(f["id"])
            fields.append({"id": f["id"], "label": f["label"], "type": f.get("type", "")})

    for phase in pipe_data.get("phases") or []:
        for f in phase.get("fields") or []:
            if f["id"] not in seen:
                seen.add(f["id"])
                fields.append({"id": f["id"], "label": f["label"], "type": f.get("type", "")})

    fields.sort(key=lambda x: x["label"])
    cache.save(pipe_id, fields)
    return fields


def validate_card_ids(pipe_id: str, card_ids: list[str]) -> dict:
    """
    Verifica quais card_ids existem e pertencem ao pipe informado.
    Retorna {"valid": [...], "not_found": [...]}.
    """
    valid: list[str] = []
    not_found: list[str] = []

    # Busca em batches de 50 para não sobrecarregar
    query = """
    query($id: ID!) {
      card(id: $id) { id }
    }
    """
    for card_id in card_ids:
        try:
            result = execute(query, {"id": card_id})
            card = (result.get("data") or {}).get("card")
            if card:
                valid.append(card_id)
            else:
                not_found.append(card_id)
        except Exception:
            not_found.append(card_id)

    return {"valid": valid, "not_found": not_found}
