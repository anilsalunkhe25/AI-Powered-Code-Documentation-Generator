# Expense Report: documented Python program

## Overview

`expense_report.py` is a small command-line utility that reads expense records
from a CSV file, validates them, and reports totals by category and overall.
It uses Python's standard library only. Monetary values use `Decimal` rather
than binary floating point to avoid floating-point rounding artifacts.

This example was documented with generative-AI assistance, then checked against
the implementation and its unit tests. The descriptions below reflect the
actual behavior of the source code.

## Input format

Provide a UTF-8 CSV file (a UTF-8 BOM is also accepted) with a header containing
these columns:

| Column | Format | Validation |
| --- | --- | --- |
| `date` | ISO date, `YYYY-MM-DD` | Must be a valid calendar date |
| `category` | Text | Leading/trailing whitespace is removed; value cannot be empty |
| `amount` | Decimal number | Must be finite and greater than or equal to zero |

Additional columns are ignored. A file containing only the header is valid and
produces a zero total.

Example:

```csv
date,category,amount
2026-01-02,Food,12.50
2026-01-03,Travel,8.00
2026-01-04,Food,5.25
```

Run it with:

```text
python expense_report.py expenses.csv
```

The program prints the number of expenses, sorted category totals, and the
grand total, with amounts formatted to two decimal places.

## Run in a web browser

Open `index.html` directly in a modern browser, then select the CSV file. No
server, Python installation, or package setup is required. The browser version
processes the selected file locally; it does not upload the CSV. Category and
grand totals use integer arithmetic internally and are displayed to two
decimal places using ties-to-even rounding, matching the Python report's
default decimal formatting. The browser version accepts decimal notation and
scientific notation; unusually large values beyond its safe processing limits
are reported as invalid.

## Function and method reference

### `Expense`

Immutable record containing:

| Attribute | Type | Meaning |
| --- | --- | --- |
| `spent_on` | `datetime.date` | Date of the expense |
| `category` | `str` | Normalized, non-empty category |
| `amount` | `decimal.Decimal` | Validated non-negative amount |

### `ExpenseSummary`

Frozen summary record containing:

| Attribute | Type | Meaning |
| --- | --- | --- |
| `category_totals` | `dict[str, Decimal]` | Sum of amounts for each category |
| `grand_total` | `Decimal` | Sum of all amounts |
| `expense_count` | `int` | Number of processed expenses |

### `parse_expenses(rows)`

Converts an iterable of mappings (such as rows from `csv.DictReader`) into a
list of `Expense` records. It expects each mapping to contain `date`,
`category`, and `amount`.

- **Input:** `Iterable[Mapping[str, str]]`
- **Returns:** `list[Expense]`, preserving input order.
- **Raises:** `ValueError` for a missing field, invalid date, empty category,
  or invalid, non-finite, or negative amount. The error identifies the row
  (data rows are numbered starting at 2, following the CSV header convention).

### `load_expenses(csv_path)`

Opens the CSV file as UTF-8 (accepting a BOM), checks its header, and delegates
record validation to `parse_expenses`.

- **Input:** `str | pathlib.Path`
- **Returns:** `list[Expense]`; an empty list for a header-only file.
- **Raises:** `OSError` if opening/reading the file fails; `ValueError` if the
  header is missing required columns or any record is invalid.

### `summarize_expenses(expenses)`

Aggregates already-validated `Expense` records. Category labels are matched
exactly after the normalization performed during parsing.

- **Input:** `Iterable[Expense]`
- **Returns:** `ExpenseSummary`. Empty input yields an empty category map, zero
  grand total, and count zero.
- **Raises:** No exceptions are explicitly raised for valid `Expense` inputs.

### `main(argv=None)`

Parses command-line arguments, loads and summarizes the requested CSV, and
prints the report.

- **Input:** Optional `list[str]` of arguments, excluding the executable name.
  If omitted, arguments are taken from the process command line.
- **Returns:** `0` on success.
- **Raises/exits:** `argparse` reports invalid arguments, file errors, or data
  validation errors and exits with status `2`.

## Logic verification

The implementation was checked against the descriptions above:

1. `load_expenses` checks for a header and the three required column names
   before parsing data, and opens with `utf-8-sig`.
2. `parse_expenses` strips category and input-value whitespace, uses
   `date.fromisoformat` and `Decimal`, and rejects empty categories,
   non-finite amounts, and negative amounts.
3. `summarize_expenses` adds each amount both to its category and to the grand
   total and increments the count once per record.
4. `main` sorts category labels for display and formats printed amounts to two
   decimal places; internally, totals retain `Decimal` precision.

Run the unit tests with:

```text
python -m unittest -v
```
