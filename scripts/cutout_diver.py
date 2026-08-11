#!/usr/bin/env python3
"""다이버 픽셀아트의 배경을 지워 투명 PNG로 만든다.

사용법:
  python scripts/cutout_diver.py <입력파일> [출력파일]
기본 출력: assets/diver/diver-cutout.png

색 키잉(같은 색을 전부 지우기)이 아니라 **네 모서리에서 시작하는 플러드 필**을 쓴다.
이 그림은 마스크 유리도 배경과 비슷한 하늘색이라, 색만 보고 지우면 얼굴에 구멍이 뚫린다.
바깥에서 이어진 영역만 지우면 안쪽 하늘색은 그대로 남는다.

픽셀아트라 안티에일리어싱이 거의 없어 경계가 깔끔하다. 다만 저장 과정에서 생긴
반투명 가장자리를 정리하려고 알파를 이진화한다.
"""
import sys
from collections import deque
from pathlib import Path

from PIL import Image

TOLERANCE = 38      # 배경으로 볼 색 거리 (0~441). 픽셀아트라 넉넉해도 안전하다
OUT_DEFAULT = Path("assets/diver/diver-cutout.png")


def close(a, b, tol=TOLERANCE):
    return sum((x - y) ** 2 for x, y in zip(a[:3], b[:3])) <= tol * tol


def main():
    if len(sys.argv) < 2:
        sys.exit("사용법: python scripts/cutout_diver.py <입력파일> [출력파일]")
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else OUT_DEFAULT
    if not src.exists():
        sys.exit(f"입력 파일이 없습니다: {src}")

    img = Image.open(src).convert("RGBA")
    w, h = img.size
    px = img.load()

    # 네 모서리 색이 서로 비슷해야 '단색 배경'이라고 볼 수 있다
    corners = [px[0, 0], px[w - 1, 0], px[0, h - 1], px[w - 1, h - 1]]
    if not all(close(corners[0], c) for c in corners[1:]):
        print("[cutout] 경고: 모서리 색이 서로 다릅니다. 배경이 단색이 아닐 수 있습니다.")
    bg = corners[0]
    print(f"[cutout] 입력 {w}x{h}, 배경색 추정 RGB{bg[:3]}")

    # 바깥에서 이어진 배경만 지운다
    seen = bytearray(w * h)
    q = deque()
    for x in range(w):
        q.append((x, 0)); q.append((x, h - 1))
    for y in range(h):
        q.append((0, y)); q.append((w - 1, y))

    removed = 0
    while q:
        x, y = q.popleft()
        i = y * w + x
        if seen[i]:
            continue
        seen[i] = 1
        if not close(px[x, y], bg):
            continue
        px[x, y] = (0, 0, 0, 0)
        removed += 1
        if x > 0:     q.append((x - 1, y))
        if x < w - 1: q.append((x + 1, y))
        if y > 0:     q.append((x, y - 1))
        if y < h - 1: q.append((x, y + 1))

    # 반투명 가장자리 정리 (픽셀아트는 알파가 0 아니면 255여야 깔끔하다)
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a and a < 255:
                px[x, y] = (r, g, b, 255 if a >= 128 else 0)

    # 남은 내용에 맞춰 여백을 잘라낸다
    box = img.getbbox()
    if box:
        img = img.crop(box)
        print(f"[cutout] 여백 제거 후 {img.size[0]}x{img.size[1]}")

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, optimize=True)
    pct = removed / (w * h) * 100
    print(f"[cutout] 배경 {removed}px 제거 ({pct:.1f}%) -> {dst} ({dst.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
