"""Adaptador DeepFace. Falhas nunca são convertidas em aprovação."""

from threading import Lock


class FaceUnavailable(RuntimeError):
    pass


class DeepFaceVerifier:
    def __init__(self):
        self._lock = Lock()

    @staticmethod
    def _backend():
        try:
            from deepface import DeepFace
            return DeepFace
        except Exception as error:
            raise FaceUnavailable("Motor facial indisponível. Confira a instalação e os modelos.") from error

    @staticmethod
    def _one_face(backend, path, anti_spoofing=False):
        faces = backend.extract_faces(
            img_path=str(path), detector_backend="opencv", enforce_detection=True,
            anti_spoofing=anti_spoofing,
        )
        if len(faces) != 1:
            raise ValueError("A imagem deve conter exatamente um rosto.")
        if anti_spoofing and not faces[0].get("is_real", False):
            raise ValueError("A selfie não passou pela verificação de autenticidade.")

    def validate_reference(self, path):
        with self._lock:
            backend = self._backend()
            try:
                self._one_face(backend, path)
            except ValueError:
                raise ValueError("Não foi possível validar um único rosto na foto.") from None
            except Exception as error:
                raise FaceUnavailable("Falha ao carregar ou executar o detector facial.") from error

    def verify(self, reference, selfie):
        with self._lock:
            backend = self._backend()
            try:
                self._one_face(backend, reference)
                self._one_face(backend, selfie, anti_spoofing=True)
                result = backend.verify(
                    img1_path=str(reference), img2_path=str(selfie), model_name="VGG-Face",
                    detector_backend="opencv", enforce_detection=True,
                )
                return bool(result["verified"])
            except ValueError:
                return False
            except Exception as error:
                raise FaceUnavailable("Falha ao carregar ou executar o modelo facial.") from error
