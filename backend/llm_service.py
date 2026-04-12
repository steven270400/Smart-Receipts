import json
import os
import time
import urllib.error
import urllib.request


class LlmError(RuntimeError):
    pass


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None:
        return default
    value = str(value).strip()
    return value if value else default


def _post_json(url: str, payload: dict, timeout_s: float) -> dict:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as exc:
        raise LlmError(f"ollama_request_failed: {exc}") from exc
    except TimeoutError as exc:
        raise LlmError("ollama_request_timeout") from exc

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise LlmError("ollama_response_not_json") from exc


def _extract_json_object(text: str) -> dict:
    # Ollama may return extra tokens; we only accept a single JSON object.
    if not text:
        raise LlmError("llm_empty_response")

    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < 0 or end <= start:
        raise LlmError("llm_no_json_object")

    snippet = text[start : end + 1]
    try:
        return json.loads(snippet)
    except json.JSONDecodeError as exc:
        raise LlmError("llm_json_parse_failed") from exc


def select_receipt_fields_from_candidates(
    clean_texts: list[str],
    candidates: dict,
    *,
    timeout_s: float | None = None,
) -> tuple[dict, dict]:
    """
    Ask LLM to select candidate IDs for receipt fields.

    Returns:
      - selection dict (parsed JSON from LLM)
      - meta dict (model, latency_ms, raw_text excerpt)
    """
    host = _env("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = _env("OLLAMA_MODEL", "qwen2.5:7b")
    timeout_s = float(timeout_s or _env("OLLAMA_TIMEOUT_S", "6"))

    system = (
        "You are a strict information extraction selector.\n"
        "You must ONLY choose values from the provided candidate IDs.\n"
        "Return ONLY a single JSON object (no markdown, no code fences, no extra text).\n"
        "If you cannot decide, return null for that field.\n"
        "Do NOT invent any values outside candidates.\n"
    )

    user = {
        "ocr_lines": clean_texts,
        "candidates": candidates,
        "output_schema": {
            "merchant_id": "string|null",
            "amount_id": "string|null",
            "date_id": "string|null",
            "payment_method_id": "string|null",
            "category_id": "string|null",
            "confidence": {
                "merchant": "number(0..1)",
                "amount": "number(0..1)",
                "date": "number(0..1)",
                "payment_method": "number(0..1)",
                "category": "number(0..1)",
            },
            "reason": "string",
        },
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }

    started = time.time()
    resp = _post_json(f"{host}/api/chat", payload, timeout_s)
    latency_ms = int((time.time() - started) * 1000)

    # Ollama /api/chat response: { message: { content: "..." }, ... }
    content = ""
    message = resp.get("message")
    if isinstance(message, dict):
        content = message.get("content") or ""
    if not isinstance(content, str):
        content = str(content)

    selection = _extract_json_object(content)
    meta = {
        "llm_provider": "ollama",
        "model": model,
        "latency_ms": latency_ms,
    }
    return selection, meta

