"""LLM integration module

Provides optional LLM functionality using Google's Gemini API.
"""

from app.llm.client import GeminiClient, analyze_code

__all__ = ["GeminiClient", "analyze_code"]
