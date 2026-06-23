"""
Para cards das listas Steinberg_Teles e Teles_Steinberg:
  - terceiro_interessado vazio  → preenche com o valor do arquivo
  - terceiro_interessado ocupado → preenche fundo_investidor

Uso: py _atualizar_steinberg.py [--dry-run]
"""
import sys, time
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
from rich.console import Console
from rich.table import Table
from lib import api, reporter

console = Console()
DRY_RUN = "--dry-run" in sys.argv

ARQUIVOS = {
    "STEINBERG&TELES": "input/Relatorio_171_Steinberg_Teles.xlsx",
    "TELES&STEINBERG": "input/Relatorio_171_Teles_Steinberg.xlsx",
}

PIPE_CFG = {
    "ADM": {
        "id":           api.PIPES["ADM"]["id"],
        "cpf_field":    "cpf_do_benefici_rio_1",
        "terceiro_id":  "terceiro_interessado",
        "fundo_id":     "fundo_investidor",
    },
    "JUD": {
        "id":           api.PIPES["JUD"]["id"],
        "cpf_field":    "cpf_do_benefici_rio",
        "terceiro_id":  "terceiro_interassado",
        "fundo_id":     "fundo_investidor",
    },
    "FIN": {
        "id":           api.PIPES["FIN"]["id"],
        "cpf_field":    "cpf_do_benefici_rio",
        "terceiro_id":  "terceiro_interessado",
        "fundo_id":     "fundo_investidor",
    },
}

FIND_QUERY = 'query($p:ID!,$c:String!){findCards(pipeId:$p,search:{fieldId:"%s",fieldValue:$c},first:1){edges{node{id title}}}}'

FETCH_QUERY_TPL = """query {{
  {aliases}
}}"""

MUTATE_TPL = """mutation {{
  {aliases}
}}"""


# ── Carrega CPFs de um arquivo (todas as abas) ──────────────
def carregar_cpfs(arq: str) -> dict:
    """Retorna {cpf_limpo: {cpf_raw, nome, jud_id}}"""
    registros = {}
    for aba in pd.ExcelFile(arq).sheet_names:
        df = pd.read_excel(arq, sheet_name=aba, dtype=str)
        df.columns = [c.strip() for c in df.columns]
        col_jud = next((c for c in df.columns if "CÓDIGO JUD" in c or "CODIGO JUD" in c), None)
        for _, row in df.iterrows():
            cpf_raw = str(row.get("CPF DO BENEFICIÁRIO", "")).strip()
            cpf     = cpf_raw.replace(".", "").replace("-", "").replace(" ", "")
            if not cpf or cpf.lower() == "nan":
                continue
            nome    = str(row.get("NOME DO BENEFICIÁRIO", "")).strip()
            jud_id  = str(row.get(col_jud, "")).strip() if col_jud else ""
            jud_id  = "" if jud_id.lower() in ("nan", "") else jud_id
            if cpf not in registros:
                registros[cpf] = {"cpf_raw": cpf_raw, "nome": nome, "jud_id": jud_id}
            elif not registros[cpf]["jud_id"] and jud_id:
                registros[cpf]["jud_id"] = jud_id
    return registros


# ── Busca card_id por CPF ───────────────────────────────────
def buscar_por_cpf(cpf_raw: str, cpf: str, pipe_id: str, cpf_field: str) -> str | None:
    query = FIND_QUERY % cpf_field
    for fmt in [cpf_raw, cpf]:
        try:
            r = api.execute(query, {"p": pipe_id, "c": fmt})
            edges = (r.get("data") or {}).get("findCards", {}).get("edges") or []
            if edges:
                return edges[0]["node"]["id"]
        except Exception:
            pass
        time.sleep(0.1)
    return None


# ── Busca valor atual de terceiro em batch ──────────────────
def fetch_terceiro_batch(card_ids: list[str], terceiro_id: str) -> dict[str, str]:
    """Retorna {card_id: valor_atual_do_terceiro}"""
    BATCH = 20
    result = {}
    for i in range(0, len(card_ids), BATCH):
        chunk = card_ids[i:i+BATCH]
        aliases = "\n".join(
            f'  c{j}: card(id:"{cid}"){{fields{{field{{id}} value}}}}'
            for j, cid in enumerate(chunk)
        )
        try:
            resp = api.execute(FETCH_QUERY_TPL.format(aliases=aliases))
            data = resp.get("data") or {}
            for j, cid in enumerate(chunk):
                card_data = data.get(f"c{j}") or {}
                valor = ""
                for f in card_data.get("fields") or []:
                    if f["field"]["id"] == terceiro_id:
                        valor = f.get("value") or ""
                        break
                result[cid] = valor
        except Exception:
            for cid in chunk:
                result.setdefault(cid, "")
        time.sleep(0.2)
    return result


# ── Executa mutations em batch ──────────────────────────────
def update_batch(tarefas: list[dict]) -> list[dict]:
    """
    tarefas: [{card_id, field_id, new_value, nome, old_terceiro, acao}]
    Retorna resultados.
    """
    BATCH = 20
    results = []
    for i in range(0, len(tarefas), BATCH):
        chunk = tarefas[i:i+BATCH]
        if DRY_RUN:
            for t in chunk:
                results.append({
                    "card_id":   t["card_id"],
                    "nome":      t["nome"],
                    "old_value": t["old_terceiro"],
                    "new_value": t["new_value"],
                    "status":    "DRY-RUN",
                    "error":     t["acao"],
                })
            continue

        aliases = "\n".join(
            f'  c{j}: updateCardField(input:{{card_id:"{t["card_id"]}",'
            f'field_id:"{t["field_id"]}",new_value:"{t["new_value"]}"}}){{success}}'
            for j, t in enumerate(chunk)
        )
        try:
            resp   = api.execute(MUTATE_TPL.format(aliases=aliases))
            data   = resp.get("data") or {}
            errors = resp.get("errors") or []
            for j, t in enumerate(chunk):
                alias_data = data.get(f"c{j}")
                if alias_data and alias_data.get("success"):
                    results.append({
                        "card_id":   t["card_id"],
                        "nome":      t["nome"],
                        "old_value": t["old_terceiro"],
                        "new_value": t["new_value"],
                        "status":    "OK",
                        "error":     t["acao"],
                    })
                else:
                    msg = next((e.get("message","") for e in errors if f"c{j}" in str(e.get("path",[]))), "falha")
                    results.append({
                        "card_id":   t["card_id"],
                        "nome":      t["nome"],
                        "old_value": t["old_terceiro"],
                        "new_value": t["new_value"],
                        "status":    "FALHA",
                        "error":     msg,
                    })
        except Exception as e:
            for t in chunk:
                results.append({
                    "card_id": t["card_id"], "nome": t["nome"],
                    "old_value": t["old_terceiro"], "new_value": t["new_value"],
                    "status": "FALHA", "error": str(e),
                })
        time.sleep(0.3)
    return results


# ── MAIN ────────────────────────────────────────────────────
def main():
    modo = "[yellow]DRY-RUN[/yellow]" if DRY_RUN else "[bold green]REAL[/bold green]"
    console.print(f"\n[bold]STEINBERG/TELES — Atualizar campos[/bold]  Modo: {modo}\n")

    todos_resultados = []

    for valor, arq in ARQUIVOS.items():
        console.rule(f"[bold cyan]{valor}[/bold cyan]")
        registros = carregar_cpfs(arq)
        console.print(f"  {len(registros)} CPFs únicos carregados\n")

        for pipe_label, cfg in PIPE_CFG.items():
            console.print(f"[yellow]  {pipe_label}[/yellow] — buscando cards por CPF...")

            # 1. Encontra card_ids
            card_map = {}  # card_id -> {nome, cpf_raw}
            for idx, (cpf, info) in enumerate(registros.items()):
                # Para JUD no arquivo Steinberg_Teles: usa CÓDIGO JUD se disponível
                if pipe_label == "JUD" and info.get("jud_id"):
                    card_map[info["jud_id"]] = {"nome": info["nome"], "cpf_raw": info["cpf_raw"]}
                else:
                    cid = buscar_por_cpf(info["cpf_raw"], cpf, cfg["id"], cfg["cpf_field"])
                    if cid:
                        card_map[cid] = {"nome": info["nome"], "cpf_raw": info["cpf_raw"]}
                if (idx + 1) % 30 == 0:
                    console.print(f"    ...{idx+1}/{len(registros)} verificados")

            console.print(f"  [green]{len(card_map)} cards encontrados no {pipe_label}[/green]")

            if not card_map:
                continue

            # 2. Verifica valor atual de terceiro_interessado
            console.print(f"  Verificando campo terceiro_interessado em {len(card_map)} cards...")
            terceiros = fetch_terceiro_batch(list(card_map.keys()), cfg["terceiro_id"])

            # 3. Decide qual campo atualizar
            tarefas = []
            for cid, val_terceiro in terceiros.items():
                nome = card_map[cid]["nome"]
                if not val_terceiro or val_terceiro.strip() == "":
                    tarefas.append({
                        "card_id":     cid,
                        "nome":        nome,
                        "field_id":    cfg["terceiro_id"],
                        "new_value":   valor,
                        "old_terceiro": val_terceiro,
                        "acao":        "→ terceiro_interessado",
                    })
                else:
                    tarefas.append({
                        "card_id":     cid,
                        "nome":        nome,
                        "field_id":    cfg["fundo_id"],
                        "new_value":   valor,
                        "old_terceiro": val_terceiro,
                        "acao":        f"→ fundo_investidor (terceiro={val_terceiro})",
                    })

            t_campo   = sum(1 for t in tarefas if t["field_id"] == cfg["terceiro_id"])
            t_fundo   = sum(1 for t in tarefas if t["field_id"] == cfg["fundo_id"])
            console.print(f"  → terceiro_interessado : {t_campo} cards")
            console.print(f"  → fundo_investidor     : {t_fundo} cards")

            # 4. Executa
            console.print(f"  Atualizando...")
            results = update_batch(tarefas)
            todos_resultados.extend(results)

            ok    = sum(1 for r in results if r["status"] in ("OK", "DRY-RUN"))
            falha = sum(1 for r in results if r["status"] == "FALHA")
            console.print(f"  [green]OK: {ok}[/green]  [red]FALHA: {falha}[/red]\n")

            # Salva log parcial
            if results:
                reporter.save(results, f"{pipe_label}_{valor.replace('&','_')}", "terceiro_fundo", DRY_RUN)

    # Resumo final
    console.rule("[bold]RESUMO FINAL[/bold]")
    t = Table(show_header=True)
    t.add_column("Status"); t.add_column("Total", justify="right")
    counts: dict[str, int] = {}
    for r in todos_resultados:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    for status, count in sorted(counts.items()):
        t.add_row(status, str(count))
    console.print(t)
    console.print(f"\n  Total processado: {len(todos_resultados)} atualizações\n")


if __name__ == "__main__":
    main()
