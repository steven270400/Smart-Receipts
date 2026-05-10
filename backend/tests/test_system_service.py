import unittest
from unittest.mock import patch

from backend.core.exceptions import NotFoundException, ParamException
from backend.services import system_service


class SystemServiceTests(unittest.TestCase):
    def test_list_categories_service_normalizes_rows(self):
        rows = [
            {"id": 1, "name": "餐饮", "receipt_count": 3, "latest_time": "2026-04-21 12:00:00"},
            {"id": 2, "name": "其他", "receipt_count": None, "latest_time": None},
        ]
        with patch("backend.services.system_service.db_service.list_categories_with_usage", return_value=rows):
            result = system_service.list_categories_service()

        self.assertEqual(result[0]["id"], 1)
        self.assertEqual(result[0]["name"], "餐饮")
        self.assertEqual(result[0]["receipt_count"], 3)
        self.assertEqual(result[1]["receipt_count"], 0)

    def test_create_category_service_duplicate_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.create_category",
            side_effect=ValueError("分类名称已存在"),
        ):
            with self.assertRaises(ParamException):
                system_service.create_category_service("餐饮")

    def test_delete_category_service_not_found_raises_not_found(self):
        with patch(
            "backend.services.system_service.db_service.delete_category_with_migration",
            side_effect=LookupError("分类不存在"),
        ):
            with self.assertRaises(NotFoundException):
                system_service.delete_category_service(999)

    def test_delete_category_service_default_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.delete_category_with_migration",
            side_effect=RuntimeError("默认分类不允许删除"),
        ):
            with self.assertRaises(ParamException):
                system_service.delete_category_service(1)

    def test_rename_category_service_success(self):
        with patch(
            "backend.services.system_service.db_service.rename_category",
            return_value={"id": 10, "name": "新分类"},
        ):
            result = system_service.rename_category_service(10, "新分类")
        self.assertEqual(result["id"], 10)
        self.assertEqual(result["name"], "新分类")

    def test_rename_category_service_not_found_raises_not_found(self):
        with patch(
            "backend.services.system_service.db_service.rename_category",
            side_effect=LookupError("分类不存在"),
        ):
            with self.assertRaises(NotFoundException):
                system_service.rename_category_service(999, "新分类")

    def test_rename_category_service_duplicate_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.rename_category",
            side_effect=ValueError("分类名称已存在"),
        ):
            with self.assertRaises(ParamException):
                system_service.rename_category_service(2, "餐饮")

    def test_rename_category_service_default_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.rename_category",
            side_effect=RuntimeError("默认分类不允许修改"),
        ):
            with self.assertRaises(ParamException):
                system_service.rename_category_service(5, "兜底分类")

    def test_create_payment_method_service_duplicate_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.create_payment_method",
            side_effect=ValueError("支付方式名称已存在"),
        ):
            with self.assertRaises(ParamException):
                system_service.create_payment_method_service("支付宝")

    def test_rename_payment_method_service_not_found_raises_not_found(self):
        with patch(
            "backend.services.system_service.db_service.rename_payment_method",
            side_effect=LookupError("支付方式不存在"),
        ):
            with self.assertRaises(NotFoundException):
                system_service.rename_payment_method_service(123, "银行卡")

    def test_rename_payment_method_service_duplicate_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.rename_payment_method",
            side_effect=ValueError("支付方式名称已存在"),
        ):
            with self.assertRaises(ParamException):
                system_service.rename_payment_method_service(2, "支付宝")

    def test_delete_payment_method_service_success(self):
        with patch(
            "backend.services.system_service.db_service.delete_payment_method_with_migration",
            return_value=None,
        ):
            system_service.delete_payment_method_service(10)

    def test_delete_payment_method_service_not_found_raises_not_found(self):
        with patch(
            "backend.services.system_service.db_service.delete_payment_method_with_migration",
            side_effect=LookupError("支付方式不存在"),
        ):
            with self.assertRaises(NotFoundException):
                system_service.delete_payment_method_service(999)

    def test_delete_payment_method_service_default_raises_param_exception(self):
        with patch(
            "backend.services.system_service.db_service.delete_payment_method_with_migration",
            side_effect=RuntimeError("默认支付方式不允许删除"),
        ):
            with self.assertRaises(ParamException):
                system_service.delete_payment_method_service(6)


if __name__ == "__main__":
    unittest.main()

