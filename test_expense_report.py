"""Unit tests for the expense CSV parser and summary calculations."""

import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from expense_report import Expense, load_expenses, parse_expenses, summarize_expenses


class ParseExpensesTests(unittest.TestCase):
    def test_parses_and_normalizes_valid_rows(self) -> None:
        result = parse_expenses(
            [{"date": "2026-01-02", "category": " Food ", "amount": "12.50"}]
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].category, "Food")
        self.assertEqual(result[0].amount, Decimal("12.50"))

    def test_rejects_missing_fields(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing required field"):
            parse_expenses([{"date": "2026-01-02", "category": "Food"}])

    def test_rejects_invalid_date_and_amount(self) -> None:
        invalid_rows = (
            {"date": "02/01/2026", "category": "Food", "amount": "2"},
            {"date": "20260102", "category": "Food", "amount": "2"},
            {"date": "2026-01-02", "category": " ", "amount": "2"},
            {"date": "2026-01-02", "category": "Food", "amount": "-2"},
            {"date": "2026-01-02", "category": "Food", "amount": "NaN"},
        )
        for row in invalid_rows:
            with self.subTest(row=row), self.assertRaises(ValueError):
                parse_expenses([row])


class ExpenseSummaryTests(unittest.TestCase):
    def test_sums_by_category_and_overall(self) -> None:
        expenses = [
            Expense(date=date(2026, 1, 2), category="Food", amount=Decimal("3.25")),
            Expense(date=date(2026, 1, 3), category="Food", amount=Decimal("1.75")),
            Expense(date=date(2026, 1, 4), category="Travel", amount=Decimal("5.00")),
        ]

        summary = summarize_expenses(expenses)

        self.assertEqual(
            summary.category_totals,
            {"Food": Decimal("5.00"), "Travel": Decimal("5.00")},
        )
        self.assertEqual(summary.grand_total, Decimal("10.00"))
        self.assertEqual(summary.expense_count, 3)

    def test_empty_input_has_zero_totals(self) -> None:
        summary = summarize_expenses([])

        self.assertEqual(summary.category_totals, {})
        self.assertEqual(summary.grand_total, Decimal("0"))
        self.assertEqual(summary.expense_count, 0)


class LoadExpensesTests(unittest.TestCase):
    def test_loads_csv_and_requires_header(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            csv_path = Path(directory) / "expenses.csv"
            with csv_path.open("w", encoding="utf-8", newline="") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=["date", "category", "amount"])
                writer.writeheader()
                writer.writerow({"date": "2026-01-02", "category": "Food", "amount": "3.25"})

            self.assertEqual(len(load_expenses(csv_path)), 1)

            csv_path.write_text("description,cost\nLunch,3.25\n", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing required column"):
                load_expenses(csv_path)


if __name__ == "__main__":
    unittest.main()
