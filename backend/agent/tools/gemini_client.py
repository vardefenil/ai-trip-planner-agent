"""
Google Gemini API client wrapper with resilient automatic model fallback.
"""
import os
import json
import re
import logging
from typing import Any, Optional, List
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Try finding .env file in backend/ or root
_backend_env = Path(__file__).resolve().parent.parent.parent / ".env"
if _backend_env.exists():
    load_dotenv(_backend_env)
else:
    load_dotenv(find_dotenv())
load_dotenv()

logger = logging.getLogger(__name__)

# Fallback candidate models in order of priority
CANDIDATE_MODELS = [
    os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite"),
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-flash-latest",
    "gemma-4-31b-it",
    "gemini-3.1-pro-preview",
]
# Remove duplicates while preserving order
_UNIQUE_MODELS = list(dict.fromkeys(CANDIDATE_MODELS))
_working_model_name: Optional[str] = None


def _get_api_key() -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set. Please add it to your backend/.env file.")
    return api_key


def get_gemini_client(model_name: Optional[str] = None) -> genai.GenerativeModel:
    """Returns a Gemini client configured with the specified or current working model."""
    global _working_model_name
    api_key = _get_api_key()
    genai.configure(api_key=api_key)

    chosen_model = model_name or _working_model_name or _UNIQUE_MODELS[0]
    return genai.GenerativeModel(
        model_name=chosen_model,
        generation_config=genai.GenerationConfig(
            temperature=0.7,
            top_p=0.95,
            max_output_tokens=8192,
        ),
    )


import asyncio


async def gemini_generate(prompt: str, system_prompt: Optional[str] = None) -> str:
    """
    Generate a response from Gemini with automatic fallback across available models.
    """
    global _working_model_name
    full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

    # Start with the working model if known, else iterate through candidates
    models_to_try = [_working_model_name] if _working_model_name else []
    models_to_try += [m for m in _UNIQUE_MODELS if m != _working_model_name]

    last_err = None
    for model_name in models_to_try:
        try:
            client = get_gemini_client(model_name=model_name)
            # Run in worker thread to prevent blocking FastAPI asyncio loop
            response = await asyncio.to_thread(client.generate_content, full_prompt)
            if response and response.text:
                _working_model_name = model_name
                return response.text
        except Exception as e:
            logger.warning(f"Gemini model '{model_name}' failed: {e}. Trying fallback...")
            last_err = e
            continue

    raise RuntimeError(f"All Gemini models failed. Last error: {last_err}")


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
    Multi-turn conversation with Gemini with automatic model fallback.
    conversation_history: list of {"role": "user"|"model", "content": "..."}
    """
    global _working_model_name
    api_key = _get_api_key()
    genai.configure(api_key=api_key)

    default_system = (
        "You are Yatra AI, a friendly and knowledgeable Indian travel planning assistant. "
        "You help users plan amazing trips across India. You speak naturally and conversationally. "
        "You know about Goa beaches, Himalayan treks, Kerala backwaters, Rajasthan forts, and more. "
        "When planning trips, you consider budget, duration, traveler count, and vibe. "
        "You respond in a warm, helpful, and enthusiastic manner."
    )

    models_to_try = [_working_model_name] if _working_model_name else []
    models_to_try += [m for m in _UNIQUE_MODELS if m != _working_model_name]

    history = [
        {
            "role": "model" if msg.get("role") in ["model", "assistant"] else "user",
            "parts": [str(msg.get("content", ""))],
        }
        for msg in conversation_history
        if msg.get("content")
    ]

    last_err = None
    for model_name in models_to_try:
        try:
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system_prompt or default_system,
            )
            chat = model.start_chat(history=history)
            response = await asyncio.to_thread(chat.send_message, user_message)
            if response and response.text:
                _working_model_name = model_name
                return response.text
        except Exception as e:
            logger.warning(f"Gemini chat model '{model_name}' failed: {e}. Trying fallback...")
            _working_model_name = None
            last_err = e
            continue

    raise RuntimeError(f"All Gemini chat models failed. Last error: {last_err}")


