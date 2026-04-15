import os
import unittest
from unittest.mock import patch

from backend.extract_service import extract_receipt_info_with_meta


class LlmSelectionTests(unittest.TestCase):
    def setUp(self):
        self._old_env = dict(os.environ)

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._old_env)

    def test_llm_can_select_from_candidates(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = [
            "商品A 8.00",
            "小计 8.00",
            "总计 12.50",
            "日期 2026-03-29",
            "支付宝",
        ]

        def fake_select(clean_texts, candidates):
            return (
                {
                    "merchant_id": None,
                    "amount_id": "a0",
                    "date_id": "d0",
                    "payment_method_id": "p0",
                    "category_id": None,
                    "amount_judgement": [{"candidate_id": "n0", "is_amount": True, "reason": "金额"}],
                    "excluded_numeric_ids": [],
                    "confidence": {
                        "amount": 0.9,
                        "date": 0.9,
                        "payment_method": 0.8,
                        "merchant": 0.0,
                        "category": 0.0,
                    },
                    "reason": "pick highest scored candidates",
                },
                {"model": "fake", "latency_ms": 1},
            )

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=fake_select):
            info, meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["amount"], 12.50)
        self.assertEqual(info["date"], "2026-03-29")
        self.assertEqual(info["payment_method"], "支付宝")
        self.assertTrue(meta["llm_enabled"])
        self.assertTrue(meta["invoked"])
        self.assertIn("selection", meta)

    def test_llm_unknown_id_falls_back_to_baseline(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = ["Date 2026/3/9", "TOTAL 5.20"]

        def fake_select(clean_texts, candidates):
            return (
                {
                    "merchant_id": None,
                    "amount_id": "a999",
                    "date_id": "d999",
                    "payment_method_id": None,
                    "category_id": None,
                    "amount_judgement": [],
                    "excluded_numeric_ids": [],
                    "confidence": {},
                    "reason": "bad ids",
                },
                {"model": "fake", "latency_ms": 1},
            )

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=fake_select):
            info, meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["date"], "2026-03-09")
        self.assertEqual(info["amount"], 5.20)
        self.assertTrue(meta["invoked"])

    def test_llm_excluded_numeric_blocks_amount_override(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = [
            "总计 12.06",
            "顾客号码：手机尾号3124",
        ]

        def fake_select(clean_texts, candidates):
            selected_amount_id = candidates["amount"][0]["id"] if candidates["amount"] else None
            selected_numeric_id = candidates["amount"][0]["numeric_id"] if candidates["amount"] else None
            return (
                {
                    "merchant_id": None,
                    "amount_id": selected_amount_id,
                    "date_id": None,
                    "payment_method_id": None,
                    "category_id": None,
                    "amount_judgement": (
                        [{"candidate_id": selected_numeric_id, "is_amount": False, "reason": "判定为非金额"}]
                        if selected_numeric_id
                        else []
                    ),
                    "excluded_numeric_ids": [selected_numeric_id] if selected_numeric_id else [],
                    "confidence": {"amount": 0.1},
                    "reason": "exclude",
                },
                {"model": "fake", "latency_ms": 1},
            )

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=fake_select):
            info, _meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["amount"], 12.06)


if __name__ == "__main__":
    unittest.main()
