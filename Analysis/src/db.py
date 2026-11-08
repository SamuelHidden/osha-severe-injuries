"""
Подключение к базе OSHA_db (PostgreSQL) для анализа в Python.

Параметры подключения читаются из Analysis/.env (PG_HOST, PG_PORT, PG_DB,
PG_USER, PG_PASSWORD), поэтому пароля в коде нет.

Использование в ноутбуке:

    from src.db import query, run_sql_file

    df = query("SELECT * FROM injuries LIMIT 5")
    df = query("SELECT * FROM injuries WHERE state = :state", {"state": "TEXAS"})
"""

import os
from functools import lru_cache
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, Engine

ANALYSIS_DIR = Path(__file__).resolve().parent.parent
PROJECT_DIR = ANALYSIS_DIR.parent
SQL_DIR = PROJECT_DIR / "SQL"

load_dotenv(ANALYSIS_DIR / ".env")


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    """Один engine на весь сеанс — создаётся при первом обращении."""
    url = URL.create(
        "postgresql+psycopg2",
        username=os.getenv("PG_USER", "postgres"),
        password=os.getenv("PG_PASSWORD"),
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        database=os.getenv("PG_DB", "OSHA_db"),
    )
    return create_engine(url)


def query(sql: str, params: dict | None = None) -> pd.DataFrame:
    """Выполняет SELECT и возвращает DataFrame. Параметры — в стиле :name."""
    with get_engine().connect() as conn:
        return pd.read_sql_query(text(sql), conn, params=params)


def run_sql_file(name: str) -> list[pd.DataFrame]:
    """
    Выполняет все запросы из файла папки SQL/ (например '01_body_parts.sql')
    и возвращает список DataFrame в том же порядке, что и запросы в файле.
    """
    raw = (SQL_DIR / name).read_text(encoding="utf-8")
    # убираем строки-комментарии, затем делим по ';'
    body = "\n".join(line for line in raw.splitlines() if not line.lstrip().startswith("--"))
    statements = [s.strip() for s in body.split(";") if s.strip()]
    return [query(s) for s in statements]
