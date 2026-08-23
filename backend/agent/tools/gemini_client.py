"""
Google Gemini API client wrapper.
"""
import os
import json
import re
from typing import Any, Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

_gemini_client = None


def get_gemini_client() -> genai.GenerativeModel:
    """Returns a singleton Gemini client."""
    global _gemini_client
    if _gemini_client is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY not set. Please add it to your .env file."
            )
        genai.configure(api_key=api_key)
        _gemini_client = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config=genai.GenerationConfig(
                temperature=0.7,
                top_p=0.95,
                max_output_tokens=8192,
            ),
        )
    return _gemini_client


async def gemini_generate(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Generate a response from Gemini given a prompt.
    Returns the text content.
    """
    client = get_gemini_client()
    full_prompt = prompt
    if system_prompt:
        full_prompt = f"{system_prompt}\n\n{prompt}"

    response = client.generate_content(full_prompt)
    return response.text


async def gemini_generate_json(prompt: str, system_prompt: Optional[str] = None) -> Any:
    """
    Generate a JSON response from Gemini.
    Extracts and parses the JSON block from the response.
    """
    json_system = (
        "You are a helpful AI assistant. Always respond with valid JSON only. "
        "No markdown, no explanation, just the raw JSON object or array."
    )
    if system_prompt:
        json_system = system_prompt + "\n\nAlways respond with valid JSON only. No markdown code blocks, no explanation."

    text = await gemini_generate(prompt, json_system)

    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
        text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to extract JSON from text
        match = re.search(r"(\{.*\}|\[.*\])", text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise ValueError(f"Gemini did not return valid JSON. Response: {text[:500]}")


async def gemini_chat(
    conversation_history: list[dict[str, str]],
    user_message: str,
    system_prompt: Optional[str] = None,
) -> str:
    """
    Multi-turn conversation with Gemini.
    conversation_history: list of {"role": "user"|"model", "content": "..."}
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set.")
    genai.configure(api_key=api_key)

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_prompt or (
            "You are Yatra AI, a friendly and knowledgeable Indian travel planning assistant. "
            "You help users plan amazing trips across India. You speak naturally and conversationally. "
            "You know about Goa beaches, Himalayan treks, Kerala backwaters, Rajasthan forts, and more. "
            "When planning trips, you consider budget, duration, traveler count, and vibe. "
            "You respond in a warm, helpful, and enthusiastic manner."
        ),
    )

    # Build chat history
    history = []
    for msg in conversation_history:
        history.append({
            "role": msg["role"],
            "parts": [msg["content"]],
        })

    chat = model.start_chat(history=history)
    response = chat.send_message(user_message)
    return response.text
