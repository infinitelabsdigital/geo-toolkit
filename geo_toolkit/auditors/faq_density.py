"""Audit FAQ and Q&A content density for AI answer extraction."""

import re


class FAQDensityAuditor:
    """Check for question-answer patterns that AI systems prefer to cite."""

    def audit(self, url, context=None):
        html = context.get("html", "") if context else ""
        if not html:
            raise ValueError("Requires HTML content in context")

        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text).strip()

        # Find questions in headings
        heading_questions = self._find_heading_questions(html)

        # Find questions in body text
        body_questions = self._find_body_questions(text)

        # Check for FAQ sections
        has_faq_section = self._has_faq_section(html)

        # Check for Q&A formatting
        qa_pairs = self._find_qa_pairs(html)

        total_questions = len(heading_questions) + len(body_questions)

        details = [
            f"Questions in headings: {len(heading_questions)}",
            f"Questions in body text: {len(body_questions)}",
            f"Q&A pairs detected: {len(qa_pairs)}",
        ]

        if has_faq_section:
            details.append("Dedicated FAQ section found")
        if heading_questions:
            details.append("Sample heading questions:")
            for q in heading_questions[:3]:
                details.append(f'  "{q[:70]}"')

        score = 0
        if heading_questions:
            score += min(40, len(heading_questions) * 10)
        if qa_pairs:
            score += min(30, len(qa_pairs) * 10)
        if has_faq_section:
            score += 20
        if body_questions:
            score += min(10, len(body_questions) * 2)
        score = min(score, 100)

        passed = total_questions >= 3 or (qa_pairs and len(qa_pairs) >= 2)

        recommendation = None
        if not passed:
            recommendation = (
                "Add question-based headings (H2/H3) that match how people ask AI assistants. "
                "Include a FAQ section with 3-5 common questions and direct answers."
            )

        return {
            "name": "FAQ & Q&A Density",
            "passed": passed,
            "warning": 0 < total_questions < 3,
            "description": (
                f"{total_questions} question(s) found — "
                + ("good Q&A density for AI extraction" if passed
                   else "add more questions for better AI citability")
            ),
            "details": details,
            "recommendation": recommendation,
            "score": score,
            "weight": 2,
        }

    def _find_heading_questions(self, html):
        """Find questions used in heading tags."""
        questions = []
        pattern = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.DOTALL | re.IGNORECASE)
        for match in pattern.finditer(html):
            text = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            if text.endswith("?") or text.lower().startswith(("what ", "how ", "why ", "when ", "where ", "who ", "which ", "can ", "does ", "is ", "are ", "should ")):
                questions.append(text)
        return questions

    def _find_body_questions(self, text):
        """Find question sentences in body text."""
        sentences = re.split(r"[.!?]+", text)
        questions = []
        for s in sentences:
            s = s.strip()
            if len(s) > 20 and (
                s.endswith("?") or
                re.match(r"^(What|How|Why|When|Where|Who|Which|Can|Does|Is|Are|Should)\s", s, re.I)
            ):
                questions.append(s)
        return questions[:10]

    def _has_faq_section(self, html):
        """Check if there's a dedicated FAQ section."""
        return bool(re.search(
            r"<h[1-6][^>]*>[^<]*(FAQ|Frequently Asked|Common Questions)[^<]*</h[1-6]>",
            html, re.IGNORECASE,
        ))

    def _find_qa_pairs(self, html):
        """Find question-answer pairs (question heading followed by paragraph)."""
        pairs = []
        pattern = re.compile(
            r"<h[2-4][^>]*>(.*?)</h[2-4]>\s*<p[^>]*>(.*?)</p>",
            re.DOTALL | re.IGNORECASE,
        )
        for match in pattern.finditer(html):
            question = re.sub(r"<[^>]+>", "", match.group(1)).strip()
            answer = re.sub(r"<[^>]+>", "", match.group(2)).strip()
            if (question.endswith("?") or question.lower().startswith(
                ("what", "how", "why", "when", "where", "who", "which", "can", "does", "is")
            )) and len(answer) > 30:
                pairs.append({"question": question, "answer": answer[:200]})
        return pairs
