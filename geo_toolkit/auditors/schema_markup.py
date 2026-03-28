"""Audit schema markup (structured data) for AI relevance.

Uses Extruct (by Scrapinghub) for robust extraction of JSON-LD,
microdata, RDFa, and OpenGraph from HTML pages.
"""

import re
import json


AI_RELEVANT_TYPES = {
    "FAQPage", "HowTo", "Article", "BlogPosting", "WebPage",
    "Product", "Review", "Organization", "Person", "BreadcrumbList",
    "QAPage", "Dataset", "SoftwareApplication", "Course",
    "NewsArticle", "TechArticle",
}


class SchemaMarkupAuditor:
    """Detect and evaluate structured data for AI citability.

    Leverages Extruct for comprehensive extraction of JSON-LD, microdata,
    RDFa, OpenGraph, and microformat data from HTML pages.
    """

    def audit(self, url, context=None):
        html = context.get("html", "") if context else ""
        if not html:
            raise ValueError("Requires HTML content in context")

        schemas, metadata = self._extract_all(html, url)
        found_types = set()
        for s in schemas:
            t = s.get("@type", "")
            if isinstance(t, list):
                found_types.update(t)
            elif t:
                found_types.add(t)

        ai_types = found_types & AI_RELEVANT_TYPES
        details = []

        # Report on all extracted metadata types
        if metadata.get("opengraph"):
            details.append(f"OpenGraph data found ({len(metadata['opengraph'])} entries)")
        if metadata.get("microdata"):
            details.append(f"Microdata found ({len(metadata['microdata'])} items)")
        if metadata.get("rdfa"):
            details.append(f"RDFa data found ({len(metadata['rdfa'])} items)")

        details.append(
            f"Schema types: {', '.join(sorted(found_types)) if found_types else 'None'}"
        )
        if ai_types:
            details.append(f"AI-relevant schemas: {', '.join(sorted(ai_types))}")

        has_faq = "FAQPage" in found_types
        has_howto = "HowTo" in found_types
        has_article = found_types & {"Article", "BlogPosting", "NewsArticle", "TechArticle"}

        if has_faq:
            details.append("FAQPage schema — excellent for AI extraction")
        if has_howto:
            details.append("HowTo schema — great for step-by-step AI answers")
        if has_article:
            details.append("Article schema — helps AI identify authorship")

        score = 0
        if schemas:
            score += 30
        if has_faq:
            score += 30
        if has_howto:
            score += 20
        if has_article:
            score += 20
        if len(ai_types) >= 3:
            score += 10
        score = min(score, 100)

        passed = len(schemas) > 0 and len(ai_types) >= 1

        recommendation = None
        if not schemas:
            recommendation = "Add JSON-LD structured data — start with Article and FAQPage schemas"
        elif not has_faq:
            recommendation = "Add FAQPage schema — #1 schema type for AI answer extraction"

        return {
            "name": "Schema Markup (Structured Data)",
            "passed": passed,
            "warning": len(schemas) > 0 and not ai_types,
            "description": (
                f"{len(ai_types)} AI-relevant schema type(s): {', '.join(sorted(ai_types))}"
                if passed
                else "No structured data detected — major gap for AI citability"
                if not schemas
                else "Schema found but missing AI-relevant types"
            ),
            "details": details,
            "recommendation": recommendation,
            "score": score,
            "weight": 3,
        }

    def _extract_all(self, html, url):
        """Extract structured data using Extruct, with regex fallback."""
        schemas = []
        metadata = {}

        # Try Extruct first (comprehensive extraction)
        try:
            import extruct
            data = extruct.extract(html, base_url=url, syntaxes=[
                'json-ld', 'microdata', 'opengraph', 'rdfa'
            ])
            # JSON-LD schemas
            for item in data.get('json-ld', []):
                if isinstance(item, dict):
                    if '@graph' in item:
                        schemas.extend(item['@graph'])
                    else:
                        schemas.append(item)

            # Microdata
            for item in data.get('microdata', []):
                if isinstance(item, dict) and item.get('type'):
                    type_name = item['type']
                    if isinstance(type_name, list):
                        for t in type_name:
                            schemas.append({"@type": t.split("/")[-1], "_source": "microdata"})
                    elif isinstance(type_name, str):
                        schemas.append({"@type": type_name.split("/")[-1], "_source": "microdata"})

            metadata = {
                'opengraph': data.get('opengraph', []),
                'microdata': data.get('microdata', []),
                'rdfa': data.get('rdfa', []),
            }
            return schemas, metadata

        except ImportError:
            pass
        except Exception:
            pass

        # Fallback: regex-based JSON-LD extraction
        pattern = re.compile(
            r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            re.DOTALL | re.IGNORECASE,
        )
        for match in pattern.finditer(html):
            try:
                data = json.loads(match.group(1))
                if isinstance(data, list):
                    schemas.extend(data)
                elif isinstance(data, dict):
                    if "@graph" in data:
                        schemas.extend(data["@graph"])
                    else:
                        schemas.append(data)
            except (json.JSONDecodeError, ValueError):
                pass

        return schemas, metadata
