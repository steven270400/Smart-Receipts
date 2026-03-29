import unittest

from backend.extract_service import extract_receipt_info


class ExtractServiceTests(unittest.TestCase):
    def test_prefers_total_amount_hints(self):
        texts = [
            "商品A 8.00",
            "小计 8.00",
            "总计 12.50",
            "日期 2026-03-29",
            "支付宝",
        ]

        result = extract_receipt_info(texts)

        self.assertEqual(result["amount"], 12.50)
        self.assertEqual(result["date"], "2026-03-29")
        self.assertEqual(result["payment_method"], "支付宝")

    def test_normalizes_slash_date(self):
        texts = ["Date 2026/3/9", "TOTAL 5.20"]

        result = extract_receipt_info(texts)

        self.assertEqual(result["date"], "2026-03-09")
        self.assertEqual(result["amount"], 5.20)

    def test_defaults_for_empty_input(self):
        result = extract_receipt_info([])

        self.assertIsNone(result["merchant"])
        self.assertIsNone(result["amount"])
        self.assertIsNone(result["date"])
        self.assertEqual(result["category"], "其他")

    def test_prefers_deduction_over_balance_amount(self):
        texts = [
            "支付成功",
            "扣款金额 100",
            "余额 980.26",
            "日期 2026-03-29",
        ]

        result = extract_receipt_info(texts)

        self.assertEqual(result["amount"], 100.0)

    def test_negative_amount_wins_even_with_balance_keyword(self):
        texts = [
            "账户变动",
            "余额 -100.00",
            "余额 980.26",
            "日期 2026-03-29",
        ]

        result = extract_receipt_info(texts)

        self.assertEqual(result["amount"], 100.0)


if __name__ == "__main__":
    unittest.main()
