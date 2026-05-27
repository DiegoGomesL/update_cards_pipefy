import sys; sys.stdout.reconfigure(encoding="utf-8", errors="replace")
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TextColumn
from lib import batch, reporter

console = Console()
ARQUIVO = "input/Relatorio_125_Processos Livres.xlsx"
ABA     = "Encerrados + Substituição"

df = pd.read_excel(ARQUIVO, sheet_name=ABA, dtype=str)
df.columns = [c.strip() for c in df.columns]

adm_ids = [v.strip() for v in df["CÓDIGO ADM"].dropna() if str(v).strip() not in ("", "nan")]
jud_ids = [v.strip() for v in df["CÓDIGO JUD"].dropna() if str(v).strip() not in ("", "nan")]

console.print(f"Aba '{ABA}': {len(df)} linhas — ADM: {len(adm_ids)} cards | JUD: {len(jud_ids)} cards\n")

TAREFAS = [
    {"pipe": "ADM", "ids": adm_ids, "field_id": "terceiro_interessado"},
    {"pipe": "JUD", "ids": jud_ids, "field_id": "terceiro_interassado"},
]

for t in TAREFAS:
    if not t["ids"]:
        console.print(f"[{t['pipe']}] Nenhum card. Pulando.\n")
        continue

    console.rule(f"[bold cyan]{t['pipe']}[/bold cyan]")

    # Verifica valores atuais
    console.print("[yellow]Verificando valores atuais...[/yellow]")
    valores = batch.fetch_current_values(t["ids"], t["field_id"])

    com_valor  = [cid for cid, v in valores.items() if v["value"]]
    sem_valor  = [cid for cid, v in valores.items() if not v["value"]]
    console.print(f"  Ja limpos    : {len(sem_valor)}")
    console.print(f"  Ainda com valor: {len(com_valor)}")
    for cid in com_valor:
        console.print(f"    [{cid}] {valores[cid]['nome']} -> '{valores[cid]['value']}'")

    if not com_valor:
        console.print("[green]  Todos ja estao limpos. Nada a fazer.[/green]\n")
        continue

    # Limpa apenas os que ainda têm valor
    console.print(f"\n[yellow]Limpando {len(com_valor)} cards...[/yellow]")
    old = {cid: valores[cid] for cid in com_valor}

    results = []
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(),
                  TaskProgressColumn(), TextColumn("{task.completed}/{task.total}"),
                  console=console) as progress:
        task = progress.add_task(f"Limpando {t['pipe']}...", total=len(com_valor))
        results = batch.run_batch(com_valor, t["field_id"], "", old,
                                  progress_callback=lambda d, total: progress.update(task, completed=d))

    log = reporter.save(results, t["pipe"], t["field_id"])
    counts = reporter.summary(results)
    console.print()
    for status, count in sorted(counts.items()):
        color = "green" if status == "OK" else "red"
        console.print(f"  [{color}]{status}[/{color}]: {count}")
    console.print(f"  Log: [bold]{log}[/bold]\n")

console.rule("[bold green]CONCLUIDO[/bold green]")
