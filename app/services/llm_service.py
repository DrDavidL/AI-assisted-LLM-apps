"""OpenAI-powered medical case generation."""

from __future__ import annotations

import uuid

import openai

from app.config import settings
from app.schemas.medical_case import MedicalCase


SYSTEM_PROMPT = (
    "You are a medical education case generator. Generate realistic, clinically accurate "
    "medical cases for computer science students learning about health informatics. "
    "Populate ALL fields with plausible clinical data. Return valid JSON matching the "
    "provided schema exactly. "
    "For case_id, always use a valid UUID v4 string (e.g. '550e8400-e29b-41d4-a716-446655440000')."
)


async def generate_case(
    *,
    specialty: str | None = None,
    prompt: str | None = None,
    difficulty: str | None = None,
) -> MedicalCase:
    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

    user_parts: list[str] = ["Generate a detailed medical case."]
    if specialty:
        user_parts.append(f"Specialty: {specialty}")
    if difficulty:
        user_parts.append(f"Difficulty: {difficulty}")
    if prompt:
        user_parts.append(f"Additional context: {prompt}")

    response = await client.responses.parse(
        model=settings.OPENAI_MODEL,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": " ".join(user_parts)},
        ],
        text_format=MedicalCase,
    )

    case = response.output_parsed
    if case is None:
        raise ValueError("LLM returned empty parsed response.")

    # Override LLM-generated case_id with a proper UUID
    case.case_id = str(uuid.uuid4())
    if specialty:
        case.specialty = specialty
    if difficulty:
        case.difficulty = difficulty  # type: ignore[assignment]
    return case
