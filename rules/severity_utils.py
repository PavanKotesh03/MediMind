# rules/severity_utils.py

SEVERITY_RANK = {
    "LOW": 1,
    "MODERATE": 2,
    "HIGH": 3,
    "EMERGENCY": 4
}

def sort_by_severity(results: list[dict]) -> list[dict]:
    return sorted(
        results,
        key=lambda r: (
            r.get("confidence", 0),  # Primary sort by confidence (higher is better)
            SEVERITY_RANK.get(r["severity"], 0)  # Secondary sort by severity
        ),
        reverse=True
    )


def highest_severity(results: list[dict]) -> str | None:
    if not results:
        return None
    return sort_by_severity(results)[0]["severity"]