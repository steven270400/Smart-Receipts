import unittest

from backend.extract_service import _now_china_naive, build_candidates, extract_receipt_info


class ExtractServiceTests(unittest.TestCase):
    def test_prefers_total_amount_hints(self):
        texts = [
            "item A 8.00",
            "subtotal 8.00",
            "total 12.50",
            "date 2026-03-29",
            "alipay",
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
            "payment success",
            "扣款金额 100",
            "balance 980.26",
            "date 2026-03-29",
        ]
        result = extract_receipt_info(texts)
        self.assertEqual(result["amount"], 100.0)

    def test_negative_amount_wins_even_with_balance_keyword(self):
        texts = [
            "account change",
            "balance -100.00",
            "balance 980.26",
            "date 2026-03-29",
        ]
        result = extract_receipt_info(texts)
        self.assertEqual(result["amount"], 100.0)

    def test_phone_tail_number_is_not_amount(self):
        texts = [
            "customer no: phone tail 3124",
            "virtual no: 17895011878 transfer 0687",
            "9.3 discount, original price 13.00*1",
            "12.06",
        ]
        result = extract_receipt_info(texts)
        self.assertEqual(result["amount"], 12.06)

    def test_prefers_paid_amount_over_original_price(self):
        texts = ["9.3 discount, original price 13.00*1", "paid 12.06"]
        result = extract_receipt_info(texts)
        self.assertEqual(result["amount"], 12.06)

    def test_build_candidates_marks_multiplier_trailing_amount(self):
        candidates = build_candidates(["原价13.00*1 12.06"], top_k=5)
        trailing = [item for item in candidates["amount"] if item.get("is_multiplier_trailing_amount")]
        self.assertTrue(trailing)
        self.assertEqual(float(trailing[0]["parsed_value"]), 12.06)
        self.assertEqual(candidates["amount"][0]["id"], trailing[0]["id"])

    def test_infers_recent_past_date_for_month_day_time(self):
        texts = ["order time: 04-06 21:46", "paid 12.06"]
        result = extract_receipt_info(texts)

        now_cn = _now_china_naive()
        expected_year = now_cn.year
        if (4, 6, 21, 46) > (now_cn.month, now_cn.day, now_cn.hour, now_cn.minute):
            expected_year -= 1
        self.assertEqual(result["date"], f"{expected_year}-04-06")

    def test_infers_recent_past_date_for_glued_month_day_time(self):
        texts = ["room: 04-0621:46", "paid 12.06"]
        result = extract_receipt_info(texts)

        now_cn = _now_china_naive()
        expected_year = now_cn.year
        if (4, 6, 21, 46) > (now_cn.month, now_cn.day, now_cn.hour, now_cn.minute):
            expected_year -= 1
        self.assertEqual(result["date"], f"{expected_year}-04-06")


if __name__ == "__main__":
    unittest.main()
