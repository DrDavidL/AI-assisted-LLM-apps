"""Tests for the cases API using TestClient with mocked DB/Redis."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient


class TestListCases:
    def test_list_cases_empty(self, client: TestClient, mock_pool):
        mock_pool.acquire.return_value.__aenter__.return_value.fetchval = AsyncMock(return_value=0)
        mock_pool.acquire.return_value.__aenter__.return_value.fetch = AsyncMock(return_value=[])

        with patch("app.api.cases.queries.list_cases", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([], 0)
            resp = client.get("/api/v1/cases/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_cases_with_search(self, client: TestClient, mock_pool):
        with patch("app.api.cases.queries.list_cases", new_callable=AsyncMock) as mock_list:
            mock_list.return_value = ([], 0)
            resp = client.get("/api/v1/cases/", params={"search": "chest"})

        assert resp.status_code == 200
        mock_list.assert_called_once()
        call_kwargs = mock_list.call_args
        assert call_kwargs.kwargs.get("search") == "chest" or call_kwargs[1].get("search") == "chest"


class TestGetCase:
    def test_get_case_not_found(self, client: TestClient, mock_redis):
        mock_redis.get = AsyncMock(return_value=None)

        with patch("app.api.cases.queries.get_case_by_id", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            resp = client.get(f"/api/v1/cases/{uuid.uuid4()}")

        assert resp.status_code == 404

    def test_get_case_from_cache(self, client: TestClient, mock_redis, sample_case_data):
        mock_redis.get = AsyncMock(return_value=json.dumps(sample_case_data, default=str))

        resp = client.get(f"/api/v1/cases/{sample_case_data['case_id']}")
        assert resp.status_code == 200
        assert resp.json()["case_id"] == sample_case_data["case_id"]


class TestGetCaseByNumber:
    def test_get_case_by_number_not_found(self, client: TestClient, mock_pool):
        with patch("app.api.cases.queries.get_case_by_number", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            resp = client.get("/api/v1/cases/by-number/999")

        assert resp.status_code == 404

    def test_get_case_by_number_success(self, client: TestClient, mock_pool, sample_case_data):
        now = datetime.now(timezone.utc)
        db_row = {
            "case_id": uuid.UUID(sample_case_data["case_id"]),
            "case_number": 1,
            "case_title": sample_case_data["case_title"],
            "specialty": sample_case_data["specialty"],
            "difficulty": sample_case_data["difficulty"],
            "case_data": sample_case_data,
            "created_at": now,
            "updated_at": now,
        }
        with patch("app.api.cases.queries.get_case_by_number", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = db_row
            resp = client.get("/api/v1/cases/by-number/1")

        assert resp.status_code == 200
        assert resp.json()["case_id"] == sample_case_data["case_id"]
        assert resp.json()["case_number"] == 1


class TestCreateCase:
    def test_create_case(self, client: TestClient, mock_pool, mock_redis, sample_case_data):
        case_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        db_row = {
            "case_id": uuid.UUID(case_id),
            "case_title": "New Case",
            "specialty": "general",
            "difficulty": "medium",
            "case_data": sample_case_data,
            "created_at": now,
            "updated_at": now,
        }

        with patch("app.api.cases.queries.insert_case", new_callable=AsyncMock) as mock_insert:
            mock_insert.return_value = db_row
            resp = client.post(
                "/api/v1/cases/",
                json={
                    "case_title": "New Case",
                    "specialty": "general",
                    "difficulty": "medium",
                    "case_data": sample_case_data,
                },
            )

        assert resp.status_code == 201
        assert resp.json()["specialty"] == "general"


class TestDeleteCase:
    def test_delete_case_not_found(self, client: TestClient, mock_redis):
        with patch("app.api.cases.queries.delete_case", new_callable=AsyncMock) as mock_del:
            mock_del.return_value = False
            resp = client.delete(f"/api/v1/cases/{uuid.uuid4()}")
        assert resp.status_code == 404

    def test_delete_case_success(self, client: TestClient, mock_redis):
        with patch("app.api.cases.queries.delete_case", new_callable=AsyncMock) as mock_del:
            mock_del.return_value = True
            resp = client.delete(f"/api/v1/cases/{uuid.uuid4()}")
        assert resp.status_code == 204


class TestGenerateCase:
    def test_generate_calls_llm(self, client: TestClient, mock_pool, mock_redis, sample_case):
        with (
            patch("app.api.cases.llm_service.generate_case", new_callable=AsyncMock) as mock_gen,
            patch("app.api.cases.queries.insert_case", new_callable=AsyncMock) as mock_insert,
        ):
            mock_gen.return_value = sample_case
            mock_insert.return_value = {}

            resp = client.post(
                "/api/v1/cases/generate",
                json={"specialty": "cardiology", "difficulty": "medium"},
            )

        assert resp.status_code == 200
        assert resp.json()["specialty"] == "cardiology"
        mock_gen.assert_called_once()
