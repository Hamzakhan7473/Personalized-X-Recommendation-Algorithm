"""Optional LLM integration for real-time generated posts/replies. Uses OpenAI or Gemini when API keys are set."""

from __future__ import annotations

import os
import re
from typing import Any

from schemas import Post, User

MAX_POST_LENGTH = 280
# Simple blocklist to avoid leaking secrets in generated text (can be extended)
BLOCK_PATTERNS = [
    r"\b(api[_-]?key|password|secret|token)\s*[:=]\s*\S+",
]
BLOCK_RE = re.compile("|".join(f"({p})" for p in BLOCK_PATTERNS), re.I)


def _sanitize(text: str) -> str:
    """Trim to 280 chars and strip blocklisted content."""
    if not text or not text.strip():
        return ""
    t = text.strip()
    # Remove blocklisted patterns
    t = BLOCK_RE.sub("[redacted]", t)
    t = t.strip()
    if len(t) > MAX_POST_LENGTH:
        t = t[: MAX_POST_LENGTH - 3] + "..."
    return t


def _build_system_prompt(user: User, kind: str) -> str:
    persona = user.persona_kind.value if user.persona_kind else "general"
    topics = ", ".join(t.value for t in user.topics) if user.topics else "general"
    return (
        f"You are generating a single tweet (max {MAX_POST_LENGTH} characters) for a synthetic user. "
        f"Persona: {persona}. Topics: {topics}. Display name: {user.display_name}. Bio: {user.bio or 'N/A'}. "
        "Write one short, punchy tweet in that voice. No hashtags unless natural. No URLs. Output only the tweet text, nothing else."
    )


def _call_openai(user: User, prompt: str, extra: str = "") -> tuple[str, str | None]:
    """Returns (sanitized_text, error_message). error_message is set only on failure."""
    try:
        from openai import OpenAI
    except ImportError:
        return "", "OpenAI package not installed (pip install openai)."
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return "", None
    try:
        try:
            client = OpenAI(api_key=key)
        except TypeError as e:
            if "proxies" in str(e):
                import httpx
                client = OpenAI(api_key=key, http_client=httpx.Client(trust_env=False))
            else:
                raise
        sys = _build_system_prompt(user, "post")
        content = prompt + ("\n\n" + extra if extra else "")
        model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": sys},
                {"role": "user", "content": content},
            ],
            max_tokens=150,
            temperature=0.8,
        )
        text = (resp.choices[0].message.content or "").strip()
        out = _sanitize(text)
        return (out, None) if out else ("", "OpenAI returned empty content.")
    except Exception as e:
        msg = str(e).strip() or type(e).__name__
        return "", f"OpenAI: {msg}"


def _call_gemini_new_sdk(key: str, model_name: str, system: str, user_content: str) -> tuple[str, str | None]:
    """Use the new google.genai SDK (no deprecation warning)."""
    try:
        from google.genai import Client
        client = Client(api_key=key)
        full_content = f"{system}\n\nUser request: {user_content}"
        response = client.models.generate_content(model=model_name, contents=full_content)
        text = (getattr(response, "text", None) or "").strip()
        return (_sanitize(text), None) if text else ("", "Gemini returned empty or blocked content.")
    except Exception as e:
        return "", f"Gemini ({model_name}): {str(e)[:120]}"


def _call_gemini_one(user: User, prompt: str, extra: str, model_name: str, genai: Any) -> tuple[str, str | None]:
    """Single attempt with one model (legacy google.generativeai). Returns (text, error)."""
    try:
        model = genai.GenerativeModel(model_name)
        sys = _build_system_prompt(user, "post")
        content = f"{sys}\n\nUser request: {prompt}" + (f"\n{extra}" if extra else "")
        response = model.generate_content(
            content,
            generation_config=genai.types.GenerationConfig(max_output_tokens=150, temperature=0.8),
        )
        try:
            text = (getattr(response, "text", None) or "").strip()
        except Exception:
            text = ""
        out = _sanitize(text)
        return (out, None) if out else ("", "Gemini returned empty or blocked content.")
    except Exception as e:
        msg = str(e).strip() or type(e).__name__
        return "", f"Gemini ({model_name}): {msg}"


def _call_gemini(user: User, prompt: str, extra: str = "") -> tuple[str, str | None]:
    """Returns (sanitized_text, error_message). Prefers new google.genai SDK; falls back to deprecated package."""
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        return "", None
    sys = _build_system_prompt(user, "post")
    user_content = prompt + (f"\n{extra}" if extra else "")
    model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash").strip()
    fallback_models = ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-3-flash-preview"]
    models_to_try = [model_name] + [m for m in fallback_models if m != model_name]

    # Prefer new google.genai SDK (no deprecation warning)
    try:
        from google.genai import Client as _  # noqa: F401
        last_error = None
        for m in models_to_try:
            text, err = _call_gemini_new_sdk(key, m, sys, user_content)
            if text:
                return (text, None)
            last_error = err or last_error
            if err and ("not found" not in (err or "").lower() and "404" not in (err or "")):
                break
        return ("", last_error or "Gemini returned no text.")
    except ImportError:
        pass

    # Fallback: deprecated google.generativeai
    try:
        import google.generativeai as genai
        genai.configure(api_key=key)
    except Exception as e:
        return "", f"Gemini import: {e}"
    last_error: str | None = None
    for m in models_to_try:
        text, err = _call_gemini_one(user, prompt, extra, m, genai)
        if text:
            return (text, None)
        last_error = err or last_error
        if err and ("not found" not in (err or "").lower() and "404" not in (err or "")):
            break
    return ("", last_error or "Gemini returned no text.")


def is_llm_available() -> bool:
    """True if at least one of OpenAI or Gemini API key is set."""
    return bool(os.environ.get("OPENAI_API_KEY", "").strip()) or bool(os.environ.get("GEMINI_API_KEY", "").strip())


def generate_post(user: User, context: list[Post] | None = None) -> tuple[str, str | None]:
    """
    Generate a single tweet as the given user. Tries OpenAI first if set, then Gemini if set (fallback).
    If USE_LANGCHAIN=1, uses LangChain for the same flow (enables chains/agents later).
    Returns (text, error_message). text is non-empty on success; error_message is set when both fail.
    """
    if os.environ.get("USE_LANGCHAIN", "").strip():
        try:
            from langchain_provider import generate_post as lc_generate_post
            return lc_generate_post(user, context)
        except Exception:
            pass  # fall back to direct API
    prompt = "Generate one new tweet that this user might post now. Keep it short and in character."
    extra = ""
    if context:
        recent = context[-5:]
        lines = [f"- {p.text[:100]}..." if len(p.text) > 100 else f"- {p.text}" for p in recent]
        extra = "Recent posts from the network (for tone only):\n" + "\n".join(lines)
    last_error: str | None = None
    if os.environ.get("OPENAI_API_KEY", "").strip():
        text, err = _call_openai(user, prompt, extra)
        if text:
            return (text, None)
        last_error = err or last_error
    if os.environ.get("GEMINI_API_KEY", "").strip():
        text, err = _call_gemini(user, prompt, extra)
        if text:
            return (text, None)
        last_error = err or last_error
    return ("", last_error or "No LLM key set.")


def generate_reply(user: User, parent: Post, parent_author_handle: str) -> tuple[str, str | None]:
    """Generate a reply to parent post. If USE_LANGCHAIN=1, uses LangChain. Returns (text, error_message)."""
    if os.environ.get("USE_LANGCHAIN", "").strip():
        try:
            from langchain_provider import generate_reply as lc_generate_reply
            return lc_generate_reply(user, parent, parent_author_handle)
        except Exception:
            pass
    prompt = f"Write a short reply to this tweet from @{parent_author_handle}: \"{parent.text[:200]}\""
    last_error: str | None = None
    if os.environ.get("OPENAI_API_KEY", "").strip():
        text, err = _call_openai(user, prompt)
        if text:
            return (text, None)
        last_error = err or last_error
    if os.environ.get("GEMINI_API_KEY", "").strip():
        text, err = _call_gemini(user, prompt)
        if text:
            return (text, None)
        last_error = err or last_error
    return ("", last_error or "No LLM key set.")
