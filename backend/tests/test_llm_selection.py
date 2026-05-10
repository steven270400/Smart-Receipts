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
            "item A 8.00",
            "subtotal 8.00",
            "total 12.50",
            "date 2026-03-29",
            "alipay",
        ]

        def fake_select(_clean_texts, _candidates):
            return (
                {
                    "merchant_id": None,
                    "amount_id": "a0",
                    "date_id": "d0",
                    "payment_method_id": "p0",
                    "category_id": None,
                    "amount_judgement": [{"candidate_id": "n0", "is_amount": True, "reason": "amount"}],
                    "excluded_numeric_ids": [],
                    "confidence": {"amount": 0.9},
                    "reason": "pick highest scored candidates",
                },
                {"model": "fake", "latency_ms": 1},
            )

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=fake_select):
            info, meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["amount"], 12.50)
        self.assertEqual(info["date"], "2026-03-29")
        self.assertEqual(info["payment_method"], "支付宝")
        self.assertEqual(meta.get("match_status"), "matched")
        self.assertIsNone(meta.get("match_failure_reason"))

    def test_llm_unknown_id_marks_failed_fallback(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = ["Date 2026/3/9", "TOTAL 5.20"]

        def fake_select(_clean_texts, _candidates):
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

        self.assertEqual(info["amount"], 5.20)
        self.assertEqual(meta.get("match_status"), "failed_fallback_auto")
        self.assertEqual(meta.get("match_failure_reason"), "invalid_or_missing_amount_selection")

    def test_llm_wrong_selection_overridden_marks_failed(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = ["原价13.00*1 12.06"]

        def fake_select(_clean_texts, candidates):
            front = next(item for item in candidates["amount"] if float(item["parsed_value"]) == 13.0)
            trailing = next(item for item in candidates["amount"] if float(item["parsed_value"]) == 12.06)
            return (
                {
                    "merchant_id": None,
                    "amount_id": front["id"],
                    "date_id": None,
                    "payment_method_id": None,
                    "category_id": None,
                    "amount_judgement": [
                        {"candidate_id": front["numeric_id"], "is_amount": True, "reason": "wrong"},
                        {"candidate_id": trailing["numeric_id"], "is_amount": False, "reason": "wrong"},
                    ],
                    "excluded_numeric_ids": [trailing["numeric_id"]],
                    "confidence": {"amount": 0.2},
                    "reason": "wrong selection",
                },
                {"model": "fake", "latency_ms": 1},
            )

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=fake_select):
            info, meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["amount"], 12.06)
        self.assertEqual(meta.get("amount_override_reason"), "multiplier_trailing_amount_priority")
        self.assertEqual(meta.get("match_status"), "failed_fallback_auto")
        self.assertEqual(meta.get("match_failure_reason"), "amount_overridden_to_rule_based")

    def test_llm_selects_trailing_amount_matches(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = ["原价13.00*1 12.06"]

        def fake_select(_clean_texts, candidates):
            trailing = next(item for item in candidates["amount"] if float(item["parsed_value"]) == 12.06)
            return (
                {
                    "merchant_id": None,
                    "amount_id": trailing["id"],
                    "date_id": None,
                    "payment_method_id": None,
                    "category_id": None,
                    "amount_judgement": [{"candidate_id": trailing["numeric_id"], "is_amount": True, "reason": "ok"}],
                    "excluded_numeric_ids": [],
                    "confidence": {"amount": 0.9},
                    "reason": "correct selection",
                },
                {"model": "fake", "latency_ms": 1},
            )

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=fake_select):
            info, meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["amount"], 12.06)
        self.assertEqual(meta.get("match_status"), "matched")
        self.assertIsNone(meta.get("match_failure_reason"))

    def test_llm_exception_marks_failed_and_fallback(self):
        os.environ["EXTRACT_LLM_ENABLE"] = "1"
        texts = ["TOTAL 5.20"]

        with patch("backend.llm_service.select_receipt_fields_from_candidates", side_effect=RuntimeError("boom")):
            info, meta = extract_receipt_info_with_meta(texts)

        self.assertEqual(info["amount"], 5.20)
        self.assertEqual(meta.get("match_status"), "failed_fallback_auto")
        self.assertEqual(meta.get("match_failure_reason"), "llm_error")


if __name__ == "__main__":
    unittest.main()
