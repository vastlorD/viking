"""API: autenticação, autorização e coordenação do registro de ponto."""

import sqlite3
import tempfile
import time
from collections import OrderedDict, deque
from pathlib import Path
from threading import Lock
from uuid import uuid4

from fastapi import Depends, FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .auth import hash_password, verify_password
from .config import Config
from .database import Database
from .face import DeepFaceVerifier, FaceUnavailable
from .images import normalize_image
from .rules import DuplicateAttendance, distance_m, save_attendance, validate_schedule, validate_username


def create_app(config=None, verifier=None):
    config = config or Config.from_env()
    database = Database(config.data_dir)
    verifier = verifier or DeepFaceVerifier()
    photos = config.data_dir / "references"
    photos.mkdir(exist_ok=True)
    app = FastAPI(title="Ponto Facial Viking", version="2.0.0")
    security = HTTPBasic()
    dummy_hash = hash_password(uuid4().hex)
    attempts = OrderedDict()
    attempts_lock = Lock()

    def current_user(request: Request, credentials: HTTPBasicCredentials = Depends(security)):
        # Limite local por cliente. Em produção, aplique também no proxy.
        key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        with attempts_lock:
            bucket = attempts.setdefault(key, deque())
            attempts.move_to_end(key)
            while bucket and now - bucket[0] > 60:
                bucket.popleft()
            if len(bucket) >= 20:
                raise HTTPException(429, "Muitas tentativas. Aguarde um minuto.")
            bucket.append(now)
            while len(attempts) > 1000:
                attempts.popitem(last=False)
        user = database.user(credentials.username.lower())
        valid = verify_password(credentials.password, user["password_hash"] if user else dummy_hash)
        if not user or not valid:
            raise HTTPException(401, "Credenciais inválidas.", headers={"WWW-Authenticate": "Basic"})
        return user

    def admin(user=Depends(current_user)):
        if user["role"] != "admin":
            raise HTTPException(403, "Acesso exclusivo de administrador.")
        return user

    def read_image(upload):
        try:
            return normalize_image(upload.file.read(config.max_upload_bytes + 1), config.max_upload_bytes)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        finally:
            upload.file.close()

    @app.get("/health", tags=["Serviço"])
    def health():
        return {"status": "ok", "facial": "validado somente durante cadastro ou verificação"}

    @app.get("/me", tags=["Conta"])
    def profile(user=Depends(current_user)):
        return {key: user[key] for key in ("id", "name", "username", "role")}

    @app.post("/colaboradores", status_code=201, tags=["Administração"])
    def register(
        nome: str = Form(..., min_length=1, max_length=100),
        usuario: str = Form(..., min_length=3, max_length=40),
        senha: str = Form(..., min_length=12, max_length=128),
        horario: str = Form("09:00"),
        tolerancia: int = Form(10, ge=0, le=180),
        foto: UploadFile = File(...),
        _admin=Depends(admin),
    ):
        try:
            username = validate_username(usuario)
            validate_schedule(horario, tolerancia)
            if not nome.strip():
                raise ValueError("Informe o nome.")
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        if database.user(username):
            raise HTTPException(409, "Usuário já cadastrado.")
        image = read_image(foto)
        path = photos / f"{uuid4().hex}.jpg"
        saved = False
        try:
            path.write_bytes(image)
            verifier.validate_reference(path)
            user_id = database.add_user(nome.strip(), username, hash_password(senha), "employee",
                                        path.name, horario, tolerancia)
            saved = True
            return {"id": user_id, "name": nome.strip(), "username": username}
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        except FaceUnavailable as error:
            raise HTTPException(503, str(error)) from error
        except sqlite3.IntegrityError as error:
            raise HTTPException(409, "Usuário já cadastrado.") from error
        finally:
            if not saved:
                path.unlink(missing_ok=True)

    @app.post("/bater-ponto", status_code=201, tags=["Presença"])
    def clock_in(
        lat: float = Form(..., ge=-90, le=90),
        lon: float = Form(..., ge=-180, le=180),
        selfie: UploadFile = File(...),
        user=Depends(current_user),
    ):
        if user["role"] != "employee" or not user["photo"]:
            raise HTTPException(403, "Cadastre um colaborador com foto para registrar presença.")
        try:
            distance = distance_m(lat, lon, config)
        except ValueError as error:
            raise HTTPException(422, str(error)) from error
        if distance > config.raio_metros:
            raise HTTPException(403, "Localização fora do raio permitido.")
        reference = (photos / user["photo"]).resolve()
        if reference.parent != photos.resolve() or not reference.is_file():
            raise HTTPException(409, "Foto de cadastro indisponível. Contate o administrador.")
        image = read_image(selfie)
        try:
            # O arquivo é fechado antes do DeepFace, inclusive no Windows.
            with tempfile.TemporaryDirectory(prefix="ponto-", dir=config.data_dir) as folder:
                path = Path(folder) / "selfie.jpg"
                path.write_bytes(image)
                if not verifier.verify(reference, path):
                    raise HTTPException(403, "Não foi possível confirmar a selfie com o cadastro.")
            return save_attendance(database, user, lat, lon, distance, config)
        except FaceUnavailable as error:
            raise HTTPException(503, str(error)) from error
        except DuplicateAttendance as error:
            raise HTTPException(409, str(error)) from error

    @app.get("/meu-extrato", tags=["Presença"])
    def statement(limit: int = Query(50, ge=1, le=500), user=Depends(current_user)):
        return database.records(user["id"], limit)

    @app.get("/registros", tags=["Administração"])
    def all_records(limit: int = Query(100, ge=1, le=1000), _admin=Depends(admin)):
        return database.records(limit=limit)

    return app
