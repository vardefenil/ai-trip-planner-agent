"""
LangGraph StateGraph definition for the AI Travel Planner pipeline.
"""
import asyncio
from typing import TypedDict, Annotated, Any
from langgraph.graph import StateGraph, END

from agent.state import TravelAgentState
from agent.nodes.parse_budget import parse_and_allocate_budget
from agent.nodes.stay_search import stay_search
from agent.nodes.transport_search import transport_search
from agent.nodes.local_rentals import local_rentals_search
from agent.nodes.rank_itinerary import rank_and_build_itinerary
from agent.nodes.present_packages import present_packages
from agent.nodes.booking_summary import generate_booking_summary


# ────────────────────────────────────────────────────────────
# Adapter: convert Pydantic model to/from dict for LangGraph
# ────────────────────────────────────────────────────────────

def state_to_dict(state: TravelAgentState) -> dict:
    return state.model_dump()


def dict_to_state(d: dict) -> TravelAgentState:
    return TravelAgentState(**d)


# ────────────────────────────────────────────────────────────
# Node wrappers (LangGraph nodes work with dicts)
# ────────────────────────────────────────────────────────────

async def _node_parse_budget(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await parse_and_allocate_budget(state)
    return state_to_dict(result)


async def _node_stay_search(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await stay_search(state)
    return state_to_dict(result)


async def _node_transport_search(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await transport_search(state)
    return state_to_dict(result)


async def _node_local_rentals(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await local_rentals_search(state)
    return state_to_dict(result)


async def _node_rank_itinerary(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await rank_and_build_itinerary(state)
    return state_to_dict(result)


async def _node_present_packages(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await present_packages(state)
    return state_to_dict(result)


async def _node_booking_summary(state_dict: dict) -> dict:
    state = dict_to_state(state_dict)
    result = await generate_booking_summary(state)
    return state_to_dict(result)


# ────────────────────────────────────────────────────────────
# Combined parallel search node (runs all 3 searches together)
# ────────────────────────────────────────────────────────────

async def _node_parallel_searches(state_dict: dict) -> dict:
    """Run stay, transport, and rental searches in parallel."""
    state = dict_to_state(state_dict)
    state.current_stage = "parallel_search"
    state.stage_logs.append("🔍 Running parallel searches...")

    # Run all three searches concurrently
    stay_task = stay_search(TravelAgentState(**state.model_dump()))
    transport_task = transport_search(TravelAgentState(**state.model_dump()))
    rentals_task = local_rentals_search(TravelAgentState(**state.model_dump()))

    stay_result, transport_result, rentals_result = await asyncio.gather(
        stay_task, transport_task, rentals_task
    )

    # Merge results back
    state.stay_options = stay_result.stay_options
    state.transport_options = transport_result.transport_options
    state.rental_options = rentals_result.rental_options
    state.stage_logs.extend(stay_result.stage_logs[-1:])
    state.stage_logs.extend(transport_result.stage_logs[-1:])
    state.stage_logs.extend(rentals_result.stage_logs[-1:])

    return state_to_dict(state)


# ────────────────────────────────────────────────────────────
# Build the graph
# ────────────────────────────────────────────────────────────

def build_travel_graph() -> StateGraph:
    """Build and compile the travel planning LangGraph pipeline."""
    graph = StateGraph(dict)

    # Add nodes
    graph.add_node("parse_budget", _node_parse_budget)
    graph.add_node("parallel_searches", _node_parallel_searches)
    graph.add_node("rank_itinerary", _node_rank_itinerary)
    graph.add_node("present_packages", _node_present_packages)
    graph.add_node("booking_summary", _node_booking_summary)

    # Define edges (linear pipeline)
    graph.set_entry_point("parse_budget")
    graph.add_edge("parse_budget", "parallel_searches")
    graph.add_edge("parallel_searches", "rank_itinerary")
    graph.add_edge("rank_itinerary", "present_packages")
    graph.add_edge("present_packages", "booking_summary")
    graph.add_edge("booking_summary", END)

    return graph.compile()


# Singleton compiled graph
_compiled_graph = None


def get_travel_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_travel_graph()
    return _compiled_graph


# ────────────────────────────────────────────────────────────
# Main entry point
# ────────────────────────────────────────────────────────────

async def run_travel_pipeline(
    raw_query: str,
    session_id: str = "",
    conversation_history: list[dict] = None,
) -> TravelAgentState:
    """
    Run the full travel planning pipeline.
    Returns the final TravelAgentState with all packages and booking summary.
    """
    graph = get_travel_graph()

    initial_state = TravelAgentState(
        raw_query=raw_query,
        session_id=session_id,
        conversation_history=conversation_history or [],
    )

    result_dict = await graph.ainvoke(state_to_dict(initial_state))
    return dict_to_state(result_dict)
