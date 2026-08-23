"""
Trip planning API router — POST /api/plan-trip with SSE streaming.
"""
import json
import uuid
import asyncio
from typing import AsyncGenerator

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agent.state import TravelAgentState
import database

router = APIRouter()


class PlanTripRequest(BaseModel):
    query: str
    session_id: str | None = None
    conversation_history: list[dict] | None = None


def _serialize_state(state: TravelAgentState) -> dict:
    """Serialize state to JSON-safe dict."""
    return json.loads(state.model_dump_json())


@router.post("/plan-trip")
async def plan_trip(request: PlanTripRequest):
    """
    Run the full travel planning pipeline and return results via SSE stream.
    Each stage emits a JSON event so the frontend can show live progress.
    """
    session_id = request.session_id or str(uuid.uuid4())

    async def event_stream() -> AsyncGenerator[str, None]:
        try:
            # Emit start event
            yield _sse_event("start", {
                "session_id": session_id,
                "message": "🚀 Starting your trip planning...",
                "stage": "init",
            })

            # Run the pipeline
            from agent.state import TravelAgentState
            from agent.nodes.parse_budget import parse_and_allocate_budget
            from agent.nodes.stay_search import stay_search
            from agent.nodes.transport_search import transport_search
            from agent.nodes.local_rentals import local_rentals_search
            from agent.nodes.rank_itinerary import rank_and_build_itinerary
            from agent.nodes.present_packages import present_packages
            from agent.nodes.booking_summary import generate_booking_summary

            state = TravelAgentState(
                raw_query=request.query,
                session_id=session_id,
                conversation_history=request.conversation_history or [],
            )

            # Save initial session in database
            await database.save_session(session_id, f"Trip: {request.query[:35]}")

            # Stage 1: Parse & Budget
            yield _sse_event("stage_start", {"stage": "parsing", "message": "🔍 Parsing your trip request..."})
            state = await parse_and_allocate_budget(state)
            if state.parsed_trip:
                await database.save_session(
                    session_id,
                    f"Trip to {state.parsed_trip.destination} ({state.parsed_trip.duration_days}D)",
                    state.parsed_trip.destination,
                )
            yield _sse_event("stage_done", {
                "stage": "parsing",
                "data": {
                    "parsed_trip": state.parsed_trip.model_dump() if state.parsed_trip else None,
                    "budget_allocation": state.budget_allocation.model_dump() if state.budget_allocation else None,
                },
                "logs": state.stage_logs[-2:],
            })

            # Stage 2: Parallel searches
            yield _sse_event("stage_start", {"stage": "searching", "message": "🔍 Searching hotels, transport & rentals..."})

            stay_state = TravelAgentState(**state.model_dump())
            transport_state = TravelAgentState(**state.model_dump())
            rental_state = TravelAgentState(**state.model_dump())

            stay_result, transport_result, rental_result = await asyncio.gather(
                stay_search(stay_state),
                transport_search(transport_state),
                local_rentals_search(rental_state),
            )

            state.stay_options = stay_result.stay_options
            state.transport_options = transport_result.transport_options
            state.rental_options = rental_result.rental_options

            yield _sse_event("stage_done", {
                "stage": "searching",
                "data": {
                    "stays_count": len(state.stay_options),
                    "transports_count": len(state.transport_options),
                    "rentals_count": len(state.rental_options),
                },
                "logs": [
                    f"Found {len(state.stay_options)} stays",
                    f"Found {len(state.transport_options)} transport options",
                    f"Found {len(state.rental_options)} rentals",
                ],
            })

            # Stage 3: Rank & Build
            yield _sse_event("stage_start", {"stage": "ranking", "message": "🎯 Building personalised itineraries..."})
            state = await rank_and_build_itinerary(state)
            yield _sse_event("stage_done", {
                "stage": "ranking",
                "data": {"packages_count": len(state.ranked_packages)},
                "logs": state.stage_logs[-1:],
            })

            # Stage 4: Present
            yield _sse_event("stage_start", {"stage": "presenting", "message": "📦 Finalising your packages..."})
            state = await present_packages(state)
            yield _sse_event("stage_done", {
                "stage": "presenting",
                "data": {
                    "packages": [p.model_dump() for p in state.presented_packages],
                },
                "logs": state.stage_logs[-1:],
            })

            # Stage 5: Booking Summary
            yield _sse_event("stage_start", {"stage": "booking", "message": "🎉 Preparing booking summary..."})
            state = await generate_booking_summary(state)
            yield _sse_event("stage_done", {
                "stage": "booking",
                "data": {
                    "booking_summary": state.booking_summary.model_dump() if state.booking_summary else None,
                },
                "logs": state.stage_logs[-1:],
            })

            # Save full packages message to database
            packages_data = [p.model_dump() for p in state.presented_packages]
            booking_data = state.booking_summary.model_dump() if state.booking_summary else None
            await database.save_message(
                session_id=session_id,
                message_id=str(uuid.uuid4()),
                role="assistant",
                content=f"Here are your {len(packages_data)} personalised trip packages for {state.parsed_trip.destination if state.parsed_trip else 'your trip'}!",
                msg_type="packages",
                payload={"packages": packages_data, "booking_summary": booking_data},
            )

            # Final complete event
            yield _sse_event("complete", {
                "session_id": session_id,
                "message": "✅ Your trip plan is ready!",
                "full_state": _serialize_state(state),
            })

        except Exception as e:
            yield _sse_event("error", {
                "message": f"Error: {str(e)}",
                "stage": "unknown",
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/modify-trip")
async def modify_trip(request: dict):
    """Apply a modification request to an existing trip plan."""
    session_id = request.get("session_id", str(uuid.uuid4()))
    modification = request.get("modification", "")
    existing_state_data = request.get("state", {})

    if not modification:
        raise HTTPException(status_code=400, detail="Modification request is required.")

    try:
        from agent.state import TravelAgentState
        from agent.nodes.present_packages import present_packages
        from agent.nodes.booking_summary import generate_booking_summary

        state = TravelAgentState(**existing_state_data)
        state.user_modification_request = modification

        state = await present_packages(state)
        state = await generate_booking_summary(state)

        return {
            "session_id": session_id,
            "packages": [p.model_dump() for p in state.presented_packages],
            "booking_summary": state.booking_summary.model_dump() if state.booking_summary else None,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event."""
    return f"data: {json.dumps({'type': event_type, **data})}\n\n"
