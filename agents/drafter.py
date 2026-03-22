# 게시글 생성 노드

# agents/drafter.py
import anthropic
import json
from dotenv import load_dotenv
from pathlib import Path
from collector import collect_rss, RSS_FEEDS
from curator import curate_topics

load_dotenv(Path(__file__).parent.parent / ".env")

client = anthropic.Anthropic()

def draft_post(topic: dict) -> str:
    response = client.messages.create(
        model="claude-sonnet-4-5",  # 글쓰기는 Sonnet
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""다음 주제로 LinkedIn 게시글을 작성해줘.

주제: {topic['title']}
관점: {topic['angle']}
출처: {topic['source_link']}

작성 규칙:
- 첫 줄은 눈에 띄는 훅 문장 (질문이나 강한 주장)
- 3~5개 핵심 포인트를 짧게 (줄바꿈 활용)
- 마지막엔 질문이나 의견 유도 문장
- 해시태그 3~5개
- 전체 길이 200~300자
- 말투는 전문적이되 딱딱하지 않게

게시글만 출력해줘 (설명이나 부가 말 없이):"""
        }]
    )
    return response.content[0].text.strip()


if __name__ == "__main__":
    print("수집 중...")
    sources = collect_rss(RSS_FEEDS)

    print("주제 선정 중...")
    topics = curate_topics(sources)

    print("게시글 초안 생성 중...\n")
    for i, topic in enumerate(topics, 1):
        post = draft_post(topic)
        print(f"{'='*50}")
        print(f"[초안 {i}] {topic['title']}")
        print(f"{'='*50}")
        print(post)
        print()