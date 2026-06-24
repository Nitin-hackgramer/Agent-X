from langgraph.graph import StateGraph, END
from nodes.research import research_node
from nodes.generate import generate_node
from nodes.approval import approval_node
from state import AgentState

MAX_RETRIES = 3


def should_retry(state: AgentState) -> str:
    if state["approval_status"] == "approved":
        return "end"
    if state.get("retry_count", 0) >= MAX_RETRIES:
        return "end"          # give up after repeated rejections
    return "research"         # re-research using the rejection feedback


graph = StateGraph(AgentState)

graph.add_node("research", research_node)
graph.add_node("generate", generate_node)
graph.add_node("approval", approval_node)

graph.set_entry_point("research")
graph.add_edge("research", "generate")
graph.add_edge("generate", "approval")
graph.add_conditional_edges("approval", should_retry, {
    "research": "research",
    "end": END,
})
