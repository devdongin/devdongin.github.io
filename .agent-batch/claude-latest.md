# Claude Nightly Implementation

- Run at: 2026-08-17 KST (사용자 대화형 실행)
- Result: implemented P1 and P2, opened a draft PR
- Handoff: `.agent-batch/codex-latest.md`, 이슈 #138 (2026-08-15 23:30 KST 재검토본)
- Baseline: `origin/main` at `7708dac`
- Branch: `claude/138-nightly-hardening`
- Commits: 4 (문서·주기 정리 / Action SHA 고정 / AI REVIEW 압축 / CSP·임베드 하드닝)
- Draft PR: 이슈 #138 연결

## 이전 실행이 막혔던 원인 해소

2026-08-16 기록의 차단 사유는 Claude Code CLI 인증 실패였다. 원인은 구독이 걸려 있던
계정을 바꾸면서 repo secret `CLAUDE_CODE_OAUTH_TOKEN`이 권한을 잃은 것이다.
`update-stats` 워크플로도 같은 이유로 2026-08-17 03:44 UTC 실행부터 실패하고 있다
(직전 성공 00:59 UTC). 실패 로그의 결과 블록이 `num_turns: 1`, `total_cost_usd: 0`,
`is_error: true`로, 작업 시작 전에 거부된 형태다.

**이 PR은 토큰을 고치지 않는다.** 토큰 재발급은 사용자만 할 수 있는 작업이라 별도로 안내했다.
그래서 이 PR을 병합해도 야간 자동 갱신은 secret 교체 전까지 계속 실패한다.

## 구현 항목

### P1 워크플로 (완료)

- `update-stats.yml`: 3시간 크론 제거, 매일 00:30 KST 1회 + `workflow_dispatch`만 남김
- `checkout` v4.4.0, `setup-python` v5.6.0, `claude-code-action` v1.0.193을 커밋 SHA로 고정
  (두 워크플로 전부, first-party 포함). 옆에 사람이 읽을 버전을 주석으로 남김
- `permissions`를 최상위에서 job 스코프로 이동
- `id-token: write` 제거. OAuth 토큰과 `GITHUB_TOKEN`을 직접 넘기고 있어 OIDC 앱 토큰
  교환 경로를 타지 않는다. run 32002798344 로그의 `Revoke app token` 스텝이 skipped다.
  **이 항목만 실행 검증을 못 했다** (secret이 죽어 있어 dispatch 불가). 되돌리려면 한 줄 복구.

### P1 히어로·AI REVIEW (완료)

- 본문을 209자 / 3문장으로 압축. 인용 수치는 150ms→40~50ms와 기여율 71% 둘로 제한
- 태그라인과 겹치는 서술, 모델 구성 상세, 커밋 총계 제거. focus.md 기반 최근 작업 1문장은 유지
- `verify_auto_update.py`에 240자·3문장 상한 추가 (`ai-meta` 제외). 초과 시 자동 병합 차단
- 워크플로 프롬프트에 같은 상한과 태그라인 중복 금지 명시

실측 (헤드리스 Chrome, 각 뷰포트 iframe):

| 뷰포트 | AI REVIEW | hero | CTA top | 판정 |
|---|---|---|---|---|
| 1440x900 | 320px → 199px | 1,073px → 951px | 890px → 769px | 버튼 3개 모두 노출, 아래 여백 80px (목표 24px 이상) |
| 390x844 | 511px → 284px | 1,279px → 1,052px | 955px → 728px | 주 CTA 스크롤 없이 노출 (목표 760px 이전) |

두 뷰포트 모두 가로 오버플로 없음. 두 목표를 압축만으로 충족해서 모바일 `<details>`
분리는 넣지 않았다. 필요하다고 판단되면 지시해 주면 추가한다.

### P2 역할 문서 (완료)

- `AGENTS.md`, `CLAUDE.md`, `README.md`의 역할 분담을 Codex 디자인·리뷰 / Claude 구현으로 교체.
  로컬에만 있던 편집을 origin/main 위로 리베이스해 보존
- 남아 있던 "3시간마다", "3~4줄" 서술을 실제 주기·상한으로 정리 (인쇄 CSS 주석 포함)

### P2 CSP·임베드 (완료)

- `index.html` head에 CSP meta 추가. 관측된 출처만 허용:
  `cdn.jsdelivr.net`(폰트), `abacus.jasoncameron.dev`(카운터 fetch), `youtube-nocookie.com`(영상)
- **`frame-ancestors`는 넣지 않았다.** meta로 전달하면 브라우저가 무시하는 지시어라
  콘솔 경고만 남기고 효력이 없다. 클릭재킹 차단이 필요하면 Pages 앞단 헤더가 필요하다.
- **`connect-src`에 `abacus.jasoncameron.dev`를 추가했다.** Codex 초안의 `connect-src 'self'`를
  그대로 쓰면 방문자 카운터가 차단된다 ("관측된 출처만 조정" 지시에 따른 반영)
- demo facade를 `createElement` + `replaceChildren`로 교체, 11자 허용 문자 패턴 통과 ID만 재생
- `render_gallery.py`의 `YT_ID`가 `\w`라 한글 11자도 통과하던 것을 `[A-Za-z0-9_-]{11}`로 좁힘

검증: securitypolicyviolation 0건, 콘솔 CSP 차단 0건, jsdelivr 스타일시트 로드,
카운터 표시(connect-src 통과), 클릭 전 iframe 0개 → 클릭 후 nocookie 임베드 1개,
`data-yt`에 스크립트 문자열 주입 시 iframe 0개.

## 보류 항목

- **P3 다이버 제거: 보류.** Codex 실행 순서상 마지막이고 "개인 시그니처로 남길 수도 있다"는
  선택지가 함께 제시된 항목이라, 사용자 판단 없이 지우지 않았다. 사용자에게 제거와
  40KB 이하 최적화 유지 중 선택을 요청했다. 에셋 252KB는 그대로다.
- **이슈 #129 (톤앤매너): 착수 못 함.** "혼자 일한 것 같다"는 피드백을 반영하려면 실제 협업
  범위라는 사실 입력이 필요한데, `CLAUDE.md` 절대 규칙 5가 이력서에 없는 경력 창작을 금지한다.
  사용자에게 사실 확인을 요청했다.

## 사용자 확인이 필요한 충돌

`CLAUDE.md`의 2026-08-04 사용자 지시는 "평가문 마지막 1문장을 요즘 하는 일에 배정"인데,
Codex #138은 "최근 작업 상세를 activity 섹션으로 옮기라"고 한다. 둘 다 만족하도록
3문장 중 마지막을 focus.md 기반 최근 작업으로 두되 상세는 덜어내는 형태로 구현했다.
사용자가 다르게 원하면 이 문장을 빼면 된다.
