# -*- coding: utf-8 -*-
"""Helper de caminhos para os geradores de relatórios.
Resolve a raiz do projeto, torna 'lib' (update_cards_pipefy) importável e
centraliza as pastas de saída (relatorios/...) e fontes (raiz)."""
import os, sys

HERE = os.path.dirname(os.path.abspath(__file__))   # .../update_cards_pipefy/geradores
UCP  = os.path.dirname(HERE)                         # .../update_cards_pipefy
ROOT = os.path.dirname(UCP)                          # raiz do projeto

# torna 'lib' importável a partir de qualquer gerador
if UCP not in sys.path:
    sys.path.insert(0, UCP)

# garante o PIPEFY_TOKEN do .env independentemente do diretório de execução
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(UCP, ".env"))
except Exception:
    pass

def _ensure(d):
    os.makedirs(d, exist_ok=True); return d

def out(cat, fname):
    """Saída .xlsx em relatorios/<cat>/."""
    return os.path.join(_ensure(os.path.join(ROOT, "relatorios", cat)), fname)

def dados(fname):
    """JSON intermediário em relatorios/dados/."""
    return os.path.join(_ensure(os.path.join(ROOT, "relatorios", "dados")), fname)

def src(fname):
    """Arquivo-fonte na raiz do projeto."""
    return os.path.join(ROOT, fname)

def ucp(fname):
    """Arquivo dentro de update_cards_pipefy/."""
    return os.path.join(UCP, fname)
