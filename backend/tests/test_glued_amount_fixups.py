import unittest

from backend.extract_service import extract_receipt_info
from backend.text_fixups import repair_glued_qty_amount


class GluedAmountFixupTests(unittest.TestCase):
    def test_repair_glued_qty_amount_variants(self):
        cases = [
            ("原价13.00*112.06", "原价13.00*1 12.06"),
            ("原价8.50x212.00", "原价8.50x2 12.00"),
            ("原价8.50X212.00", "原价8.50X2 12.00"),
            ("原价8.50×10105.80", "原价8.50×10 105.80"),
            ("原价8.50*19.9", "原价8.50*1 9.9"),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                self.assertEqual(repair_glued_qty_amount(source), expected)

    def test_repair_keeps_non_glued_numbers_unchanged(self):
        cases = [
            "实付 12.06",
            "原价13.00*1 12.06",
            "订单号 202603091230",
            "手机号 13800138000",
            "*12.06",
        ]
        for source in cases:
            with self.subTest(source=source):
                self.assertEqual(repair_glued_qty_amount(source), source)

    def test_extract_amount_with_glued_qty_amount(self):
        cases = [
            ("9.3折，原价13.00*112.06", 12.06),
            ("原价8.50x212.00", 12.00),
            ("原价8.50×10105.80", 105.80),
            ("原价8.50*19.9", 9.9),
        ]
        for source, expected in cases:
            with self.subTest(source=source):
                result = extract_receipt_info([source])
                self.assertEqual(result["amount"], expected)

    def test_extract_keeps_plain_number_behavior(self):
        result = extract_receipt_info(["订单号 202603091230", "实付 12.06"])
        self.assertEqual(result["amount"], 12.06)


if __name__ == "__main__":
    unittest.main()
