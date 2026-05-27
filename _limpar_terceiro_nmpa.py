"""
Limpa o campo TERCEIRO INTERESSADO nos 3 pipes (ADM, JUD, FIN)
para os cards da lista NMPA_125.

Uso: py _limpar_terceiro_nmpa.py [--dry-run]
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn

from lib import api, batch, reporter
from lib.input_reader import read_file

console = Console()

DRY_RUN = "--dry-run" in sys.argv

TAREFAS = [
    {
        "pipe_label": "ADM",
        "field_id":   "terceiro_interessado",
        "arquivo":    "input/NMPA_125_ADM_ids.xlsx",
    },
    {
        "pipe_label": "JUD",
        "field_id":   "terceiro_interassado",
        "arquivo":    "input/NMPA_125_JUD_ids.xlsx",
    },
    {
        "pipe_label": "FIN",
        "field_id":   "terceiro_interessado",
        "arquivo":    "input/NMPA_125_FIN_ids.xlsx",
    },
]


def executar_pipe(tarefa: dict):
    pipe_label = tarefa["pipe_label"]
    field_id   = tarefa["field_id"]
    arquivo    = tarefa["arquivo"]

    console.rule(f"[bold cyan]{pipe_label}[/bold cyan]")

    if not Path(arquivo).exists():
        console.print(f"[red]Arquivo nao encontrado: {arquivo}[/red]")
        return

    card_ids = read_file(arquivo)
    if not card_ids:
        console.print(f"[yellow]Nenhum card_id no arquivo. Pulando.[/yellow]")
        return

    console.print(f"  {len(card_ids)} card_ids carregados")

    console.print("[yellow]Capturando valores atuais...[/yellow]")
    old_values = batch.fetch_current_values(card_ids, field_id)

    results: list[dict] = []
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TextColumn("{task.completed}/{task.total}"),
            console=console,
        ) as progress:
            task = progress.add_task(f"Limpando campo em {pipe_label}...", total=len(card_ids))

            def on_progress(done, total):
                progress.update(task, completed=done)

            results = batch.run_batch(
                card_ids, field_id, "",
                old_values,
                dry_run=DRY_RUN,
                progress_callback=on_progress,
            )
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrompido. Salvando progresso parcial...[/yellow]")

    log_path = reporter.save(results, pipe_label, field_id, DRY_RUN)
    counts   = reporter.summary(results)

    console.print()
    for status, count in sorted(counts.items()):
        color = "green" if status == "OK" else "yellow" if status in ("DRY-RUN", "INTERROMPIDO") else "red"
        console.print(f"  [{color}]{status}[/{color}]: {count}")
    console.print(f"  Log: [bold]{log_path}[/bold]\n")


def main():
    modo = "[yellow]DRY-RUN — nada sera alterado[/yellow]" if DRY_RUN else "[bold green]REAL — campos serao limpos[/bold green]"
    console.print(Panel(
        f"Campo: TERCEIRO INTERESSADO\nAcao: Limpar (valor vazio)\nModo: {modo}",
        title="[bold]LIMPAR TERCEIRO NMPA 125[/bold]",
        border_style="cyan"
    ))
    console.print()

    for tarefa in TAREFAS:
        executar_pipe(tarefa)

    console.rule("[bold green]CONCLUIDO[/bold green]")


if __name__ == "__main__":
    main()
