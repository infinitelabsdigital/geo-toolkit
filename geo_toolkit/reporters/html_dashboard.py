"""Generate an interactive HTML dashboard report from GEO audit results.

Produces a single self-contained HTML file with:
- Ahrefs-inspired metric cards for AI citation readiness
- Animated score ring with letter grade
- Individual audit cards with progress bars and recommendations
- AI crawler access matrix
- Responsive layout that works on desktop and mobile
"""

import json
from datetime import datetime


def generate_html_dashboard(results, output_path=None):
    """Generate a self-contained HTML dashboard from audit results.

    Args:
        results: Dict from GEOAuditor.audit()
        output_path: Optional file path to write the HTML to.

    Returns:
        HTML string
    """
    url = results["url"]
    score = results["score"]
    grade = results.get("grade", _grade(score))
    timestamp = results.get("timestamp", datetime.utcnow().isoformat())
    audits = results["audits"]

    passed = sum(1 for a in audits if a.get("passed"))
    warned = sum(1 for a in audits if a.get("warning"))
    failed = sum(1 for a in audits if not a.get("passed") and not a.get("warning"))

    # Extract specific data for hero cards
    crawler_audit = _find_audit(audits, "AI Crawler Access")
    llms_audit = _find_audit(audits, "llms.txt")
    schema_audit = _find_audit(audits, "Schema Markup")
    passage_audit = _find_audit(audits, "Passage")
    faq_audit = _find_audit(audits, "FAQ")

    crawlers_allowed = 0
    crawlers_total = 10
    if crawler_audit and "crawlers" in crawler_audit:
        crawlers_allowed = sum(1 for c in crawler_audit["crawlers"] if c.get("allowed"))
        crawlers_total = len(crawler_audit["crawlers"])

    # Build crawler rows HTML
    crawler_rows = ""
    if crawler_audit and "crawlers" in crawler_audit:
        for c in crawler_audit["crawlers"]:
            status_class = "allowed" if c["allowed"] else "blocked"
            status_text = "Allowed" if c["allowed"] else "Blocked"
            crawler_rows += f"""
            <tr>
                <td>{c["name"]}</td>
                <td class="mono">{c["user_agent"]}</td>
                <td><span class="crawler-status {status_class}">{status_text}</span></td>
            </tr>"""

    # Build audit card HTML
    audit_cards = ""
    for a in audits:
        s = a.get("score", 0)
        status = "pass" if a.get("passed") else "warn" if a.get("warning") else "fail"
        status_label = "PASS" if a.get("passed") else "WARN" if a.get("warning") else "FAIL"
        bar_class = "high" if s >= 70 else "mid" if s >= 40 else "low"

        details_html = ""
        if a.get("details"):
            items = "".join(f"<li>{d}</li>" for d in a["details"])
            details_html = f'<details class="card-details"><summary>View details</summary><ul>{items}</ul></details>'

        rec_html = ""
        if a.get("recommendation"):
            rec_html = f'<div class="recommendation">{a["recommendation"]}</div>'

        audit_cards += f"""
        <div class="audit-card">
            <div class="card-top">
                <h3>{a["name"]}</h3>
                <span class="badge {status}">{status_label}</span>
            </div>
            <p class="card-desc">{a.get("description", "")}</p>
            <div class="score-row"><span class="score-num">{s}/100</span></div>
            <div class="bar"><div class="bar-fill {bar_class}" style="width:{max(2, s)}%"></div></div>
            {rec_html}
            {details_html}
        </div>"""

    # Score ring offset (circumference = 2*pi*80 ≈ 502.65)
    circumference = 502.65
    offset = circumference - (score / 100) * circumference

    # Grade color
    gc = "#22c55e" if score >= 80 else "#3b82f6" if score >= 70 else "#eab308" if score >= 50 else "#ef4444"

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>GEO Audit — {url}</title>
<style>
:root {{
    --bg: #0f1117; --surface: #1a1d2e; --surface2: #232738; --border: #2a2e42;
    --text: #e2e8f0; --muted: #8892a8; --dim: #5a6478;
    --blue: #5b8def; --purple: #8b5cf6; --green: #34d399; --amber: #f59e0b;
    --red: #ef4444; --cyan: #22d3ee;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); min-height:100vh; }}
.wrap {{ max-width:1200px; margin:0 auto; padding:24px 20px; }}

/* Top bar */
.topbar {{ display:flex; justify-content:space-between; align-items:center; padding:16px 0 24px; border-bottom:1px solid var(--border); margin-bottom:24px; flex-wrap:wrap; gap:12px; }}
.topbar h1 {{ font-size:22px; font-weight:700; }}
.topbar h1 em {{ font-style:normal; color:var(--blue); }}
.topbar .url-tag {{ display:inline-flex; align-items:center; gap:6px; background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:6px 14px; font-size:13px; color:var(--muted); }}
.topbar .url-tag .dot {{ width:8px; height:8px; border-radius:50%; background:var(--green); }}
.topbar .ts {{ font-size:12px; color:var(--dim); }}

/* Hero metric cards (Ahrefs-style) */
.hero {{ display:grid; grid-template-columns: 240px 1fr 1fr; gap:20px; margin-bottom:24px; }}
@media(max-width:900px) {{ .hero {{ grid-template-columns:1fr; }} }}

.score-card {{ background: linear-gradient(135deg, #1e1b4b, #312e81); border-radius:16px; padding:32px 24px; text-align:center; position:relative; }}
.ring {{ width:160px; height:160px; margin:0 auto 12px; position:relative; }}
.ring svg {{ transform:rotate(-90deg); }}
.ring .inner {{ position:absolute; top:50%; left:50%; transform:translate(-50%,-50%); text-align:center; }}
.ring .big {{ font-size:44px; font-weight:800; color:#fff; display:block; line-height:1; }}
.ring .sub {{ font-size:13px; color:var(--muted); }}
.grade {{ display:inline-block; background:{gc}; color:#fff; font-weight:700; font-size:15px; padding:4px 16px; border-radius:20px; margin-top:4px; }}
.pills {{ display:flex; justify-content:center; gap:10px; margin-top:14px; }}
.pill {{ font-size:12px; font-weight:600; padding:4px 12px; border-radius:16px; }}
.pill.p {{ background:rgba(52,211,153,.12); color:var(--green); border:1px solid rgba(52,211,153,.25); }}
.pill.w {{ background:rgba(245,158,11,.12); color:var(--amber); border:1px solid rgba(245,158,11,.25); }}
.pill.f {{ background:rgba(239,68,68,.12); color:var(--red); border:1px solid rgba(239,68,68,.25); }}

/* AI Visibility cards */
.ai-cards {{ display:grid; grid-template-columns:1fr 1fr; grid-template-rows:1fr 1fr; gap:12px; }}
.ai-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px 20px; }}
.ai-card .label {{ font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--dim); margin-bottom:6px; }}
.ai-card .val {{ font-size:28px; font-weight:700; color:#fff; }}
.ai-card .val .unit {{ font-size:14px; color:var(--muted); font-weight:400; }}
.ai-card .tag {{ display:inline-block; font-size:11px; padding:2px 8px; border-radius:10px; margin-top:6px; }}
.ai-card .tag.ok {{ background:rgba(52,211,153,.12); color:var(--green); }}
.ai-card .tag.bad {{ background:rgba(239,68,68,.12); color:var(--red); }}
.ai-card .tag.warn {{ background:rgba(245,158,11,.12); color:var(--amber); }}

/* Search metrics panel */
.search-panel {{ display:grid; grid-template-columns:1fr 1fr; grid-template-rows:1fr 1fr; gap:12px; }}
.s-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:16px 20px; }}
.s-card .label {{ font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--dim); margin-bottom:6px; }}
.s-card .val {{ font-size:26px; font-weight:700; color:#fff; }}

/* Audit grid */
.section-title {{ font-size:16px; font-weight:600; color:var(--text); margin:28px 0 14px; padding-left:2px; }}
.audit-grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(340px, 1fr)); gap:14px; margin-bottom:24px; }}
.audit-card {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; padding:20px; transition:border-color .15s; }}
.audit-card:hover {{ border-color:#3d4260; }}
.card-top {{ display:flex; justify-content:space-between; align-items:start; margin-bottom:8px; }}
.card-top h3 {{ font-size:14px; font-weight:600; }}
.badge {{ font-size:11px; font-weight:700; padding:2px 10px; border-radius:6px; text-transform:uppercase; letter-spacing:.5px; }}
.badge.pass {{ background:rgba(52,211,153,.12); color:var(--green); }}
.badge.warn {{ background:rgba(245,158,11,.12); color:var(--amber); }}
.badge.fail {{ background:rgba(239,68,68,.12); color:var(--red); }}
.card-desc {{ font-size:13px; color:var(--muted); line-height:1.5; margin-bottom:10px; }}
.score-row {{ text-align:right; margin-bottom:4px; }}
.score-num {{ font-size:12px; color:var(--dim); }}
.bar {{ height:5px; background:var(--surface2); border-radius:3px; overflow:hidden; }}
.bar-fill {{ height:100%; border-radius:3px; transition:width 1.2s ease; }}
.bar-fill.high {{ background:linear-gradient(90deg,#22c55e,#34d399); }}
.bar-fill.mid {{ background:linear-gradient(90deg,#eab308,#facc15); }}
.bar-fill.low {{ background:linear-gradient(90deg,#ef4444,#f87171); }}
.recommendation {{ font-size:12px; color:#a78bfa; background:rgba(139,92,246,.06); padding:10px 12px; border-radius:8px; border-left:3px solid #7c3aed; margin-top:12px; line-height:1.5; }}
.card-details {{ margin-top:10px; }}
.card-details summary {{ font-size:12px; color:var(--blue); cursor:pointer; }}
.card-details ul {{ list-style:none; padding:8px 0 0; }}
.card-details li {{ font-size:12px; color:var(--dim); padding:2px 0 2px 14px; position:relative; }}
.card-details li::before {{ content:"›"; position:absolute; left:0; color:var(--dim); }}

/* Crawler table */
.crawler-wrap {{ background:var(--surface); border:1px solid var(--border); border-radius:12px; overflow:hidden; margin-bottom:24px; }}
.crawler-wrap table {{ width:100%; border-collapse:collapse; }}
.crawler-wrap th {{ text-align:left; font-size:11px; text-transform:uppercase; letter-spacing:.8px; color:var(--dim); padding:12px 16px; border-bottom:1px solid var(--border); }}
.crawler-wrap td {{ padding:10px 16px; font-size:13px; border-bottom:1px solid rgba(42,46,66,.4); }}
.crawler-wrap tr:last-child td {{ border-bottom:none; }}
.mono {{ font-family:ui-monospace, 'SFMono-Regular', Consolas, monospace; font-size:12px; color:var(--muted); }}
.crawler-status {{ font-size:11px; font-weight:600; padding:2px 10px; border-radius:10px; }}
.crawler-status.allowed {{ background:rgba(52,211,153,.12); color:var(--green); }}
.crawler-status.blocked {{ background:rgba(239,68,68,.12); color:var(--red); }}

/* Footer */
.foot {{ text-align:center; font-size:12px; color:var(--dim); padding:20px 0; border-top:1px solid var(--border); margin-top:12px; }}
.foot a {{ color:var(--blue); text-decoration:none; }}
</style>
</head>
<body>
<div class="wrap">

<!-- Top bar -->
<div class="topbar">
    <div>
        <h1><em>geo</em>-toolkit</h1>
    </div>
    <div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap">
        <span class="url-tag"><span class="dot"></span>{url}</span>
        <span class="ts">{timestamp[:10]}</span>
    </div>
</div>

<!-- Hero -->
<div class="hero">
    <!-- Score ring -->
    <div class="score-card">
        <div class="ring">
            <svg width="160" height="160" viewBox="0 0 180 180">
                <circle cx="90" cy="90" r="80" fill="none" stroke="rgba(255,255,255,.08)" stroke-width="10"/>
                <circle cx="90" cy="90" r="80" fill="none" stroke="{gc}" stroke-width="10"
                        stroke-linecap="round" stroke-dasharray="{circumference}" stroke-dashoffset="{offset}"/>
            </svg>
            <div class="inner">
                <span class="big">{score}</span>
                <span class="sub">/ 100</span>
            </div>
        </div>
        <div class="grade">Grade {grade}</div>
        <div class="pills">
            <span class="pill p">{passed} pass</span>
            <span class="pill w">{warned} warn</span>
            <span class="pill f">{failed} fail</span>
        </div>
    </div>

    <!-- AI Visibility cards -->
    <div class="ai-cards">
        <div class="ai-card">
            <div class="label">AI Crawlers</div>
            <div class="val">{crawlers_allowed}<span class="unit"> / {crawlers_total}</span></div>
            <span class="tag {"ok" if crawlers_allowed == crawlers_total else "bad"}">{"All allowed" if crawlers_allowed == crawlers_total else f"{crawlers_total - crawlers_allowed} blocked"}</span>
        </div>
        <div class="ai-card">
            <div class="label">llms.txt</div>
            <div class="val">{"Found" if llms_audit and llms_audit.get("passed") else "Missing"}</div>
            <span class="tag {"ok" if llms_audit and llms_audit.get("passed") else "bad"}">{"Compliant" if llms_audit and llms_audit.get("passed") else "Not found"}</span>
        </div>
        <div class="ai-card">
            <div class="label">Schema Types</div>
            <div class="val">{schema_audit.get("score", 0) if schema_audit else 0}<span class="unit"> / 100</span></div>
            <span class="tag {"ok" if schema_audit and schema_audit.get("passed") else "warn"}">{"AI-ready" if schema_audit and schema_audit.get("passed") else "Needs work"}</span>
        </div>
        <div class="ai-card">
            <div class="label">Citable Passages</div>
            <div class="val">{passage_audit.get("score", 0) if passage_audit else 0}<span class="unit"> / 100</span></div>
            <span class="tag {"ok" if passage_audit and passage_audit.get("passed") else "bad" if passage_audit and not passage_audit.get("warning") else "warn"}">{"Strong" if passage_audit and passage_audit.get("passed") else "Weak"}</span>
        </div>
    </div>

    <!-- Search readiness -->
    <div class="search-panel">
        <div class="s-card">
            <div class="label">Content Depth</div>
            <div class="val">{_find_audit_score(audits, "Content Depth")}<span class="unit"> / 100</span></div>
        </div>
        <div class="s-card">
            <div class="label">FAQ Density</div>
            <div class="val">{faq_audit.get("score", 0) if faq_audit else 0}<span class="unit"> / 100</span></div>
        </div>
        <div class="s-card">
            <div class="label">Entity Clarity</div>
            <div class="val">{_find_audit_score(audits, "Entity")}<span class="unit"> / 100</span></div>
        </div>
        <div class="s-card">
            <div class="label">Meta Signals</div>
            <div class="val">{_find_audit_score(audits, "Meta Tags")}<span class="unit"> / 100</span></div>
        </div>
    </div>
</div>

<!-- Crawler Matrix -->
<div class="section-title">AI Crawler Access Matrix</div>
<div class="crawler-wrap">
    <table>
        <thead><tr><th>AI Platform</th><th>User-Agent</th><th>Status</th></tr></thead>
        <tbody>{crawler_rows}</tbody>
    </table>
</div>

<!-- Detailed Audits -->
<div class="section-title">Detailed Audit Results</div>
<div class="audit-grid">
{audit_cards}
</div>

<div class="foot">
    Generated by <a href="https://github.com/infinitelabsdigital/geo-toolkit">geo-toolkit</a> v0.1.0
    &mdash; Open-source Generative Engine Optimization Auditor
    &mdash; Built by <a href="https://infinitelabsdigital.com">Infinite Labs Digital</a>
</div>

</div>
</body>
</html>"""

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)

    return html


def _grade(score):
    if score >= 90: return "A+"
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 40: return "D"
    return "F"


def _find_audit(audits, name_contains):
    for a in audits:
        if name_contains.lower() in a.get("name", "").lower():
            return a
    return None


def _find_audit_score(audits, name_contains):
    a = _find_audit(audits, name_contains)
    return a.get("score", 0) if a else 0
