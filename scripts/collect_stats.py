#!/usr/bin/env python3
"""전 저장소·전 브랜치 커밋 집계 → data/stats.json

두 계정의 최근 12개월 커밋을 전 저장소·전 브랜치에서 집계한다
(SHA 중복 제거, KST 기준). 표준 라이브러리만 사용한다.

환경변수:
  STATS_TOKEN  - GitHub PAT (스캔 대상 조직/계정 저장소 읽기 권한)
  STATS_CONFIG - JSON 설정. 내부 저장소명이 공개 레포·공개 로그에 남지 않도록
                 반드시 secret으로 주입한다. 형식:
    {
      "authors": ["login1", "login2"],
      "scan": ["org:SomeOrg", "user:someuser"],
      "repo_stats": {"owner/repo": "slug", ...}
    }

  - authors:    author로 인정할 GitHub 계정 로그인
  - scan:       히트맵 집계 대상 (조직 전체 또는 개인 계정 전체)
  - repo_stats: 기본 브랜치 기여 통계(contributors API)를 낼 저장소와
                data/stats.json 에 기록될 공개용 슬러그

출력(data/stats.json)에는 일자별 합계·슬러그별 수치만 남고
저장소 실명은 포함되지 않는다. 로그에도 저장소명을 출력하지 않는다.
"""
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

CACHE_PATH = "data/scan_cache.json"

API = "https://api.github.com"
KST = timezone(timedelta(hours=9))

# data/stats.json 은 public 이므로, 설정 실수로 내부 저장소명이 slug 로
# 흘러들지 않도록 렌더러가 아는 공개 슬러그만 허용한다.
ALLOWED_SLUGS = {"seeuonclient", "culockerfsfd", "cufacesdk", "seeuoncp"}


def gh(token, path, params=None):
    url = API + path
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "devdongin-github-io-stats",
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < 3:
                # 실제 리셋 시각까지 대기 (시간당 한도라 최대 1시간)
                reset = int(e.headers.get("X-RateLimit-Reset", "0"))
                wait = min(max(reset - time.time() + 5, 10), 3700)
                print(f"[collect] rate limited, waiting {int(wait)}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if e.code in (404, 409):  # 접근 불가 / 빈 저장소
                return None
            raise
        except urllib.error.URLError:
            if attempt < 3:
                time.sleep(10)
                continue
            raise
    return None


def gh_paged(token, path, params=None):
    params = dict(params or {}, per_page=100)
    page = 1
    while True:
        params["page"] = page
        data = gh(token, path, params)
        if not data:
            return
        yield from data
        if len(data) < 100:
            return
        page += 1


def main():
    token = os.environ["STATS_TOKEN"]
    config = json.loads(os.environ["STATS_CONFIG"])
    authors = set(config["authors"])

    end = datetime.now(KST).date()
    start = end - timedelta(days=365)
    since_iso = datetime(start.year, start.month, start.day, tzinfo=KST).isoformat()

    repos = []
    for target in config["scan"]:
        kind, name = target.split(":", 1)
        if kind == "org":
            listing = gh_paged(token, f"/orgs/{name}/repos", {"type": "all"})
        else:
            listing = gh_paged(token, f"/users/{name}/repos", {"type": "owner"})
        repos += [(r["full_name"], r.get("pushed_at") or "") for r in listing]

    # 스킵 캐시: 과거 스캔에서 커밋이 한 건도 없던 레포는 제외한다.
    # public 파일이므로 레포명은 sha256 해시로만 기록한다.
    # 캐시를 지우고 커밋하면 전체 레포를 다시 스캔한다.
    try:
        cache = json.load(open(CACHE_PATH, encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        cache = {"repos": {}}

    targets = []
    skipped_cache = skipped_dormant = 0
    for full_name, pushed_at in repos:
        h = hashlib.sha256(full_name.encode()).hexdigest()[:16]
        entry = cache["repos"].get(h)
        if entry and not entry.get("found"):
            skipped_cache += 1
            continue
        if pushed_at:
            pushed = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
            if pushed < datetime(start.year, start.month, start.day, tzinfo=KST):
                # 집계 기간 시작 이후 push가 없으면 새 커밋도 없다
                skipped_dormant += 1
                continue
        targets.append((full_name, h))
    print(f"[collect] {len(repos)} repos listed, scanning {len(targets)} "
          f"(cache-skip {skipped_cache}, dormant-skip {skipped_dormant})", file=sys.stderr)

    daily = {}
    seen = set()
    for i, (repo, h) in enumerate(targets, 1):
        found_before = len(seen)
        for branch in gh_paged(token, f"/repos/{repo}/branches"):
            for author in authors:
                commits = gh_paged(token, f"/repos/{repo}/commits", {
                    "sha": branch["name"], "author": author, "since": since_iso,
                })
                for c in commits:
                    sha = c["sha"]
                    if sha in seen:
                        continue
                    seen.add(sha)
                    iso = c["commit"]["author"]["date"].replace("Z", "+00:00")
                    d = datetime.fromisoformat(iso).astimezone(KST).date()
                    if start <= d <= end:
                        daily[d.isoformat()] = daily.get(d.isoformat(), 0) + 1
        cache["repos"][h] = {
            "found": len(seen) > found_before,
            "scanned_at": datetime.now(KST).isoformat(timespec="seconds"),
        }
        print(f"[collect] repo {i}/{len(targets)} done, {len(seen)} unique commits", file=sys.stderr)

    repo_stats = {}
    for full_name, slug in config.get("repo_stats", {}).items():
        if slug not in ALLOWED_SLUGS:
            sys.exit(f"[collect] error: slug not in allowlist: '{slug}'")
        contribs = list(gh_paged(token, f"/repos/{full_name}/contributors"))
        if not contribs:
            print(f"[collect] warn: no contributor data for slug '{slug}'", file=sys.stderr)
            continue
        total = sum(c["contributions"] for c in contribs)
        mine = sum(c["contributions"] for c in contribs if c.get("login") in authors)
        rank = next((i + 1 for i, c in enumerate(contribs) if c.get("login") in authors), None)
        repo_stats[slug] = {
            "mine": mine,
            "total": total,
            "percent": round(mine / total * 100) if total else 0,
            "rank": rank,
        }

    out = {
        "collected_at": end.isoformat(),
        "window": {"start": start.isoformat(), "end": end.isoformat()},
        "total_commits": sum(daily.values()),
        "daily": dict(sorted(daily.items())),
        "repo_stats": repo_stats,
    }
    os.makedirs("data", exist_ok=True)
    with open("data/stats.json", "w", encoding="utf-8", newline="\n") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
        f.write("\n")
    with open(CACHE_PATH, "w", encoding="utf-8", newline="\n") as f:
        json.dump(cache, f, indent=1, sort_keys=True)
        f.write("\n")
    print(f"[collect] total {out['total_commits']} commits, "
          f"{len(repo_stats)} repo stats -> data/stats.json", file=sys.stderr)


if __name__ == "__main__":
    main()
