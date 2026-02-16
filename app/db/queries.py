"""Raw SQL query functions for the cases table."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import asyncpg


async def init_schema(pool: asyncpg.Pool) -> None:
    sql = (Path(__file__).parent / "schema.sql").read_text()
    async with pool.acquire() as conn:
        await conn.execute(sql)


async def insert_case(
    pool: asyncpg.Pool,
    *,
    case_id: str,
    case_title: str,
    specialty: str,
    difficulty: str,
    case_data: dict,
) -> dict:
    now = datetime.now(timezone.utc)
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO cases (case_id, case_title, specialty, difficulty, case_data, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5::jsonb, $6, $7)
            RETURNING *
            """,
            uuid.UUID(case_id),
            case_title,
            specialty,
            difficulty,
            json.dumps(case_data),
            now,
            now,
        )
    return dict(row)


async def get_case_by_id(pool: asyncpg.Pool, case_id: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM cases WHERE case_id = $1", uuid.UUID(case_id))
    return dict(row) if row else None


async def list_cases(
    pool: asyncpg.Pool,
    *,
    page: int = 1,
    page_size: int = 20,
    specialty: str | None = None,
) -> tuple[list[dict], int]:
    offset = (page - 1) * page_size
    conditions = []
    params: list = []

    if specialty:
        conditions.append(f"specialty = ${len(params) + 1}")
        params.append(specialty)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    async with pool.acquire() as conn:
        count = await conn.fetchval(f"SELECT count(*) FROM cases {where}", *params)  # noqa: S608
        rows = await conn.fetch(
            f"SELECT * FROM cases {where} ORDER BY created_at DESC LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}",  # noqa: S608
            *params,
            page_size,
            offset,
        )
    return [dict(r) for r in rows], count


async def update_case(pool: asyncpg.Pool, case_id: str, *, updates: dict) -> dict | None:
    set_clauses = []
    params: list = []
    for key, value in updates.items():
        params.append(json.dumps(value) if key == "case_data" else value)
        set_clauses.append(f"{key} = ${len(params)}{'::jsonb' if key == 'case_data' else ''}")

    params.append(datetime.now(timezone.utc))
    set_clauses.append(f"updated_at = ${len(params)}")

    params.append(uuid.UUID(case_id))
    sql = f"UPDATE cases SET {', '.join(set_clauses)} WHERE case_id = ${len(params)} RETURNING *"  # noqa: S608

    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *params)
    return dict(row) if row else None


async def delete_case(pool: asyncpg.Pool, case_id: str) -> bool:
    async with pool.acquire() as conn:
        result = await conn.execute("DELETE FROM cases WHERE case_id = $1", uuid.UUID(case_id))
    return result == "DELETE 1"
