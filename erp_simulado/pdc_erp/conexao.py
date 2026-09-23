"""Conexão com o PostgreSQL do ERP simulado (credenciais somente por variáveis de ambiente)."""

from __future__ import annotations

import os

import psycopg


def conectar() -> psycopg.Connection:
    return psycopg.connect(
        host=os.environ.get("PG_HOST", "localhost"),
        port=int(os.environ.get("PG_PORT", "5432")),
        dbname=os.environ.get("PG_DB", "erp_protheus"),
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
    )
