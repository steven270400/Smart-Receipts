import os
import re
import time
from datetime import datetime, timedelta, timezone

AMOUNT_PATTERN = re.compile(r"(?<!\d)-?\d{1,9}(?:\.\d{1,2})?(?!\d)")

DATE_PATTERNS_WITH_YEAR = [
    re.compile(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})(?:\s*(\d{1,2}):(\d{2}))?"),
    re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日?(?:\s*(\d{1,2}):(\d{2}))?"),
]
DATE_PATTERNS_NO_YEAR = [
    re.compile(r"(?<!\d)(\d{1,2})[-/](\d{1,2})(?:\s*(\d{1,2}):(\d{2}))?(?!\d)"),
    re.compile(r"(?<!\d)(\d{1,2})月(\d{1,2})[日号]?(?:\s*(\d{1,2}):(\d{2}))?(?!\d)"),
]

CHINA_TZ = timezone(timedelta(hours=8))

AMOUNT_HINTS = ["金额", "total", "amount", "paid"]
PAID_HINTS = ["合计", "总计", "实付", "应付", "折后", "支付金额", "到手", "支付", "付款", "扣款", "消费"]
ORIGINAL_PRICE_HINTS = ["原价", "门市价", "划线价", "单价", "原单价"]
BALANCE_HINTS = ["余额", "剩余", "可用", "结余", "账户余额", "balance", "remaining", "available"]
PHONE_CONTEXT_HINTS = [
    "手机尾号",
    "手机号",
    "顾客号码",
    "虚拟号码",
    "备用号码",
    "联系方式",
    "联系号码",
    "电话",
    "转",
]
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
    "餐饮": ["餐", "美食", "饭", "餐厅", "餐饮", "外卖", "肯德基", "麦当劳", "美团", "饿了么"],
    "交通": ["公交", "地铁", "打车", "滴滴", "车费", "交通"],
    "购物": ["超市", "商城", "购物", "便利店", "商店"],
}


def _normalize_texts(texts) -> list[str]:
    normalized: list[str] = []
    for text in texts or []:
        if text is None:
            continue
        clean = str(text).strip()
        # OCR may glue date and time together, e.g. "04-0621:46" -> "04-06 21:46".
        clean = re.sub(
            r"(?<!\d)((?:20\d{2}[-/.]\d{1,2}[-/.]\d{1,2})|(?:\d{1,2}[-/]\d{1,2})|(?:\d{1,2}月\d{1,2}[日号]?))(?=\d{1,2}:\d{2}\b)",
            r"\1 ",
            clean,
        )
        clean = re.sub(r"\s+", " ", clean)
        if clean:
            normalized.append(clean)
    return normalized


def _now_china_naive() -> datetime:
    return datetime.now(CHINA_TZ).replace(tzinfo=None)


def _build_datetime_safe(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime | None:
    try:
        return datetime(year, month, day, hour, minute, 0)
    except ValueError:
        return None


def _infer_recent_past_datetime(month: int, day: int, hour: int = 0, minute: int = 0) -> datetime | None:
    now_cn = _now_china_naive()
    candidate_this_year = _build_datetime_safe(now_cn.year, month, day, hour, minute)
    if candidate_this_year and candidate_this_year <= now_cn:
        return candidate_this_year

    for year in (now_cn.year - 1, now_cn.year - 2, now_cn.year - 3):
        candidate = _build_datetime_safe(year, month, day, hour, minute)
        if candidate:
            return candidate
    return None


def _extract_date_time(texts: list[str]) -> tuple[str | None, str | None]:
    for text in texts:
        for pattern in DATE_PATTERNS_WITH_YEAR:
            match = pattern.search(text)
            if not match:
                continue
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            hour = int(match.group(4) or 0)
            minute = int(match.group(5) or 0)
            parsed = _build_datetime_safe(year, month, day, hour, minute)
            if not parsed:
                continue
            return parsed.strftime("%Y-%m-%d"), parsed.strftime("%Y-%m-%d %H:%M:%S")

    for text in texts:
        for pattern in DATE_PATTERNS_NO_YEAR:
            match = pattern.search(text)
            if not match:
                continue
            month = int(match.group(1))
            day = int(match.group(2))
            hour = int(match.group(3) or 0)
            minute = int(match.group(4) or 0)
            parsed = _infer_recent_past_datetime(month, day, hour, minute)
            if not parsed:
                continue
            return parsed.strftime("%Y-%m-%d"), parsed.strftime("%Y-%m-%d %H:%M:%S")
    return None, None


def _is_phone_like_number(line: str, raw: str, start: int, end: int) -> bool:
    lowered = line.lower()
    context = lowered[max(0, start - 12) : min(len(lowered), end + 12)]
    digits = re.sub(r"\D", "", raw)
    if any(hint in lowered or hint in context for hint in PHONE_CONTEXT_HINTS):
        return True
    if "." not in raw and len(digits) >= 7:
        return True
    if "转" in context and "." not in raw:
        return True
    return False


def _line_has_date(line: str) -> bool:
    return any(pattern.search(line) for pattern in (DATE_PATTERNS_WITH_YEAR + DATE_PATTERNS_NO_YEAR))


def _infer_numeric_kind(line: str, raw: str, start: int, end: int) -> str:
    if _is_phone_like_number(line, raw, start, end):
        return "phone_like"
    if _line_has_date(line):
        return "date_fragment"
    digits = re.sub(r"\D", "", raw)
    if "." not in raw and len(digits) >= 7:
        return "id_like"
    return "amount_candidate"


def _score_amount_candidate(line: str, raw: str, start: int, end: int) -> int:
    lowered = line.lower()
    context = lowered[max(0, start - 12) : min(len(lowered), end + 12)]
    score = 0

    if any(hint in lowered for hint in AMOUNT_HINTS):
        score += 2
    if any(hint in lowered for hint in PAID_HINTS):
        score += 6
    if any(hint in lowered for hint in ORIGINAL_PRICE_HINTS):
        score -= 4
    if any(hint in lowered for hint in BALANCE_HINTS):
        score -= 8

    if any(hint in context for hint in PAID_HINTS):
        score += 4
    if any(hint in context for hint in ORIGINAL_PRICE_HINTS):
        score -= 3
    if any(hint in context for hint in BALANCE_HINTS):
        score -= 8

    if "*" in context and any(token in context for token in ORIGINAL_PRICE_HINTS):
        score -= 2

    if "折" in context and "." in raw:
        try:
            discount = float(raw)
            if 0 < discount <= 10:
                score -= 6
        except ValueError:
            pass

    if raw.startswith("-"):
        score += 2
    if "." in raw:
        score += 1
    return score


def _collect_numeric_candidates(clean_texts: list[str], *, top_k: int) -> list[dict]:
    items: list[dict] = []
    for text in clean_texts:
        for match in AMOUNT_PATTERN.finditer(text):
            raw = match.group()
            start = match.start()
            end = match.end()
            kind = _infer_numeric_kind(text, raw, start, end)
            score = _score_amount_candidate(text, raw, start, end) if kind == "amount_candidate" else -20

            parsed_value = None
            try:
                parsed_value = float(raw)
            except ValueError:
                parsed_value = None

            items.append(
                {
                    "source_line": text,
                    "raw_value": raw,
                    "parsed_value": parsed_value,
                    "kind_hint": kind,
                    "rule_score": int(score),
                }
            )

    items = items[: max(top_k * 4, 20)]
    for idx, item in enumerate(items):
        item["id"] = f"n{idx}"
    return items


def _find_amount_candidates(text: str) -> list[tuple[float, str, int, int]]:
    candidates: list[tuple[float, str, int, int]] = []
    if _line_has_date(text):
        return candidates

    for match in AMOUNT_PATTERN.finditer(text):
        raw = match.group()
        try:
            amount = float(raw)
        except ValueError:
            continue

        if _is_phone_like_number(text, raw, match.start(), match.end()):
            continue

        if "." not in raw and raw.startswith("0") and len(raw) > 1:
            continue

        if abs(amount) < 100000:
            candidates.append((amount, raw, match.start(), match.end()))
    return candidates


def _extract_amount(texts: list[str]):
    scored_candidates: list[tuple[int, float]] = []
    for text in texts:
        for amount, raw, start, end in _find_amount_candidates(text):
            score = _score_amount_candidate(text, raw, start, end)
            scored_candidates.append((score, amount))

    if not scored_candidates:
        return None

    negative = [item for item in scored_candidates if item[1] < 0]
    if negative:
        selected = max(negative, key=lambda item: (item[0], abs(item[1])))
        return round(abs(selected[1]), 2)

    positive = [item for item in scored_candidates if item[0] > 0]
    neutral = [item for item in scored_candidates if item[0] == 0]

    if positive:
        return round(max(positive, key=lambda item: (item[0], item[1]))[1], 2)
    if neutral:
        return round(max(neutral, key=lambda item: item[1])[1], 2)
    return round(max(scored_candidates, key=lambda item: item[0])[1], 2)


def _extract_date(texts: list[str]):
    date_value, _transaction_time = _extract_date_time(texts)
    return date_value


def _extract_transaction_time(texts: list[str]):
    _date_value, transaction_time = _extract_date_time(texts)
    return transaction_time


def _looks_like_merchant(text: str) -> bool:
    lowered = text.lower()
    if any(token in lowered for token in ["合计", "总计", "实付", "应付", "金额", "税", "电话", "地址"]):
        return False
    if any(keyword in lowered or keyword in text for keyword, _ in PAYMENT_KEYWORDS):
        return False
    if _line_has_date(text):
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
        "transaction_time": _extract_transaction_time(clean_texts),
        "payment_method": _extract_payment_method(clean_texts),
        "category": _extract_category(clean_texts),
    }


def _hint_tokens(text: str, hints: list[str]) -> list[str]:
    lowered = text.lower()
    return [hint for hint in hints if hint in lowered]


def build_candidates(clean_texts: list[str], *, top_k: int = 5) -> dict:
    top_k = int(top_k) if top_k else 5
    top_k = max(1, min(top_k, 10))

    numeric_items = _collect_numeric_candidates(clean_texts, top_k=top_k)

    amount_items: list[dict] = []
    for numeric in numeric_items:
        if numeric.get("kind_hint") != "amount_candidate":
            continue
        parsed = numeric.get("parsed_value")
        if not isinstance(parsed, (int, float)):
            continue
        if abs(float(parsed)) >= 100000:
            continue

        parsed_amount = abs(float(parsed)) if float(parsed) < 0 else float(parsed)
        source_line = str(numeric.get("source_line") or "")
        matched = (
            _hint_tokens(source_line, AMOUNT_HINTS)
            + _hint_tokens(source_line, PAID_HINTS)
            + _hint_tokens(source_line, ORIGINAL_PRICE_HINTS)
            + _hint_tokens(source_line, BALANCE_HINTS)
        )
        amount_items.append(
            {
                "source_line": source_line,
                "parsed_value": round(parsed_amount, 2),
                "rule_score": int(numeric.get("rule_score", 0)),
                "matched_hints": matched[:8],
                "kind_hint": "amount_candidate",
                "numeric_id": numeric.get("id"),
            }
        )

    amount_items.sort(key=lambda it: (it["rule_score"], float(it["parsed_value"])), reverse=True)
    amount_items = amount_items[:top_k]
    for idx, item in enumerate(amount_items):
        item["id"] = f"a{idx}"

    date_items: list[dict] = []
    for text in clean_texts:
        for pattern in DATE_PATTERNS_WITH_YEAR:
            match = pattern.search(text)
            if not match:
                continue
            year = int(match.group(1))
            month = int(match.group(2))
            day = int(match.group(3))
            parsed = _build_datetime_safe(year, month, day)
            if not parsed:
                continue
            date_items.append(
                {
                    "source_line": text,
                    "parsed_value": parsed.strftime("%Y-%m-%d"),
                    "rule_score": 12,
                    "matched_hints": ["date_with_year"],
                }
            )
            break
        else:
            for pattern in DATE_PATTERNS_NO_YEAR:
                match = pattern.search(text)
                if not match:
                    continue
                month = int(match.group(1))
                day = int(match.group(2))
                parsed = _infer_recent_past_datetime(month, day)
                if not parsed:
                    continue
                date_items.append(
                    {
                        "source_line": text,
                        "parsed_value": parsed.strftime("%Y-%m-%d"),
                        "rule_score": 10,
                        "matched_hints": ["date_without_year_recent_past"],
                    }
                )
                break

    date_items = date_items[:top_k]
    for idx, item in enumerate(date_items):
        item["id"] = f"d{idx}"

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
    cat_items.append({"source_line": "", "parsed_value": "其他", "rule_score": 0, "matched_hints": ["default"]})

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
        "numeric": numeric_items,
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


def _get_candidate(candidates: dict, field: str, candidate_id: str | None) -> dict | None:
    if not candidate_id:
        return None
    for item in candidates.get(field) or []:
        if item.get("id") == candidate_id:
            return item
    return None


def _validate_amount(value) -> float | None:
    if value is None:
        return None
    try:
        return round(float(value), 2)
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


def _collect_excluded_numeric_ids(selection: dict) -> set[str]:
    excluded: set[str] = set()
    raw_excluded = selection.get("excluded_numeric_ids")
    if isinstance(raw_excluded, list):
        for item in raw_excluded:
            if isinstance(item, str) and item:
                excluded.add(item)

    amount_judgement = selection.get("amount_judgement")
    if isinstance(amount_judgement, list):
        for item in amount_judgement:
            if not isinstance(item, dict):
                continue
            candidate_id = item.get("candidate_id")
            is_amount = item.get("is_amount")
            if isinstance(candidate_id, str) and candidate_id and is_amount is False:
                excluded.add(candidate_id)
    return excluded


def _is_amount_selection_allowed(candidates: dict, amount_id: str | None, excluded_numeric_ids: set[str]) -> bool:
    if not amount_id:
        return False
    if amount_id in excluded_numeric_ids:
        return False

    amount_candidate = _get_candidate(candidates, "amount", amount_id)
    if not amount_candidate:
        return False

    numeric_id = amount_candidate.get("numeric_id")
    if isinstance(numeric_id, str) and numeric_id in excluded_numeric_ids:
        return False
    return True


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
    except Exception as exc:
        meta["error"] = str(exc)
        meta["latency_ms_total"] = int((time.time() - started) * 1000)
        return baseline, meta

    meta["latency_ms_total"] = int((time.time() - started) * 1000)
    final = dict(baseline)

    merchant = _map_candidate_value(candidates, "merchant", selection.get("merchant_id"))
    if isinstance(merchant, str) and merchant.strip():
        final["merchant"] = merchant

    excluded_numeric_ids = _collect_excluded_numeric_ids(selection)
    if _is_amount_selection_allowed(candidates, selection.get("amount_id"), excluded_numeric_ids):
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
