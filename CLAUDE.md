# CLAUDE.md — devdongin.github.io

선동인의 개인 포트폴리오 사이트. GitHub Pages 정적 호스팅, 단일 `index.html` (외부 의존성은 Pretendard 폰트 CDN 하나).

## 에이전트 역할 분담

- **Claude Code — 메인 개발 담당.** 콘텐츠 작성, 디자인, 구현, 커밋, 배포까지 수행한다.
- **Codex — 리뷰 담당.** 코드를 직접 수정하지 않고 리뷰만 한다 (상세 규칙은 `AGENTS.md`).
- Claude는 의미 있는 변경(콘텐츠 추가, 구조 변경) 후 Codex 리뷰를 받을 수 있도록 커밋을 작게 유지한다.

## 절대 규칙

1. **이름 표기는 "선동인"** — "손동인"은 오기. (macOS 계정명 sundongin에서 유추하지 말 것)
2. **민감 정보 게시 금지**: 전화번호, 집주소, 연봉/희망연봉, 출생연도/나이, 학점.
3. 이메일 `devdongin@gmail.com`은 **Contact 섹션에만** 노출.
4. 공개 범위 (2026-07-30 사용자 승인): POC 고객사 실명, 스크린 캡처 방지 기법명(API 후킹·DLL 인젝션), 커밋 기여 통계, 매출 기여 수치는 게시 허용.
5. 이력서/사실에 없는 수치·경력을 창작하지 말 것.

## 디자인 시스템

- 색상은 반드시 `:root` CSS 변수만 사용 (`--accent`, `--green-dim`, `--on-accent` 등). 리터럴 색상 하드코딩 금지.
- 컴포넌트 재사용 우선: `.skill-card`, `.project`, `.badge`, `.chip`, `.timeline`, `.stack`, `.edu-grid`.
- 스크롤 애니메이션은 새 요소에 `class="reveal"`만 부여 (IntersectionObserver가 처리, JS 수정 불필요).
- 섹션 배경 교차 유지: 기본 → `.alt` → 기본 → `.alt`.
- 아바타는 `login_avatar.jpg`(실제 미모지), 파비콘은 `memoji.svg`.

## 배포

- `main` 푸시 → GitHub Pages 자동 배포 (약 30초~2분).
- remote는 개인 계정 SSH 별칭 사용: `git@github.com-devdongin:devdongin/devdongin.github.io.git`
- 커밋 author: `devdongin <devdongin@users.noreply.github.com>` (repo-local 설정 완료).
- 배포 후 `curl -s https://devdongin.github.io | grep <새 콘텐츠>` 로 반영 확인.
