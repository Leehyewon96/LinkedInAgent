# RSS, GitHub 수집

import feedparser
import json
from pathlib import Path

RSS_FEEDS = [
    "https://huggingface.co/blog/feed.xml",
    "https://hnrss.org/frontpage",
    "https://feeds.feedburner.com/TechCrunch/",
]

HISTORY_FILE = Path(__file__).parent.parent / "posted_links.json"


def load_history() -> set:
    if HISTORY_FILE.exists():
        return set(json.loads(HISTORY_FILE.read_text()))
    return set()


def save_to_history(link: str):
    history = load_history()
    history.add(link)
    HISTORY_FILE.write_text(json.dumps(list(history), ensure_ascii=False, indent=2))


def collect_rss(feeds: list[str]) -> list[dict]:
    history = load_history()
    items = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:10]:  # 3 → 10개: 이미 쓴 글 제외하고도 충분히 확보
            if entry.link in history:
                continue  # 이미 게시한 출처는 스킵
            items.append({
                "title": entry.title,
                "summary": entry.get("summary", "")[:300],
                "link": entry.link,
                "source": feed.feed.get("title", url),
            })
    return items

if __name__ == "__main__":
    sources = collect_rss(RSS_FEEDS)
    for i, item in enumerate(sources, 1):
        print(f"\n[{i}] {item['source']}")
        print(f"  제목: {item['title']}")
        print(f"  요약: {item['summary'][:100]}...")
        print(f"  링크: {item['link']}")