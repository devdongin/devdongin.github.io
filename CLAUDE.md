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

## 작업 후 필수: 3자 관점 리뷰

모든 의미 있는 변경 후, 랜딩 페이지의 **디자인·전체 화면·내용을 제3자 관점에서 리뷰**한다. 특히 다음 두 페르소나를 반드시 적용한다:

- **기업 HR 관점** — 10초 스캔에서 핵심(누구인지, 뭘 잘하는지, 증거)이 잡히는가. 신뢰를 깎는 요소(오타, 과장, 어색한 문구, 빈약한 섹션)는 없는가. 연락 동선이 명확한가.
- **CTO/개발 리더 관점** — 기술 주장에 증거가 따라붙는가(커밋 수치, MS 등재, 납품 실적). 기술 용어가 정확한가. 깊이를 보여주는 디테일과 나열식 스택 사이의 균형. 코드 품질 신호(사이트 자체의 HTML/CSS 품질 포함).

리뷰는 데스크톱·모바일 양쪽 렌더링을 실제로 확인하고, 발견 사항은 사소한 것까지 기록 후 수정한다. 수정 → 재리뷰를 반복해 지적 사항이 나오지 않을 때까지 진행하는 것을 기본으로 한다.

## 개인화

이 계정의 Claude는 사용자(선동인)에 대해 축적된 개인 설정·메모리(경력, 강점, 계정 구조, 승인된 공개 범위)를 이 포트폴리오 업데이트에 적극 활용한다.

## 배포

- `main` 푸시 → GitHub Pages 자동 배포 (약 30초~2분).
- remote는 개인 계정 SSH 별칭 사용: `git@github.com-devdongin:devdongin/devdongin.github.io.git`
- 커밋 author: `devdongin <devdongin@users.noreply.github.com>` (repo-local 설정 완료).
- 배포 후 `curl -s https://devdongin.github.io | grep <새 콘텐츠>` 로 반영 확인.
