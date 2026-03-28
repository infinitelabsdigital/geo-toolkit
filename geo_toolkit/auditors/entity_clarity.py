"""Audit entity clarity for AI knowledge extraction."""

import re


class EntityClarityAuditor:
    """Check if entities (people, orgs, concepts) are clearly defined."""

    def audit(self, url, context=None):
        html = context.get("html", "") if context else ""
        if not html:
            raise ValueError("Requires HTML content in context")

        # Strip HTML tags for text analysis
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        # Detect entities
        proper_nouns = self._find_proper_nouns(text)
        defined_entities = self._find_defined_entities(text)
        acronyms = self._find_acronyms(text)
        undefined_acronyms = self._find_undefined_acronyms(text, acronyms)

        details = [
            f"Proper nouns detected: {len(proper_nouns)}",
            f"Entities with definitions: {len(defined_entities)}",
            f"Acronyms found: {len(acronyms)}",
        ]

        issues = 0
        if undefined_acronyms:
            details.append(
                f"Undefined acronyms: {', '.join(list(undefined_acronyms)[:5])}"
            )
            issues += 1

        # Check if the page clearly identifies its subject
        has_clear_subject = self._has_clear_subject(text)
        if has_clear_subject:
            details.append("Clear subject identification in opening content")
        else:
            details.append("Subject not clearly identified in opening — may confuse AI systems")
            issues += 1

        # Check for author/org attribution
        has_attribution = self._has_attribution(html)
        if has_attribution:
            details.append("Author/organization attribution found")
        else:
            details.append("No clear author/organization attribution — weakens E-E-A-T for AI")
            issues += 1

        score = 70
        if defined_entities:
            score += min(15, len(defined_entities) * 3)
        if has_clear_subject:
            score += 10
        if has_attribution:
            score += 10
        if undefined_acronyms:
            score -= len(undefined_acronyms) * 5
        if not has_clear_subject:
            score -= 15
        score = min(max(score, 0), 100)

        passed = issues == 0 and score >= 60

        recommendation = None
        if undefined_acronyms:
            recommendation = f"Define acronyms on first use: {', '.join(list(undefined_acronyms)[:3])}"
        elif not has_clear_subject:
            recommendation = "Clearly identify the main subject in your opening paragraph"
        elif not has_attribution:
            recommendation = "Add author name and credentials for E-E-A-T signals"

        return {
            "name": "Entity Clarity",
            "passed": passed,
            "warning": issues == 1,
            "description": (
                "Entities are clearly defined and attributed"
                if passed
                else f"{issues} entity clarity issue(s) — may confuse AI parsing"
            ),
            "details": details,
            "recommendation": recommendation,
            "score": score,
            "weight": 2,
        }

    def _find_proper_nouns(self, text):
        """Find capitalized multi-word phrases (likely proper nouns)."""
        matches = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b", text)
        return list(set(matches))[:20]

    def _find_defined_entities(self, text):
        """Find entities that are explicitly defined in the text."""
        patterns = [
            r"([A-Z][a-zA-Z\s]+)\s+(?:is|are)\s+(?:a|an|the)\s+\w+",
            r"([A-Z][a-zA-Z\s]+),\s+(?:which|who)\s+(?:is|are)",
            r"([A-Z][a-zA-Z\s]+)\s+(?:refers to|means|is defined as)",
        ]
        entities = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                entity = match.group(1).strip()
                if len(entity) > 2 and len(entity) < 50:
                    entities.add(entity)
        return list(entities)

    def _find_acronyms(self, text):
        """Find acronyms (2+ uppercase letters)."""
        return list(set(re.findall(r"\b([A-Z]{2,6})\b", text)))

    def _find_undefined_acronyms(self, text, acronyms):
        """Find acronyms that aren't defined with their full form."""
        undefined = set()
        common = {"US", "UK", "EU", "AI", "IT", "CEO", "CTO", "API", "URL",
                   "HTML", "CSS", "SEO", "FAQ", "PDF", "HTTP", "HTTPS", "RSS"}
        for acr in acronyms:
            if acr in common:
                continue
            # Check for pattern: Full Name (ACRONYM)
            pattern = rf"\w+[\w\s]+\({re.escape(acr)}\)"
            if not re.search(pattern, text):
                undefined.add(acr)
        return undefined

    def _has_clear_subject(self, text):
        """Check if the opening 200 chars clearly state the subject."""
        opening = text[:500]
        # Look for definitive statements
        return bool(re.search(
            r"\b(is a|is an|is the|are the|refers to|this guide|this article|this tool)\b",
            opening, re.I
        ))

    def _has_attribution(self, html):
        """Check for author/org attribution in HTML."""
        patterns = [
            r'rel=["\']author["\']',
            r'class=["\'][^"\']*author[^"\']*["\']',
            r'<meta[^>]+name=["\']author["\']',
            r'"author"\s*:\s*[{"]',
            r'itemprop=["\']author["\']',
        ]
        return any(re.search(p, html, re.I) for p in patterns)
