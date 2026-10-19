"""Validate expense records from CSV files and summarize their amounts."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Mapping


@dataclass(frozen=True)
class Expense:
    """One validated expense.

    Attributes:
        spent_on: Calendar date on which the expense occurred.
        category: Non-empty expense category.
        amount: Non-negative amount represented exactly as a Decimal.
    """

    spent_on: date
    category: str
    amount: Decimal


@dataclass(frozen=True)
class ExpenseSummary:
    """Aggregated totals for a collection of expenses."""

    category_totals: dict[str, Decimal]
    grand_total: Decimal
    expense_count: int


def parse_expenses(rows: Iterable[Mapping[str, str]]) -> list[Expense]:
    """Validate mapping records and convert them into expenses.

    Each record must contain ``date``, ``category``, and ``amount`` fields.
    Dates use ISO ``YYYY-MM-DD`` format and amounts must be finite,
    non-negative decimal numbers.

    Args:
        rows: Iterable of records, usually rows returned by ``csv.DictReader``.

    Returns:
        Validated expenses in the same order as the input records.

    Raises:
        ValueError: If a record is missing a required field or contains an
            invalid date, empty category, or invalid/negative amount.
    """
    required_fields = {"date", "category", "amount"}
    expenses: list[Expense] = []

    for row_number, row in enumerate(rows, start=2):
        missing_fields = required_fields.difference(row)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"Row {row_number}: missing required field(s): {missing}")

        try:
            date_text = row["date"].strip()
            spent_on = date.fromisoformat(date_text)
            if spent_on.isoformat() != date_text:
                raise ValueError
        except (AttributeError, TypeError, ValueError) as error:
            raise ValueError(
                f"Row {row_number}: date must use YYYY-MM-DD format"
            ) from error

        try:
            category = row["category"].strip()
        except (AttributeError, TypeError) as error:
            raise ValueError(f"Row {row_number}: category must be text") from error
        if not category:
            raise ValueError(f"Row {row_number}: category cannot be empty")

        try:
            amount = Decimal(row["amount"].strip())
        except (AttributeError, InvalidOperation, TypeError, ValueError) as error:
            raise ValueError(f"Row {row_number}: amount must be a decimal number") from error

        if not amount.is_finite() or amount < 0:
            raise ValueError(f"Row {row_number}: amount must be finite and non-negative")

        expenses.append(Expense(spent_on=spent_on, category=category, amount=amount))

    return expenses


def load_expenses(csv_path: str | Path) -> list[Expense]:
    """Read and validate expenses from a CSV file.

    The CSV header must include ``date``, ``category``, and ``amount``.

    Args:
        csv_path: Path to the UTF-8 (optionally BOM-prefixed) CSV input file.

    Returns:
        Validated expenses in file order; an empty list for a header-only file.

    Raises:
        OSError: If the file cannot be opened or read.
        ValueError: If the required columns or valid expense data are absent.
    """
    with Path(csv_path).open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if reader.fieldnames is None:
            raise ValueError("CSV file is missing a header row")

        missing_fields = {"date", "category", "amount"}.difference(reader.fieldnames)
        if missing_fields:
            missing = ", ".join(sorted(missing_fields))
            raise ValueError(f"CSV file is missing required column(s): {missing}")

        return parse_expenses(reader)


def summarize_expenses(expenses: Iterable[Expense]) -> ExpenseSummary:
    """Calculate per-category and overall totals.

    Args:
        expenses: Validated expenses to aggregate.

    Returns:
        An ``ExpenseSummary``; empty input produces zero totals and count.
    """
    category_totals: dict[str, Decimal] = {}
    grand_total = Decimal("0")
    expense_count = 0

    for expense in expenses:
        category_totals[expense.category] = (
            category_totals.get(expense.category, Decimal("0")) + expense.amount
        )
        grand_total += expense.amount
        expense_count += 1

    return ExpenseSummary(
        category_totals=category_totals,
        grand_total=grand_total,
        expense_count=expense_count,
    )


def main(argv: list[str] | None = None) -> int:
    """Run the CSV expense-report command-line interface.

    Args:
        argv: Optional command-line arguments, excluding the program name.
            When omitted, arguments are read from the process command line.

    Returns:
        Exit status: zero on success, or two for invalid input or file errors.
    """
    parser = argparse.ArgumentParser(description="Summarize expenses from a CSV file.")
    parser.add_argument("csv_path", type=Path, help="CSV file with date, category, amount columns")
    args = parser.parse_args(argv)

    try:
        summary = summarize_expenses(load_expenses(args.csv_path))
    except (OSError, ValueError) as error:
        parser.error(str(error))

    print(f"Expenses: {summary.expense_count}")
    for category, amount in sorted(summary.category_totals.items()):
        print(f"{category}: {amount:.2f}")
    print(f"Total: {summary.grand_total:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
