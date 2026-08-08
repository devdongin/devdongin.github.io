#!/usr/bin/env python3
"""자동 갱신 PR 게시 전 검증 게이트.

승인 0건 자동 병합이라 사람 리뷰가 개입하지 않는다. 대신 기계적으로 확인
가능한 것들을 여기서 막는다: 하나라도 실패하면 PR을 만들지 않고 워크플로가
실패한다(조용히 잘못된 내용이 main에 들어가는 것보다 낫다).

사용법: python scripts/verify_auto_update.py <base_ref>
  base_ref  비교 기준 (보통 origin/main)
"""
import json
import pathlib
import re
import subprocess
import sys

ALLOWED = {"index.html", "gallery.html", "data/stats.json", "data/blog.json",
           "data/scan_cache.json"}

# 마커 구간: 렌더러/AI가 갱신하는 곳. 짝이 맞고 중복이 없어야 한다.
# 목록을 하드코딩하면 새 마커가 생길 때마다 "마커 밖 변경"으로 오탐하므로
# (실제로 STAT-HIGHLIGHT-ACTIVITY 추가 때 그랬다) HTML에서 직접 찾아낸다.
MARKER_RE = re.compile(r"<!-- ([A-Z][A-Z0-9_-]*):START -->")


def markers_in(text):
    return sorted(set(MARKER_RE.findall(text)))

# 공개 금지: CLAUDE.md 절대 규칙과 #24에서 정리한 보안 표현
FORBIDDEN = [
    (r"010[-\s]?\d{4}[-\s]?\d{4}", "전화번호"),
    (r"강동구|아리수로", "주소"),
    (r"희망연봉|직전\s*연봉", "연봉"),
    (r"학점\s*3\.\d", "학점"),
    (r"SHA-?256|salt|공유\s*키|키가\s*든", "보안 구현값(알고리즘·키 구성·저장 위치)"),
    (r"SECERN-AI/[A-Za-z0-9_-]+", "내부 저장소 경로"),
    (r"손동인", "이름 오기"),
]

# 통계로 증명되지 않는 인과 해석 (#27)
CAUSAL = [
    (r"커밋[^.]{0,40}(운영\s*대응|신규\s*개발|생산성|품질)[^.]{0,20}(이어지|늘|증가|향상)", "커밋량→업무원인 추론"),
]


def sh(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def main():
    base = sys.argv[1] if len(sys.argv) > 1 else "origin/main"
    fails = []

    # 1) 변경 파일이 허용 목록 안인가
    changed = [f for f in sh("git", "diff", "--name-only", base, "--").splitlines() if f]
    for f in changed:
        if f not in ALLOWED:
            fails.append(f"허용되지 않은 파일 변경: {f}")
    if not changed:
        print("[verify] 변경 없음: 검증 생략")
        return 0
    print(f"[verify] 변경 파일: {', '.join(changed)}")

    html = pathlib.Path("index.html").read_text(encoding="utf-8")

    # 2) 마커 무결성: START/END 각각 정확히 1개
    names = markers_in(html)
    if not names:
        fails.append("index.html에서 마커를 찾지 못함")
    print(f"[verify] 마커 {len(names)}개 확인")
    for name in names:
        s = html.count(f"<!-- {name}:START -->")
        e = html.count(f"<!-- {name}:END -->")
        if (s, e) != (1, 1):
            fails.append(f"마커 {name}: START {s}개 / END {e}개 (각각 1개여야 함)")

    # 3) 마커 밖 비의도 변경: 마커 구간을 지운 뒤에도 diff가 남는지
    if "index.html" in changed:
        def strip(text):
            for name in set(names) | set(markers_in(text)):
                text = re.sub(rf"<!-- {name}:START -->.*?<!-- {name}:END -->",
                              f"<!--{name}-->", text, flags=re.S)
            return text
        old = sh("git", "show", f"{base}:index.html")
        if old and strip(old) != strip(html):
            fails.append("index.html 마커 구간 밖이 변경됨 (자동 갱신은 마커 안만 건드려야 함)")

    # 4) 금지 표현
    for pat, label in FORBIDDEN:
        if re.search(pat, html):
            fails.append(f"금지 표현 발견({label}): {re.search(pat, html).group()[:40]}")

    # 5) 통계로 증명 불가한 인과 해석
    review = re.search(r"<!-- AI-REVIEW:START -->(.*?)<!-- AI-REVIEW:END -->", html, re.S)
    if review:
        text = re.sub(r"<[^>]+>", "", review.group(1))
        for pat, label in CAUSAL:
            if re.search(pat, text):
                fails.append(f"AI REVIEW 인과 추론({label}): 수치·추세까지만 서술할 것")
        if len(text.strip()) < 80:
            fails.append("AI REVIEW가 비었거나 지나치게 짧음")

    # 6) stats.json 정합성
    if "data/stats.json" in changed:
        try:
            d = json.loads(pathlib.Path("data/stats.json").read_text())
            if sum(d["daily"].values()) != d["total_commits"]:
                fails.append("stats.json: daily 합계와 total_commits 불일치")
            for slug, s in d.get("repo_stats", {}).items():
                if s["mine"] > s["total"]:
                    fails.append(f"stats.json: {slug} mine > total")
        except Exception as exc:
            fails.append(f"stats.json 파싱 실패: {exc}")

    # 7) 공백 오류
    if subprocess.run(["git", "diff", "--check", base, "--"]).returncode != 0:
        fails.append("git diff --check 실패 (공백 오류)")

    if fails:
        print("\n[verify] ❌ 검증 실패: PR을 생성하지 않습니다", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("[verify] ✅ 전 항목 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
