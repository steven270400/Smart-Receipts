from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang="ch",
    use_angle_cls=False
)


def _append_text(texts: list[str], value) -> None:
    if isinstance(value, str):
        cleaned = value.strip()
        if cleaned:
            texts.append(cleaned)


def _walk_ocr_result(node, texts: list[str]) -> None:
    if isinstance(node, dict):
        rec_texts = node.get("rec_texts")
        if isinstance(rec_texts, list):
            for item in rec_texts:
                _append_text(texts, item)

        _append_text(texts, node.get("text"))

        for key, value in node.items():
            if key in {"rec_texts", "text"}:
                continue
            _walk_ocr_result(value, texts)
        return

    if isinstance(node, (list, tuple)):
        # PaddleOCR v2 style often includes (text, score) pairs.
        if len(node) == 2 and isinstance(node[0], str) and isinstance(node[1], (int, float)):
            _append_text(texts, node[0])
            return

        for item in node:
            _walk_ocr_result(item, texts)


def _dedupe_keep_order(texts: list[str]) -> list[str]:
    seen = set()
    deduped = []
    for text in texts:
        if text in seen:
            continue
        seen.add(text)
        deduped.append(text)
    return deduped


def recognize_text(image_path):
    try:
        result = ocr.ocr(image_path)
    except Exception:
        return []

    if not result:
        return []

    texts: list[str] = []
    _walk_ocr_result(result, texts)
    return _dedupe_keep_order(texts)
