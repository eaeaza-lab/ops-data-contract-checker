import tempfile
import unittest
from pathlib import Path

from ops_contract_checker.readers import read_csv_text, read_json_text, read_records


class CsvReaderTests(unittest.TestCase):
    def test_reads_records_in_file_order(self) -> None:
        result = read_csv_text("record_id,currency\nSYN-1,TST\nSYN-2,TST\n")
        self.assertTrue(result.ok)
        self.assertEqual(result.columns, ["record_id", "currency"])
        self.assertEqual([r["record_id"] for r in result.records], ["SYN-1", "SYN-2"])

    def test_bom_and_blank_lines(self) -> None:
        result = read_csv_text("﻿a,b\n1,2\n\n3,4\n")
        self.assertTrue(result.ok)
        self.assertEqual(len(result.records), 2)

    def test_reports_wrong_column_count_and_duplicate_header(self) -> None:
        result = read_csv_text("a,a\n1\n")
        messages = [str(p) for p in result.problems]
        self.assertIn("CSV header repeats column 'a'", messages)
        self.assertIn("record 1: expected 2 values but found 1", messages)

    def test_empty_input(self) -> None:
        self.assertFalse(read_csv_text("  \n").ok)


class JsonReaderTests(unittest.TestCase):
    def test_list_and_records_wrapper(self) -> None:
        a = read_json_text('[{"id": "SYN-1", "n": 1}]')
        b = read_json_text('{"records": [{"id": "SYN-1", "n": 1}]}')
        self.assertEqual(a.records, b.records)
        self.assertEqual(a.columns, ["id", "n"])

    def test_invalid_json_and_shape(self) -> None:
        self.assertIn("invalid JSON", str(read_json_text("{oops").problems[0]))
        self.assertFalse(read_json_text('"text"').ok)

    def test_non_object_record(self) -> None:
        result = read_json_text('[{"a": 1}, 5]')
        self.assertEqual(len(result.records), 1)
        self.assertEqual(str(result.problems[0]), "record 2: record is not a JSON object")


class ReadRecordsTests(unittest.TestCase):
    def test_dispatch_and_errors(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            csv_path = Path(tmp) / "x.csv"
            csv_path.write_text("a\n1\n", encoding="utf-8")
            self.assertEqual(read_records(csv_path).records, [{"a": "1"}])
            self.assertIn("not found", str(read_records(Path(tmp) / "missing.json").problems[0]))
            self.assertIn("unsupported", str(read_records(Path(tmp) / "x.txt").problems[0]))
            bad = Path(tmp) / "bad.csv"
            bad.write_bytes(b"\xff\xfe\x00")
            self.assertIn("UTF-8", str(read_records(bad).problems[0]))


if __name__ == "__main__":
    unittest.main()
