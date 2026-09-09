import sqlite3
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image

from ponto.auth import hash_password, verify_password
from ponto.config import Config
from ponto.database import Database
from ponto.face import DeepFaceVerifier, FaceUnavailable
from ponto.images import normalize_image
from ponto.rules import (DuplicateAttendance, arrival_status, distance_m, save_attendance,
                         validate_schedule, validate_username)


class CoreTests(unittest.TestCase):
    def test_password_round_trip_and_random_salt(self):
        password = "Senha-de-teste-123"
        first, second = hash_password(password), hash_password(password)
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password(password, first))
        self.assertFalse(verify_password("incorreta", first))

    def test_invalid_hash_and_password_length(self):
        for stored in [None, "corrompido", "pbkdf2_sha256$999999999$00$00"]:
            self.assertFalse(verify_password("teste", stored))
        for password in ["curta", "x" * 129]:
            with self.assertRaises(ValueError):
                hash_password(password)

    def test_user_validation(self):
        self.assertEqual(validate_username("Pessoa_01"), "pessoa_01")
        for user in ["../foto", "ab", "a/b/c", " x ", "x" * 41]:
            with self.assertRaises(ValueError):
                validate_username(user)

    def test_schedule_validation(self):
        validate_schedule("23:59", 0)
        for schedule, tolerance in [("24:00", 10), ("9:00", 10), ("09:60", 10), ("09:00", -1)]:
            with self.assertRaises(ValueError):
                validate_schedule(schedule, tolerance)

    def test_geo_distance_and_invalid_coordinates(self):
        config = Config(Path("unused"), 0, 0)
        self.assertEqual(distance_m(0, 0, config), 0)
        self.assertAlmostEqual(distance_m(0, 1, config), 111195, delta=2)
        for lat, lon in [(91, 0), (0, 181), (float("nan"), 0), (0, float("inf"))]:
            with self.assertRaises(ValueError):
                distance_m(lat, lon, config)

    def test_invalid_config(self):
        with self.assertRaises(ValueError):
            Config(Path("unused"), 0, 0, raio_metros=-1)

    def test_schedule_uses_local_timezone_and_exact_tolerance(self):
        now = datetime(2026, 9, 9, 12, 10, tzinfo=timezone.utc)
        self.assertEqual(arrival_status(now, "09:00", 10, "America/Sao_Paulo"), "No horário")
        self.assertTrue(arrival_status(now + timedelta(seconds=1), "09:00", 10,
                                       "America/Sao_Paulo").startswith("Atrasado"))

    def test_image_normalization(self):
        output = BytesIO()
        Image.new("RGB", (2000, 1000)).save(output, format="PNG")
        normalized = normalize_image(output.getvalue(), 5_000_000)
        with Image.open(BytesIO(normalized)) as image:
            self.assertEqual(image.size, (1600, 800))
            self.assertEqual(image.format, "JPEG")
            self.assertFalse(image.getexif())

    def test_invalid_and_oversized_images(self):
        for raw, limit in [(b"not an image", 100), (b"abc", 2), (b"", 100)]:
            with self.assertRaises(ValueError):
                normalize_image(raw, limit)


class DatabaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Config(Path(self.temp.name), 0, 0)
        self.db = Database(self.config.data_dir)
        self.db.add_user("Pessoa", "pessoa", "hash-teste", "employee")
        self.user = self.db.user("pessoa")
        self.now = datetime(2026, 9, 9, 12, tzinfo=timezone.utc)

    def test_sql_injection_is_not_a_query(self):
        self.assertIsNone(self.db.user("' OR 1=1 --"))

    def test_unique_username(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.add_user("Outra", "pessoa", "hash", "employee")

    def test_save_preserves_utc_and_coordinates(self):
        result = save_attendance(self.db, self.user, 0, 0, 0, self.config, self.now)
        self.assertTrue(result["recorded_at"].endswith("+00:00"))
        self.assertEqual(self.db.records(self.user["id"])[0]["latitude"], 0)
        self.assertEqual(self.db.records(999), [])

    def test_duplicate_is_rejected_without_insert(self):
        save_attendance(self.db, self.user, 0, 0, 0, self.config, self.now)
        with self.assertRaises(DuplicateAttendance):
            save_attendance(self.db, self.user, 0, 0, 0, self.config, self.now)
        save_attendance(self.db, self.user, 0, 0, 0, self.config, self.now + timedelta(seconds=60))
        self.assertEqual(len(self.db.records()), 2)

    def test_concurrent_duplicates(self):
        def save(_):
            try:
                save_attendance(self.db, self.user, 0, 0, 0, self.config, self.now)
                return True
            except DuplicateAttendance:
                return False
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(save, range(2)))
        self.assertEqual(sum(results), 1)


class FaceAdapterTests(unittest.TestCase):
    def setUp(self):
        self.backend = Mock()
        self.backend.extract_faces.return_value = [{"is_real": True}]
        self.backend.verify.return_value = {"verified": True}
        self.verifier = DeepFaceVerifier()
        self.patch = patch.object(self.verifier, "_backend", return_value=self.backend)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def test_match_and_antispoofing_request(self):
        self.assertTrue(self.verifier.verify("reference", "selfie"))
        self.assertTrue(self.backend.extract_faces.call_args.kwargs["anti_spoofing"])

    def test_multiple_faces_rejected(self):
        self.backend.extract_faces.return_value = [{}, {}]
        self.assertFalse(self.verifier.verify("reference", "selfie"))
        self.backend.verify.assert_not_called()

    def test_spoof_rejected(self):
        self.backend.extract_faces.return_value = [{"is_real": False}]
        self.assertFalse(self.verifier.verify("reference", "selfie"))

    def test_no_face_rejected(self):
        self.backend.extract_faces.side_effect = ValueError("no face")
        self.assertFalse(self.verifier.verify("reference", "selfie"))

    def test_model_failure_is_unavailable(self):
        self.backend.extract_faces.side_effect = RuntimeError("model failure")
        with self.assertRaises(FaceUnavailable):
            self.verifier.verify("reference", "selfie")


if __name__ == "__main__":
    unittest.main()
