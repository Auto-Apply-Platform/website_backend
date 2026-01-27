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
