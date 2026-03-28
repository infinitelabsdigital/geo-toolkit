"""Core GEO auditor that orchestrates all audit modules.

Composes multiple best-in-class OSS libraries:
- Scrapling (33k+ stars) for intelligent web fetching
- Protego (Scrapy team) for robots.txt parsing
- Trafilatura (used by HuggingFace, IBM, Microsoft) for content extraction
- Extruct (Scrapinghub) for structured data extraction
"""

import urllib.request
import urllib.error
from urllib.parse import urlparse
from datetime import datetime, timezone

from geo_toolkit.auditors.crawler_access import CrawlerAccessAuditor
from geo_toolkit.auditors.llms_txt import LLMSTxtAuditor
from geo_toolkit.auditors.content_structure import ContentStructureAuditor
from geo_toolkit.auditors.schema_markup import SchemaMarkupAuditor
from geo_toolkit.auditors.passage_citability import PassageCitabilityAuditor
from geo_toolkit.auditors.entity_clarity import EntityClarityAuditor
from geo_toolkit.auditors.faq_density import FAQDensityAuditor
from geo_toolkit.scorers.geo_scorer import GEOScorer


class GEOAuditor:
    """Main auditor that runs all GEO checks against a URL.

    Orchestrates 7 specialized auditors to produce a comprehensive
    AI Citability Score (0-100) with actionable recommendations.
    """

    def __init__(self, timeout=15, use_scrapling=True):
        self.timeout = timeout
        self.use_scrapling = use_scrapling
        self.auditors = [
            CrawlerAccessAuditor(),
            LLMSTxtAuditor(),
            ContentStructureAuditor(),
            SchemaMarkupAuditor(),
            PassageCitabilityAuditor(),
            EntityClarityAuditor(),
            FAQDensityAuditor(),
        ]
        self.scorer = GEOScorer()

    def audit(self, input_url):
        """Run a full GEO audit on the given URL.

        Args:
            input_url: The URL to audit (with or without protocol).

        Returns:
            dict with url, timestamp, score, grade, and audit results.
        """
        url = input_url if input_url.startswith("http") else f"https://{input_url}"
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        # Fetch page HTML
        html = self._fetch_page(url)

        # Extract clean content with Trafilatura if available
        extracted = self._extract_content(html, url)

        # Build context for auditors
        context = {
            "html": html,
            "url": url,
            "base_url": base_url,
            "extracted": extracted,
        }

        # Run all auditors
        audit_results = []
        for auditor in self.auditors:
            try:
                result = auditor.audit(url, context)
                if isinstance(result, list):
                    audit_results.extend(result)
                else:
                    audit_results.append(result)
            except Exception as e:
                audit_results.append({
                    "name": auditor.__class__.__name__,
                    "passed": False,
                    "warning": True,
                    "description": f"Audit skipped: {str(e)}",
                    "details": [],
                    "recommendation": None,
                    "score": 0,
                    "weight": 1,
                })

        # Calculate overall score
        score, grade = self.scorer.calculate(audit_results)

        return {
            "url": url,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "score": score,
            "grade": grade,
            "audits": audit_results,
        }

    def _fetch_page(self, url):
        """Fetch page HTML. Uses Scrapling if available, falls back to urllib."""
        if self.use_scrapling:
            try:
                from scrapling import Fetcher
                fetcher = Fetcher(auto_match=False)
                response = fetcher.get(url, timeout=self.timeout)
                return response.html_content if hasattr(response, 'html_content') else str(response)
            except ImportError:
                pass
            except Exception:
                pass

        # Fallback: stdlib urllib
        req = urllib.request.Request(url, headers={
            "User-Agent": "geo-toolkit/0.1.0 (+https://github.com/infinitelabsdigital/geo-toolkit)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })
        with urllib.request.urlopen(req, timeout=self.timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")

    def _extract_content(self, html, url):
        """Extract clean article content using Trafilatura."""
        try:
            import trafilatura
            result = trafilatura.extract(
                html,
                url=url,
                include_comments=False,
                include_tables=True,
                output_format='txt',
            )
            metadata = trafilatura.extract(
                html,
                url=url,
                output_format='xmltei',
                include_comments=False,
            )
            return {
                "text": result or "",
                "metadata_raw": metadata or "",
                "source": "trafilatura",
            }
        except ImportError:
            return {"text": "", "metadata_raw": "", "source": "none"}
        except Exception:
            return {"text": "", "metadata_raw": "", "source": "error"}
