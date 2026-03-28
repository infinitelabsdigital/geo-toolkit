"""Audit llms.txt compliance for AI content discovery."""

import re
import urllib.request
import urllib.error
from urllib.parse import urlparse


class LLMSTxtAuditor:
    """Check for llms.txt file presence and compliance."""

    def audit(self, url, context=None):
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        paths = ["/llms.txt", "/llms-full.txt", "/.well-known/llms.txt"]
        found = False
        found_url = None
        content = ""
        size = 0

        for path in paths:
            try:
                check_url = f"{base_url}{path}"
                req = urllib.request.Request(check_url, headers={"User-Agent": "geo-toolkit/0.1.0"})
                with urllib.request.urlopen(req, timeout=8) as resp:
                    if resp.status == 200:
                        content = resp.read().decode("utf-8", errors="replace")
                        if content.strip():
                            found = True
                            found_url = check_url
                            size = len(content.encode("utf-8"))
                            break
            except Exception:
                continue

        sections = self._parse_sections(content) if found else []
        has_title = found and content.strip().startswith("#")

        details = []
        if found:
            details.append(f"Found at: {found_url}")
            details.append(f"File size: {size} bytes")
            if sections:
                details.append(f"Sections: {', '.join(sections)}")
            if not has_title:
                details.append("Missing: Title header (should start with # Title)")
        else:
            details.append("Checked: /llms.txt, /llms-full.txt, /.well-known/llms.txt")

        score = 0
        if found:
            score += 40 if has_title else 20
            score += 30 if len(sections) > 0 else 0
            score += min(30, len(sections) * 15) if len(sections) >= 2 else 0
        score = min(score, 100)

        recommendation = None
        if not found:
            recommendation = "Create an llms.txt file at your domain root. See https://llmstxt.org"
        elif not has_title:
            recommendation = "Add a title header (# YourSiteName) to the top of llms.txt"

        return {
            "name": "llms.txt Compliance",
            "passed": found,
            "warning": False,
            "description": (
                f"llms.txt file found with {len(sections)} section(s)"
                if found
                else "No llms.txt file detected — AI systems cannot discover your content structure"
            ),
            "details": details,
            "recommendation": recommendation,
            "score": score,
            "weight": 2,
            "found": found,
            "url": found_url,
            "size": size,
            "sections": sections,
        }

    def _parse_sections(self, content):
        sections = []
        for line in content.split("\n"):
            match = re.match(r"^#{1,3}\s+(.+)", line)
            if match:
                sections.append(match.group(1).strip())
        return sections
