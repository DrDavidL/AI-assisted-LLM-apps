"""Tests for Pydantic schema validation."""

from __future__ import annotations

import uuid

import pytest

from app.schemas.medical_case import (
    Difficulty,
    MedicalCase,
    PatientDemographics,
    VitalSigns,
)


class TestMedicalCaseRoundTrip:
    def test_minimal_case_validates(self, sample_case_data: dict):
        case = MedicalCase.model_validate(sample_case_data)
        assert case.specialty == "cardiology"
        assert case.demographics.age == 55

    def test_round_trip_json(self, sample_case: MedicalCase):
        json_str = sample_case.model_dump_json()
        restored = MedicalCase.model_validate_json(json_str)
        assert restored.case_id == sample_case.case_id
        assert restored.demographics.age == sample_case.demographics.age

    def test_optional_fields_default_none(self, sample_case_data: dict):
        case = MedicalCase.model_validate(sample_case_data)
        assert case.physical_exam is None
        assert case.diagnostics is None
        assert case.plan is None

    def test_list_fields_default_empty(self, sample_case_data: dict):
        case = MedicalCase.model_validate(sample_case_data)
        assert case.review_of_systems == []
        assert case.family_history == []


class TestVitalSignsValidation:
    def test_valid_vitals(self):
        v = VitalSigns(heart_rate=80, spo2=98.0, gcs=15)
        assert v.heart_rate == 80

    def test_heart_rate_out_of_range(self):
        with pytest.raises(ValueError):
            VitalSigns(heart_rate=500)

    def test_spo2_out_of_range(self):
        with pytest.raises(ValueError):
            VitalSigns(spo2=105.0)

    def test_gcs_below_minimum(self):
        with pytest.raises(ValueError):
            VitalSigns(gcs=2)

    def test_pain_scale_range(self):
        with pytest.raises(ValueError):
            VitalSigns(pain_scale=11)


class TestDemographicsValidation:
    def test_valid_demographics(self):
        d = PatientDemographics(age=30, sex="female")
        assert d.age == 30

    def test_age_out_of_range(self):
        with pytest.raises(ValueError):
            PatientDemographics(age=-1, sex="male")

    def test_age_upper_bound(self):
        with pytest.raises(ValueError):
            PatientDemographics(age=200, sex="male")


class TestCaseIdValidation:
    def test_valid_uuid(self, sample_case_data: dict):
        case = MedicalCase.model_validate(sample_case_data)
        uuid.UUID(case.case_id)  # should not raise

    def test_invalid_uuid_gets_replaced(self, sample_case_data: dict):
        sample_case_data["case_id"] = "not-a-uuid"
        case = MedicalCase.model_validate(sample_case_data)
        # Should auto-generate a valid UUID instead of raising
        uuid.UUID(case.case_id)  # doesn't raise


class TestDifficultyEnum:
    def test_all_values(self):
        assert set(Difficulty) == {Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD}

    def test_string_coercion(self, sample_case_data: dict):
        sample_case_data["difficulty"] = "hard"
        case = MedicalCase.model_validate(sample_case_data)
        assert case.difficulty == Difficulty.HARD
