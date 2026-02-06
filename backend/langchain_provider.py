"""
Optional LangChain-based LLM provider for post/reply generation.
Enable with USE_LANGCHAIN=1. Uses the same prompts and sanitization as llm_provider.
"""

from __future__ import annotations

import os
from typing import Any

from schemas import Post, User

# Reuse sanitize and prompt builder from main provider
from llm_provider import _build_system_prompt, _sanitize


def _invoke_langchain_openai(system: str, content: str, model: str) -> tuple[str, str | None]:
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        return "", "LangChain OpenAI not installed (pip install langchain-openai)."
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return "", None
    try:
        llm = ChatOpenAI(
            model=model,
            api_key=key,
            temperature=0.8,
            max_tokens=150,
        )
        messages = [SystemMessage(content=system), HumanMessage(content=content)]
        msg = llm.invoke(messages)
        text = (getattr(msg, "content", None) or "").strip()
        return (_sanitize(text), None) if text else ("", "LangChain OpenAI returned empty.")
    except Exception as e:
        return "", f"LangChain OpenAI: {str(e)[:150]}"


def _invoke_langchain_gemini(system: str, content: str, model: str) -> tuple[str, str | None]:
    try:
        from langchain_core.messages import HumanMessage
        from langchain_google_genai import ChatGoogleGenerativeAI
    except ImportError:
        return "", "LangChain Google GenAI not installed (pip install langchain-google-genai)."
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return "", None
    try:
        llm = ChatGoogleGenerativeAI(
            model=model,
            google_api_key=key,
            temperature=0.8,
            max_output_tokens=150,
        )
        full = f"{system}\n\nUser request: {content}"
        msg = llm.invoke([HumanMessage(content=full)])
        text = (getattr(msg, "content", None) or "").strip()
        return (_sanitize(text), None) if text else ("", "LangChain Gemini returned empty.")
    except Exception as e:
        return "", f"LangChain Gemini: {str(e)[:150]}"


def generate_post(user: User, context: list[Post] | None = None) -> tuple[str, str | None]:
    """Generate a tweet using LangChain (OpenAI then Gemini fallback)."""
    prompt = "Generate one new tweet that this user might post now. Keep it short and in character."
    extra = ""
    if context:
        recent = context[-5:]
        lines = [f"- {p.text[:100]}..." if len(p.text) > 100 else f"- {p.text}" for p in recent]
        extra = "Recent posts from the network (for tone only):\n" + "\n".join(lines)
    system = _build_system_prompt(user, "post")
    content = prompt + ("\n\n" + extra if extra else "")

    last_error: str | None = None
    if os.environ.get("OPENAI_API_KEY", "").strip():
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        text, err = _invoke_langchain_openai(system, content, model)
        if text:
            return (text, None)
        last_error = err or last_error
    if os.environ.get("GEMINI_API_KEY", "").strip():
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        text, err = _invoke_langchain_gemini(system, content, model)
        if text:
            return (text, None)
        last_error = err or last_error
    return ("", last_error or "No LLM key set.")


def generate_reply(user: User, parent: Post, parent_author_handle: str) -> tuple[str, str | None]:
    """Generate a reply using LangChain."""
    prompt = f"Write a short reply to this tweet from @{parent_author_handle}: \"{parent.text[:200]}\""
    system = _build_system_prompt(user, "post")

    last_error: str | None = None
    if os.environ.get("OPENAI_API_KEY", "").strip():
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        text, err = _invoke_langchain_openai(system, prompt, model)
        if text:
            return (text, None)
        last_error = err or last_error
    if os.environ.get("GEMINI_API_KEY", "").strip():
        model = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
        text, err = _invoke_langchain_gemini(system, prompt, model)
        if text:
            return (text, None)
        last_error = err or last_error
    return ("", last_error or "No LLM key set.")


def is_llm_available() -> bool:
    return bool(os.environ.get("OPENAI_API_KEY", "").strip()) or bool(os.environ.get("GEMINI_API_KEY", "").strip())
