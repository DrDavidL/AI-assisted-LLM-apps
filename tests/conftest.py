"""Shared test fixtures."""

from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.cases import router as cases_router
from app.schemas.medical_case import MedicalCase


@pytest.fixture()
def sample_case_data() -> dict:
    """Minimal valid MedicalCase as a dict."""
    return {
        "case_id": str(uuid.uuid4()),
        "case_title": "Test Case: Chest Pain",
        "specialty": "cardiology",
        "difficulty": "medium",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "demographics": {"age": 55, "sex": "male"},
        "chief_complaint_hpi": {
            "chief_complaint": "Chest pain",
            "hpi_narrative": "55yo M presents with substernal chest pain x 2 hours.",
        },
        "vitals": {"heart_rate": 92, "bp_systolic": 145, "bp_diastolic": 88, "spo2": 96.0},
        "medications": [{"name": "Aspirin", "dose": "81mg", "route": "PO", "frequency": "daily"}],
        "allergies": [{"substance": "Penicillin", "reaction": "rash", "severity": "mild"}],
        "assessment": {
            "differential_diagnoses": [
                {"rank": 1, "diagnosis": "NSTEMI", "reasoning": "Elevated troponin, ECG changes"},
                {"rank": 2, "diagnosis": "Unstable angina", "reasoning": "Negative troponin possible"},
            ],
            "working_diagnosis": "Acute coronary syndrome",
        },
    }


@pytest.fixture()
def sample_case(sample_case_data: dict) -> MedicalCase:
    return MedicalCase.model_validate(sample_case_data)


@pytest.fixture()
def mock_pool():
    return AsyncMock()


@pytest.fixture()
def mock_redis():
    r = AsyncMock()
    r.get = AsyncMock(return_value=None)
    r.set = AsyncMock()
    r.delete = AsyncMock()
    return r


@pytest.fixture()
def client(mock_pool, mock_redis) -> TestClient:
    @asynccontextmanager
    async def noop_lifespan(app: FastAPI):
        yield

    test_app = FastAPI(lifespan=noop_lifespan)
    test_app.include_router(cases_router)
    test_app.state.db_pool = mock_pool
    test_app.state.redis = mock_redis

    with TestClient(test_app, raise_server_exceptions=True) as c:
        yield c
