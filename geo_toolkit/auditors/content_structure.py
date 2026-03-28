"""Audit content structure for AI citability."""

import re
from html.parser import HTMLParser


class SimpleHTMLParser(HTMLParser):
    """Lightweight HTML parser for content structure analysis."""

    def __init__(self):
        super().__init__()
        self.headings = []
        self.paragraphs = []
        self.lists = 0
        self.tables = 0
        self.meta = {}
        self.title = ""
        self.links = {"internal": 0, "external": 0}
        self._current_tag = None
        self._current_data = ""
        self._in_title = False
        self._in_heading = False
        self._heading_level = 0
        self._in_p = False
        self._skip_tags = {"script", "style", "nav", "footer", "header"}
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)

        if tag in self._skip_tags:
            self._skip_depth += 1
            return

        if tag == "title":
            self._in_title = True
            self._current_data = ""
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._in_heading = True
            self._heading_level = int(tag[1])
            self._current_data = ""
        elif tag == "p":
            self._in_p = True
            self._current_data = ""
        elif tag in ("ul", "ol"):
            self.lists += 1
        elif tag == "table":
            self.tables += 1
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            if name == "description":
                self.meta["description"] = content
            elif prop == "og:title":
                self.meta["og_title"] = content
            elif prop == "og:description":
                self.meta["og_description"] = content
        elif tag == "link":
            rel = attrs_dict.get("rel", "")
            if rel == "canonical":
                self.meta["canonical"] = attrs_dict.get("href", "")

    def handle_endtag(self, tag):
        if tag in self._skip_tags and self._skip_depth > 0:
            self._skip_depth -= 1
            return

        if tag == "title":
            self._in_title = False
            self.title = self._current_data.strip()
        elif tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._in_heading:
            self._in_heading = False
            self.headings.append({
                "level": self._heading_level,
                "text": self._current_data.strip()[:100],
            })
        elif tag == "p" and self._in_p:
            self._in_p = False
            text = self._current_data.strip()
            if text:
                self.paragraphs.append(text)

    def handle_data(self, data):
        if self._skip_depth > 0:
            return
        if self._in_title or self._in_heading or self._in_p:
            self._current_data += data


class ContentStructureAuditor:
    """Audit page content structure for AI readability."""

    def audit(self, url, context=None):
        html = context.get("html", "") if context else ""
        if not html:
            raise ValueError("Requires HTML content in context")

        parser = SimpleHTMLParser()
        parser.feed(html)

        results = []
        results.append(self._audit_headings(parser))
        results.append(self._audit_meta(parser))
        results.append(self._audit_depth(parser, html))
        return results

    def _audit_headings(self, parser):
        headings = parser.headings
        h1s = [h for h in headings if h["level"] == 1]
        h2s = [h for h in headings if h["level"] == 2]
        h3s = [h for h in headings if h["level"] == 3]

        details = [f"H1: {len(h1s)}, H2: {len(h2s)}, H3: {len(h3s)}"]
        issues = 0

        if len(h1s) == 0:
            details.append("Missing H1 tag — critical for AI parsing")
            issues += 1
        if len(h1s) > 1:
            details.append(f"Multiple H1 tags ({len(h1s)}) — should have exactly one")
            issues += 1
        if len(h2s) == 0:
            details.append("No H2 tags — content lacks clear section structure")
            issues += 1

        # Check heading level skips
        prev = 0
        for h in headings:
            if h["level"] > prev + 1 and prev > 0:
                details.append(f"Heading skip: H{prev} to H{h['level']}")
                issues += 1
                break
            prev = h["level"]

        score = max(0, 100 - issues * 25)

        return {
            "name": "Heading Hierarchy",
            "passed": issues == 0,
            "warning": issues == 1,
            "description": (
                f"Clean heading structure with {len(headings)} headings ({len(h2s)} sections)"
                if issues == 0
                else f"{issues} heading structure issue(s) detected"
            ),
            "details": details,
            "recommendation": (
                "Fix heading hierarchy — AI systems use headings to extract answers"
                if issues > 0 else None
            ),
            "score": score,
            "weight": 2,
        }

    def _audit_meta(self, parser):
        title = parser.title
        meta = parser.meta
        details = []
        issues = 0

        if not title:
            details.append("Missing <title> tag")
            issues += 1
        elif len(title) < 30:
            details.append(f"Title too short ({len(title)} chars)")
            issues += 1
        elif len(title) > 70:
            details.append(f"Title may be truncated ({len(title)} chars)")
        else:
            details.append(f'Title: "{title[:60]}"')

        desc = meta.get("description", "")
        if not desc:
            details.append("Missing meta description")
            issues += 1
        else:
            details.append(f"Meta description: {len(desc)} chars")

        if not meta.get("og_title"):
            details.append("Missing og:title")
            issues += 1
        if not meta.get("og_description"):
            details.append("Missing og:description")
            issues += 1
        if not meta.get("canonical"):
            details.append("Missing canonical URL")
            issues += 1

        score = max(0, 100 - issues * 20)

        return {
            "name": "Meta Tags & AI Signals",
            "passed": issues == 0,
            "warning": 0 < issues <= 2,
            "description": (
                "All essential meta tags present"
                if issues == 0
                else f"{issues} meta tag issue(s) affecting AI discoverability"
            ),
            "details": details,
            "recommendation": (
                "Complete all meta tags — AI systems use these to determine relevance"
                if issues > 0 else None
            ),
            "score": score,
            "weight": 2,
        }

    def _audit_depth(self, parser, html):
        # Estimate word count from all paragraphs
        all_text = " ".join(parser.paragraphs)
        word_count = len(all_text.split())

        details = [
            f"Word count: ~{word_count}",
            f"Paragraphs: {len(parser.paragraphs)}, Lists: {parser.lists}, Tables: {parser.tables}",
        ]

        issues = 0
        if word_count < 300:
            details.append("Thin content — AI prefers comprehensive answers (800+ words)")
            score = 20
            issues += 1
        elif word_count < 800:
            details.append("Content could be more comprehensive (aim for 1500+ words)")
            score = 50
        elif word_count >= 1500:
            details.append("Good content depth for AI citation")
            score = 90
        else:
            score = 70

        if parser.lists > 0:
            score = min(100, score + 5)
        if parser.tables > 0:
            score = min(100, score + 5)

        return {
            "name": "Content Depth",
            "passed": word_count >= 800,
            "warning": 300 <= word_count < 800,
            "description": (
                f"Comprehensive content ({word_count} words) suitable for AI citation"
                if word_count >= 800
                else f"Content may be too thin for AI citation ({word_count} words)"
            ),
            "details": details,
            "recommendation": (
                "Expand content to 800+ words with structured sections"
                if word_count < 800 else None
            ),
            "score": score,
            "weight": 2,
        }
