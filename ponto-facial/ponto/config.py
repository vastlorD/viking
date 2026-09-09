"""Configuração explícita; nenhum segredo ou endereço real no código."""

import math
import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo

@dataclass(frozen=True)
class Config:
    data_dir: Path
    latitude: float
    longitude: float
    raio_metros: float = 100
    timezone: str = "America/Sao_Paulo"
    intervalo_segundos: int = 60
    max_upload_bytes: int = 5 * 1024 * 1024

    def __post_init__(self):
        if not math.isfinite(self.latitude) or not -90 <= self.latitude <= 90:
            raise ValueError("SEDE_LAT deve estar entre -90 e 90.")
        if not math.isfinite(self.longitude) or not -180 <= self.longitude <= 180:
            raise ValueError("SEDE_LON deve estar entre -180 e 180.")
        if not math.isfinite(self.raio_metros) or self.raio_metros <= 0:
            raise ValueError("RAIO_METROS deve ser positivo.")
        if self.intervalo_segundos < 1 or self.max_upload_bytes < 1:
            raise ValueError("Limites de intervalo e arquivo devem ser positivos.")
        ZoneInfo(self.timezone)

    @classmethod
    def from_env(cls):
        from dotenv import load_dotenv

        load_dotenv()
        try:
            lat, lon = float(os.environ["SEDE_LAT"]), float(os.environ["SEDE_LON"])
        except (KeyError, ValueError) as error:
            raise ValueError("Configure SEDE_LAT e SEDE_LON no arquivo .env.") from error
        return cls(
            data_dir=Path(os.getenv("DATA_DIR", "data")).resolve(),
            latitude=lat,
            longitude=lon,
            raio_metros=float(os.getenv("RAIO_METROS", "100")),
            timezone=os.getenv("TIMEZONE", "America/Sao_Paulo"),
            intervalo_segundos=int(os.getenv("INTERVALO_SEGUNDOS", "60")),
        )
