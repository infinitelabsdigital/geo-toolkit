"""Tests for individual GEO audit modules."""

import unittest
from geo_toolkit.auditors.crawler_access import CrawlerAccessAuditor
from geo_toolkit.auditors.content_structure import ContentStructureAuditor
from geo_toolkit.auditors.schema_markup import SchemaMarkupAuditor
from geo_toolkit.auditors.passage_citability import PassageCitabilityAuditor
from geo_toolkit.auditors.entity_clarity import EntityClarityAuditor
from geo_toolkit.auditors.faq_density import FAQDensityAuditor
from geo_toolkit.scorers.geo_scorer import GEOScorer


SAMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>What is Generative Engine Optimization (GEO)?</title>
    <meta name="description" content="GEO is the practice of optimizing content for AI-powered search engines like ChatGPT and Perplexity.">
    <meta property="og:title" content="What is GEO?">
    <meta property="og:description" content="Learn about Generative Engine Optimization">
    <link rel="canonical" href="https://example.com/geo-guide">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "Article",
        "headline": "What is GEO?",
        "author": {"@type": "Person", "name": "Test Author"}
    }
    </script>
</head>
<body>
    <h1>What is Generative Engine Optimization (GEO)?</h1>
    <p>Generative Engine Optimization (GEO) is the practice of optimizing content to be cited, referenced, and surfaced by AI-powered search engines including ChatGPT, Perplexity AI, and Google AI Overviews.</p>
    <h2>Why Does GEO Matter?</h2>
    <p>Over 50% of Google searches now return AI-generated answers. Tools like Perplexity serve millions of users who never click a link. Traditional SEO gets you ranked, but GEO gets you cited.</p>
    <h2>How to Optimize for AI Citations</h2>
    <p>The key to GEO is structuring content with clear, self-contained statements that directly answer questions. Use the answer-first pattern: state your conclusion, then elaborate with supporting evidence.</p>
    <h3>What is the answer-first pattern?</h3>
    <p>The answer-first pattern means leading with a direct, concise answer to the question before providing additional context. This is how AI systems extract citations — they look for passages that stand alone as complete answers.</p>
    <h2>FAQ</h2>
    <h3>What tools can I use for GEO?</h3>
    <p>geo-toolkit is an open-source Python library that audits your content for AI citability across 7 dimensions including crawler access, schema markup, and passage-level scoring.</p>
    <h3>Is GEO different from SEO?</h3>
    <p>Yes. SEO focuses on ranking in traditional search results. GEO focuses on being cited by AI systems. They complement each other — good SEO provides the foundation, and GEO ensures AI systems can extract and cite your content.</p>
</body>
</html>
"""

MINIMAL_HTML = """
<html><head><title>Short</title></head>
<body><p>Hello world.</p></body></html>
"""

ROBOTS_BLOCK_ALL = """
User-agent: GPTBot
Disallow: /

User-agent: ClaudeBot
Disallow: /

User-agent: PerplexityBot
Disallow: /
"""


class TestContentStructure(unittest.TestCase):
    def test_good_html(self):
        auditor = ContentStructureAuditor()
        results = auditor.audit("https://example.com", {"html": SAMPLE_HTML})
        # Should return list of 3 audit results
        self.assertEqual(len(results), 3)
        # Heading hierarchy should pass
        heading_result = results[0]
        self.assertEqual(heading_result["name"], "Heading Hierarchy")
        self.assertTrue(heading_result["passed"])

    def test_minimal_html(self):
        auditor = ContentStructureAuditor()
        results = auditor.audit("https://example.com", {"html": MINIMAL_HTML})
        # Content depth should fail (too thin)
        depth_result = results[2]
        self.assertFalse(depth_result["passed"])


class TestSchemaMarkup(unittest.TestCase):
    def test_with_json_ld(self):
        auditor = SchemaMarkupAuditor()
        result = auditor.audit("https://example.com", {"html": SAMPLE_HTML})
        self.assertTrue(result["passed"])
        self.assertIn("Article", result["description"])

    def test_without_schema(self):
        auditor = SchemaMarkupAuditor()
        result = auditor.audit("https://example.com", {"html": MINIMAL_HTML})
        self.assertFalse(result["passed"])


class TestPassageCitability(unittest.TestCase):
    def test_citable_content(self):
        auditor = PassageCitabilityAuditor()
        result = auditor.audit("https://example.com", {"html": SAMPLE_HTML})
        self.assertGreater(result["score"], 0)
        self.assertIn("citable", result["description"].lower())


class TestEntityClarity(unittest.TestCase):
    def test_clear_entities(self):
        auditor = EntityClarityAuditor()
        result = auditor.audit("https://example.com", {"html": SAMPLE_HTML})
        self.assertIsInstance(result["score"], (int, float))


class TestFAQDensity(unittest.TestCase):
    def test_with_faq(self):
        auditor = FAQDensityAuditor()
        result = auditor.audit("https://example.com", {"html": SAMPLE_HTML})
        self.assertTrue(result["passed"])
        self.assertIn("question", result["description"].lower())


class TestGEOScorer(unittest.TestCase):
    def test_scoring(self):
        scorer = GEOScorer()
        results = [
            {"score": 80, "weight": 3},
            {"score": 60, "weight": 2},
            {"score": 100, "weight": 1},
        ]
        score, grade = scorer.calculate(results)
        self.assertGreater(score, 0)
        self.assertLessEqual(score, 100)
        self.assertIn(grade, ["A+", "A", "B", "C", "D", "F"])

    def test_perfect_score(self):
        scorer = GEOScorer()
        results = [{"score": 100, "weight": 1} for _ in range(5)]
        score, grade = scorer.calculate(results)
        self.assertEqual(score, 100)
        self.assertEqual(grade, "A+")

    def test_zero_score(self):
        scorer = GEOScorer()
        results = [{"score": 0, "weight": 1} for _ in range(5)]
        score, grade = scorer.calculate(results)
        self.assertEqual(score, 0)
        self.assertEqual(grade, "F")


if __name__ == "__main__":
    unittest.main()
