import re

AMOUNT_PATTERN = re.compile(r"(?<!\d)-?\d{1,6}(?:\.\d{1,2})?(?!\d)")
DATE_PATTERNS = [
    re.compile(r"(20\d{2})[-/.](\d{1,2})[-/.](\d{1,2})"),
    re.compile(r"(20\d{2})年(\d{1,2})月(\d{1,2})日?"),
]

AMOUNT_HINTS = [
    "合计", "总计", "实付", "应付", "金额", "total", "amount", "paid"
]

DEDUCTION_HINTS = [
    "扣款", "扣除", "支出", "消费", "付款", "支付", "实付", "应付", "pay", "spent", "debit"
]

BALANCE_HINTS = [
    "余额", "剩余", "可用", "结余", "账户余额", "balance", "remaining", "available"
]

MERCHANT_HINTS = [
    "公司", "有限公司", "商户", "店", "超市", "集团", "mart", "store", "shop", "ltd", "inc"
]

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
    normalized = []
    for text in texts or []:
        if text is None:
            continue
        clean = re.sub(r"\s+", " ", str(text).strip())
        if clean:
            normalized.append(clean)
    return normalized


def _find_amount_candidates(text: str) -> list[tuple[float, str, int, int]]:
    candidates = []

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
    context = lowered[max(0, start - 10):min(len(lowered), end + 10)]
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


def extract_receipt_info(texts):
    clean_texts = _normalize_texts(texts)

    return {
        "merchant": _extract_merchant(clean_texts),
        "amount": _extract_amount(clean_texts),
        "date": _extract_date(clean_texts),
        "payment_method": _extract_payment_method(clean_texts),
        "category": _extract_category(clean_texts),
    }
