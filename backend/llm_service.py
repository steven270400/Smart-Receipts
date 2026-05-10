import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


class LlmError(RuntimeError):
    pass


_PROMPT_CONFIG_PATH = Path(__file__).resolve().parent / "prompts" / "receipt_selector_prompt.json"
_PROMPT_CACHE: dict[str, Any] | None = None
_PROMPT_MTIME: float | None = None


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


def _normalize_selection(selection: dict) -> dict:
    return {
        "merchant_id": selection.get("merchant_id"),
        "amount_id": selection.get("amount_id"),
        "date_id": selection.get("date_id"),
        "payment_method_id": selection.get("payment_method_id"),
        "category_id": selection.get("category_id"),
        "amount_judgement": selection.get("amount_judgement") if isinstance(selection.get("amount_judgement"), list) else [],
        "excluded_numeric_ids": selection.get("excluded_numeric_ids")
        if isinstance(selection.get("excluded_numeric_ids"), list)
        else [],
        "confidence": selection.get("confidence") if isinstance(selection.get("confidence"), dict) else {},
        "reason": selection.get("reason") if isinstance(selection.get("reason"), str) else "",
    }


def _validate_prompt_config(config: dict[str, Any]) -> None:
    system = config.get("system")
    amount_rules = config.get("amount_rules")
    output_schema = config.get("output_schema")

    if not isinstance(system, str) or not system.strip():
        raise LlmError("prompt_config_invalid:system")
    if not isinstance(amount_rules, list) or not all(isinstance(item, str) for item in amount_rules):
        raise LlmError("prompt_config_invalid:amount_rules")
    if not isinstance(output_schema, dict):
        raise LlmError("prompt_config_invalid:output_schema")


def _load_prompt_config() -> dict[str, Any]:
    global _PROMPT_CACHE, _PROMPT_MTIME

    try:
        current_mtime = _PROMPT_CONFIG_PATH.stat().st_mtime
    except OSError as exc:
        raise LlmError(f"prompt_config_invalid:file_unavailable:{exc}") from exc

    if _PROMPT_CACHE is not None and _PROMPT_MTIME is not None and current_mtime == _PROMPT_MTIME:
        return _PROMPT_CACHE

    try:
        raw = _PROMPT_CONFIG_PATH.read_text(encoding="utf-8")
        parsed = json.loads(raw)
    except OSError as exc:
        raise LlmError(f"prompt_config_invalid:file_read_failed:{exc}") from exc
    except json.JSONDecodeError as exc:
        raise LlmError("prompt_config_invalid:json_parse_failed") from exc

    if not isinstance(parsed, dict):
        raise LlmError("prompt_config_invalid:not_object")

    _validate_prompt_config(parsed)
    _PROMPT_CACHE = parsed
    _PROMPT_MTIME = current_mtime
    return parsed


def select_receipt_fields_from_candidates(
    clean_texts: list[str],
    candidates: dict,
    *,
    timeout_s: float | None = None,
) -> tuple[dict, dict]:
    host = _env("OLLAMA_HOST", "http://localhost:11434").rstrip("/")
    model = _env("OLLAMA_MODEL", "qwen2.5:7b")
    timeout_s = float(timeout_s or _env("OLLAMA_TIMEOUT_S", "6"))
    prompt_config = _load_prompt_config()

    user = {
        "ocr_lines": clean_texts,
        "candidates": candidates,
        "amount_rules": prompt_config["amount_rules"],
        "output_schema": prompt_config["output_schema"],
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": prompt_config["system"]},
            {"role": "user", "content": json.dumps(user, ensure_ascii=False)},
        ],
        "stream": False,
        "options": {"temperature": 0},
    }

    started = time.time()
    resp = _post_json(f"{host}/api/chat", payload, timeout_s)
    latency_ms = int((time.time() - started) * 1000)

    content = ""
    message = resp.get("message")
    if isinstance(message, dict):
        content = message.get("content") or ""
    if not isinstance(content, str):
        content = str(content)

    selection = _normalize_selection(_extract_json_object(content))
    meta = {
        "llm_provider": "ollama",
        "model": model,
        "latency_ms": latency_ms,
    }
    return selection, meta
