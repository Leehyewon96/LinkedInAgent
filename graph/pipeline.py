# LangGraph 그래프 정의

from typing import TypedDict
from dotenv import load_dotenv
from pathlib import Path
from langgraph.graph import StateGraph, END

load_dotenv(Path(__file__).parent.parent / ".env")

import sys
sys.path.append(str(Path(__file__).parent.parent / "agents"))

from collector import collect_rss, RSS_FEEDS, save_to_history
from curator import curate_topics
from drafter import draft_post
from publisher import post_to_linkedin


# ── State 정의 ────────────────────────────────────────
class AgentState(TypedDict):
    raw_sources: list[dict]
    curated_topics: list[dict]
    selected_topic: dict
    draft_post: str
    quality_passed: bool
    redraft_count: int  # 무한 루프 방지용


# ── 노드 정의 ─────────────────────────────────────────
def collect_node(state: AgentState) -> AgentState:
    print("\n[노드 1] 수집 중...")
    sources = collect_rss(RSS_FEEDS)
    print(f"  → {len(sources)}개 수집 완료")
    return {"raw_sources": sources, "redraft_count": 0}


def curate_node(state: AgentState) -> AgentState:
    print("\n[노드 2] 주제 선정 중...")
    topics = curate_topics(state["raw_sources"])
    selected = topics[0]
    print(f"  → 선택된 주제: {selected['title']}")
    return {
        "curated_topics": topics,
        "selected_topic": selected,
    }


def draft_node(state: AgentState) -> AgentState:
    print("\n[노드 3] 게시글 생성 중...")
    post = draft_post(state["selected_topic"])
    print(f"  → {len(post)}자 생성 완료")
    return {
        "draft_post": post,
        "redraft_count": state.get("redraft_count", 0) + 1,
    }


def quality_node(state: AgentState) -> AgentState:
    print("\n[노드 4] 퀄리티 체크 중...")
    post = state["draft_post"]

    issues = []
    if len(post) < 100:
        issues.append("너무 짧음")
    if len(post) > 700:
        issues.append("너무 김")
    if "#" not in post:
        issues.append("해시태그 없음")

    passed = len(issues) == 0
    if passed:
        print("  → 통과")
    else:
        print(f"  → 실패: {', '.join(issues)}")

    return {"quality_passed": passed}

def publish_node(state: AgentState) -> AgentState:
    print("\n[노드 5] LinkedIn 게시 중...")
    result = post_to_linkedin(
        text=state["draft_post"],
        source_link=state["selected_topic"]["source_link"],
        title=state["selected_topic"]["title"],
        description=state["selected_topic"]["angle"],
        dry_run=False  # 실제 개시
    )
    # 게시 성공 후 출처 URL을 이력에 저장 → 다음 실행 때 중복 제외
    save_to_history(state["selected_topic"]["source_link"])
    print(f"  → {result}")
    return {}


# ── 조건 분기 ─────────────────────────────────────────
def check_quality(state: AgentState) -> str:
    if state["quality_passed"]:
        return "publish"
    elif state.get("redraft_count", 0) >= 3:  # 3회 초과 시 강제 게시
        print("  → 재시도 한도 초과, 강제 게시")
        return "publish"
    else:
        return "redraft"


# ── 그래프 조립 ───────────────────────────────────────
def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("collect", collect_node)
    graph.add_node("curate",  curate_node)
    graph.add_node("draft",   draft_node)
    graph.add_node("quality", quality_node)
    graph.add_node("publish", publish_node)

    graph.set_entry_point("collect")
    graph.add_edge("collect", "curate")
    graph.add_edge("curate",  "draft")
    graph.add_edge("draft",   "quality")
    graph.add_conditional_edges(
        "quality",
        check_quality,
        {
            "publish": "publish",
            "redraft": "draft",  # 퀄리티 실패 시 draft로 돌아감
        }
    )
    graph.add_edge("publish", END)

    return graph.compile()


if __name__ == "__main__":
    app = build_graph()
    app.invoke({})