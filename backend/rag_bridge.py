"""
Optional NeuroBot RAG chat from repo root chatbot/chatbot.py (LangChain + Pinecone).
Install: pip install -r chatbot/req.txt and set OPENAI_API_KEY, PINECONE_*, etc.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable, Optional

_chat_fn: Optional[Callable[[str], str]] = None
_load_error: Optional[str] = None


def get_rag_chat() -> tuple[Optional[Callable[[str], str]], Optional[str]]:
    global _chat_fn, _load_error
    if _chat_fn is not None:
        return _chat_fn, None
    if _load_error is not None:
        return None, _load_error
    try:
        root = Path(__file__).resolve().parent.parent
        path = root / "chatbot" / "chatbot.py"
        spec = importlib.util.spec_from_file_location("_neurobot_rag_chatbot", path)
        if spec is None or spec.loader is None:
            _load_error = "Could not load chatbot/chatbot.py"
            return None, _load_error
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        fn = getattr(mod, "chat", None)
        if not callable(fn):
            _load_error = "chatbot.py has no chat(message) function"
            return None, _load_error
        _chat_fn = fn  # type: ignore[assignment]
        return _chat_fn, None
    except Exception as e:
        _load_error = str(e)
        return None, _load_error
