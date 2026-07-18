#!/usr/bin/env python3
from __future__ import annotations

import base64
import html
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

API_URL = "https://wakatime.com/api/v1/users/current/stats/{range}"
OUTPUT_DIR = Path("assets")

LANGUAGE_COLORS = {
    "Java": "#ED8B00",
    "TypeScript": "#3178C6",
    "JavaScript": "#F7DF1E",
    "PHP": "#777BB4",
    "Python": "#3776AB",
    "CSS": "#663399",
    "HTML": "#E34F26",
    "Markdown": "#5B6B7A",
    "JSON": "#8A8A8A",
    "SQL": "#336791",
    "XML": "#F97316",
    "Text": "#94A3B8",
    "YAML": "#CB171E",
    "Shell": "#89E051",
    "Bash": "#4EAA25",
    "Vue.js": "#42B883",
    "React": "#61DAFB",
    "Kotlin": "#7F52FF",
    "Swift": "#F05138",
    "C#": "#512BD4",
    "C++": "#00599C",
    "Go": "#00ADD8",
    "Rust": "#DEA584",
}

THEMES = {
    "light": {
        "background": "#FFFFFF",
        "border": "#D0D7DE",
        "title": "#1F2328",
        "muted": "#656D76",
        "text": "#1F2328",
        "track": "#EAEFF4",
        "shadow": "#1F23281A",
    },
    "dark": {
        "background": "#0D1117",
        "border": "#30363D",
        "title": "#F0F6FC",
        "muted": "#8B949E",
        "text": "#E6EDF3",
        "track": "#21262D",
        "shadow": "#00000066",
    },
}

def fetch_stats(api_key: str, time_range: str) -> dict[str, Any]:
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    request = urllib.request.Request(
        API_URL.format(range=time_range),
        headers={
            "Authorization": f"Basic {token}",
            "Accept": "application/json",
            "User-Agent": "karamusluk-wakatime-svg-card/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"WakaTime API returned HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Could not reach WakaTime API: {exc.reason}") from exc

def esc(value: object) -> str:
    return html.escape(str(value), quote=True)

def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(value, maximum))

def language_color(name: str, index: int) -> str:
    fallback = ["#7C3AED", "#06B6D4", "#22C55E", "#F59E0B", "#EC4899", "#6366F1"]
    return LANGUAGE_COLORS.get(name, fallback[index % len(fallback)])

def build_svg(data: dict[str, Any], theme_name: str, max_languages: int) -> str:
    theme = THEMES[theme_name]
    stats = data.get("data", {})
    languages = stats.get("languages", [])[:max_languages]

    width = 820
    top = 118
    row_height = 58
    bottom = 42
    height = top + max(len(languages), 1) * row_height + bottom

    title = "Weekly Development Activity"
    range_text = stats.get("human_readable_range", "Last 7 days")
    total_text = (
        stats.get("human_readable_total_including_other_language")
        or stats.get("human_readable_total")
        or "No activity"
    )

    rows = []
    if not languages:
        rows.append(
            f'<text x="40" y="{top + 28}" class="empty">No coding activity found for this period.</text>'
        )
    else:
        for index, language in enumerate(languages):
            name = esc(language.get("name", "Unknown"))
            duration = esc(language.get("text", "0 secs"))
            percent = clamp(float(language.get("percent", 0)), 0, 100)
            y = top + index * row_height
            color = language_color(str(language.get("name", "")), index)

            bar_x = 310
            bar_width = 390
            fill_width = max(3 if percent > 0 else 0, bar_width * percent / 100)

            rows.append(f'''
<circle cx="43" cy="{y + 16}" r="6" fill="{color}" />
<text x="60" y="{y + 21}" class="language">{name}</text>
<text x="258" y="{y + 21}" text-anchor="end" class="duration">{duration}</text>
<rect x="{bar_x}" y="{y + 5}" width="{bar_width}" height="16" rx="8" fill="{theme["track"]}" />
<rect x="{bar_x}" y="{y + 5}" width="{fill_width:.1f}" height="16" rx="8" fill="{color}" />
<text x="778" y="{y + 21}" text-anchor="end" class="percent">{percent:05.2f}%</text>
''')

    rows_markup = "".join(rows)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">
<title id="title">{esc(title)}</title>
<desc id="desc">{esc(total_text)} of coding activity during {esc(range_text)}.</desc>

<defs>
  <filter id="shadow" x="-10%" y="-10%" width="120%" height="130%">
    <feDropShadow dx="0" dy="8" stdDeviation="12" flood-color="{theme["shadow"]}" />
  </filter>
</defs>

<style>
  text {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
  }}
  .title {{ fill: {theme["title"]}; font-size: 25px; font-weight: 700; }}
  .meta {{ fill: {theme["muted"]}; font-size: 13px; font-weight: 500; }}
  .total {{ fill: {theme["text"]}; font-size: 17px; font-weight: 650; }}
  .language {{ fill: {theme["text"]}; font-size: 15px; font-weight: 600; }}
  .duration {{ fill: {theme["muted"]}; font-size: 14px; }}
  .percent {{ fill: {theme["muted"]}; font-size: 13px; font-variant-numeric: tabular-nums; }}
  .empty {{ fill: {theme["muted"]}; font-size: 15px; }}
</style>

<rect x="12" y="12" width="{width - 24}" height="{height - 24}" rx="20"
      fill="{theme["background"]}" stroke="{theme["border"]}" filter="url(#shadow)" />

<text x="40" y="53" class="title">{esc(title)}</text>
<text x="40" y="78" class="meta">{esc(range_text)}</text>
<text x="780" y="53" text-anchor="end" class="meta">TOTAL CODING TIME</text>
<text x="780" y="78" text-anchor="end" class="total">{esc(total_text)}</text>

<line x1="40" y1="97" x2="780" y2="97" stroke="{theme["border"]}" />

{rows_markup}
</svg>
'''

def main() -> int:
    api_key = os.getenv("WAKATIME_API_KEY", "").strip()
    if not api_key:
        print("WAKATIME_API_KEY is not set.", file=sys.stderr)
        return 1

    time_range = os.getenv("WAKATIME_RANGE", "last_7_days").strip()
    max_languages = int(os.getenv("MAX_LANGUAGES", "8"))
    payload = fetch_stats(api_key, time_range)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for theme in ("light", "dark"):
        output = OUTPUT_DIR / f"wakatime-{theme}.svg"
        output.write_text(build_svg(payload, theme, max_languages), encoding="utf-8")
        print(f"Generated {output}")

    return 0

if __name__ == "__main__":
    raise SystemExit(main())
