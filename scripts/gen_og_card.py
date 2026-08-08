#!/usr/bin/env python3
"""assets/images/og-card.png 생성: 링크 공유 시 노출되는 1200x630 카드.

사이트 다크 팔레트(index.html :root)와 동일한 톤. 로컬에서 실행:
  pip install pillow
  python scripts/gen_og_card.py
텍스트·수치가 바뀌지 않는 정적 카드라서 자동 갱신 대상이 아니다.
폰트는 Windows 맑은 고딕(malgun)을 사용한다 (Pretendard 근사치).
"""
from PIL import Image, ImageDraw, ImageFont, ImageOps
from pathlib import Path

W, H = 1200, 630
BG = "#0d1117"
CARD = "#161b22"
BORDER = "#1f2733"
TEXT = "#e6edf3"
DIM = "#9ba7b4"
ACCENT = "#58a6ff"

FONT_DIR = "C:/Windows/Fonts/"
ASSET_DIR = Path("assets/images")


def font(name, size):
    return ImageFont.truetype(FONT_DIR + name, size)


def main():
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 상단 액센트 라인
    d.rectangle([0, 0, W, 6], fill=ACCENT)

    margin = 90
    y = 118

    # eyebrow
    eyebrow = "AI PRODUCT ENGINEERING · C++ SYSTEMS & INFERENCE"
    f_eye = font("malgunbd.ttf", 22)
    # 자간 벌리기
    x = margin
    for ch in eyebrow:
        d.text((x, y), ch, font=f_eye, fill=ACCENT)
        x += d.textlength(ch, font=f_eye) + 3
    y += 72

    # 이름
    f_name = font("malgunbd.ttf", 92)
    d.text((margin, y), "선동인", font=f_name, fill=TEXT)
    name_w = d.textlength("선동인", font=f_name)
    f_handle = font("malgun.ttf", 40)
    d.text((margin + name_w + 28, y + 62), "devdongin", font=f_handle, fill=DIM)
    y += 164

    # 헤드라인 두 줄: 아바타 영역(x>780)을 침범하지 않는다
    f_head = font("malgunbd.ttf", 46)
    d.text((margin, y), "AI 모델을,", font=f_head, fill=TEXT)
    y += 66
    d.text((margin, y), "실제 환경의 소프트웨어로", font=f_head, fill=ACCENT)

    # 하단 URL
    f_url = font("malgunbd.ttf", 30)
    d.rectangle([margin, H - 108, margin + 6, H - 68], fill=ACCENT)
    d.text((margin + 24, H - 106), "devdongin.github.io", font=f_url, fill=TEXT)

    # 우측 아바타 (원형 + 액센트 링)
    avatar_size = 260
    cx, cy = W - 90 - avatar_size // 2, H // 2 - 40
    avatar = Image.open(ASSET_DIR / "login_avatar.jpg").convert("RGB")
    avatar = ImageOps.fit(avatar, (avatar_size, avatar_size))
    mask = Image.new("L", (avatar_size * 4, avatar_size * 4), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, avatar_size * 4, avatar_size * 4], fill=255)
    mask = mask.resize((avatar_size, avatar_size))
    ring = avatar_size // 2 + 10
    d.ellipse([cx - ring, cy - ring, cx + ring, cy + ring], fill=CARD, outline=ACCENT, width=4)
    img.paste(avatar, (cx - avatar_size // 2, cy - avatar_size // 2), mask)

    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    img.save(ASSET_DIR / "og-card.png", optimize=True)
    print("assets/images/og-card.png written")


if __name__ == "__main__":
    main()
