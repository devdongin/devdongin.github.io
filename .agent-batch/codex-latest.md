# Codex Daily Design and Security Review

- Reviewed at: 2026-08-15 23:30 KST
- Production: https://devdongin.github.io/
- Code baseline: `origin/main` at `40c7d6f` after PR #146
- Local-state note: local `main` is behind current `origin/main` and already has unrelated edits in `AGENTS.md`, `CLAUDE.md`, `README.md`, and `.github/workflows/update-stats.yml`; this review did not modify or discard them.
- Image generation: not used. The material improvements are hierarchy, copy length, workflow hardening, and asset reduction; a new raster asset would add weight without solving them.

## Summary

No P0 issue was found. No prohibited phone number, address, salary, birth year, GPA, customer name, internal repository name, or misplaced email was found in the current public page. The page has no horizontal overflow at 390px or 1440px, and visible images, buttons, and links have accessible names.

Two P1 items should be handled before routine visual polish: the production workflow still runs and auto-merges AI-authored changes every three hours with mutable third-party Action tags, and the AI REVIEW pushes the primary CTA below the first viewport at both tested sizes. No Claude implementation PR was created after the previous review. Eight more automated AI update PRs (#139 through #146) merged instead.

## Findings

### P1: Pin all write-capable Actions and reduce the AI update cadence before the next autonomous merge

Evidence:

- `.github/workflows/update-stats.yml:12-20` schedules both the 00:30 KST run and a three-hour run, while granting `contents: write`, `pull-requests: write`, and `id-token: write`.
- `.github/workflows/update-stats.yml:32-35,72-79` references `actions/checkout@v4`, `actions/setup-python@v5`, and `anthropics/claude-code-action@v1` by mutable major-version tags. The Claude action receives both `CLAUDE_CODE_OAUTH_TOKEN` and the write-capable `GITHUB_TOKEN`.
- `.github/workflows/update-stats.yml:128-152` creates and automatically merges the resulting PR with no human approval.
- `.github/workflows/update-gallery.yml:25-27` also uses mutable Action tags in a write-capable job.
- Remote history now contains sixteen automated update merges between PR #130 and #146 after the last non-automation merge, including eight new merges since the 2026-08-14 review. This confirms that the intended once-daily cadence is not active on `origin/main`.

Impact:

- A compromised or retagged third-party Action can execute with repository-write privileges and access supplied credentials. The automatic merge path raises the consequence of that dependency compromise.
- Three-hour AI rewrites create unnecessary repository churn and directly caused the oversized hero copy reviewed below.

Required implementation:

1. Change the stats workflow to one daily scheduled run at 00:30 KST; retain `workflow_dispatch` for manual recovery.
2. Pin every Action to a reviewed full commit SHA, including first-party Actions. Keep a comment with the human-readable release tag beside each SHA.
3. Keep permissions at job scope and only as broad as required. Confirm whether `id-token: write` is still required when an OAuth token is explicitly supplied; remove it if the pinned action does not require it.
4. Preserve `verify_auto_update.py` and the PR route. Add a maximum AI REVIEW text length or sentence-count gate so a valid but visually destructive rewrite cannot auto-merge.

Verification:

- Workflow has one scheduled trigger per day plus manual dispatch.
- `git grep` finds no `uses: ...@vN`, `@main`, `@master`, or `@latest` in `.github/workflows`.
- A dry run updates only allowed marker/data files, passes the verifier, creates one PR, and does not expose secret values in logs.

### P1: Restore first-viewport hierarchy by making AI REVIEW a short proof, not a second introduction

Evidence:

- `index.html:1089-1099` repeats the hero positioning, performance figure, pipeline inventory, contribution percentage, total commits, Windows systems experience, current macOS work, and update metadata in one block.
- `index.html:834-844` keeps the entire review expanded on mobile and places actions after it.
- Repeated real-browser measurements at 1440x900: hero height 1,073px, AI REVIEW height 320px, and CTA top 890px. The primary CTA begins at the viewport edge and is effectively below the fold.
- Repeated real-browser measurements at 390x844: hero height 1,279px, AI REVIEW height 511px, and CTA top 955px. The visitor sees none of the actions in the first viewport.

Impact:

- The ten-second HR scan loses the intended next action. The auto-generated proof visually outweighs the human-authored positioning statement.
- On mobile, more than 60% of the viewport height is consumed by the review card before any CTA appears.

Design specification:

1. Desktop AI REVIEW: maximum 3 visual lines of body copy plus one metadata line. Target 180-240 Korean characters, two evidence sentences after the bold thesis, and at most two quantitative proofs.
2. Mobile: show the same short thesis and one strongest proof by default. Put remaining evidence in a native `<details>` labeled `평가 근거 보기`; keep the CTA group before the expandable evidence.
3. Remove content already stated in the tagline. Recommended proof set: 150ms to 40-50ms and one contribution/commit statistic. Move current-work detail to the activity section.
4. Desktop acceptance target at 1440x900: all three hero actions fully visible with at least 24px below them. Mobile target at 390x844: the primary action is visible without scrolling, or at worst begins before 760px.
5. Extend `scripts/verify_auto_update.py:105-114` with maximum plain-text length and sentence-count checks in addition to the existing minimum-length check.

Verification:

- Capture fresh 1440x900 and 390x844 screenshots after the generated text settles.
- Measure `.hero-actions` top and `.ai-review-box` height in both viewports against the targets above.
- Confirm keyboard focus reaches the primary CTA before any collapsed evidence control.

### P2: Add a realistic static-site CSP and remove string-built iframe markup

Evidence:

- Production response headers include HSTS but no `Content-Security-Policy`.
- `index.html:34-36` loads CSS from jsDelivr; `index.html:1740-1748` injects a YouTube iframe using `innerHTML` and an unvalidated `data-yt` string.
- The current `data-yt` value is author-controlled and no immediate exploit was demonstrated, so this is defense in depth rather than an active vulnerability.

Required implementation:

1. Add a `<meta http-equiv="Content-Security-Policy">` suitable for GitHub Pages. Start from `default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; img-src 'self' data:; font-src 'self' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline'; frame-src https://www.youtube-nocookie.com; connect-src 'self'` and adjust only for observed required origins.
2. Validate YouTube IDs with an exact 11-character allowlist pattern before use.
3. Replace `frame.innerHTML` with `document.createElement('iframe')` and property assignment.
4. Longer term, self-host Pretendard to remove the runtime CDN dependency and tighten `style-src`/`font-src`.

Verification:

- Browser console has no CSP violations during initial load and after manually starting the demo.
- Invalid `data-yt` values produce no iframe.
- YouTube is still not contacted before user activation.

### P2: Publish the new role and once-daily operating rules to the remote source of truth

Evidence:

- The local worktree contains newer role/cadence edits, but `origin/main` still describes Claude as the design owner and the AI REVIEW as a three-hour process in `AGENTS.md`, `CLAUDE.md`, `README.md`, and `.github/workflows/update-stats.yml`.
- A clean nightly worker or GitHub-hosted workflow reads `origin/main`, not this machine's uncommitted files.

Required implementation:

1. Rebase or otherwise reconcile the existing local documentation/workflow edits with current `origin/main` without discarding unrelated work.
2. Publish them through a dedicated PR. Resolve conflicts using the newer rule: Codex owns design direction, image decisions, and security/implementation review; Claude implements the handoff.
3. Make the public AI metadata say `매일` rather than `3시간마다` once the workflow cadence is changed.

Verification:

- A fresh clone of `main` contains the new role assignment and once-daily wording.
- Production metadata matches the actual schedule.

### P3: Remove or substantially reduce the decorative diver payload

Evidence:

- `index.html:1050-1061` and `assets/diver/diver-animation.css` add a small floating pixel diver that is visually unrelated to the otherwise restrained professional system.
- The three diver sprite sheets total about 248KB in the repository, while the visible desktop sprite is small and absent below 860px.
- In the 1440px render it competes with the avatar and navigation without encoding portfolio information.

Recommendation:

- Prefer removing it. If it is retained as a personal signature, use one optimized idle asset under 40KB, disable it for reduced motion, keep it outside the hero's reading path, and load it after the main content.

Verification:

- Confirm the hero still has a clear focal path with the sprite enabled and disabled.
- Compare transferred asset bytes and largest-content timing before and after.

## Claude implementation order

1. P1 workflow pinning and once-daily cadence.
2. P1 hero/AI REVIEW compression plus verifier limit.
3. P2 role-document publication and CSP/iframe hardening.
4. P3 diver removal only after the first three items pass desktop and mobile checks.
