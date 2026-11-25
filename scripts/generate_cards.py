#!/usr/bin/env python3
"""
ORVANTE Monochrome Editorial GitHub Profile SVG Generator
Generates animated, font-embedded SVGs powered by live GitHub GraphQL/REST telemetry.
Zero external dependencies (Python 3 stdlib only).
"""

import base64
import html
import json
import os
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FONTS_DIR = ROOT / "fonts"
CARDS_DIR = ROOT / "cards"
USERNAME = os.environ.get("GITHUB_USER", "Legxcy77")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")


def load_fonts_css() -> str:
    """Base64-encode local WOFF2 fonts into @font-face CSS rules for GitHub CSP compatibility."""
    font_specs = [
        ("Instrument Serif", "normal", "400", "instrument-serif-400-normal.woff2"),
        ("Instrument Serif", "italic", "400", "instrument-serif-400-italic.woff2"),
        ("JetBrains Mono", "normal", "400", "jetbrains-mono-400-normal.woff2"),
        ("JetBrains Mono", "normal", "700", "jetbrains-mono-700-normal.woff2"),
        ("Plus Jakarta Sans", "normal", "700", "plus-jakarta-sans-700-normal.woff2"),
        ("Plus Jakarta Sans", "normal", "800", "plus-jakarta-sans-800-normal.woff2"),
    ]
    rules = []
    for family, style, weight, filename in font_specs:
        path = FONTS_DIR / filename
        if path.exists():
            b64 = base64.b64encode(path.read_bytes()).decode("ascii")
            rules.append(
                f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
                f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}"
            )
    return "".join(rules)


def fetch_github_telemetry() -> dict:
    """Fetch real GitHub stats, languages, and monthly contribution velocity via GraphQL."""
    fallback = {
        "total_contributions": 201,
        "total_commits": 186,
        "total_prs": 8,
        "repo_count": 12,
        "languages": [
            ("TypeScript", 64.2, "#e5e5e5"),
            ("C#", 17.8, "#f59e0b"),
            ("Swift", 10.4, "#10b981"),
            ("HTML", 7.6, "#737373"),
        ],
        "monthly": [
            ("Feb", 12), ("Mar", 18), ("Apr", 25), ("May", 14),
            ("Jun", 20), ("Jul", 9), ("Aug", 16), ("Sep", 24),
            ("Oct", 29), ("Nov", 34),
        ],
        "weeks": [],
    }

    if not GITHUB_TOKEN:
        return fallback

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
          totalPullRequestContributions
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                contributionCount
                date
              }
            }
          }
        }
        repositories(first: 40, privacy: PUBLIC, isFork: false, orderBy: {field: PUSHED_AT, direction: DESC}) {
          totalCount
          nodes {
            languages(first: 6, orderBy: {field: SIZE, direction: DESC}) {
              edges {
                size
                node {
                  name
                }
              }
            }
          }
        }
      }
    }
    """
    payload = json.dumps({"query": query, "variables": {"login": USERNAME}}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={
            "Authorization": f"Bearer {GITHUB_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "Legxcy77-Profile-Builder",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        user = data["data"]["user"]
        cal = user["contributionsCollection"]["contributionCalendar"]
        total_contributions = cal["totalContributions"]
        total_commits = user["contributionsCollection"]["totalCommitContributions"]
        total_prs = user["contributionsCollection"]["totalPullRequestContributions"]
        repo_count = user["repositories"]["totalCount"]

        # Aggregate monthly contributions (last 10 months)
        month_totals = {}
        for week in cal["weeks"]:
            for day in week["contributionDays"]:
                ym = day["date"][:7]  # YYYY-MM
                month_totals[ym] = month_totals.get(ym, 0) + day["contributionCount"]
        sorted_months = sorted(month_totals.items())[-10:]
        monthly = []
        for ym, count in sorted_months:
            label = datetime.strptime(ym, "%Y-%m").strftime("%b")
            monthly.append((label, count))

        # Aggregate language bytes
        lang_bytes = {}
        for repo in user["repositories"]["nodes"]:
            for edge in repo["languages"]["edges"]:
                name = edge["node"]["name"]
                if name in ("CSS", "SCSS", "Less"):
                    continue
                lang_bytes[name] = lang_bytes.get(name, 0) + edge["size"]

        total_bytes = sum(lang_bytes.values()) or 1
        palette = ["#f5f5f5", "#10b981", "#f59e0b", "#60a5fa", "#737373"]
        top_langs = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:4]
        languages = [
            (name, round((size / total_bytes) * 100, 1), palette[i % len(palette)])
            for i, (name, size) in enumerate(top_langs)
        ]
        if not languages:
            languages = fallback["languages"]

        return {
            "total_contributions": total_contributions,
            "total_commits": total_commits,
            "total_prs": total_prs,
            "repo_count": repo_count,
            "languages": languages,
            "monthly": monthly or fallback["monthly"],
            "weeks": cal["weeks"],
        }
    except (urllib.error.URLError, KeyError, ValueError, TypeError):
        return fallback


BASE_CSS = """
@keyframes pulseDot{0%,100%{opacity:1;transform:scale(1)}50%{opacity:.35;transform:scale(.85)}}
@keyframes blinkCursor{0%,49%{opacity:1}50%,100%{opacity:0}}
@keyframes fadeUp{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:none}}
@keyframes growX{from{transform:scaleX(0)}to{transform:scaleX(1)}}
@keyframes growY{from{transform:scaleY(0)}to{transform:scaleY(1)}}
@keyframes pop{0%{opacity:0;transform:scale(.3)}70%{opacity:1;transform:scale(1.12)}100%{opacity:1;transform:none}}
@keyframes sheen{0%{transform:translateX(-340px) skewX(-20deg)}28%,100%{transform:translateX(520px) skewX(-20deg)}}
.pulse{transform-box:fill-box;transform-origin:center;animation:pulseDot 2s ease-in-out infinite}
.blink{animation:blinkCursor 1.1s steps(1) infinite}
.fade{opacity:0;animation:fadeUp .7s cubic-bezier(.2,.7,.2,1) both}
.gx{transform-box:fill-box;transform-origin:left;animation:growX .9s cubic-bezier(.2,.8,.2,1) both}
.gy{transform-box:fill-box;transform-origin:bottom;animation:growY .8s cubic-bezier(.2,.8,.2,1) both}
.p{opacity:0;transform-box:fill-box;transform-origin:center;animation:pop .38s ease-out both}
.sheen{animation:sheen 6s ease-in-out infinite}
@media (prefers-reduced-motion:reduce){
  .pulse,.blink,.fade,.gx,.gy,.p,.sheen{animation:none!important;opacity:1!important;transform:none!important}
}
"""


def render_hero(fonts_css: str) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="880" height="248" viewBox="0 0 880 248" role="img" aria-label="Pawalit Legxcy77 Hero Banner">
  <defs>
    <pattern id="grid" width="24" height="24" patternUnits="userSpaceOnUse">
      <path d="M 24 0 L 0 0 0 24" fill="none" stroke="#ffffff" stroke-opacity="0.03" stroke-width="1"/>
    </pattern>
    <radialGradient id="glow" cx="25%" cy="20%" r="70%">
      <stop offset="0%" stop-color="#10b981" stop-opacity="0.10"/>
      <stop offset="100%" stop-color="#0a0a0a" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="cardClip"><rect width="880" height="248" rx="16"/></clipPath>
  </defs>
  <style>{fonts_css}{BASE_CSS}</style>
  <g clip-path="url(#cardClip)">
    <rect width="880" height="248" rx="16" fill="#0a0a0a"/>
    <rect width="880" height="248" fill="url(#grid)"/>
    <rect width="880" height="248" fill="url(#glow)"/>
    <rect x="0.5" y="0.5" width="879" height="247" rx="15.5" fill="none" stroke="#262626"/>

    <!-- Left Editorial Content -->
    <g class="fade" style="animation-delay:0.05s">
      <rect x="32" y="28" width="176" height="24" rx="12" fill="#10b981" fill-opacity="0.10" stroke="#10b981" stroke-opacity="0.35"/>
      <circle class="pulse" cx="46" cy="40" r="3.5" fill="#10b981"/>
      <text x="56" y="44" font-family="'JetBrains Mono', monospace" font-size="10.5" font-weight="600" letter-spacing="0.8" fill="#34d399">AVAILABLE FOR 2026</text>
    </g>

    <g class="fade" style="animation-delay:0.15s">
      <text x="32" y="102" font-family="'Plus Jakarta Sans', sans-serif" font-size="42" font-weight="800" letter-spacing="-1.5" fill="#fafafa">PAWALIT</text>
      <text x="228" y="102" font-family="'Instrument Serif', Georgia, serif" font-style="italic" font-size="42" fill="#a3a3a3">/ Legxcy77</text>
    </g>

    <g class="fade" style="animation-delay:0.25s">
      <text x="32" y="136" font-family="'JetBrains Mono', monospace" font-size="12.5" fill="#a3a3a3">Full-Stack Engineer &amp; Systems Architect · Bangkok, TH</text>
      <text x="32" y="158" font-family="'JetBrains Mono', monospace" font-size="11.5" fill="#737373">Crafting hyper-fluid interfaces &amp; resilient cloud backends.</text>
    </g>

    <!-- Stack Pills -->
    <g class="fade" style="animation-delay:0.35s" font-family="'JetBrains Mono', monospace" font-size="10.5" fill="#d4d4d4">
      <rect x="32" y="186" width="84" height="26" rx="13" fill="#141414" stroke="#2a2a2a"/>
      <text x="74" y="203" text-anchor="middle">Next.js 15</text>

      <rect x="124" y="186" width="110" height="26" rx="13" fill="#141414" stroke="#2a2a2a"/>
      <text x="179" y="203" text-anchor="middle">ASP.NET Core 10</text>

      <rect x="242" y="186" width="88" height="26" rx="13" fill="#141414" stroke="#2a2a2a"/>
      <text x="286" y="203" text-anchor="middle">Cloudflare</text>

      <rect x="338" y="186" width="66" height="26" rx="13" fill="#141414" stroke="#2a2a2a"/>
      <text x="371" y="203" text-anchor="middle">Docker</text>

      <rect x="412" y="186" width="76" height="26" rx="13" fill="#141414" stroke="#2a2a2a"/>
      <text x="450" y="203" text-anchor="middle">Postgres</text>
    </g>

    <!-- Right Terminal Window -->
    <g class="fade" style="animation-delay:0.2s">
      <rect x="524" y="28" width="324" height="192" rx="12" fill="#111113" stroke="#27272a"/>
      <line x1="524" y1="56" x2="848" y2="56" stroke="#27272a"/>
      <circle cx="542" cy="42" r="4" fill="#ef4444" fill-opacity="0.8"/>
      <circle cx="556" cy="42" r="4" fill="#f59e0b" fill-opacity="0.8"/>
      <circle cx="570" cy="42" r="4" fill="#10b981" fill-opacity="0.8"/>
      <text x="686" y="45" text-anchor="middle" font-family="'JetBrains Mono', monospace" font-size="10" fill="#71717a">zsh — legxcy77@prod</text>

      <g font-family="'JetBrains Mono', monospace" font-size="11.5">
        <text x="542" y="82" fill="#10b981">$</text>
        <text x="556" y="82" fill="#e4e4e7">whoami</text>
        <text x="542" y="100" fill="#a1a1aa">&gt; fullstack_systems_architect</text>

        <text x="542" y="126" fill="#10b981">$</text>
        <text x="556" y="126" fill="#e4e4e7">cat stack.json</text>
        <text x="542" y="144" fill="#a1a1aa">&gt; ["TS", "C#", "Swift", "SQL"]</text>

        <text x="542" y="170" fill="#10b981">$</text>
        <text x="556" y="170" fill="#e4e4e7">deploy --status</text>
        <text x="542" y="188" fill="#34d399">&gt; 3 live cloud apps online</text>

        <text x="542" y="208" fill="#10b981">$</text>
        <rect class="blink" x="556" y="198" width="7" height="12" fill="#fafafa"/>
      </g>
    </g>
  </g>
</svg>"""


def render_project_card(
    fonts_css: str,
    title: str,
    subtitle: str,
    badge: str,
    accent: str,
    line1: str,
    line2: str,
    tags: list[str],
    delay: str,
) -> str:
    tag_svg = []
    x = 22
    for t in tags[:3]:
        w = len(t) * 6.8 + 18
        tag_svg.append(
            f'<rect x="{x}" y="170" width="{w:.1f}" height="22" rx="11" fill="#171717" stroke="#2a2a2a"/>'
            f'<text x="{x + w / 2:.1f}" y="184.5" text-anchor="middle" font-family="\'JetBrains Mono\', monospace" font-size="9.5" fill="#d4d4d4">{html.escape(t)}</text>'
        )
        x += w + 6

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="286" height="214" viewBox="0 0 286 214" role="img" aria-label="{html.escape(title)}">
  <defs>
    <clipPath id="pClip"><rect width="286" height="214" rx="16"/></clipPath>
    <linearGradient id="sheenGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0"/>
      <stop offset="50%" stop-color="#ffffff" stop-opacity="0.06"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </linearGradient>
  </defs>
  <style>{fonts_css}{BASE_CSS}</style>
  <g clip-path="url(#pClip)">
    <rect width="286" height="214" rx="16" fill="#0c0c0d"/>
    <rect x="0.5" y="0.5" width="285" height="213" rx="15.5" fill="none" stroke="{accent}" stroke-opacity="0.35"/>
    <rect class="sheen" x="-80" y="0" width="90" height="214" fill="url(#sheenGrad)"/>

    <g class="fade" style="animation-delay:{delay}">
      <rect x="22" y="22" width="{len(badge) * 6.5 + 24:.0f}" height="22" rx="11" fill="{accent}" fill-opacity="0.12" stroke="{accent}" stroke-opacity="0.4"/>
      <circle class="pulse" cx="34" cy="33" r="3" fill="{accent}"/>
      <text x="43" y="36.5" font-family="'JetBrains Mono', monospace" font-size="9.5" font-weight="700" letter-spacing="0.6" fill="{accent}">{html.escape(badge)}</text>

      <text x="264" y="37" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="14" fill="#737373">↗</text>

      <text x="22" y="80" font-family="'Plus Jakarta Sans', sans-serif" font-size="22" font-weight="800" letter-spacing="-0.5" fill="#fafafa">{html.escape(title)}</text>
      <text x="22" y="100" font-family="'JetBrains Mono', monospace" font-size="10.5" fill="#737373">{html.escape(subtitle)}</text>

      <text x="22" y="130" font-family="'JetBrains Mono', monospace" font-size="11" fill="#b5b5b5">{html.escape(line1)}</text>
      <text x="22" y="148" font-family="'JetBrains Mono', monospace" font-size="11" fill="#b5b5b5">{html.escape(line2)}</text>

      {''.join(tag_svg)}
    </g>
  </g>
</svg>"""


def render_languages(fonts_css: str, telemetry: dict) -> str:
    langs = telemetry["languages"]
    bar_width = 368
    segments = []
    cur_x = 32.0
    for name, pct, color in langs:
        w = max(8.0, (pct / 100.0) * bar_width)
        segments.append(f'<rect x="{cur_x:.1f}" y="94" width="{w:.1f}" height="12" fill="{color}"/>')
        cur_x += w

    legend = []
    positions = [(32, 136), (220, 136), (32, 162), (220, 162)]
    for i, (name, pct, color) in enumerate(langs[:4]):
        lx, ly = positions[i]
        legend.append(
            f'<circle cx="{lx + 5}" cy="{ly - 4}" r="4.5" fill="{color}"/>'
            f'<text x="{lx + 16}" y="{ly}" font-family="\'JetBrains Mono\', monospace" font-size="11.5" fill="#e5e5e5">{html.escape(name)}</text>'
            f'<text x="{lx + 158}" y="{ly}" text-anchor="end" font-family="\'JetBrains Mono\', monospace" font-size="11.5" fill="#737373">{pct}%</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="432" height="196" viewBox="0 0 432 196" role="img" aria-label="Language DNA">
  <defs>
    <clipPath id="barClip"><rect x="32" y="94" width="368" height="12" rx="6"/></clipPath>
  </defs>
  <style>{fonts_css}{BASE_CSS}</style>
  <rect width="432" height="196" rx="16" fill="#0a0a0a"/>
  <rect x="0.5" y="0.5" width="431" height="195" rx="15.5" fill="none" stroke="#262626"/>

  <text x="32" y="38" font-family="'Instrument Serif', Georgia, serif" font-size="23" fill="#fafafa">Language <tspan font-style="italic" fill="#a3a3a3">DNA</tspan></text>
  <text x="400" y="36" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="10.5" fill="#737373">{telemetry["repo_count"]} PUBLIC REPOS</text>
  <text x="32" y="66" font-family="'JetBrains Mono', monospace" font-size="11" fill="#737373">Aggregated from active non-fork repositories</text>

  <g clip-path="url(#barClip)">
    <g class="gx" style="animation-delay:0.2s">
      {''.join(segments)}
    </g>
  </g>

  <g class="fade" style="animation-delay:0.35s">
    {''.join(legend)}
  </g>
</svg>"""


def render_velocity(fonts_css: str, telemetry: dict) -> str:
    monthly = telemetry["monthly"]
    max_val = max((c for _, c in monthly), default=1) or 1
    bars = []
    start_x = 34
    step = 37
    base_y = 158
    max_h = 66

    for idx, (label, count) in enumerate(monthly):
        h = max(6, int((count / max_val) * max_h))
        y = base_y - h
        x = start_x + idx * step
        is_latest = idx == len(monthly) - 1
        fill = "#10b981" if is_latest else ("#d4d4d4" if count >= max_val * 0.6 else "#525252")
        delay = f"{0.15 + idx * 0.05:.2f}s"
        bars.append(
            f'<rect class="gy" style="animation-delay:{delay}" x="{x}" y="{y}" width="22" height="{h}" rx="4" fill="{fill}">'
            f'<title>{label}: {count} contributions</title></rect>'
            f'<text x="{x + 11}" y="176" text-anchor="middle" font-family="\'JetBrains Mono\', monospace" font-size="9.5" fill="#737373">{label}</text>'
        )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="432" height="196" viewBox="0 0 432 196" role="img" aria-label="Shipped Velocity">
  <style>{fonts_css}{BASE_CSS}</style>
  <rect width="432" height="196" rx="16" fill="#0a0a0a"/>
  <rect x="0.5" y="0.5" width="431" height="195" rx="15.5" fill="none" stroke="#262626"/>

  <text x="32" y="38" font-family="'Instrument Serif', Georgia, serif" font-size="23" fill="#fafafa">Shipped <tspan font-style="italic" fill="#10b981">Velocity</tspan></text>
  <text x="400" y="36" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="10.5" fill="#10b981">{telemetry["total_contributions"]} / YR</text>
  <text x="32" y="66" font-family="'JetBrains Mono', monospace" font-size="11" fill="#737373">{telemetry["total_commits"]} commits · {telemetry["total_prs"]} PRs · auto-synced</text>

  <line x1="32" y1="158" x2="400" y2="158" stroke="#1f1f1f"/>
  {''.join(bars)}
</svg>"""


def render_heatmap(fonts_css: str, telemetry: dict) -> str:
    """Render monochrome white-to-gray contribution heatmap on a deep black frame."""
    weeks = telemetry.get("weeks") or []
    # Fallback 53 weeks if run locally without token
    if not weeks:
        weeks = [{"contributionDays": [{"contributionCount": 0, "date": ""} for _ in range(7)]} for _ in range(53)]

    weeks = weeks[-53:]
    all_nonzero = [
        d["contributionCount"]
        for w in weeks
        for d in w.get("contributionDays", [])
        if d.get("contributionCount", 0) > 0
    ]
    max_count = max(all_nonzero, default=1)

    def mono_color(count: int) -> str:
        if count <= 0:
            return "#161618"
        ratio = count / max_count
        if ratio <= 0.25:
            return "#4a4a4e"
        if ratio <= 0.50:
            return "#7a7a80"
        if ratio <= 0.75:
            return "#bdbdc2"
        return "#ffffff"

    rects = []
    month_labels = []
    seen_months = set()
    start_x = 44
    start_y = 84
    col_step = 15
    row_step = 15

    for w_idx, week in enumerate(weeks):
        x = start_x + w_idx * col_step
        days = week.get("contributionDays", [])
        if days and days[0].get("date"):
            ym = days[0]["date"][:7]
            if ym not in seen_months:
                seen_months.add(ym)
                if len(seen_months) > 1 or w_idx == 0:
                    m_txt = datetime.strptime(ym, "%Y-%m").strftime("%b")
                    month_labels.append(
                        f'<text x="{x}" y="206" font-family="\'JetBrains Mono\', monospace" font-size="10" fill="#737373">{m_txt}</text>'
                    )

        for d_idx, day in enumerate(days):
            y = start_y + d_idx * row_step
            cnt = day.get("contributionCount", 0)
            date_str = day.get("date", "")
            fill = mono_color(cnt)
            delay = f"{0.15 + w_idx * 0.025 + d_idx * 0.015:.2f}s"
            tip = f"{date_str}: {cnt} contributions" if date_str else f"{cnt} contributions"
            rects.append(
                f'<rect class="p" style="animation-delay:{delay}" x="{x}" y="{y}" width="12" height="12" rx="3" fill="{fill}">'
                f'<title>{html.escape(tip)}</title></rect>'
            )

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="880" height="236" viewBox="0 0 880 236" role="img" aria-label="Contribution graph in monochrome">
  <style>{fonts_css}{BASE_CSS}</style>
  <rect width="880" height="236" rx="16" fill="#0a0a0a"/>
  <rect x="0.5" y="0.5" width="879" height="235" rx="15.5" fill="none" stroke="#262626"/>

  <g class="fade" style="animation-delay:0.05s">
    <text x="44" y="46" font-family="'Instrument Serif', Georgia, serif" font-size="28" fill="#fafafa">Every commit, <tspan font-style="italic" fill="#a3a3a3">in monochrome</tspan></text>
    <text x="836" y="44" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="11" letter-spacing="1" fill="#737373">{telemetry["total_contributions"]} CONTRIBUTIONS · REFRESHED DAILY</text>
  </g>
  <line x1="44" y1="64" x2="836" y2="64" stroke="#1a1a1a"/>

  {''.join(rects)}

  <g class="fade" style="animation-delay:0.8s">
    {''.join(month_labels)}
    <text x="744" y="206" text-anchor="end" font-family="'JetBrains Mono', monospace" font-size="10" fill="#737373">Less</text>
    <rect x="752" y="196" width="11" height="11" rx="2.5" fill="#161618"/>
    <rect x="766" y="196" width="11" height="11" rx="2.5" fill="#4a4a4e"/>
    <rect x="780" y="196" width="11" height="11" rx="2.5" fill="#7a7a80"/>
    <rect x="794" y="196" width="11" height="11" rx="2.5" fill="#bdbdc2"/>
    <rect x="808" y="196" width="11" height="11" rx="2.5" fill="#ffffff"/>
    <text x="824" y="206" font-family="'JetBrains Mono', monospace" font-size="10" fill="#737373">More</text>
  </g>
</svg>"""


def main() -> None:
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    fonts_css = load_fonts_css()
    telemetry = fetch_github_telemetry()

    (CARDS_DIR / "hero.svg").write_text(render_hero(fonts_css), encoding="utf-8")
    (CARDS_DIR / "heatmap.svg").write_text(render_heatmap(fonts_css, telemetry), encoding="utf-8")
    (CARDS_DIR / "project-stellar.svg").write_text(
        render_project_card(
            fonts_css,
            title="STELLAR JOB",
            subtitle="GIS Field Operations",
            badge="LIVE · VERCEL",
            accent="#10b981",
            line1="Leaflet routing &amp; live dispatch",
            line2="Digital sign &amp; Thai PDF export",
            tags=["Next.js 15", "Zustand", "NeonDB"],
            delay="0.1s",
        ),
        encoding="utf-8",
    )
    (CARDS_DIR / "project-privategym.svg").write_text(
        render_project_card(
            fonts_css,
            title="PRIVATEGYM",
            subtitle="Luxury Pod Booking",
            badge="LIVE · RENDER",
            accent="#f59e0b",
            line1="5-role RBAC &amp; live pod booking",
            line2="Dockerized .NET 10 + Postgres",
            tags=[".NET 10", "EF Core 9", "Docker"],
            delay="0.2s",
        ),
        encoding="utf-8",
    )
    (CARDS_DIR / "project-keystay.svg").write_text(
        render_project_card(
            fonts_css,
            title="KEYSTAY",
            subtitle="Edge Microservices",
            badge="105 EDGE APIs",
            accent="#38bdf8",
            line1="Cloudflare Workers + D1 SQLite",
            line2="Outbox pattern &amp; QStash queue",
            tags=["Workers", "Drizzle", "QStash"],
            delay="0.3s",
        ),
        encoding="utf-8",
    )
    (CARDS_DIR / "languages.svg").write_text(render_languages(fonts_css, telemetry), encoding="utf-8")
    (CARDS_DIR / "velocity.svg").write_text(render_velocity(fonts_css, telemetry), encoding="utf-8")
    print("Generated 7 SVGs in cards/:", json.dumps(telemetry))


if __name__ == "__main__":
    main()

