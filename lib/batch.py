import time
from lib import api

BATCH_SIZE = 20  # mutations por request


def fetch_current_values(card_ids: list[str], field_id: str) -> dict[str, dict]:
    """
    Busca o valor atual de field_id e o título (nome do beneficiário) em cada card.
    Retorna {card_id: {"value": str, "nome": str}}.
    Usa batches de BATCH_SIZE para não sobrecarregar a API.
    """
    result: dict[str, dict] = {}

    for i in range(0, len(card_ids), BATCH_SIZE):
        chunk = card_ids[i : i + BATCH_SIZE]

        aliases = "\n".join(
            f'  c{j}: card(id: "{cid}") {{ title fields {{ field {{ id }} value }} }}'
            for j, cid in enumerate(chunk)
        )
        query = f"query {{\n{aliases}\n}}"

        try:
            response = api.execute(query)
            data = response.get("data") or {}
            for j, cid in enumerate(chunk):
                card_data = data.get(f"c{j}")
                value = ""
                nome  = ""
                if card_data:
                    nome = card_data.get("title") or ""
                    for f in card_data.get("fields") or []:
                        if f["field"]["id"] == field_id:
                            value = f.get("value") or ""
                            break
                result[cid] = {"value": value, "nome": nome}
        except Exception:
            for cid in chunk:
                result.setdefault(cid, {"value": "", "nome": ""})

        time.sleep(0.2)

    return result


def _get(old_values: dict, cid: str, key: str) -> str:
    return old_values.get(cid, {}).get(key, "")


def run_batch(
    card_ids: list[str],
    field_id: str,
    new_value: str,
    old_values: dict[str, dict],
    dry_run: bool = False,
    progress_callback=None,
) -> list[dict]:
    """
    Atualiza field_id com new_value em todos os card_ids.

    - dry_run=True: simula sem chamar a API
    - progress_callback(done, total): chamado após cada batch
    - Suporta KeyboardInterrupt: salva progresso parcial

    Retorna lista de dicts:
      {card_id, nome, old_value, new_value, status, error}
    """
    results: list[dict] = []
    total = len(card_ids)
    done  = 0

    def build_mutation(chunk: list[str]) -> str:
        aliases = "\n".join(
            f'  c{j}: updateCardField(input: {{'
            f'card_id: "{cid}", '
            f'field_id: "{field_id}", '
            f'new_value: "{new_value}"'
            f'}}) {{ success }}'
            for j, cid in enumerate(chunk)
        )
        return f"mutation {{\n{aliases}\n}}"

    def make_row(cid, status, error=""):
        return {
            "card_id":   cid,
            "nome":      _get(old_values, cid, "nome"),
            "old_value": _get(old_values, cid, "value"),
            "new_value": new_value,
            "status":    status,
            "error":     error,
        }

    try:
        for i in range(0, total, BATCH_SIZE):
            chunk = card_ids[i : i + BATCH_SIZE]

            if dry_run:
                for cid in chunk:
                    results.append(make_row(cid, "DRY-RUN"))
                done += len(chunk)
                if progress_callback:
                    progress_callback(done, total)
                continue

            try:
                response = api.execute(build_mutation(chunk))
                data     = response.get("data") or {}
                errors   = response.get("errors") or []

                if errors and not data:
                    msg = errors[0].get("message", "erro desconhecido")
                    for cid in chunk:
                        results.append(make_row(cid, "FALHA", msg))
                else:
                    for j, cid in enumerate(chunk):
                        alias_data = data.get(f"c{j}")
                        if alias_data and alias_data.get("success"):
                            results.append(make_row(cid, "OK"))
                        else:
                            alias_err = next(
                                (e.get("message", "") for e in errors
                                 if f"c{j}" in str(e.get("path", []))),
                                "success=false"
                            )
                            results.append(make_row(cid, "FALHA", alias_err))

            except Exception as e:
                for cid in chunk:
                    results.append(make_row(cid, "FALHA", str(e)))

            done += len(chunk)
            if progress_callback:
                progress_callback(done, total)

            time.sleep(0.3)

    except KeyboardInterrupt:
        processed = {r["card_id"] for r in results}
        for cid in card_ids:
            if cid not in processed:
                results.append(make_row(cid, "INTERROMPIDO", "execucao cancelada pelo usuario"))
        raise

    return results


def retry_failed(results: list[dict], field_id: str) -> list[dict]:
    """Re-executa apenas os cards com status FALHA."""
    failed = [r for r in results if r["status"] == "FALHA"]
    if not failed:
        return results

    old_vals  = {r["card_id"]: {"value": r["old_value"], "nome": r["nome"]} for r in failed}
    new_value = failed[0]["new_value"]

    retry_results = run_batch(
        [r["card_id"] for r in failed], field_id, new_value, old_vals
    )
    retry_map = {r["card_id"]: r for r in retry_results}
    return [retry_map.get(r["card_id"], r) for r in results]
