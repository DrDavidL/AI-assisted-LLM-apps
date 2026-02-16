"""OpenAI-powered medical case generation."""

from __future__ import annotations

import openai

from app.config import settings
from app.schemas.medical_case import MedicalCase


SYSTEM_PROMPT = (
    "You are a medical education case generator. Generate realistic, clinically accurate "
    "medical cases for computer science students learning about health informatics. "
    "Populate ALL fields with plausible clinical data. Return valid JSON matching the "
    "provided schema exactly."
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

    completion = await client.beta.chat.completions.parse(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": " ".join(user_parts)},
        ],
        response_format=MedicalCase,
    )

    message = completion.choices[0].message
    if message.refusal:
        raise ValueError(f"LLM refused to generate case: {message.refusal}")
    if message.parsed is None:
        raise ValueError("LLM returned empty parsed response.")

    case: MedicalCase = message.parsed
    if specialty:
        case.specialty = specialty
    if difficulty:
        case.difficulty = difficulty  # type: ignore[assignment]
    return case
