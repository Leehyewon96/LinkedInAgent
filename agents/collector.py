# RSS, GitHub 수집

import feedparser

RSS_FEEDS = [
    "https://huggingface.co/blog/feed.xml",
    "https://hnrss.org/frontpage",
    "https://feeds.feedburner.com/TechCrunch/",
]

def collect_rss(feeds: list[str]) -> list[dict]:
    items = []
    for url in feeds:
        feed = feedparser.parse(url)
        for entry in feed.entries[:3]:
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