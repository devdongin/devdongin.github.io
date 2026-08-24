#!/usr/bin/env python3
"""Tistory RSS → data/blog.json (최근 글 카드용).

secret 불필요 (공개 RSS). 실패 시 기존 blog.json을 유지하기 위해
경고만 남기고 정상 종료한다: 블로그 수집 실패가 전체 갱신을 막지 않게.
"""
import html
import json
import os
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

RSS_URL = "https://he11oworld.tistory.com/rss"
OUT_PATH = "data/blog.json"
MAX_POSTS = 8
KST = timezone(timedelta(hours=9))


def main():
    try:
        req = urllib.request.Request(RSS_URL, headers={"User-Agent": "devdongin-github-io"})
        with urllib.request.urlopen(req, timeout=30) as r:
            root = ET.fromstring(r.read())
    except Exception as e:
        print(f"[blog] warn: RSS fetch failed ({type(e).__name__}), keeping old data", file=sys.stderr)
        return

    posts = []
    for item in root.iter("item"):
        # Tistory RSS는 제목을 이중 인코딩하므로 entity를 한 번 되돌린다
        title = html.unescape((item.findtext("title") or "").strip())
        link = (item.findtext("link") or "").strip()
        if not title or not link:
            continue
        category = html.unescape((item.findtext("category") or "").strip())
        # 포트폴리오 하단 노출용이므로 기술 글("개발/*" 카테고리)만 선별한다
        if not category.startswith("개발/"):
            continue
        category = category.rsplit("/", 1)[-1] or "Blog"  # "개발/AI" → "AI"
        try:
            date = parsedate_to_datetime(item.findtext("pubDate")).astimezone(KST).date().isoformat()
        except Exception:
            date = ""
        posts.append({"title": title, "link": link, "category": category, "date": date})
        if len(posts) >= MAX_POSTS:
            break

    if not posts:
        print("[blog] warn: RSS parsed but no items, keeping old data", file=sys.stderr)
        return

    os.makedirs("data", exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8", newline="\n") as f:
        # collected_at 은 워크플로가 "언제 마지막으로 받아왔는지"를 판단하는 근거다.
        # 이게 없으면 블로그 갱신 주기를 통계에 묶을 수밖에 없다.
        json.dump({"collected_at": datetime.now(KST).date().isoformat(),
                   "posts": posts}, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(f"[blog] {len(posts)} posts -> {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
