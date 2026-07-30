#!/usr/bin/env python3
"""gallery/ 폴더 스캔 → gallery.html 카드 재생성.

운영 방식: gallery/ 폴더에 이미지·영상 파일을 넣고 push하면
GitHub Actions(update-gallery.yml)가 이 스크립트를 실행해 페이지에 반영한다.
로그인·업로드 기능 없음 — git이 곧 CMS다.

캡션 = 파일명(확장자 제외, '-'/'_' → 공백).
정렬 = 파일명 내림차순 — 'YYYY-MM_제목.ext' 형식으로 넣으면 최신이 앞에 온다.
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
CAPTIONS = {
    "해커톤-1.webp": "서울시 하드웨어 해커톤 2019",
    "해커톤-2.webp": "서울시 하드웨어 해커톤 2019",
    "해커톤-3.webp": "서울시 하드웨어 해커톤 2019",
    "liveness-데모.mp4": "Windows 로그인 세션 liveness 데모 — 보안 솔루션의 시작 지점인 로그인 단계라 성능보다 위변조 탐지 강도를 우선해 설정했습니다",
}


def build_card(name):
    stem, ext = os.path.splitext(name)
    ext = ext.lower()
    if ext not in IMG_EXT | VID_EXT:
        return None
    caption = html.escape(CAPTIONS.get(name, re.sub(r"[-_]+", " ", stem).strip()))
    url = f"{GALLERY_DIR}/{urllib.parse.quote(name)}"
    if ext in VID_EXT:
        mime = "video/webm" if ext == ".webm" else "video/mp4"
        media = (f'<video controls preload="metadata" playsinline>'
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
