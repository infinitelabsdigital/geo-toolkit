"""Audit AI crawler access via robots.txt analysis.

Uses Protego (by the Scrapy team) for robust robots.txt parsing,
with stdlib fallback if not available.
"""

import urllib.request
import urllib.error
from urllib.parse import urlparse

AI_CRAWLERS = [
    {"name": "OpenAI / ChatGPT", "user_agent": "GPTBot"},
    {"name": "OpenAI (ChatGPT User)", "user_agent": "ChatGPT-User"},
    {"name": "Anthropic / Claude", "user_agent": "ClaudeBot"},
    {"name": "Anthropic (Claude Web)", "user_agent": "anthropic-ai"},
    {"name": "Perplexity AI", "user_agent": "PerplexityBot"},
    {"name": "Google AI (Extended)", "user_agent": "Google-Extended"},
    {"name": "Meta AI", "user_agent": "FacebookBot"},
    {"name": "Apple Intelligence", "user_agent": "Applebot-Extended"},
    {"name": "Cohere", "user_agent": "cohere-ai"},
    {"name": "Common Crawl", "user_agent": "CCBot"},
]


class CrawlerAccessAuditor:
    """Check if AI crawlers are blocked in robots.txt.

    Leverages Protego for accurate robots.txt parsing with support for
    modern conventions (crawl-delay, sitemaps, wildcards).
    """

    def audit(self, url, context=None):
        parsed = urlparse(url if url.startswith("http") else f"https://{url}")
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

        robots_txt = ""
        has_robots = False

        try:
            req = urllib.request.Request(robots_url, headers={"User-Agent": "geo-toolkit/0.1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                if resp.status == 200:
                    robots_txt = resp.read().decode("utf-8", errors="replace")
                    has_robots = True
        except Exception:
            pass

        # Use Protego for parsing if available
        parser = self._get_parser(robots_txt, robots_url) if has_robots else None

        crawlers = []
        for c in AI_CRAWLERS:
            if parser:
                allowed = self._check_with_protego(parser, c["user_agent"], url)
            elif has_robots:
                allowed = self._check_manual(robots_txt, c["user_agent"])
            else:
                allowed = True
            crawlers.append({**c, "allowed": allowed})

        blocked = [c for c in crawlers if not c["allowed"]]
        allowed_list = [c for c in crawlers if c["allowed"]]
        total = len(crawlers)

        details = []
        if blocked:
            details.append(f"Blocked: {', '.join(c['name'] for c in blocked)}")
        if allowed_list:
            details.append(f"Allowed: {', '.join(c['name'] for c in allowed_list)}")

        recommendation = None
        if blocked:
            recommendation = (
                f"Unblock AI crawlers in robots.txt to improve AI search visibility. "
                f"Currently blocking: {', '.join(c['user_agent'] for c in blocked)}"
            )

        score = round((len(allowed_list) / total) * 100) if total > 0 else 0

        return {
            "name": "AI Crawler Access",
            "passed": len(blocked) == 0,
            "warning": 0 < len(blocked) < total,
            "description": (
                f"All {total} AI crawlers have access to your content"
                if not blocked
                else f"{len(blocked)} of {total} AI crawlers are blocked in robots.txt"
            ),
            "details": details,
            "recommendation": recommendation,
            "score": score,
            "weight": 3,
            "crawlers": crawlers,
            "has_robots_txt": has_robots,
            "robots_txt_url": robots_url,
        }

    def _get_parser(self, robots_txt, robots_url):
        """Try to use Protego for parsing, return None if unavailable."""
        try:
            from protego import Protego
            return Protego.parse(robots_txt)
        except ImportError:
            return None

    def _check_with_protego(self, parser, user_agent, url):
        """Check crawler access using Protego parser."""
        return parser.can_fetch(url, user_agent)

    def _check_manual(self, robots_txt, user_agent):
        """Fallback manual robots.txt parsing."""
        lines = robots_txt.lower().split("\n")
        in_matching = False
        in_wildcard = False
        specific_disallow = False
        wildcard_disallow = False

        for line in lines:
            line = line.strip()
            if line.startswith("#"):
                continue
            if line.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                in_matching = agent == user_agent.lower()
                in_wildcard = agent == "*"
            elif line.startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path in ("/", "/*"):
                    if in_matching:
                        specific_disallow = True
                    if in_wildcard:
                        wildcard_disallow = True

        if specific_disallow:
            return False
        if wildcard_disallow:
            return False
        return True
