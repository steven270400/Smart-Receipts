try:
    from paddleocr import PaddleOCR  # type: ignore
except ModuleNotFoundError:
    PaddleOCR = None

from backend.text_fixups import repair_glued_qty_amount

_ocr = None


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
        if (
            len(node) == 2
            and isinstance(node[0], str)
            and isinstance(node[1], (int, float))
        ):
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


def _normalize_ocr_texts(texts: list[str]) -> list[str]:
    normalized: list[str] = []
    for text in texts:
        repaired = repair_glued_qty_amount(text).strip()
        if repaired:
            normalized.append(repaired)
    return normalized


def recognize_text(image_path: str) -> list[str]:
    global _ocr

    if PaddleOCR is None:
        return []

    if _ocr is None:
        _ocr = PaddleOCR(
            lang="ch",
            use_angle_cls=False,
            use_gpu=False,   # 先强制 CPU，恢复稳定
            show_log=False,  # 关闭 DEBUG 日志
        )

    try:
        result = _ocr.ocr(image_path, cls=False)
    except Exception as e:
        print("OCR GPU/Runtime error:", repr(e))
        return []

    if not result:
        return []

    texts: list[str] = []
    _walk_ocr_result(result, texts)
    return _dedupe_keep_order(_normalize_ocr_texts(texts))
