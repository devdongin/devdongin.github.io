#!/usr/bin/env python3
"""gallery/ 폴더 스캔 → gallery.html 카드 재생성.

운영 방식: gallery/ 폴더에 이미지·영상 파일을 넣고 push하면
GitHub Actions(update-gallery.yml)가 이 스크립트를 실행해 페이지에 반영한다.
로그인·업로드 기능 없음: git이 곧 CMS다.

캡션 = 파일명(확장자 제외, '-'/'_' → 공백).
정렬 = 파일명 내림차순: 'YYYY-MM_제목.ext' 형식으로 넣으면 최신이 앞에 온다.

유튜브 영상은 '.youtube' 파일로 넣는다: 파일 내용에 영상 URL이나 ID 한 줄.
저장소 용량·대역폭을 쓰지 않으므로 긴 영상은 이 방식을 쓴다.
"""
import html
import os
import re
import sys
import urllib.parse

GALLERY_DIR = "gallery"
PAGE = "gallery.html"
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".jfif", ".avif"}
VID_EXT = {".mp4", ".webm"}
YT_EXT = {".youtube"}
# \w 는 파이썬에서 유니코드까지 매칭해 한글 11자도 통과한다. 유튜브 ID 문자 집합으로
# 정확히 좁힌다 (#138 P2). 이 값은 그대로 iframe src 에 들어간다.
YT_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
CAPTIONS = {
    "해커톤-1.webp": "서울시 하드웨어 해커톤 2019",
    "해커톤-2.webp": "서울시 하드웨어 해커톤 2019",
    "해커톤-3.webp": "서울시 하드웨어 해커톤 2019",
    "liveness-데모.mp4": "Windows 로그인 세션 liveness 데모: 보안 솔루션의 시작 지점인 로그인 단계라 성능보다 위변조 탐지 강도를 우선해 설정했습니다",
    "얼굴-위변조-탐지-데모.youtube": "얼굴 위변조(anti-spoofing) 탐지 테스트 앱: 사진·화면 재생 같은 제시형 공격을 실시간으로 판별합니다",
    "SEEUON-macOS-클라이언트.youtube": "SEEUON macOS 클라이언트: AI 코딩 하네스를 실무에 들여 구축 중인 macOS 버전. 실시간 얼굴 인증과 감시 정책이 동작하는 화면입니다 (소리 없음)",
}
# 로컬 영상의 대표 이미지: 재생 전 검은 화면 대신 첫인상을 준다
POSTERS = {
    "liveness-데모.mp4": "assets/images/liveness-poster.webp",
}


def youtube_id(path):
    """.youtube 파일에서 영상 ID를 뽑는다 (URL 또는 ID 한 줄)."""
    with open(path, encoding="utf-8") as f:
        raw = f.read().strip()
    if not raw:
        return None
    if YT_ID.match(raw):
        return raw
    m = re.search(r"(?:v=|youtu\.be/|embed/|shorts/)([A-Za-z0-9_-]{11})", raw)
    return m.group(1) if m else None


def build_card(name):
    stem, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in IMG_EXT | VID_EXT | YT_EXT:
        return None
    caption = html.escape(CAPTIONS.get(name, re.sub(r"[-_]+", " ", stem).strip()))
    url = f"{GALLERY_DIR}/{urllib.parse.quote(name)}"
    if ext in YT_EXT:
        vid = youtube_id(os.path.join(GALLERY_DIR, name))
        if not vid:
            print(f"[gallery] skip {name}: no video id", file=sys.stderr)
            return None
        # nocookie 도메인: 재생 전에는 추적 쿠키를 심지 않는다
        media = (f'<div class="g-embed"><iframe src="https://www.youtube-nocookie.com/embed/{vid}" '
                 f'title="{caption}" loading="lazy" allowfullscreen '
                 f'allow="accelerometer; clipboard-write; encrypted-media; picture-in-picture" '
                 f'referrerpolicy="strict-origin-when-cross-origin"></iframe></div>')
    elif ext in VID_EXT:
        mime = "video/webm" if ext == ".webm" else "video/mp4"
        poster = POSTERS.get(name)
        attr = f' poster="{poster}"' if poster else ""
        media = (f'<video controls preload="metadata" playsinline{attr}>'
                 f'<source src="{url}" type="{mime}"></video>')
    else:
        media = (f'<a href="{url}" target="_blank" rel="noopener">'
                 f'<img src="{url}" alt="{caption}" loading="lazy"></a>')
    return f'<figure class="g-card">{media}<figcaption>{caption}</figcaption></figure>'


def main():
    cards = [c for c in (build_card(n) for n in sorted(os.listdir(GALLERY_DIR), reverse=True)) if c]
    inner = "\n  " + "\n  ".join(cards) + "\n  " if cards else "\n  "

    with open(PAGE, encoding="utf-8") as f:
        page = f.read()
    if "<!-- GALLERY:START -->" not in page:
        sys.exit("[gallery] marker not found in gallery.html")
    page = re.sub(r"(<!-- GALLERY:START -->)(.*?)(<!-- GALLERY:END -->)",
                  lambda m: m.group(1) + inner + m.group(3), page, count=1, flags=re.S)
    with open(PAGE, "w", encoding="utf-8", newline="\n") as f:
        f.write(page)
    print(f"[gallery] {len(cards)} items rendered", file=sys.stderr)


if __name__ == "__main__":
    main()
