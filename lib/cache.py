import json
from pathlib import Path

CACHE_FILE = Path(__file__).parent.parent / "cache" / "pipe_fields.json"


def load(pipe_id: str) -> list[dict] | None:
    if not CACHE_FILE.exists():
        return None
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        return data.get(str(pipe_id))
    except (json.JSONDecodeError, OSError):
        return None


def save(pipe_id: str, fields: list[dict]) -> None:
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if CACHE_FILE.exists():
        try:
            data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            data = {}
    data[str(pipe_id)] = fields
    CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear(pipe_id: str | None = None) -> None:
    """Remove cache de um pipe específico ou de todos se pipe_id=None."""
    if not CACHE_FILE.exists():
        return
    if pipe_id is None:
        CACHE_FILE.unlink()
        return
    try:
        data = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
        data.pop(str(pipe_id), None)
        CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except (json.JSONDecodeError, OSError):
        pass
