# Geradores de relatórios

Scripts que geram os relatórios em `relatorios/`. Rodar a partir da raiz do projeto:

```bash
py update_cards_pipefy/geradores/<script>.py      # Python (Pipefy/Excel)
node update_cards_pipefy/geradores/enio_financeiro.js   # precisa do túnel do banco
```

`_paths.py` resolve a raiz do projeto, torna `lib` importável e carrega o `.env`
(token do Pipefy). As saídas vão para `relatorios/<categoria>/`.

## Script → saída

| Script | Saída |
|---|---|
| `relatorio_waimea_protocolos.py` | `relatorios/waimea/WAIMEA_900_PROTOCOLOS.xlsx` (carteira + Pipefy + complemento) |
| `relatorio_waimea_pipefy.py` | `relatorios/waimea/WAIMEA_PIPEFY.xlsx` |
| `relatorio_waimea_no_financeiro.py` | `relatorios/waimea/WAIMEA_no_financeiro.xlsx` |
| `relatorio_processos_livres.py` | `relatorios/processos/PROCESSOS_LIVRES_EM_ANDAMENTO.xlsx` (sem fundo + em andamento) |
| `relatorio_sem_fundo.py` | `relatorios/processos/PROCESSOS_SEM_FUNDO.xlsx` (sem fundo, todas as fases) |
| `relatorio_vinculos.py` | `relatorios/processos/PROCESSOS_VINCULADOS.xlsx` (com terceiro/fundo) |
| `relatorio_fin_sem_fundo_terceiro.py` | `relatorios/processos/FINANCEIRO_sem_fundo_terceiro.xlsx` |
| `validar_livres.py` | (console) valida `Livres - Pipefy.xlsx` |
| `vinculos_lista.py` | `relatorios/validacoes/Livres_Pipefy_VALIDADO.xlsx` |
| `validar_assegurar.py` | `relatorios/validacoes/Assegurar_VALIDADO.xlsx` |
| `enio_pull.py` | `relatorios/dados/enio_casos.json` + `enio_metrics.json` |
| `enio_financeiro.js` | `relatorios/dados/enio_financeiro.json` (requer túnel do banco) |
| `gerar_planilha_enio.py` | `relatorios/enio/ENIO_Casos_v2.xlsx` |
| `gerar_dados_enio.py` | `relatorios/enio/ENIO_Dados_Apresentacao.xlsx` |

## Cadeia ENIO (ordem)
1. `enio_pull.py`  → casos + métricas (Pipefy)
2. `enio_financeiro.js`  → financeiro (banco, túnel)
3. `gerar_planilha_enio.py`  → Excel de casos
4. `gerar_dados_enio.py`  → dados da apresentação

## Fontes (na raiz, não mover)
`WAIMEA_900_Processos.xlsx`, `BASE JUD.xlsx`, `processos waimea.xlsx`,
`Livres - Pipefy.xlsx`, `Protocolos - Assegurar (2).xlsx`.
