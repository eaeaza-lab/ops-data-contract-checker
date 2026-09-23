import os
import tempfile
import unittest

from ops_contract_checker.store import RunStore
from ops_contract_checker.validation import Finding


class RunStoreTests(unittest.TestCase):
    def test_round_trip_preserves_order_and_nulls(self):
        findings = [
            Finding("schema", "missing column 'sku'"),
            Finding("required", "value is required", row=2, field="order_id"),
        ]
        with RunStore(":memory:") as store:
            run_id = store.save_run(
                "orders.csv", "synthetic-orders", "1.0.0", 3, findings,
                created_at="2026-01-01T00:00:00+00:00",
            )
            run = store.get_run(run_id)
            self.assertEqual(run.input_path, "orders.csv")
            self.assertEqual(run.contract_name, "synthetic-orders")
            self.assertEqual(run.record_count, 3)
            self.assertEqual(run.finding_count, 2)
            self.assertEqual(run.created_at, "2026-01-01T00:00:00+00:00")
            self.assertEqual(store.get_findings(run_id), findings)

    def test_runs_are_separate(self):
        with RunStore(":memory:") as store:
            first = store.save_run("a.csv", "c", "1", 1, [Finding("type", "bad", 1, "x")])
            second = store.save_run("b.csv", "c", "1", 2, [])
            self.assertNotEqual(first, second)
            self.assertEqual(len(store.get_findings(first)), 1)
            self.assertEqual(store.get_findings(second), [])
            self.assertEqual([r.id for r in store.list_runs()], [first, second])

    def test_missing_run(self):
        with RunStore(":memory:") as store:
            self.assertIsNone(store.get_run(99))
            self.assertEqual(store.get_findings(99), [])

    def test_persists_on_disk(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "runs.sqlite")
            with RunStore(path) as store:
                run_id = store.save_run("a.json", "c", "1", 1, [Finding("date", "late", 1, "d")])
            with RunStore(path) as store:
                self.assertEqual(store.get_findings(run_id), [Finding("date", "late", 1, "d")])


if __name__ == "__main__":
    unittest.main()
