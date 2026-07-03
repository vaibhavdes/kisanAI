import re


def normalize_phone(value: str, default_country_code: str = "91") -> str:
    digits = re.sub(r"\D+", "", value)
    if not digits:
        raise ValueError("phone number is required")
    if len(digits) == 10:
        return f"{default_country_code}{digits}"
    if digits.startswith("0") and len(digits) == 11:
        return f"{default_country_code}{digits[1:]}"
    return digits
