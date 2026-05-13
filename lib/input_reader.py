import pandas as pd
from pathlib import Path


class InputError(Exception):
    """Erro amigável de leitura/validação da planilha."""


def read_file(path: str) -> list[str]:
    """
    Lê um arquivo Excel (.xlsx) ou CSV (.csv) e retorna lista de card_ids.

    Regras:
    - Deve conter a coluna 'card_id' (case-insensitive)
    - Colunas extras são ignoradas
    - Linhas com card_id vazio são descartadas
    - Duplicatas são removidas (mantém ordem de aparição)

    Raises InputError com mensagem amigável em caso de problema.
    """
    file = Path(path)

    if not file.exists():
        raise InputError(f"Arquivo não encontrado: {path}")

    suffix = file.suffix.lower()
    if suffix not in (".xlsx", ".csv"):
        raise InputError(f"Formato não suportado: '{suffix}'. Use .xlsx ou .csv")

    try:
        if suffix == ".xlsx":
            df = pd.read_excel(file, dtype=str)
        else:
            df = pd.read_csv(file, dtype=str)
    except Exception as e:
        raise InputError(f"Erro ao ler o arquivo: {e}")

    # Normaliza nomes das colunas para lower sem espaços
    df.columns = [c.strip().lower() for c in df.columns]

    if "card_id" not in df.columns:
        cols = ", ".join(df.columns.tolist())
        raise InputError(
            f"Coluna 'card_id' não encontrada.\n"
            f"  Colunas encontradas no arquivo: {cols}\n"
            f"  Renomeie a coluna correta para 'card_id' e tente novamente."
        )

    # Extrai, limpa e deduplica
    raw = df["card_id"].dropna().astype(str).str.strip()
    raw = raw[raw != ""]  # remove strings vazias pós-strip
    raw = raw[raw.str.lower() != "nan"]  # remove "nan" vindo de células vazias

    # Deduplica mantendo ordem
    seen: set[str] = set()
    ids: list[str] = []
    for val in raw:
        if val not in seen:
            seen.add(val)
            ids.append(val)

    if not ids:
        raise InputError("Nenhum card_id válido encontrado no arquivo.")

    return ids
