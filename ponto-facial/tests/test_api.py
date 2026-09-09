"""Integração HTTP com banco temporário e motor facial substituído somente nos testes."""

from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

from fastapi.testclient import TestClient
from PIL import Image

from ponto.api import create_app
from ponto.auth import hash_password
from ponto.config import Config
from ponto.database import Database
from ponto.face import FaceUnavailable


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.password = "Senha-ficticia-teste-123"
        cls.password_hash = hash_password(cls.password)
        output = BytesIO()
        Image.new("RGB", (100, 100), "white").save(output, format="JPEG")
        cls.image = output.getvalue()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.config = Config(Path(self.temp.name), 0, 0)
        self.db = Database(self.config.data_dir)
        self.db.add_user("Admin", "admin", self.password_hash, "admin")
        self.db.add_user("Pessoa", "pessoa", self.password_hash, "employee", "reference.jpg")
        self.verifier = Mock()
        self.verifier.verify.return_value = True
        self.client = TestClient(create_app(self.config, self.verifier))
        self.addCleanup(self.client.close)
        (self.config.data_dir / "references" / "reference.jpg").write_bytes(self.image)
        self.employee = ("pessoa", self.password)
        self.admin = ("admin", self.password)

    def clock(self, **data):
        return self.client.post("/bater-ponto", auth=self.employee,
                                data={"lat": 0, "lon": 0, **data},
                                files={"selfie": ("foto.jpg", self.image, "image/jpeg")})

    def register(self, **data):
        return self.client.post("/colaboradores", auth=self.admin,
                                data={"nome": "Teste", "usuario": "novo", "senha": self.password, **data},
                                files={"foto": ("foto.jpg", self.image, "image/jpeg")})

    def test_statement_requires_login(self):
        self.assertEqual(self.client.get("/meu-extrato").status_code, 401)
        self.assertEqual(self.client.get("/meu-extrato/pessoa").status_code, 404)

    def test_unknown_and_wrong_password_same_response(self):
        a = self.client.get("/me", auth=("pessoa", "incorreta"))
        b = self.client.get("/me", auth=("ausente", "incorreta"))
        self.assertEqual((a.status_code, a.json()), (b.status_code, b.json()))

    def test_employee_cannot_access_admin(self):
        self.assertEqual(self.client.get("/registros", auth=self.employee).status_code, 403)
        response = self.client.post("/colaboradores", auth=self.employee,
            data={"nome": "Outro", "usuario": "outro", "senha": self.password},
            files={"foto": ("foto.jpg", self.image)})
        self.assertEqual(response.status_code, 403)

    def test_register_and_duplicate(self):
        self.assertEqual(self.register().status_code, 201)
        self.assertEqual(self.db.user("novo")["role"], "employee")
        self.assertEqual(self.register().status_code, 409)

    def test_path_traversal_rejected(self):
        self.assertEqual(self.register(usuario="../escape").status_code, 422)
        self.assertFalse((self.config.data_dir / "escape.jpg").exists())

    def test_bad_schedule_and_blank_name(self):
        self.assertEqual(self.register(horario="99:99").status_code, 422)
        self.assertEqual(self.register(nome=" ").status_code, 422)

    def test_enrollment_failure_cleans_photo(self):
        self.verifier.validate_reference.side_effect = ValueError("face absent")
        self.assertEqual(self.register().status_code, 422)
        self.assertEqual(len(list((self.config.data_dir / "references").iterdir())), 1)
        self.assertIsNone(self.db.user("novo"))

    def test_clock_success_and_no_selfie_retained(self):
        response = self.clock()
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(len(self.db.records()), 1)
        self.assertEqual(list(self.config.data_dir.glob("ponto-*")), [])

    def test_outside_geofence_rejected_before_face(self):
        self.assertEqual(self.clock(lat=1).status_code, 403)
        self.verifier.verify.assert_not_called()
        self.assertEqual(self.db.records(), [])

    def test_invalid_coordinates(self):
        self.assertEqual(self.clock(lat=91).status_code, 422)
        self.assertEqual(self.clock(lon="nan").status_code, 422)

    def test_mismatch_does_not_record_or_keep_selfie(self):
        self.verifier.verify.return_value = False
        self.assertEqual(self.clock().status_code, 403)
        self.assertEqual(self.db.records(), [])
        self.assertEqual(list(self.config.data_dir.glob("ponto-*")), [])

    def test_engine_unavailable_does_not_approve(self):
        self.verifier.verify.side_effect = FaceUnavailable("indisponível")
        self.assertEqual(self.clock().status_code, 503)
        self.assertEqual(self.db.records(), [])
        self.assertEqual(list(self.config.data_dir.glob("ponto-*")), [])

    def test_duplicate_returns_conflict(self):
        self.assertEqual(self.clock().status_code, 201)
        self.assertEqual(self.clock().status_code, 409)
        self.assertEqual(len(self.db.records()), 1)

    def test_statement_is_scoped_to_authenticated_user(self):
        self.clock()
        self.db.add_user("Outra", "outra", self.password_hash, "employee")
        response = self.client.get("/meu-extrato", auth=("outra", self.password))
        self.assertEqual(response.json(), [])

    def test_invalid_photo_rejected(self):
        response = self.client.post("/bater-ponto", auth=self.employee, data={"lat": 0, "lon": 0},
                                    files={"selfie": ("fake.jpg", b"not an image")})
        self.assertEqual(response.status_code, 422)

    def test_rate_limit(self):
        for _ in range(20):
            self.assertEqual(self.client.get("/me", auth=("missing", "wrong")).status_code, 401)
        self.assertEqual(self.client.get("/me", auth=self.employee).status_code, 429)


if __name__ == "__main__":
    unittest.main()
