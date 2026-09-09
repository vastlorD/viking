import json
import os
import tempfile
import unittest
from pathlib import Path

from integrity_guard.core import IntegrityError, build_baseline, compare, scan, verify_baseline
from integrity_guard.storage import atomic_json, create_key, read_json, read_key


class IntegrityCoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "target"
        self.root.mkdir()
        (self.root / "config.txt").write_text("version=1\n", encoding="utf-8")
        (self.root / "folder").mkdir()
        (self.root / "folder" / "data.bin").write_bytes(b"abc")
        self.key = b"k" * 32

    def test_clean_scan(self):
        baseline = build_baseline(self.root, self.key)
        verify_baseline(baseline, self.key)
        self.assertEqual(compare(baseline["entries"], scan(self.root))["status"], "clean")

    def test_created_modified_and_removed(self):
        baseline = build_baseline(self.root, self.key)
        (self.root / "config.txt").write_text("version=2\n", encoding="utf-8")
        (self.root / "folder" / "data.bin").unlink()
        (self.root / "new.txt").write_text("new", encoding="utf-8")
        result = compare(baseline["entries"], scan(self.root))
        self.assertEqual(result["status"], "changed")
        self.assertEqual(result["created"], ["new.txt"])
        self.assertEqual(result["modified"], ["config.txt"])
        self.assertEqual(result["removed"], ["folder/data.bin"])

    def test_touch_without_content_change_is_clean(self):
        baseline = build_baseline(self.root, self.key)
        os.utime(self.root / "config.txt", None)
        self.assertEqual(compare(baseline["entries"], scan(self.root))["status"], "clean")

    def test_excludes_and_protected_files(self):
        ignored = self.root / "cache.tmp"
        protected = self.root / "baseline.json"
        ignored.write_text("one")
        protected.write_text("base")
        result = scan(self.root, excludes=["*.tmp"], protected_paths=[protected])
        self.assertNotIn("cache.tmp", result)
        self.assertNotIn("baseline.json", result)

    def test_tampered_baseline_and_wrong_key_are_rejected(self):
        baseline = build_baseline(self.root, self.key)
        baseline["entries"]["config.txt"]["size"] = 999
        with self.assertRaises(IntegrityError):
            verify_baseline(baseline, self.key)
        with self.assertRaises(IntegrityError):
            verify_baseline(build_baseline(self.root, self.key), b"x" * 32)

    def test_invalid_structure_is_rejected(self):
        baseline = build_baseline(self.root, self.key)
        baseline["entries"] = []
        with self.assertRaises(IntegrityError):
            verify_baseline(baseline, self.key)

    def test_missing_root_and_short_key_are_rejected(self):
        with self.assertRaises(IntegrityError):
            scan(self.root / "missing")
        with self.assertRaises(IntegrityError):
            build_baseline(self.root, b"short")

    @unittest.skipIf(os.name == "nt", "Criar symlink no Windows exige permissão específica")
    def test_symlink_target_change_is_detected_without_following_it(self):
        outside = Path(self.temporary.name) / "outside.txt"
        outside.write_text("secret")
        link = self.root / "shortcut"
        link.symlink_to(outside)
        baseline = build_baseline(self.root, self.key)
        link.unlink()
        link.symlink_to("config.txt")
        result = compare(baseline["entries"], scan(self.root))
        self.assertEqual(result["modified"], ["shortcut"])


class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def test_key_creation_and_duplicate_protection(self):
        path = self.root / "key"
        create_key(path)
        self.assertEqual(len(read_key(path)), 32)
        with self.assertRaises(IntegrityError):
            create_key(path)
        create_key(path, force=True)

    def test_atomic_json_round_trip(self):
        path = self.root / "folder" / "result.json"
        atomic_json(path, {"status": "clean"})
        self.assertEqual(read_json(path), {"status": "clean"})
        leftovers = list(path.parent.glob(f".{path.name}.*"))
        self.assertEqual(leftovers, [])

    def test_invalid_json_and_key(self):
        invalid = self.root / "invalid"
        invalid.write_text("not-json")
        with self.assertRaises(IntegrityError):
            read_json(invalid)
        invalid.write_text("abcd")
        with self.assertRaises(IntegrityError):
            read_key(invalid)


if __name__ == "__main__":
    unittest.main()
