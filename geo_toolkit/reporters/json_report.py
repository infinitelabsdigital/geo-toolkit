"""Generate JSON reports from audit results."""


def generate_json_report(results):
    """Generate a JSON-serializable GEO audit report."""
    audits = results["audits"]
    passed = sum(1 for a in audits if a.get("passed"))
    warned = sum(1 for a in audits if a.get("warning"))
    failed = sum(1 for a in audits if not a.get("passed") and not a.get("warning"))

    return {
        "url": results["url"],
        "timestamp": results.get("timestamp"),
        "score": results["score"],
        "grade": results.get("grade"),
        "summary": {
            "total_checks": len(audits),
            "passed": passed,
            "warnings": warned,
            "failed": failed,
        },
        "audits": [
            {
                "name": a["name"],
                "passed": a.get("passed", False),
                "warning": a.get("warning", False),
                "score": a.get("score", 0),
                "description": a.get("description", ""),
                "details": a.get("details", []),
                "recommendation": a.get("recommendation"),
            }
            for a in audits
        ],
        "generator": "geo-toolkit v0.1.0",
        "repository": "https://github.com/infinitelabsdigital/geo-toolkit",
    }
