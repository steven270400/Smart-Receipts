import unittest
from unittest.mock import patch

from backend import ocr_service


class _FakeOCR:
    def __init__(self, result):
        self._result = result

    def ocr(self, _image_path, cls=False):
        return self._result


class OcrServiceTests(unittest.TestCase):
    def test_normalize_ocr_texts_repairs_glued_values(self):
        texts = ["原价13.00*112.06", "实付 12.06"]
        self.assertEqual(
            ocr_service._normalize_ocr_texts(texts),
            ["原价13.00*1 12.06", "实付 12.06"],
        )

    def test_recognize_text_returns_repaired_ocr_result(self):
        fake_result = [{"rec_texts": ["原价13.00*112.06", "实付 12.06"]}]
        fake_ocr = _FakeOCR(fake_result)

        with patch.object(ocr_service, "PaddleOCR", object()), patch.object(
            ocr_service, "_ocr", fake_ocr
        ):
            result = ocr_service.recognize_text("dummy.jpg")

        self.assertEqual(result, ["原价13.00*1 12.06", "实付 12.06"])

    def test_recognize_text_keeps_non_glued_values(self):
        fake_result = [{"rec_texts": ["订单号 202603091230", "实付 12.06"]}]
        fake_ocr = _FakeOCR(fake_result)

        with patch.object(ocr_service, "PaddleOCR", object()), patch.object(
            ocr_service, "_ocr", fake_ocr
        ):
            result = ocr_service.recognize_text("dummy.jpg")

        self.assertEqual(result, ["订单号 202603091230", "实付 12.06"])


if __name__ == "__main__":
    unittest.main()
