import os
import re
import time
from datetime import datetime

AMOUNT_PATTERN = re.compile(r"(?<!\d)-?\d{1,6}(?:\.\d{1,2})?(?!\d)")
DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})"),
    re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日?"),
]

AMOUNT_HINTS = ["合计", "总计", "实付", "应付", "金额", "total", "amount", "paid"]
DEDUCTION_HINTS = ["扣款", "扣除", "支出", "消费", "付款", "支付", "实付", "应付", "pay", "spent", "debit"]
BALANCE_HINTS = ["余额", "剩余", "可用", "结余", "账户余额", "balance", "remaining", "available"]
MERCHANT_HINTS = ["公司", "有限公司", "商户", "店", "超市", "集团", "mart", "store", "shop", "ltd", "inc"]

PAYMENT_KEYWORDS = [
    ("支付宝", "支付宝"),
    ("alipay", "支付宝"),
    ("微信", "微信"),
    ("weixin", "微信"),
    ("银行卡", "银行卡"),
    ("card", "银行卡"),
    ("cash", "现金"),
    ("现金", "现金"),
]

CATEGORY_RULES = {
    "生活缴费": ["电费", "水费", "燃气", "燃气费", "电力", "供电", "水务"],
    "餐饮": ["餐", "美食", "饭", "餐厅", "餐饮", "外卖", "肯德基", "麦当劳"],
    "交通": ["公交", "地铁", "打车", "滴滴", "车费", "交通"],
    "购物": ["超市", "商城", "购物", "便利店", "商店"],
}


def _normalize_texts(texts) -> list[str]:
    normalized: list[str] = []
    for text in texts or []:
        if text is None:
            continue
        clean = re.sub(r"\s+", " ", str(text).strip())
        if clean:
            normalized.append(clean)
    return normalized


def _find_amount_candidates(text: str) -> list[tuple[float, str, int, int]]:
    candidates: list[tuple[float, str, int, int]] = []

    if any(pattern.search(text) for pattern in DATE_PATTERNS):
        return candidates

    for match in AMOUNT_PATTERN.finditer(text):
        raw = match.group()
        try:
            amount = float(raw)
        except ValueError:
            continue

        # Skip date-like integer fragments such as 03/09.
        if "." not in raw and raw.startswith("0") and len(raw) > 1:
            continue

        if abs(amount) < 100000:
            candidates.append((amount, raw, match.start(), match.end()))

    return candidates


def _score_amount_candidate(line: str, raw: str, start: int, end: int) -> int:
    lowered = line.lower()
    context = lowered[max(0, start - 10) : min(len(lowered), end + 10)]
    score = 0

    if any(hint in lowered for hint in AMOUNT_HINTS):
        score += 3
    if any(hint in lowered for hint in DEDUCTION_HINTS):
        score += 4
    if any(hint in lowered for hint in BALANCE_HINTS):
        score -= 6

    # Local context around the amount is stronger than whole-line hints.
    if any(hint in context for hint in DEDUCTION_HINTS):
        score += 3
    if any(hint in context for hint in BALANCE_HINTS):
        score -= 8

    if raw.startswith("-"):
        score += 2

    return score


def _extract_amount(texts: list[str]):
    scored_candidates: list[tuple[int, float]] = []

    for text in texts:
        for amount, raw, start, end in _find_amount_candidates(text):
            score = _score_amount_candidate(text, raw, start, end)
            scored_candidates.append((score, amount))

    if not scored_candidates:
        return None

    # User rule: if a negative amount exists, treat it as the payment amount.
    negative = [item for item in scored_candidates if item[1] < 0]
    if negative:
        selected = max(negative, key=lambda item: (item[0], abs(item[1])))
        return abs(selected[1])

    positive = [item for item in scored_candidates if item[0] > 0]
    neutral = [item for item in scored_candidates if item[0] == 0]

    if positive:
        return max(positive, key=lambda item: (item[0], item[1]))[1]

    if neutral:
        return max(neutral, key=lambda item: item[1])[1]

    return max(scored_candidates, key=lambda item: item[0])[1]


def _extract_date(texts: list[str]):
    for text in texts:
        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            year, month, day = match.group(1), match.group(2), match.group(3)
            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
    return None


def _looks_like_merchant(text: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in ["合计", "总计", "实付", "应付", "金额", "税", "电话", "地址"]):
        return False

    if any(keyword in lowered or keyword in text for keyword, _ in PAYMENT_KEYWORDS):
        return False

    if any(pattern.search(text) for pattern in DATE_PATTERNS):
        return False

    if re.fullmatch(r"[\d\W_]+", text):
        return False

    return True


def _extract_merchant(texts: list[str]):
    for text in texts:
        lowered = text.lower()
        if any(hint in lowered for hint in MERCHANT_HINTS) and _looks_like_merchant(text):
            return text

    for text in texts:
        if _looks_like_merchant(text):
            return text

    return None


def _extract_payment_method(texts: list[str]):
    for text in texts:
        lowered = text.lower()
        for keyword, method in PAYMENT_KEYWORDS:
            if keyword in lowered or keyword in text:
                return method
    return None


def _extract_category(texts: list[str]):
    for text in texts:
        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in text for keyword in keywords):
                return category
    return "其他"


def _baseline_extract(clean_texts: list[str]) -> dict:
    return {
        "merchant": _extract_merchant(clean_texts),
        "amount": _extract_amount(clean_texts),
        "date": _extract_date(clean_texts),
        "payment_method": _extract_payment_method(clean_texts),
        "category": _extract_category(clean_texts),
    }


def _hint_tokens(text: str, hints: list[str]) -> list[str]:
    lowered = text.lower()
    return [hint for hint in hints if hint in lowered]


def build_candidates(clean_texts: list[str], *, top_k: int = 5) -> dict:
    """
    Build candidate lists for each field.

    Candidate item schema:
      - id: stable string within this extraction call (e.g., "a0")
      - source_line: original OCR line text
      - parsed_value: normalized value used as dict field (e.g., float, YYYY-MM-DD, string)
      - rule_score: integer score from heuristics
      - matched_hints: list[str]
    """
    top_k = int(top_k) if top_k else 5
    top_k = max(1, min(top_k, 10))

    # Amount candidates
    amount_items: list[dict] = []
    for text in clean_texts:
        for amount, raw, start, end in _find_amount_candidates(text):
            score = _score_amount_candidate(text, raw, start, end)
            parsed = abs(amount) if amount < 0 else amount
            matched = (
                _hint_tokens(text, AMOUNT_HINTS)
                + _hint_tokens(text, DEDUCTION_HINTS)
                + _hint_tokens(text, BALANCE_HINTS)
            )
            amount_items.append(
                {
                    "source_line": text,
                    "parsed_value": parsed,
                    "rule_score": int(score),
                    "matched_hints": matched[:8],
                }
            )

    amount_items.sort(key=lambda it: (it["rule_score"], float(it["parsed_value"])), reverse=True)
    amount_items = amount_items[:top_k]
    for idx, item in enumerate(amount_items):
        item["id"] = f"a{idx}"

    # Date candidates
    date_items: list[dict] = []
    for text in clean_texts:
        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            year, month, day = match.group(1), match.group(2), match.group(3)
            parsed = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            date_items.append(
                {
                    "source_line": text,
                    "parsed_value": parsed,
                    "rule_score": 10,
                    "matched_hints": ["date_pattern"],
                }
            )
            break

    date_items = date_items[:top_k]
    for idx, item in enumerate(date_items):
        item["id"] = f"d{idx}"

    # Merchant candidates
    merchant_items: list[dict] = []
    for text in clean_texts:
        if not _looks_like_merchant(text):
            continue
        lowered = text.lower()
        score = 0
        matched = []
        for hint in MERCHANT_HINTS:
            if hint in lowered:
                score += 5
                matched.append(hint)
        if len(text) >= 6:
            score += 1
        merchant_items.append(
            {
                "source_line": text,
                "parsed_value": text,
                "rule_score": score,
                "matched_hints": matched[:8],
            }
        )

    merchant_items.sort(key=lambda it: (it["rule_score"], len(str(it["parsed_value"]))), reverse=True)
    merchant_items = merchant_items[:top_k]
    for idx, item in enumerate(merchant_items):
        item["id"] = f"m{idx}"

    # Payment method candidates
    pm_items: list[dict] = []
    seen_methods: set[str] = set()
    for text in clean_texts:
        lowered = text.lower()
        for keyword, method in PAYMENT_KEYWORDS:
            if keyword in lowered or keyword in text:
                if method in seen_methods:
                    continue
                seen_methods.add(method)
                pm_items.append(
                    {
                        "source_line": text,
                        "parsed_value": method,
                        "rule_score": 10,
                        "matched_hints": [keyword],
                    }
                )

    pm_items = pm_items[:top_k]
    for idx, item in enumerate(pm_items):
        item["id"] = f"p{idx}"

    # Category candidates
    cat_items: list[dict] = []
    for text in clean_texts:
        for category, keywords in CATEGORY_RULES.items():
            if any(keyword in text for keyword in keywords):
                cat_items.append(
                    {
                        "source_line": text,
                        "parsed_value": category,
                        "rule_score": 10,
                        "matched_hints": [kw for kw in keywords if kw in text][:8],
                    }
                )

    # Default category always exists as a low-score option.
    cat_items.append(
        {
            "source_line": "",
            "parsed_value": "其他",
            "rule_score": 0,
            "matched_hints": ["default"],
        }
    )

    # Deduplicate by category name and keep best score.
    dedup: dict[str, dict] = {}
    for item in cat_items:
        name = str(item["parsed_value"])
        if name not in dedup or int(item["rule_score"]) > int(dedup[name]["rule_score"]):
            dedup[name] = item
    cat_items = list(dedup.values())
    cat_items.sort(key=lambda it: it["rule_score"], reverse=True)
    cat_items = cat_items[:top_k]
    for idx, item in enumerate(cat_items):
        item["id"] = f"c{idx}"

    return {
        "merchant": merchant_items,
        "amount": amount_items,
        "date": date_items,
        "payment_method": pm_items,
        "category": cat_items,
    }


def _is_llm_enabled() -> bool:
    value = os.getenv("EXTRACT_LLM_ENABLE", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _should_store_candidates() -> bool:
    value = os.getenv("EXTRACT_LLM_STORE_CANDIDATES", "").strip().lower()
    return value in {"1", "true", "yes", "on"}


def _map_candidate_value(candidates: dict, field: str, candidate_id: str | None):
    if not candidate_id:
        return None
    items = candidates.get(field) or []
    for item in items:
        if item.get("id") == candidate_id:
            return item.get("parsed_value")
    return None


def _validate_amount(value) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _validate_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        datetime.strptime(str(value), "%Y-%m-%d")
        return str(value)
    except (TypeError, ValueError):
        return None


def extract_receipt_info_with_meta(texts) -> tuple[dict, dict]:
    clean_texts = _normalize_texts(texts)
    baseline = _baseline_extract(clean_texts)

    meta: dict = {"llm_enabled": _is_llm_enabled(), "invoked": False}
    if not meta["llm_enabled"]:
        return baseline, meta

    top_k = int(os.getenv("EXTRACT_LLM_TOPK", "5") or "5")
    candidates = build_candidates(clean_texts, top_k=top_k)
    meta["invoked"] = True

    started = time.time()
    try:
        from backend.llm_service import select_receipt_fields_from_candidates

        selection, llm_meta = select_receipt_fields_from_candidates(clean_texts, candidates)
        meta.update(llm_meta)
        meta["selection"] = selection
    except Exception as exc:  # fallback must be bulletproof
        meta["error"] = str(exc)
        meta["latency_ms_total"] = int((time.time() - started) * 1000)
        return baseline, meta

    meta["latency_ms_total"] = int((time.time() - started) * 1000)

    # Merge: LLM-selected values override baseline only if valid and mapped.
    final = dict(baseline)

    merchant = _map_candidate_value(candidates, "merchant", selection.get("merchant_id"))
    if isinstance(merchant, str) and merchant.strip():
        final["merchant"] = merchant

    amount = _validate_amount(_map_candidate_value(candidates, "amount", selection.get("amount_id")))
    if amount is not None:
        final["amount"] = amount

    date_value = _validate_date(_map_candidate_value(candidates, "date", selection.get("date_id")))
    if date_value is not None:
        final["date"] = date_value

    pm = _map_candidate_value(candidates, "payment_method", selection.get("payment_method_id"))
    if isinstance(pm, str) and pm.strip():
        final["payment_method"] = pm

    category = _map_candidate_value(candidates, "category", selection.get("category_id"))
    if isinstance(category, str) and category.strip():
        final["category"] = category

    if _should_store_candidates():
        meta["candidates"] = candidates

    return final, meta


def extract_receipt_info(texts):
    info, _meta = extract_receipt_info_with_meta(texts)
    return info

