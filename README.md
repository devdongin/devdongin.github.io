# devdongin.github.io

선동인의 개인 포트폴리오 사이트 — **https://devdongin.github.io**

AI 모델을 C++ 추론 SDK와 클라이언트 소프트웨어에 통합해온 개발 경험을 담았습니다.
실시간 최적화 · Windows 시스템 연동 · 커널 드라이버 · 배포 파이프라인 · 운영 장애 분석까지.

## 무엇으로 만들었나

의존성 없는 **정적 HTML**입니다 — 랜딩(`index.html`)과 갤러리(`gallery.html`) 두 장뿐이고,
빌드 단계도, 프레임워크도, 번들러도 없습니다. CSS·JS는 전부 인라인입니다.

외부로 나가는 요청은 이게 전부입니다:

| 대상 | 어디서 | 시점 |
|---|---|---|
| Pretendard 폰트 CDN | 두 페이지 | 로드 시 |
| Abacus (방문자 카운터) | 랜딩 푸터 | 로드 시 |
| `youtube-nocookie.com` | 히어로 데모·갤러리 | **재생 클릭 후** (그전엔 썸네일만) |

```
index.html          랜딩 페이지 (인라인 CSS/JS)
gallery.html        대외 활동 갤러리
assets/images/      아바타 · 공유 카드 · 갤러리 사진
data/               자동 수집된 통계 · 블로그 피드 (JSON)
scripts/            수집기와 렌더러 (Python)
.github/workflows/  자동 갱신 파이프라인
```

## 스스로 갱신되는 페이지

정적 사이트지만 내용은 고정되어 있지 않습니다. GitHub Actions가 주기적으로 데이터를 다시 모아 페이지에 렌더링합니다.

| 갱신 대상 | 주기 | 방식 |
|---|---|---|
| 커밋 히트맵 · 기여 통계 | 매일 00:30 KST | GitHub API로 전 저장소·전 브랜치 집계 → 결정적 SVG 렌더링 |
| 블로그 최근 글 | 매일 00:30 KST | RSS 수집 → 티커 카드 |
| AI REVIEW | 3시간마다 | Claude Code가 최신 통계를 근거로 3~4줄 평가 재작성 |
| 갤러리 | `gallery/` push 시 | 폴더를 스캔해 카드 재생성 — git이 곧 CMS |

커밋 히트맵은 GitHub 기본 잔디와 다릅니다. 고객사별 코드가 브랜치로 나뉘어 운영되기 때문에,
기본 브랜치만 세는 기본 그래프 대신 **전 브랜치 push를 중복 제거해 집계**합니다.
집계 대상 저장소 목록은 사내 정보라 저장소 시크릿으로만 주입되며, 공개 파일과 로그에는 수치만 남습니다.

## AI 협업 방식

이 저장소는 두 AI 에이전트가 역할을 나눠 관리합니다.

- **Claude Code** — 메인 개발. 콘텐츠·디자인·구현·배포를 담당합니다 (`CLAUDE.md`)
- **Codex** — 리뷰. 리뷰 결과를 GitHub Issue로 남기고, Claude가 처리 후 근거와 함께 종료합니다 (`AGENTS.md`)

서로 다른 모델이 교차 검증하는 구조라, 한쪽이 놓친 사실관계나 접근성 문제가 이슈 트래커에 기록으로 남습니다.

## 로컬에서 보기

빌드가 없으므로 파일을 열기만 하면 됩니다.

```bash
python3 -m http.server 8000
```

---

문의는 [사이트의 Contact 섹션](https://devdongin.github.io/#contact)으로 주세요. [프로필](https://github.com/devdongin) · [블로그](https://he11oworld.tistory.com)
