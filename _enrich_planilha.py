"""
Adiciona coluna card_id a uma planilha buscando pelo CPF na API do Pipefy.
Uso interativo: py _enrich_planilha.py
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import pandas as pd
import questionary
from rich.console import Console

from lib import api

console = Console()
INPUT_DIR = Path(__file__).parent / "input"

FIND_QUERY = """
query($pipeId: ID!, $cpf: String!) {
  findCards(pipeId: $pipeId, search: {fieldId: "%s", fieldValue: $cpf}, first: 1) {
    edges { node { id title } }
  }
}
"""

CPF_FIELD_IDS = {
    "ADM": "cpf_do_benefici_rio_1",
    "JUD": "cpf_do_benefici_rio",
    "FIN": "cpf_do_benefici_rio",
}


def escolher_arquivo() -> Path | None:
    arquivos = sorted(INPUT_DIR.glob("*.xlsx")) + sorted(INPUT_DIR.glob("*.csv"))
    if not arquivos:
        console.print("[red]Pasta input/ vazia.[/red]")
        return None
    choices = [questionary.Choice(f.name, value=f) for f in arquivos]
    choices.append(questionary.Choice("[ Cancelar ]", value=None))
    return questionary.select("Selecione o arquivo de entrada:", choices=choices).ask()


def escolher_pipe() -> str | None:
    choices = [
        questionary.Choice(f"{label} — {info['name']}", value=label)
        for label, info in api.PIPES.items()
    ]
    choices.append(questionary.Choice("[ Cancelar ]", value=None))
    return questionary.select("Em qual pipe buscar os cards por CPF?", choices=choices).ask()


def detectar_coluna_cpf(df: pd.DataFrame) -> str | None:
    for col in df.columns:
        if "cpf" in col.lower():
            return col
    return None


def main():
    console.rule("[bold cyan]Enriquecer Planilha — Adicionar card_id por CPF[/bold cyan]")
    console.print()

    input_path = escolher_arquivo()
    if not input_path:
        console.print("[yellow]Cancelado.[/yellow]")
        return

    pipe_label = escolher_pipe()
    if not pipe_label:
        console.print("[yellow]Cancelado.[/yellow]")
        return

    pipe_id    = api.PIPES[pipe_label]["id"]
    cpf_field  = CPF_FIELD_IDS.get(pipe_label, "cpf_do_benefici_rio")
    query      = FIND_QUERY % cpf_field

    df = pd.read_excel(str(input_path), dtype=str) if str(input_path).endswith(".xlsx") \
         else pd.read_csv(str(input_path), dtype=str)
    df.columns = [c.strip() for c in df.columns]

    cpf_col = detectar_coluna_cpf(df)
    if not cpf_col:
        console.print(f"[red]Coluna CPF nao encontrada. Colunas: {list(df.columns)}[/red]")
        return

    console.print(f"[green]Arquivo:[/green] {input_path.name}  ({len(df)} linhas)")
    console.print(f"[green]Pipe:[/green]    {pipe_label}")
    console.print(f"[green]Coluna CPF:[/green] '{cpf_col}'\n")

    card_ids = []
    nao_encontrados = []

    for idx, row in df.iterrows():
        cpf = str(row[cpf_col]).strip().replace(" ", "").replace(".", "").replace("-", "")
        if not cpf or cpf.lower() in ("nan", ""):
            card_ids.append("")
            continue

        try:
            result = api.execute(query, {"pipeId": pipe_id, "cpf": cpf})
            edges  = (result.get("data") or {}).get("findCards", {}).get("edges") or []
            if edges:
                cid  = edges[0]["node"]["id"]
                nome = edges[0]["node"]["title"]
                card_ids.append(cid)
                console.print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> card {cid} ({nome})")
            else:
                # Tenta com CPF formatado
                cpf_fmt = f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}" if len(cpf) == 11 else cpf
                result2 = api.execute(query, {"pipeId": pipe_id, "cpf": cpf_fmt})
                edges2  = (result2.get("data") or {}).get("findCards", {}).get("edges") or []
                if edges2:
                    cid  = edges2[0]["node"]["id"]
                    nome = edges2[0]["node"]["title"]
                    card_ids.append(cid)
                    console.print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> card {cid} ({nome})")
                else:
                    card_ids.append("")
                    nao_encontrados.append(cpf)
                    console.print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> [red]NAO ENCONTRADO[/red]")
        except Exception as e:
            card_ids.append("")
            nao_encontrados.append(cpf)
            console.print(f"  [{idx+1}/{len(df)}] CPF {cpf} -> [red]ERRO: {e}[/red]")

        time.sleep(0.2)

    df.insert(0, "card_id", card_ids)

    stem   = input_path.stem
    suffix = input_path.suffix
    output = input_path.parent / f"{stem}_{pipe_label}_ids{suffix}"
    if suffix == ".xlsx":
        df.to_excel(str(output), index=False)
    else:
        df.to_csv(str(output), index=False)

    encontrados = sum(1 for c in card_ids if c)
    console.print()
    console.rule("[bold]RESULTADO[/bold]")
    console.print(f"  [green]Encontrados   : {encontrados}[/green]")
    console.print(f"  [red]Nao encontrados: {len(nao_encontrados)}[/red]")
    console.print(f"  Arquivo salvo : [bold]{output}[/bold]")

    if nao_encontrados:
        console.print("\n[yellow]CPFs nao encontrados:[/yellow]")
        for cpf in nao_encontrados[:20]:
            console.print(f"  {cpf}")
        if len(nao_encontrados) > 20:
            console.print(f"  ... e mais {len(nao_encontrados) - 20}")


if __name__ == "__main__":
    main()
