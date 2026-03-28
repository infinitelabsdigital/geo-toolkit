# geo-toolkit

> The first open-source Generative Engine Optimization (GEO) audit toolkit. Measure and improve how your content gets cited by ChatGPT, Perplexity, Google AI Overviews, and other AI-powered search engines.

[![MIT License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-10%20passing-brightgreen.svg)]()
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/infinitelabsdigital/geo-toolkit/pulls)

## The Problem

Traditional SEO gets your content ranked. But today, over **60% of Google searches** trigger AI-generated answers. ChatGPT, Perplexity, and Google AI Overviews serve millions of users who read AI-synthesized responses — and may never click a link.

**If AI can't cite your content, you're invisible to a growing share of search traffic.**

There's no open-source tool to audit, measure, or improve AI citability. `geo-toolkit` fills that gap.

## What It Does

`geo-toolkit` runs 7 specialized audits against any URL and produces an **AI Citability Score (0-100)** with actionable recommendations:

| Audit | What It Checks |
|-------|---------------|
| **AI Crawler Access** | Are GPTBot, ClaudeBot, PerplexityBot blocked in `robots.txt`? |
| **llms.txt Compliance** | Does the site have an `llms.txt` file for AI content discovery? |
| **Heading Hierarchy** | Clean H1→H2→H3 structure AI systems use to parse content? |
| **Meta Tags & AI Signals** | Title, description, OG tags, canonical — all present? |
| **Content Depth** | Enough substance (800+ words) for AI to cite meaningfully? |
| **Schema Markup** | JSON-LD structured data (FAQ, Article, HowTo) for AI extraction? |
| **Passage-Level Citability** | Are individual paragraphs clear, self-contained, and citable? |
| **Entity Clarity** | Are people, orgs, and concepts clearly defined? Acronyms expanded? |
| **FAQ & Q&A Density** | Question-based headings and answer patterns AI systems prefer? |

## Built on Open-Source Giants

`geo-toolkit` doesn't reinvent the wheel. It composes best-in-class OSS libraries into a GEO-specific audit pipeline:

| Library | Role | Why |
|---------|------|-----|
| [**Scrapling**](https://github.com/D4Vinci/Scrapling) (33k+ stars) | Web fetching | Adaptive scraping with anti-bot bypass |
| [**Protego**](https://github.com/scrapy/protego) (Scrapy team) | robots.txt parsing | Battle-tested parser with modern conventions |
| [**Trafilatura**](https://github.com/adbar/trafilatura) (HuggingFace, IBM, Microsoft) | Content extraction | Best-in-class main content isolation |
| [**Extruct**](https://github.com/scrapinghub/extruct) (Scrapinghub) | Structured data | JSON-LD, microdata, RDFa, OpenGraph extraction |

The audit logic, scoring system, and GEO-specific checks are original — that's where `geo-toolkit` adds value.

## Quick Start

### Install

```bash
pip install geo-toolkit
```

Or install from source:

```bash
git clone https://github.com/infinitelabsdigital/geo-toolkit.git
cd geo-toolkit
pip install -e .
```

### CLI Usage

```bash
# Full GEO audit
geo-audit audit https://example.com

# Check AI crawler access only
geo-audit check-crawlers example.com

# Check llms.txt compliance
geo-audit check-llms-txt example.com

# Export as Markdown report
geo-audit audit https://example.com -f markdown -o report.md

# Export as JSON
geo-audit audit https://example.com -f json -o report.json
```

### Python API

```python
from geo_toolkit import GEOAuditor

auditor = GEOAuditor()
results = auditor.audit("https://example.com")

print(f"AI Citability Score: {results['score']}/100 (Grade: {results['grade']})")

for audit in results['audits']:
    status = "PASS" if audit['passed'] else "FAIL"
    print(f"  [{status}] {audit['name']}: {audit['description']}")
    if audit.get('recommendation'):
        print(f"         Fix: {audit['recommendation']}")
```

## Example Output

```
  geo-toolkit v0.1.0
  Generative Engine Optimization Auditor

  ✓ Audit complete!

  ╭───────────────────────────╮
  │  72/100  Grade: B         │
  │  AI Citability Score      │
  ╰───────────────────────────╯

  [PASS] AI Crawler Access
         All 10 AI crawlers have access to your content

  [FAIL] llms.txt Compliance
         No llms.txt file detected
         Fix: Create an llms.txt file at your domain root

  [PASS] Heading Hierarchy
         Clean heading structure with 8 headings (4 sections)

  [WARN] Schema Markup (Structured Data)
         1 AI-relevant schema type(s): Article
         Fix: Add FAQPage schema — #1 schema type for AI answer extraction

  [PASS] Passage-Level Citability
         5 highly citable passages (42% citability rate)

  [PASS] Entity Clarity
         Entities are clearly defined and attributed

  [WARN] FAQ & Q&A Density
         2 question(s) found — add more questions for better AI citability
         Fix: Add question-based headings that match how people ask AI assistants

  ─────────────────────────────────────
  4 passed  2 warnings  1 failed
```

## What is GEO?

**Generative Engine Optimization (GEO)** is the practice of optimizing content to be cited, referenced, and surfaced by AI-powered search engines. It's the next evolution beyond traditional SEO:

- **SEO** = Getting ranked in search results
- **GEO** = Getting cited by AI systems

Key GEO factors include passage-level citability (can AI extract a clean answer from your content?), structured data (does your schema help AI understand your content?), and crawler access (can AI systems even reach your pages?).

## Project Structure

```
geo-toolkit/
├── geo_toolkit/
│   ├── __init__.py          # Package entry point
│   ├── auditor.py           # Main orchestrator
│   ├── cli.py               # Click-based CLI
│   ├── auditors/
│   │   ├── crawler_access.py    # AI crawler robots.txt check
│   │   ├── llms_txt.py         # llms.txt compliance
│   │   ├── content_structure.py # Headings, meta, depth
│   │   ├── schema_markup.py     # JSON-LD / structured data
│   │   ├── passage_citability.py # Passage scoring
│   │   ├── entity_clarity.py    # Entity & acronym checks
│   │   └── faq_density.py       # Q&A pattern detection
│   ├── scorers/
│   │   └── geo_scorer.py       # Weighted score calculation
│   └── reporters/
│       ├── markdown.py          # Markdown report generation
│       └── json_report.py       # JSON report generation
├── tests/
│   └── test_auditors.py        # 10 unit tests
├── pyproject.toml
├── LICENSE
└── README.md
```

## Contributing

Contributions welcome! This is a new space and there's a lot to build.

**Areas where help is needed:**

- **New auditors** — Internal linking analysis, readability scoring, image alt-text for AI
- **Benchmarking** — Correlating GEO scores with actual AI citation frequency
- **Platform integrations** — WordPress plugin, GitHub Action, CI/CD integration
- **Documentation** — Guides on GEO best practices

If you work in SEO, content marketing, or AI search — your domain knowledge is as valuable as code. Open an issue to discuss.

## Roadmap

- [ ] Batch URL auditing (crawl entire site)
- [ ] Historical score tracking
- [ ] WordPress / CMS plugin
- [ ] GitHub Action for CI/CD
- [ ] Competitive GEO benchmarking (compare vs. competitors)
- [ ] AI citation correlation research
- [ ] Browser extension for on-page analysis
- [ ] API server mode

## Maintainer

Built and maintained by [Infinite Labs Digital](https://infinitelabsdigital.com) — a digital marketing agency specializing in AI-powered search visibility, SEO, and content optimization.

## License

MIT © Infinite Labs Digital
