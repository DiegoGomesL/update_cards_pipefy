import csv
from datetime import datetime
from pathlib import Path

LOGS_DIR = Path(__file__).parent.parent / "logs"

COLUMNS = ["card_id", "nome", "old_value", "new_value", "status", "error", "timestamp"]


def save(
    results: list[dict],
    pipe_label: str,
    field_id: str,
    dry_run: bool = False,
) -> Path:
    """
    Salva resultados em CSV no diretório logs/.
    Sempre salva, independente de haver falhas.
    Retorna o Path do arquivo gerado.
    """
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    now       = datetime.now()
    suffix    = "_DRYRUN" if dry_run else ""
    filename  = f"{now.strftime('%Y-%m-%d_%H-%M')}_{pipe_label}_{field_id}{suffix}.csv"
    filepath  = LOGS_DIR / filename
    timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for r in results:
            writer.writerow({
                "card_id":   r.get("card_id", ""),
                "nome":      r.get("nome", ""),
                "old_value": r.get("old_value", ""),
                "new_value": r.get("new_value", ""),
                "status":    r.get("status", ""),
                "error":     r.get("error", ""),
                "timestamp": timestamp,
            })

    return filepath


def summary(results: list[dict]) -> dict:
    """Retorna contagens por status."""
    counts: dict[str, int] = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    return counts
