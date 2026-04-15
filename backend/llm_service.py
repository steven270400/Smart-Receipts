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


def _normalize_selection(selection: dict) -> dict:
    normalized = {
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
    return normalized


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
        "你是严格的信息抽取选择器。\n"
        "你必须只在给定候选ID中做选择，绝对不能编造候选外的值。\n"
        "你必须先判断 numeric 候选中哪些是金额、哪些不是金额，并给出简短中文理由。\n"
        "严禁把手机号尾号、虚拟号码、转接号码、顾客号码当作金额。\n"
        "如果识别到日期与时间粘连（例如 04-0621:46），必须理解为 04-06 21:46，并据此判断日期候选。\n"
        "当同一行出现折扣与原价时，优先选择实付/应付/总计/合计等真实支付金额。\n"
        "输出必须是单个JSON对象，不要输出markdown、代码块或额外文本。\n"
        "无法判断时字段填 null。\n"
    )

    user = {
        "ocr_lines": clean_texts,
        "candidates": candidates,
        "金额判定规则": [
            "包含手机号、尾号、虚拟号码、顾客号码、备用号码、转接号码上下文的数字不是金额",
            "纯长数字（通常>=7位）通常是号码/编号，不是金额",
            "优先实付/应付/总计/合计/折后金额，原价不是优先金额",
            "日期时间粘连（如 04-0621:46）需要先拆分为 04-06 21:46 再判断日期",
        ],
        "output_schema": {
            "merchant_id": "string|null",
            "amount_id": "string|null",
            "date_id": "string|null",
            "payment_method_id": "string|null",
            "category_id": "string|null",
            "amount_judgement": [
                {
                    "candidate_id": "string(来自candidates.numeric[*].id)",
                    "is_amount": "boolean",
                    "reason": "string(中文简短理由)",
                }
            ],
            "excluded_numeric_ids": ["string(明确排除为非金额的numeric候选ID)"],
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

    selection = _normalize_selection(_extract_json_object(content))
    meta = {
        "llm_provider": "ollama",
        "model": model,
        "latency_ms": latency_ms,
    }
    return selection, meta

