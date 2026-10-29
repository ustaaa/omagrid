"""Fault injection for the gate, independent of a compiled application."""
import copy
import unittest

from corpus import validate_report


def report():
    return {"schema": "gridcraft-check/1", "files": [{
        "path": "/temporary/book.xlsx", "opened": True, "error": None, "warnings": [],
        "calc": {"formulaCells": 1, "checked": 1, "matched": 1, "mismatched": 0,
                 "noOracle": 0, "staleCache": 0, "volatile": 0, "boolAsNumber": 0, "mismatches": []},
        "roundTrip": {"error": None, "differing": [], "categories": {"cells": {"equal": True, "diffs": 0}}}
    }]}


class StrictGate(unittest.TestCase):
    def test_only_path_is_normalized_without_mutating_evidence(self):
        raw = report()
        before = copy.deepcopy(raw)
        expected = copy.deepcopy(raw)
        expected["files"][0]["path"] = "<workbook>"
        self.assertEqual(validate_report(raw, 1), expected)
        self.assertEqual(raw, before)

    def test_warning_is_a_failure_even_without_calc_mismatch(self):
        raw = report()
        raw["files"][0]["warnings"] = ["Unsupported part omitted"]
        with self.assertRaisesRegex(ValueError, "open warnings"):
            validate_report(raw, 1)

    def test_missing_or_stale_oracle_and_skipped_volatile_are_not_success(self):
        for key in ("noOracle", "staleCache", "volatile", "boolAsNumber"):
            with self.subTest(key=key):
                raw = report()
                raw["files"][0]["calc"][key] = 1
                with self.assertRaisesRegex(ValueError, key):
                    validate_report(raw, 1)

    def test_silent_formula_removal_or_category_difference_fails(self):
        with self.assertRaises(ValueError):
            validate_report(report(), 2)
        raw = report()
        raw["files"][0]["roundTrip"]["categories"]["cells"]["diffs"] = 1
        with self.assertRaisesRegex(ValueError, "category cells"):
            validate_report(raw, 1)


if __name__ == "__main__":
    unittest.main()
