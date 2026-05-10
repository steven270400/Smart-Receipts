import re

_GLUED_MULTIPLIER_PATTERN = re.compile(r"([*xX×])(\d{2,}\.\d{1,2})(?!\d)")
_AMOUNT_PATTERN = re.compile(r"(?:0|[1-9]\d*)\.\d{1,2}$")
_DECIMAL_SUFFIX_PATTERN = re.compile(r"\d+\.\d{1,2}\s*$")


def _choose_qty_amount_split(number: str) -> tuple[str, str] | None:
    dot_index = number.find(".")
    if dot_index <= 1:
        return None

    candidates: list[tuple[float, str, str]] = []
    max_qty_len = min(4, dot_index - 1)
    for qty_len in range(1, max_qty_len + 1):
        qty = number[:qty_len]
        amount = number[qty_len:]

        if not qty.isdigit():
            continue
        if len(qty) > 1 and qty.startswith("0"):
            continue
        if int(qty) <= 0:
            continue
        if not _AMOUNT_PATTERN.fullmatch(amount):
            continue

        amount_int_len = len(amount.split(".", 1)[0])
        score = 0.0
        if qty_len <= 2:
            score += 2.0
        elif qty_len == 3:
            score += 0.8
        if amount_int_len >= 2:
            score += 1.2
        score -= qty_len * 0.05
        candidates.append((score, qty, amount))

    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    return candidates[0][1], candidates[0][2]


def repair_glued_qty_amount(text: str) -> str:
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        operator = match.group(1)
        number = match.group(2)
        prefix = text[: match.start(1)]
        if not _DECIMAL_SUFFIX_PATTERN.search(prefix):
            return match.group(0)
        split = _choose_qty_amount_split(number)
        if not split:
            return match.group(0)
        qty, amount = split
        return f"{operator}{qty} {amount}"

    return _GLUED_MULTIPLIER_PATTERN.sub(_replace, text)
