# LinkedInAgent
LinkedIn Post Automation Agent

# 🤖 LinkedIn Auto Poster

> AI 기반 LinkedIn 게시물 자동 생성 및 발행 파이프라인

매일 오전 9시, 최신 AI/개발 트렌드를 자동으로 수집·큐레이션·작성·게시하는 **멀티 에이전트 시스템**입니다.

---

## 📌 주요 기능

- **자동 수집** — HuggingFace, Hacker News, TechCrunch RSS 피드에서 최신 글 수집
- **AI 큐레이션** — Claude(Haiku)가 LinkedIn에 적합한 주제 3개 자동 선정
- **AI 초안 작성** — Claude(Sonnet)가 훅·핵심 포인트·해시태그를 포함한 게시물 생성
- **퀄리티 체크** — 길이·해시태그 등 기본 품질 기준 자동 검증 및 재생성
- **자동 발행** — LinkedIn REST API를 통해 링크 카드와 함께 게시
- **일일 스케줄링** — APScheduler로 매일 09:00 KST 자동 실행

---

## 🏗️ 아키텍처

```
[Scheduler] ──매일 09:00──▶ [Pipeline (LangGraph)]
                                     │
                          ┌──────────▼──────────┐
                          │   1. Collector       │  RSS 피드 수집
                          │   2. Curator         │  Claude Haiku 필터링
                          │   3. Drafter         │  Claude Sonnet 작성
                          │   4. Quality Check   │  길이·해시태그 검증
                          │        │                        │
                          │     통과 ──▶ 5. Publisher    실패 ──▶ 3. Drafter (재시도)
                          └─────────────────────┘
```

**LangGraph** 의 `StateGraph`로 각 노드를 연결하며, 퀄리티 체크 실패 시 Drafter 노드로 자동 복귀합니다.

---

## 🗂️ 프로젝트 구조

```
.
├── collector.py      # RSS 피드 수집
├── curator.py        # LLM 기반 주제 선정
├── drafter.py        # LLM 기반 게시물 초안 생성
├── publisher.py      # LinkedIn API 발행
├── pipeline.py       # LangGraph 그래프 정의
├── scheduler.py      # APScheduler 스케줄러
├── get_token.py      # LinkedIn OAuth 토큰 발급 유틸리티
├── logs/
│   └── scheduler.log
└── .env
```

---

## 🛠️ 기술 스택

| 분류 | 기술 |
|------|------|
| AI 모델 | Anthropic Claude (Haiku · Sonnet) |
| 에이전트 오케스트레이션 | LangGraph (`StateGraph`) |
| 스케줄링 | APScheduler (CronTrigger) |
| RSS 파싱 | feedparser |
| 외부 API | LinkedIn REST API (OAuth 2.0) |

---

## ⚙️ 설치 및 실행

### 1. 패키지 설치

```bash
pip install anthropic langgraph feedparser apscheduler requests python-dotenv
```

### 2. 환경 변수 설정

`.env` 파일을 프로젝트 루트에 생성합니다.

```env
ANTHROPIC_API_KEY=your_anthropic_api_key

LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_ACCESS_TOKEN=your_access_token
LINKEDIN_REFRESH_TOKEN=your_refresh_token
```

LinkedIn 토큰은 `get_token.py`를 실행해 OAuth 인증 후 발급받을 수 있습니다.

```bash
python get_token.py
```

### 3. 실행

**즉시 실행 (테스트용)**
```bash
python scheduler.py --now
```

**스케줄러 상시 실행 (매일 09:00 KST)**
```bash
python scheduler.py
```

---

## 🔄 파이프라인 상세 흐름

| 단계 | 노드 | 모델 | 역할 |
|------|------|------|------|
| 1 | `collect_node` | — | RSS 피드에서 최신 글 수집 |
| 2 | `curate_node` | Claude Haiku | 게시 가치 있는 주제 3개 선정 |
| 3 | `draft_node` | Claude Sonnet | 200~300자 LinkedIn 게시물 작성 |
| 4 | `quality_node` | — | 길이·해시태그 품질 검증 |
| 5 | `publish_node` | — | LinkedIn에 링크 카드와 함께 게시 |

퀄리티 체크 기준: 길이 100~700자, 해시태그 1개 이상 포함. 미통과 시 3번 단계로 자동 재시도.

---

## 📋 게시물 생성 규칙

Claude Sonnet에 적용되는 프롬프트 지침:

- 첫 줄: 질문 또는 강한 주장의 훅 문장
- 3~5개 핵심 포인트 (줄바꿈 활용)
- 마지막 줄: 의견 유도 또는 질문
- 해시태그 3~5개
- 전체 길이 200~300자
- 전문적이되 딱딱하지 않은 말투

---

## 📝 로그 예시

```
2025-01-15 09:00:01 [INFO] 파이프라인 시작
2025-01-15 09:00:03 [INFO] [노드 1] 수집 중... → 9개 수집 완료
2025-01-15 09:00:05 [INFO] [노드 2] 주제 선정 중... → 선택된 주제: ...
2025-01-15 09:00:08 [INFO] [노드 3] 게시글 생성 중... → 247자 생성 완료
2025-01-15 09:00:08 [INFO] [노드 4] 퀄리티 체크 중... → 통과
2025-01-15 09:00:10 [INFO] [노드 5] LinkedIn 게시 중... → 게시 성공!
2025-01-15 09:00:10 [INFO] 파이프라인 완료
```

---

## 🔐 보안 참고

`get_token.py`에 포함된 `CLIENT_SECRET` 등 민감 정보는 반드시 `.env`로 분리하고, `.gitignore`에 `.env`를 추가하세요.

```gitignore
.env
logs/
__pycache__/
```
