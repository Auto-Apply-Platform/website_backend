from __future__ import annotations


async def parse_resume_ai(file_path: str) -> dict:
    """
    TODO: будет реализовано позже
    Возвращает словарь с данными кандидата
    """
    return {
        "full_name": "",
        "role": "",
        "grade": "",
        "grade_raw": "",
        "experience_years": 0.3,
        "stack": {
            "core": [],
            "additional": [],
        },
        "work_format": "",
        "employment_type": None,
        "location": "",
        "salary_expectations": "",
        "education_level": "",
        "additional_information": "",
    }


async def determine_parsing_status(parsed: dict) -> str:
    required_fields = [
        "full_name",
        "role",
        "grade",
        "experience_years",
        "work_format",
    ]
    for field in required_fields:
        if field not in parsed:
            return "rejected"
        value = parsed.get(field)
        if value is None:
            return "rejected"
        if isinstance(value, str) and not value.strip():
            return "rejected"
        if isinstance(value, list) and not value:
            return "rejected"
    return "accepted"
