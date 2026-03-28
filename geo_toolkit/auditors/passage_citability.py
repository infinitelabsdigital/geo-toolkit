"""Audit passage-level citability for AI extraction."""

import re


class PassageCitabilityAuditor:
    """Score individual content passages for AI citation readiness."""

    def audit(self, url, context=None):
        html = context.get("html", "") if context else ""
        if not html:
            raise ValueError("Requires HTML content in context")

        passages = self._extract_passages(html)
        citable = [p for p in passages if p["score"] >= 60]

        details = [
            f"Total content passages: {len(passages)}",
            f"Citable passages (score >= 60): {len(citable)}",
        ]

        if citable:
            best = sorted(citable, key=lambda p: p["score"], reverse=True)[:3]
            details.append("Top citable passages:")
            for i, p in enumerate(best):
                details.append(f'  {i+1}. [Score: {p["score"]}/100] "{p["text"][:80]}..."')

        # Check for answer-first pattern
        has_answer_first = self._detect_answer_first(html)
        if has_answer_first:
            details.append("Answer-first pattern detected — ideal for AI extraction")
        else:
            details.append("No answer-first pattern — AI prefers direct answers before elaboration")

        # Definition patterns
        defs = self._count_definitions(passages)
        if defs > 0:
            details.append(f"{defs} definition-style passage(s) — great for AI knowledge extraction")

        ratio = len(citable) / len(passages) if passages else 0
        score = round(ratio * 60)
        if has_answer_first:
            score += 20
        if defs > 0:
            score += min(20, defs * 5)
        score = min(score, 100)

        passed = len(citable) >= 3 and ratio >= 0.3

        return {
            "name": "Passage-Level Citability",
            "passed": passed,
            "warning": 0 < len(citable) < 3,
            "description": (
                f"{len(citable)} highly citable passages ({round(ratio*100)}% citability rate)"
                if passed
                else f"Only {len(citable)} citable passage(s) — aim for 3+ per page"
                if citable
                else "No highly citable passages — content needs restructuring"
            ),
            "details": details,
            "recommendation": (
                'Use the "answer first, then elaborate" pattern with clear, self-contained statements.'
                if not passed else None
            ),
            "score": score,
            "weight": 3,
        }

    def _extract_passages(self, html):
        """Extract text passages from HTML paragraphs and list items."""
        passages = []
        seen = set()

        # Simple regex extraction for <p>, <li>, <blockquote>, <td> tags
        for tag in ("p", "li", "blockquote", "td"):
            pattern = re.compile(rf"<{tag}[^>]*>(.*?)</{tag}>", re.DOTALL | re.IGNORECASE)
            for match in pattern.finditer(html):
                text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
                text = re.sub(r"\s+", " ", text)
                if 40 <= len(text) <= 500 and text not in seen:
                    seen.add(text)
                    passages.append({
                        "text": text,
                        "tag": tag,
                        "score": self._score_passage(text),
                    })

        return passages

    def _score_passage(self, text):
        """Score a passage for AI citability (0-100)."""
        score = 30

        # Definitive statements
        if re.match(r"^[A-Z].+\b(is|are|was|were|means|refers to|defined as)\b", text):
            score += 20

        # Contains statistics
        if re.search(r"\d+%|\$[\d,]+|\d+\.\d+", text):
            score += 15

        # Proper sentence structure
        if re.match(r"^[A-Z]", text) and re.search(r"[.!]$", text):
            score += 10

        # Comparison language
        if re.search(r"\b(best|worst|most|least|compared to|versus|vs\.?|unlike|better|worse)\b", text, re.I):
            score += 10

        # Good citation length
        if 60 <= len(text) <= 200:
            score += 10

        # Contains year reference
        if re.search(r"20[12]\d", text):
            score += 5

        # Penalty for vague language
        if re.search(r"\b(maybe|perhaps|might|could|somewhat|generally)\b", text, re.I):
            score -= 10

        return min(max(score, 0), 100)

    def _detect_answer_first(self, html):
        """Check if content leads with a direct answer."""
        # Find first <p> after an <h1> or <h2>
        match = re.search(r"<h[12][^>]*>.*?</h[12]>\s*<p[^>]*>(.*?)</p>", html, re.DOTALL | re.IGNORECASE)
        if not match:
            return False
        text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
        return bool(re.match(r"^[A-Z].+\b(is|are|means|refers to)\b", text)) or len(text) <= 200

    def _count_definitions(self, passages):
        count = 0
        for p in passages:
            if re.search(r"\b(is defined as|refers to|is a |are a |means that)\b", p["text"], re.I):
                count += 1
        return count
