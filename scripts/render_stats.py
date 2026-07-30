#!/usr/bin/env python3
"""data/stats.json → index.html 마커 구간 결정적 렌더링.

갱신 구간 (index.html 안의 HTML 주석 마커):
  HEATMAP           커밋 히트맵 SVG
  HEATMAP-TITLE     h3 안의 기간·총 커밋 수
  COLLECTED         activity-note 안의 수집일
  MONTHLY           월별 커밋 합계 테이블 (접근성 대체 텍스트)
  STAT-SEEUONCLIENT / STAT-CULOCKERFSFD / STAT-CUFACESDK
                    프로젝트별 기본 브랜치 기여 통계

AI-REVIEW 구간은 이 스크립트가 건드리지 않는다 (Claude가 별도 갱신).
"""
import html as html_mod
import json
import re
import sys
from datetime import date, timedelta

INDEX = "index.html"
STATS = "data/stats.json"
BLOG = "data/blog.json"

# LinkedIn 프로필 URL — 비어 있으면 카드 미출력
LINKEDIN_URL = "https://www.linkedin.com/in/%EB%8F%99%EC%9D%B8-%EC%84%A0-9056021a3/"

CELL, STEP, X0, Y0 = 11, 13, 8, 18
COLS = 54  # 마지막 열이 집계 종료일이 속한 주가 되도록 54주 고정
PALETTE = ["#1b222c", "#0e4429", "#006d32", "#26a641", "#39d353"]


def color(n):
    if n <= 0:
        return PALETTE[0]
    if n <= 2:
        return PALETTE[1]
    if n <= 5:
        return PALETTE[2]
    if n <= 9:
        return PALETTE[3]
    return PALETTE[4]


def build_svg(daily, start, end, total):
    dow_end = (end.weekday() + 1) % 7  # 일요일=0
    grid_start = end - timedelta(days=dow_end) - timedelta(weeks=COLS - 1)
    width = X0 + (COLS - 1) * STEP + CELL + 10
    height = 131
    parts = []

    prev_month = grid_start.month
    for col in range(1, COLS):
        sunday = grid_start + timedelta(weeks=col)
        if sunday.month != prev_month:
            parts.append(f'<text x="{X0 + col * STEP}" y="12" font-size="10" '
                         f'fill="#9ba7b4">{sunday.month}월</text>')
        prev_month = sunday.month

    for col in range(COLS):
        for dow in range(7):
            d = grid_start + timedelta(weeks=col, days=dow)
            if d > end:
                continue
            x, y = X0 + col * STEP, Y0 + dow * STEP
            if d < start:
                parts.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" '
                             f'fill="#12161d" stroke="#1f2733" stroke-dasharray="2 2" '
                             f'stroke-width="0.5"><title>{d.isoformat()} · 집계 기간 이전'
                             f'</title></rect>')
            else:
                n = daily.get(d.isoformat(), 0)
                parts.append(f'<rect x="{x}" y="{y}" width="11" height="11" rx="2" '
                             f'fill="{color(n)}"><title>{d.isoformat()} · {n} commits'
                             f'</title></rect>')

    parts.append(f'<text x="{width - 167}" y="112" font-size="10" fill="#9ba7b4">Less</text>')
    for i, c in enumerate(PALETTE):
        parts.append(f'<rect x="{width - 133 + i * 13}" y="102" width="11" height="11" '
                     f'rx="2" fill="{c}"/>')
    parts.append(f'<text x="{width - 64}" y="112" font-size="10" fill="#9ba7b4">More</text>')

    label = f"커밋 히트맵 {start.isoformat()}부터 {end.isoformat()}까지, 총 {total} 커밋"
    return (f'<svg viewBox="0 0 {width} {height}" width="{width}" '
            f'xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{label}">'
            + "".join(parts) + "</svg>")


def build_monthly(daily, start, end):
    rows = []
    y, m = start.year, start.month
    while (y, m) <= (end.year, end.month):
        key = f"{y:04d}-{m:02d}"
        n = sum(v for k, v in daily.items() if k.startswith(key))
        rows.append(f"<tr><td>{key}</td><td>{n}</td></tr>")
        m += 1
        if m == 13:
            y, m = y + 1, 1
    return ("<table><thead><tr><th>월</th><th>commits</th></tr></thead><tbody>"
            + "".join(rows) + "</tbody></table>")


def _blog_half(posts, focusable):
    esc = html_mod.escape
    extra = "" if focusable else ' tabindex="-1"'
    # LinkedIn이 현재 주 활동 채널 — 카드를 맨 앞에 배치
    entries = []
    if LINKEDIN_URL:
        entries.append(("LinkedIn", "최근 활동 & 프로필 보기 →", "linkedin.com", LINKEDIN_URL))
    entries += [(p["category"], p["title"], p["date"], p["link"]) for p in posts]
    entries.append(("Tech Blog", "블로그 전체 보기 →", "he11oworld.tistory.com",
                    "https://he11oworld.tistory.com"))
    entries.append(("GitHub", "저장소 보기 →", "github.com/devdongin",
                    "https://github.com/devdongin"))
    return "".join(
        f'<a class="flow-card" href="{esc(link)}" target="_blank" rel="noopener"{extra}>'
        f'<span class="fc-tag">{esc(tag)}</span>'
        f'<span class="fc-title">{esc(title)}</span>'
        f'<span class="fc-meta">{esc(meta)}</span></a>'
        for tag, title, meta, link in entries)


def build_blog_cards(posts):
    # 끊김 없는 무한 스크롤을 위해 동일한 절반을 2벌 렌더.
    # 두 번째 절반은 스크린리더(aria-hidden·inert)와 탭 순서(tabindex)에서 제외.
    return (f'\n      <div class="ticker-half">{_blog_half(posts, True)}</div>'
            f'\n      <div class="ticker-half" aria-hidden="true" inert>'
            f'{_blog_half(posts, False)}</div>\n      ')


def replace(html, name, new_inner, required=True):
    pattern = re.compile(
        rf"(<!-- {re.escape(name)}:START -->)(.*?)(<!-- {re.escape(name)}:END -->)",
        re.DOTALL,
    )
    if not pattern.search(html):
        if required:
            sys.exit(f"[render] marker not found: {name}")
        print(f"[render] warn: marker not found, skipped: {name}", file=sys.stderr)
        return html
    return pattern.sub(lambda m: m.group(1) + new_inner + m.group(3), html, count=1)


def main():
    with open(STATS, encoding="utf-8") as f:
        stats = json.load(f)
    with open(INDEX, encoding="utf-8") as f:
        html = f.read()

    daily = stats["daily"]
    start = date.fromisoformat(stats["window"]["start"])
    end = date.fromisoformat(stats["window"]["end"])
    total = stats["total_commits"]
    repo_stats = stats.get("repo_stats", {})

    svg = build_svg(daily, start, end, total)
    html = replace(html, "HEATMAP", f"\n        {svg}\n        ")
    html = replace(html, "HEATMAP-TITLE", f"{start} – {end} · {total} commits")
    html = replace(html, "COLLECTED", f"{end} 수집 · merge 커밋 포함 · author 계정 기준 통합.")
    html = replace(html, "MONTHLY",
                   f"\n        {build_monthly(daily, start, end)}\n        ")

    s = repo_stats.get("seeuonclient")
    if s:
        html = replace(html, "STAT-SEEUONCLIENT",
                       f'<strong>커밋 {s["percent"]}% · {s["rank"]}위 기여자</strong> '
                       f'({s["mine"]:,} / {s["total"]:,} 커밋 · 기본 브랜치 · {end} 기준)',
                       required=False)
    s = repo_stats.get("culockerfsfd")
    if s:
        html = replace(html, "STAT-CULOCKERFSFD",
                       f'<strong>{s["mine"]}/{s["total"]} ({s["percent"]}% · {end} 기준)</strong>',
                       required=False)
    s = repo_stats.get("cufacesdk")
    if s:
        html = replace(html, "STAT-CUFACESDK",
                       f'<strong>기여 {s["rank"]}위 (커밋 {s["mine"]}회 · {end} 기준)</strong>',
                       required=False)
    s = repo_stats.get("seeuoncp")
    if s:
        html = replace(html, "STAT-SEEUONCP",
                       f' — 사내 저장소 커밋 <strong>{s["mine"]:,}/{s["total"]:,} '
                       f'({s["percent"]}% · {end} 기준)</strong>',
                       required=False)

    try:
        with open(BLOG, encoding="utf-8") as f:
            posts = json.load(f).get("posts", [])
    except (FileNotFoundError, json.JSONDecodeError):
        posts = []
    if posts:
        html = replace(html, "BLOG-CARDS", build_blog_cards(posts), required=False)

    with open(INDEX, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print(f"[render] index.html updated ({start} – {end}, {total} commits)", file=sys.stderr)


if __name__ == "__main__":
    main()
