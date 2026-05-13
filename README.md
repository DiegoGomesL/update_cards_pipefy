# Pipefy CLI — Automação de atualização de campos

Ferramenta em Python para atualizar campos de cards no Pipefy via GraphQL,
com suporte a atualização pontual (por planilha) e em massa (por relatório de pipe).

---

## Instalação

```bash
pip install -r requirements.txt
```

## Configuração

1. Copie o arquivo de exemplo:
   ```bash
   copy .env.example .env
   ```
2. Abra `.env` e cole seu token do Pipefy:
   ```
   PIPEFY_TOKEN=seu_token_aqui
   ```
   O token pode ser gerado em: **Pipefy → Settings → Personal Access Tokens**

---

## Uso

### Menu interativo (recomendado)

```bash
py pipefy_cli.py
```

O menu vai guiar você por:
1. Escolha do modo (pontual ou em massa)
2. Seleção do pipe (ADM / JUD / FIN)
3. Seleção do campo a atualizar
4. Valor a preencher
5. Caminho da planilha com os `card_ids`
6. Validação e resumo antes de executar
7. Barra de progresso durante execução
8. Relatório CSV salvo automaticamente em `logs/`

---

### Atualização Pontual

Atualiza um campo específico em uma lista de cards fornecida via planilha.

**Formato da planilha** (`.xlsx` ou `.csv`):

| card_id    | nome        | cpf             |
|------------|-------------|-----------------|
| 1249121516 | JOSE SILVA  | 123.456.789-00  |
| 1208415895 | MARIA SOUZA | 987.654.321-00  |

- A coluna `card_id` é obrigatória
- Colunas extras são ignoradas
- Duplicatas são removidas automaticamente

**Dry-run** — simula a execução sem alterar nada:
```
? Ativar modo dry-run (simular sem alterar)? Yes
```

---

### Atualização em Massa

Atualiza todos os cards de um relatório do pipe:

```bash
py update_cards_by_report.py ADM
py update_cards_by_report.py JUD
py update_cards_by_report.py FIN
```

---

## Relatórios de execução

Todos os resultados são salvos em `logs/` automaticamente:

```
logs/
└── 2026-05-12_14-30_ADM_terceiro_interessado.csv
```

**Colunas do relatório:**

| card_id | old_value | new_value | status | error | timestamp |
|---|---|---|---|---|---|
| 1249121516 | | Marcelo | OK | | 2026-05-12 14:31:00 |
| 1208415895 | Outro | Marcelo | FALHA | timeout | 2026-05-12 14:31:01 |

- `old_value` — valor anterior ao update (útil para rollback manual)
- `status` — `OK`, `FALHA`, `DRY-RUN` ou `INTERROMPIDO`

---

## Cache de campos

Os campos de cada pipe são armazenados em `cache/pipe_fields.json`
para evitar chamadas desnecessárias à API.

Para forçar atualização do cache:
- No menu: selecione **"Atualizar cache de campos de todos os pipes"**
- Ou via código: `api.fetch_pipe_fields(pipe_id, force_refresh=True)`

---

## Estrutura do projeto

```
update_cards_pipefy/
├── pipefy_cli.py              # Entry point — menu interativo
├── update_cards_by_report.py  # Atualização em massa por relatório
├── lib/
│   ├── api.py                 # Cliente GraphQL
│   ├── batch.py               # Batching de mutations (20/request)
│   ├── cache.py               # Cache local de campos
│   ├── input_reader.py        # Leitura de Excel e CSV
│   └── reporter.py            # Geração de relatório CSV
├── cache/
│   └── pipe_fields.json       # Cache dos campos por pipe
├── logs/                      # Relatórios gerados (não versionado)
├── .env                       # Token do Pipefy (não versionado)
├── .env.example               # Modelo do .env
├── requirements.txt
└── README.md
```

---

## Pipes configurados

| Label | ID         | Nome |
|-------|------------|------|
| ADM   | 305726681  | FLUXO PREVIDENCIÁRIO ADM |
| JUD   | 305859312  | FLUXO JUDICIAL |
| FIN   | 305859195  | FINANCEIRO |
