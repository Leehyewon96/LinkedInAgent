# LLM 필터링 노드

import anthropic
import json
import requests
from dotenv import load_dotenv
from pathlib import Path
from collector import collect_rss, RSS_FEEDS

load_dotenv(Path(__file__).parent.parent / ".env")

client = anthropic.Anthropic()


def is_valid_url(url: str) -> bool:
    try:
        response = requests.head(
            url,
            timeout=5,
            allow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        return response.status_code < 400
    except requests.RequestException:
        return False


def curate_topics(sources: list[dict]) -> list[dict]:
    # 인덱스 번호와 함께 전달 — Claude는 번호만 고르면 됨
    content = "\n".join(
        f"[{i}] [{s['source']}] {s['title']}\n    {s['summary'][:200]}"
        for i, s in enumerate(sources)
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
    "index": 소스_번호,
    "angle": "어떤 관점으로 쓸지 한 줄 설명"
  }}
]"""
        }]
    )

    raw = response.content[0].text.strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]

    print("Claude 응답 원문:", raw)
    picks = json.loads(raw)

    # 인덱스로 원본 소스에서 링크를 직접 가져옴 → hallucination 원천 차단
    topics = []
    for pick in picks:
        idx = pick["index"]
        source = sources[idx]
        url = source["link"]  # RSS에서 수집한 실제 URL 그대로 사용

        if not is_valid_url(url):
            print(f"  ❌ 무효 (제외): {url}")
            continue

        topics.append({
            "title": source["title"],
            "angle": pick["angle"],
            "source_link": url,  # collector의 link와 동일한 값 → 히스토리 매칭 보장
        })
        print(f"  ✅ 유효: {url}")

    if not topics:
        raise ValueError("유효한 링크가 있는 주제가 없습니다. 수집 소스를 확인해주세요.")

    return topics


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