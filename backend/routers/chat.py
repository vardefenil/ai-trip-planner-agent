"""
Chat API router — conversational AI assistant for travel Q&A.
"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from agent.tools.gemini_client import gemini_chat

router = APIRouter()

YATRA_SYSTEM_PROMPT = """You are Yatra AI 🌏, an expert Indian travel planning assistant. 

You help users:
1. Plan amazing trips across India (Goa, Manali, Kerala, Rajasthan, Ladakh, Andaman, etc.)
2. Answer travel questions (visas, weather, budget, packing, safety)
3. Suggest destinations based on budget and preferences
4. Explain what's in their trip packages
5. Help modify their trip plans

Your personality:
- Warm, enthusiastic, and knowledgeable
- Uses travel emojis naturally 🏖️🏔️🚂✈️
- Gives specific, actionable advice (not generic)
- Knows Indian geography, culture, cuisine, and travel logistics
- Speaks in natural conversational English (with occasional Hindi words)
- Always mentions budget considerations (₹ INR)

When a user describes a trip they want to plan, encourage them to use specific phrases like:
"Plan a 5-day Goa trip for 2 people with ₹30,000 budget"
This helps the AI generate the best package for them.

For general questions, answer directly and helpfully.
"""


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    conversation_history: list[dict] | None = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    is_trip_request: bool
    suggested_query: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Handle a conversational chat message.
    Returns an AI response and flags if the message is a trip planning request.
    """
    session_id = request.session_id or str(uuid.uuid4())
    history = request.conversation_history or []

    # Detect if this is a trip planning request
    is_trip_request = _is_trip_planning_request(request.message)
    suggested_query = None

    if is_trip_request:
        # Help user format a good trip request
        suggested_query = await _extract_trip_query(request.message, history)

    try:
        response_text = await gemini_chat(
            conversation_history=history,
            user_message=request.message,
            system_prompt=YATRA_SYSTEM_PROMPT,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")

    return ChatResponse(
        response=response_text,
        session_id=session_id,
        is_trip_request=is_trip_request,
        suggested_query=suggested_query,
    )


def _is_trip_planning_request(message: str) -> bool:
    """Detect if the message is a trip planning request."""
    trip_keywords = [
        "plan", "trip", "travel", "visit", "go to", "budget",
        "days", "nights", "book", "package", "itinerary",
        "goa", "manali", "kerala", "rajasthan", "ladakh",
        "₹", "rs.", "rupees", "lakh", "thousand",
        "holiday", "vacation", "tour",
    ]
    message_lower = message.lower()
    matches = sum(1 for kw in trip_keywords if kw in message_lower)
    return matches >= 2


async def _extract_trip_query(message: str, history: list[dict]) -> str | None:
    """Try to extract/format a structured trip query from the message."""
    try:
        from agent.tools.gemini_client import gemini_generate
        prompt = f"""
The user said: "{message}"

If this is a travel planning request, rewrite it as a clear, structured trip planning query.
Format: "[destination] trip for [N] people, [N] days, budget ₹[amount]"

If key details are missing (destination, budget, or duration), return null.
Return ONLY the formatted query string or the word "null". No explanation.
"""
        result = await gemini_generate(prompt)
        result = result.strip().strip('"')
        if result.lower() == "null" or not result:
            return None
        return result
    except Exception:
        return None
