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
           "data/scan_cache.json", "data/focus.md"}

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

# AI REVIEW 분량 상한 (#138 P1).
# 문법·사실관계가 모두 맞아도 길이만으로 히어로 위계가 무너져 CTA가 첫 화면 밖으로
# 밀린 사례가 있었다. 사람 승인 0건으로 자동 병합되므로 여기서 기계적으로 막는다.
# ai-meta(자동 생성 안내 문장)는 길이에서 제외하고 평가 본문만 센다.
REVIEW_MIN_CHARS = 80
REVIEW_MAX_CHARS = 240
REVIEW_MAX_SENTENCES = 3


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

    # 4-1) data/focus.md 도 같은 기준으로 본다.
    # 사람이 손으로 적는 파일이고 public 저장소에 그대로 올라가므로,
    # AI REVIEW 를 거치기 전에 이미 노출된다. 여기가 마지막 방어선이다.
    focus_path = pathlib.Path("data/focus.md")
    if focus_path.exists():
        focus = focus_path.read_text(encoding="utf-8")
        for pat, label in FORBIDDEN:
            m = re.search(pat, focus)
            if m:
                fails.append(f"focus.md 금지 표현({label}): {m.group()[:40]}")
        print("[verify] focus.md 금지 표현 검사 완료")

    # 5) 통계로 증명 불가한 인과 해석
    review = re.search(r"<!-- AI-REVIEW:START -->(.*?)<!-- AI-REVIEW:END -->", html, re.S)
    if review:
        raw = review.group(1)
        text = re.sub(r"<[^>]+>", "", raw)
        for pat, label in CAUSAL:
            if re.search(pat, text):
                fails.append(f"AI REVIEW 인과 추론({label}): 수치·추세까지만 서술할 것")

        # 평가 본문만 남긴다: 자동 생성 안내(ai-meta)는 분량 판단 대상이 아니다.
        body = re.sub(r'<span class="ai-meta">.*?</span>', "", raw, flags=re.S)
        body = re.sub(r"<[^>]+>", "", body)
        body = re.sub(r"\s+", " ", body).strip()
        # 마침표 뒤에 공백이나 끝이 와야 문장 경계로 본다. "40~50ms" 같은 수치는 안 쪼개진다.
        sentences = [s for s in re.split(r"[.!?]+(?:\s|$)", body) if s.strip()]

        if len(body) < REVIEW_MIN_CHARS:
            fails.append("AI REVIEW가 비었거나 지나치게 짧음")
        if len(body) > REVIEW_MAX_CHARS:
            fails.append(
                f"AI REVIEW 본문 {len(body)}자로 상한 {REVIEW_MAX_CHARS}자 초과: "
                "히어로 CTA가 첫 화면 밖으로 밀린다")
        if len(sentences) > REVIEW_MAX_SENTENCES:
            fails.append(
                f"AI REVIEW 문장 {len(sentences)}개로 상한 {REVIEW_MAX_SENTENCES}개 초과: "
                "핵심 평가 1문장에 근거 2문장까지만 쓴다")
        print(f"[verify] AI REVIEW 본문 {len(body)}자 / {len(sentences)}문장")

    # 6) stats.json 정합성
    if "data/stats.json" in changed:
        try:
            d = json.loads(pathlib.Path("data/stats.json").read_text(encoding="utf-8"))
            if sum(d["daily"].values()) != d["total_commits"]:
                fails.append("stats.json: daily 합계와 total_commits 불일치")
            for slug, s in d.get("repo_stats", {}).items():
                if s["mine"] > s["total"]:
                    fails.append(f"stats.json: {slug} mine > total")

            # 6-1) 급락 가드 (2026-08-18 추가)
            #
            # STATS_CONFIG 의 조직·저장소명이 틀리면 GitHub API 가 404 를 준다.
            # gh() 는 404 를 "접근 불가/빈 저장소"로 보고 None 을 돌려주므로
            # 수집이 조용히 빈 결과로 끝나고, 워크플로는 초록불로 통과한다.
            # 실제로 총 커밋이 1,037 에서 81 로 떨어진 채 그대로 게시됐다.
            # 집계 구간이 365일 롤링이라 하루치 정상 변동은 몇 % 수준이므로,
            # 30% 이상 빠지면 사람이 봐야 할 사고로 본다.
            old_raw = sh("git", "show", f"{base}:data/stats.json")
            if old_raw:
                o = json.loads(old_raw)
                prev, now = o.get("total_commits", 0), d.get("total_commits", 0)
                if prev and now < prev * 0.7:
                    fails.append(
                        f"총 커밋 급락: {prev:,} -> {now:,} "
                        f"({round((1 - now / prev) * 100)}% 감소). "
                        "STATS_TOKEN 권한이나 STATS_CONFIG 의 조직·저장소명을 확인할 것")
                gone = sorted(set(o.get("repo_stats", {})) - set(d.get("repo_stats", {})))
                if gone:
                    fails.append(
                        f"기여율 슬러그 소실: {', '.join(gone)}. "
                        "해당 저장소에 접근하지 못했을 가능성이 크다")
                # 의도적으로 줄인 경우(집계 대상 축소 등)에는 사람이 직접
                # 새 stats.json 을 커밋해 기준선을 낮춘 뒤 다시 돌리면 된다.
        except Exception as exc:
            fails.append(f"stats.json 파싱 실패: {exc}")

    # 7) 공백 오류
    if subprocess.run(["git", "diff", "--check", base, "--"]).returncode != 0:
        fails.append("git diff --check 실패 (공백 오류)")

    if fails:
        print("\n[verify] FAIL 검증 실패: PR을 생성하지 않습니다", file=sys.stderr)
        for f in fails:
            print(f"  - {f}", file=sys.stderr)
        return 1
    print("[verify] PASS 전 항목 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
