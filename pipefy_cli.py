"""
Pipefy CLI — Interface interativa para atualização de campos em cards.
Uso: py pipefy_cli.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from pathlib import Path
import questionary
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn
from rich.panel import Panel

from lib import api, batch, reporter
from lib.input_reader import read_file, InputError

console = Console()
CANCELAR = "__cancelar__"


# =============================================================================
# HELPERS
# =============================================================================

def print_header():
    console.print(Panel.fit(
        "[bold cyan]Pipefy CLI[/bold cyan] — Atualizacao de campos em cards",
        border_style="cyan"
    ))
    console.print()


def cancelado():
    console.print("\n[yellow]Operacao cancelada. Voltando ao menu...[/yellow]\n")


def escolher_pipe() -> tuple[str, str] | None:
    """Retorna (label, pipe_id) ou None se cancelado."""
    choices = [
        questionary.Choice(f"{label} — {info['name']}", value=label)
        for label, info in api.PIPES.items()
    ]
    choices.append(questionary.Choice("[ Cancelar ]", value=CANCELAR))

    label = questionary.select("Selecione o pipe:", choices=choices).ask()
    if label is None or label == CANCELAR:
        return None
    return label, api.PIPES[label]["id"]


def escolher_campo(pipe_id: str) -> dict | None:
    """Retorna {id, label, type} ou None se cancelado."""
    fields = api.fetch_pipe_fields(pipe_id)

    def build_choices(fields):
        choices = [questionary.Choice(f"{f['label']}  [{f['id']}]", value=f) for f in fields]
        choices.append(questionary.Choice("🔄  Atualizar lista de campos (refresh)", value="__refresh__"))
        choices.append(questionary.Choice("[ Cancelar ]", value=CANCELAR))
        return choices

    field = questionary.select("Selecione o campo a atualizar:", choices=build_choices(fields)).ask()
    if field is None or field == CANCELAR:
        return None

    if field == "__refresh__":
        console.print("[yellow]Atualizando cache de campos...[/yellow]")
        fields = api.fetch_pipe_fields(pipe_id, force_refresh=True)
        console.print(f"[green]Cache atualizado — {len(fields)} campos.[/green]\n")
        field = questionary.select("Selecione o campo a atualizar:", choices=build_choices(fields)).ask()
        if field is None or field == CANCELAR:
            return None

    return field


INPUT_DIR = Path(__file__).parent / "input"


def carregar_planilha() -> list[str] | None:
    """Lista arquivos em input/ e retorna lista de card_ids ou None se cancelado."""
    while True:
        arquivos = sorted(INPUT_DIR.glob("*.xlsx")) + sorted(INPUT_DIR.glob("*.csv"))

        if arquivos:
            choices = [questionary.Choice(f.name, value=str(f)) for f in arquivos]
            choices.append(questionary.Choice("[ Digitar caminho manualmente ]", value="__manual__"))
            choices.append(questionary.Choice("[ Cancelar ]", value=CANCELAR))
            path = questionary.select("Selecione o arquivo da pasta input/:", choices=choices).ask()
        else:
            console.print("[yellow]  Pasta input/ vazia. Digite o caminho do arquivo:[/yellow]")
            path = "__manual__"

        if path is None or path == CANCELAR:
            return None

        if path == "__manual__":
            path = questionary.text("Caminho completo do arquivo (.xlsx ou .csv): (Enter vazio = cancelar)").ask()
            if not path or path.strip() == "":
                return None
            path = path.strip().strip('"')

        try:
            ids = read_file(path)
            console.print(f"[green]  {len(ids)} card_ids carregados de '{Path(path).name}'[/green]\n")
            return ids
        except InputError as e:
            console.print(f"[red]  Erro: {e}[/red]")
            continuar = questionary.confirm("Tentar outro arquivo?", default=True).ask()
            if not continuar:
                return None


def validar_cards(pipe_id: str, card_ids: list[str]) -> tuple[list[str], list[str]]:
    console.print("[yellow]Validando card_ids na API do Pipefy...[/yellow]")
    with console.status("[cyan]Consultando API...[/cyan]"):
        resultado = api.validate_card_ids(pipe_id, card_ids)
    return resultado["valid"], resultado["not_found"]


def mostrar_resumo(pipe_label, field, new_value, valid_ids, not_found, dry_run):
    """Exibe painel de resumo com campo e valor que serão atualizados."""
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column(style="bold white")
    table.add_column()

    table.add_row("Pipe",   f"{pipe_label} — {api.PIPES[pipe_label]['name']}")
    table.add_row("Campo",  f"[bold yellow]{field['label']}[/bold yellow]  [dim][{field['id']}][/dim]")
    table.add_row("Valor",  f"[bold green]{new_value}[/bold green]")
    table.add_row("Cards",
        f"[green]{len(valid_ids)} validos[/green]"
        + (f"  [red]{len(not_found)} nao encontrados[/red]" if not_found else "")
    )
    table.add_row("Modo",   "[yellow]DRY-RUN — nada sera alterado[/yellow]"
                            if dry_run else "[bold green]REAL — campos serao atualizados[/bold green]")

    console.print(Panel(table, title="[bold]RESUMO DA OPERACAO[/bold]", border_style="blue"))

    if not_found:
        console.print(f"[red]Cards nao encontrados:[/red] {', '.join(not_found[:10])}"
                      + (" ..." if len(not_found) > 10 else ""))
    console.print()


# =============================================================================
# MODO PONTUAL
# =============================================================================

def modo_pontual():
    console.rule("[bold cyan]Atualizacao Pontual[/bold cyan]")
    console.print()

    # 1. Pipe
    resultado = escolher_pipe()
    if resultado is None:
        cancelado(); return
    pipe_label, pipe_id = resultado

    # 2. Campo
    field = escolher_campo(pipe_id)
    if field is None:
        cancelado(); return

    # 3. Valor
    new_value = questionary.text(f"Valor a preencher em '{field['label']}': (Enter vazio = cancelar)").ask()
    if not new_value or new_value.strip() == "":
        cancelado(); return
    new_value = new_value.strip()
    console.print()

    # 4. Arquivo
    card_ids = carregar_planilha()
    if card_ids is None:
        cancelado(); return

    # 5. Validacao
    valid_ids, not_found = validar_cards(pipe_id, card_ids)
    if not valid_ids:
        console.print("[red]Nenhum card valido encontrado. Encerrando.[/red]")
        return

    # 6. Dry-run?
    dry_run = questionary.confirm("Ativar modo dry-run (simular sem alterar)?", default=False).ask()
    if dry_run is None:
        cancelado(); return

    # 7. Resumo claro antes da confirmacao
    mostrar_resumo(pipe_label, field, new_value, valid_ids, not_found, dry_run)

    # 8. Confirmacao final
    confirmar = questionary.select(
        "Deseja prosseguir?",
        choices=[
            questionary.Choice("Sim, executar agora", value="sim"),
            questionary.Choice("Cancelar e voltar ao menu", value="nao"),
        ]
    ).ask()

    if confirmar != "sim":
        cancelado(); return

    # 9. Busca valores atuais (para log de rollback)
    console.print("\n[yellow]Capturando valores atuais para log de rollback...[/yellow]")
    with console.status("[cyan]Consultando cards...[/cyan]"):
        old_values = batch.fetch_current_values(valid_ids, field["id"])

    # 10. Execucao com barra de progresso
    console.print()
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
            task = progress.add_task("Atualizando cards...", total=len(valid_ids))

            def on_progress(done, total):
                progress.update(task, completed=done)

            results = batch.run_batch(
                valid_ids, field["id"], new_value, old_values,
                dry_run=dry_run,
                progress_callback=on_progress,
            )

    except KeyboardInterrupt:
        console.print("\n[yellow]Execucao interrompida. Salvando progresso parcial...[/yellow]")

    # 11. Salva relatorio
    log_path = reporter.save(results, pipe_label, field["id"], dry_run)
    counts   = reporter.summary(results)

    # 12. Resultado final
    console.print()
    console.rule("[bold]RESULTADO[/bold]")
    for status, count in sorted(counts.items()):
        color = "green" if status == "OK" else "yellow" if status == "DRY-RUN" else "red"
        console.print(f"  [{color}]{status}[/{color}]: {count}")
    console.print(f"\n  Log salvo em: [bold]{log_path}[/bold]")

    # 13. Retry se houver falhas
    falhas = [r for r in results if r["status"] == "FALHA"]
    if falhas and not dry_run:
        console.print()
        retry = questionary.confirm(
            f"Tentar novamente os {len(falhas)} cards com falha?", default=True
        ).ask()
        if retry:
            console.print("[yellow]Re-tentando cards com falha...[/yellow]")
            old_retry = {r["card_id"]: {"value": r["old_value"], "nome": r["nome"]} for r in falhas}
            retry_results = batch.run_batch(
                [r["card_id"] for r in falhas], field["id"], new_value, old_retry
            )
            retry_map = {r["card_id"]: r for r in retry_results}
            results   = [retry_map.get(r["card_id"], r) for r in results]
            log_path  = reporter.save(results, pipe_label, field["id"], dry_run)
            counts    = reporter.summary(results)

            console.print()
            console.rule("[bold]RESULTADO APOS RETRY[/bold]")
            for status, count in sorted(counts.items()):
                color = "green" if status == "OK" else "red"
                console.print(f"  [{color}]{status}[/{color}]: {count}")
            console.print(f"\n  Log atualizado: [bold]{log_path}[/bold]")


# =============================================================================
# MODO EM MASSA
# =============================================================================

def modo_massa():
    console.print(Panel(
        "Para atualizacao em massa via relatorios do pipe, execute:\n\n"
        "  [bold cyan]py update_cards_by_report.py ADM[/bold cyan]\n"
        "  [bold cyan]py update_cards_by_report.py JUD[/bold cyan]\n"
        "  [bold cyan]py update_cards_by_report.py FIN[/bold cyan]",
        title="Atualizacao em Massa",
        border_style="yellow"
    ))


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    print_header()

    modo = questionary.select(
        "O que deseja fazer?",
        choices=[
            questionary.Choice("Atualizacao Pontual  (lista de cards via planilha)", value="pontual"),
            questionary.Choice("Atualizacao em Massa (relatorio do pipe)",           value="massa"),
            questionary.Choice("Atualizar cache de campos de todos os pipes",        value="cache"),
            questionary.Choice("[ Sair ]",                                           value="sair"),
        ]
    ).ask()

    if modo is None or modo == "sair":
        console.print("[dim]Ate logo.[/dim]\n")
        sys.exit(0)

    if modo == "pontual":
        modo_pontual()
    elif modo == "massa":
        modo_massa()
    elif modo == "cache":
        console.print("\n[yellow]Atualizando cache de campos para todos os pipes...[/yellow]")
        for label, info in api.PIPES.items():
            with console.status(f"[cyan]{label}...[/cyan]"):
                fields = api.fetch_pipe_fields(info["id"], force_refresh=True)
            console.print(f"  [green]{label}[/green]: {len(fields)} campos atualizados")
        console.print("\n[green]Cache atualizado com sucesso.[/green]")

    console.print()


if __name__ == "__main__":
    main()
