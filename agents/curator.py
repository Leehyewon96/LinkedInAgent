# LLM 필터링 노드

import anthropic
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
from collector import collect_rss, RSS_FEEDS

load_dotenv(Path(__file__).parent.parent / ".env")  # 상위 폴더의 .env 읽기

client = anthropic.Anthropic()


def is_valid_url(url: str) -> bool:
    """URL이 실제로 접근 가능한지 확인 (404·연결 오류 제외)"""
    try:
        response = requests.head(
            url,
            timeout=5,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},  # 봇 차단 우회
        )
        return response.status_code < 400
    except requests.RequestException:
        return False


def curate_topics(sources: list[dict]) -> list[dict]:
    content = "\n".join(
        f"- [{s['source']}] {s['title']}\n  {s['summary'][:200]}"
        for s in sources
    )

    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""다음 소스들 중 LinkedIn에 올릴 만한 AI/ML·개발 트렌드 주제 3개를 골라줘.

선택 기준:
- 개발자 커뮤니티에서 화제가 될 만한 것
- 인사이트나 배울 점이 있는 것
- 너무 홍보성이거나 뻔한 내용은 제외

소스 목록:
{content}

아래 JSON 형식으로만 응답해줘 (다른 말 없이):
[
  {{
    "title": "주제 제목",
    "angle": "어떤 관점으로 쓸지 한 줄 설명",
    "source_link": "출처 URL"
  }}
]"""
        }]
    )

    raw = response.content[0].text.strip()

    # 혹시 ```json ... ``` 감싸져 있으면 제거
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    print("Claude 응답 원문:", raw)
    topics = json.loads(raw)

    # 유효한 링크만 남기기
    valid_topics = []
    for topic in topics:
        url = topic.get("source_link", "")
        if is_valid_url(url):
            valid_topics.append(topic)
            print(f"  ✅ 유효: {url}")
        else:
            print(f"  ❌ 무효 (제외): {url}")

    if not valid_topics:
        raise ValueError("유효한 링크가 있는 주제가 없습니다. 수집 소스를 확인해주세요.")

    return valid_topics


if __name__ == "__main__":
    print("수집 중...")
    sources = collect_rss(RSS_FEEDS)
    print(f"{len(sources)}개 수집 완료\n")

    print("주제 선정 중...")
    topics = curate_topics(sources)

    for i, topic in enumerate(topics, 1):
        print(f"\n[{i}] {topic['title']}")
        print(f"  관점: {topic['angle']}")
        print(f"  출처: {topic['source_link']}")