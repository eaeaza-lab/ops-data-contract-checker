import copy
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

from ops_contract_checker.contract import (
    ContractError,
    bundled_contract_paths,
    load_contract,
    parse_contract,
)


def minimal() -> dict:
    return {
        "format_version": 1,
        "name": "synthetic-min",
        "version": "1.0.0",
        "fields": [
            {"name": "record_id", "required": True},
            {"name": "amount", "type": "number"},
            {"name": "seen_on", "type": "date"},
        ],
    }


class BundledContractTests(unittest.TestCase):
    def test_bundled_examples_exist_and_load(self) -> None:
        paths = bundled_contract_paths()
        self.assertGreaterEqual(len(paths), 2)
        for path in paths:
            with self.subTest(path=path.name):
                contract = load_contract(path)
                self.assertEqual(contract.format_version, 1)
                self.assertTrue(contract.required_fields)

    def test_orders_contract_details(self) -> None:
        path = next(p for p in bundled_contract_paths() if "orders" in p.name)
        contract = load_contract(path)
        self.assertEqual(contract.name, "synthetic-orders")
        self.assertEqual(contract.duplicate_keys, ("record_id",))
        self.assertEqual(contract.totals[0].component_fields, ("net_amount", "tax_amount"))
        self.assertEqual(contract.date_rules[0].min, date(2026, 1, 1))
        self.assertEqual(contract.currency_rules[0].allowed, ("TST", "XTS"))


class ParseContractTests(unittest.TestCase):
    def test_minimal_contract_defaults(self) -> None:
        contract = parse_contract(minimal())
        self.assertEqual(contract.field_names, ("record_id", "amount", "seen_on"))
        self.assertEqual(contract.required_fields, ("record_id",))
        self.assertEqual(contract.fields[0].type, "string")
        self.assertEqual(contract.totals, ())

    def assert_invalid(self, data: object, fragment: str) -> None:
        with self.assertRaises(ContractError) as ctx:
            parse_contract(data)
        self.assertTrue(
            any(fragment in p for p in ctx.exception.problems),
            f"{fragment!r} not in {ctx.exception.problems}",
        )

    def test_rejects_non_object(self) -> None:
        self.assert_invalid([], "JSON object")

    def test_rejects_unsupported_version_and_unknown_keys(self) -> None:
        data = minimal()
        data["format_version"] = 2
        data["surprise"] = 1
        with self.assertRaises(ContractError) as ctx:
            parse_contract(data)
        joined = "; ".join(ctx.exception.problems)
        self.assertIn("format_version", joined)
        self.assertIn("surprise", joined)

    def test_rejects_bad_fields(self) -> None:
        data = minimal()
        data["fields"].append({"name": "amount"})
        data["fields"].append({"name": "x", "type": "blob"})
        with self.assertRaises(ContractError) as ctx:
            parse_contract(data)
        joined = "; ".join(ctx.exception.problems)
        self.assertIn("duplicates", joined)
        self.assertIn("type must be one of", joined)

    def test_rejects_undeclared_field_references(self) -> None:
        data = minimal()
        data["duplicate_keys"] = ["missing"]
        data["identifiers"] = [{"field": "missing", "pattern": "^a$"}]
        self.assert_invalid(data, "duplicate_keys[0]")

    def test_rejects_bad_regex(self) -> None:
        data = minimal()
        data["identifiers"] = [{"field": "record_id", "pattern": "("}]
        self.assert_invalid(data, "regular expression")

    def test_totals_require_numeric_fields(self) -> None:
        data = minimal()
        data["totals"] = [{"total_field": "amount", "component_fields": ["record_id"]}]
        self.assert_invalid(data, "must be numeric")

    def test_date_rules(self) -> None:
        data = minimal()
        data["date_rules"] = [{"field": "seen_on", "min": "2026-13-01"}]
        self.assert_invalid(data, "not a valid ISO date")
        data = copy.deepcopy(minimal())
        data["date_rules"] = [{"field": "seen_on", "min": "2026-05-01", "max": "2026-01-01"}]
        self.assert_invalid(data, "must not be after")
        data["date_rules"] = [{"field": "amount", "min": "2026-01-01"}]
        self.assert_invalid(data, "type 'date'")

    def test_currency_rules_need_allowed_values(self) -> None:
        data = minimal()
        data["currency_rules"] = [{"field": "record_id", "allowed": []}]
        self.assert_invalid(data, "non-empty list of strings")


class LoadContractTests(unittest.TestCase):
    def test_missing_file_and_bad_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ContractError):
                load_contract(Path(tmp) / "nope.json")
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(ContractError) as ctx:
                load_contract(bad)
            self.assertIn("not valid JSON", str(ctx.exception))

    def test_loads_valid_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "c.json"
            path.write_text(json.dumps(minimal()), encoding="utf-8")
            self.assertEqual(load_contract(path).name, "synthetic-min")


if __name__ == "__main__":
    unittest.main()
