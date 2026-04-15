import unittest

from backend.extract_service import _now_china_naive, extract_receipt_info


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

    def test_phone_tail_number_is_not_amount(self):
        texts = [
            "顾客号码：手机尾号3124",
            "虚拟号码：17895011878转0687",
            "9.3折，原价13.00*1",
            "12.06",
        ]
        result = extract_receipt_info(texts)
        self.assertEqual(result["amount"], 12.06)

    def test_prefers_paid_amount_over_original_price(self):
        texts = ["9.3折，原价13.00*1", "实付 12.06"]
        result = extract_receipt_info(texts)
        self.assertEqual(result["amount"], 12.06)

    def test_infers_recent_past_date_for_month_day_time(self):
        texts = ["下单时间：04-06 21:46", "实付 12.06"]
        result = extract_receipt_info(texts)

        now_cn = _now_china_naive()
        expected_year = now_cn.year
        if (4, 6, 21, 46) > (now_cn.month, now_cn.day, now_cn.hour, now_cn.minute):
            expected_year -= 1
        self.assertEqual(result["date"], f"{expected_year}-04-06")

    def test_infers_recent_past_date_for_glued_month_day_time(self):
        texts = ["单间：04-0621:46", "实付 12.06"]
        result = extract_receipt_info(texts)

        now_cn = _now_china_naive()
        expected_year = now_cn.year
        if (4, 6, 21, 46) > (now_cn.month, now_cn.day, now_cn.hour, now_cn.minute):
            expected_year -= 1
        self.assertEqual(result["date"], f"{expected_year}-04-06")


if __name__ == "__main__":
    unittest.main()
