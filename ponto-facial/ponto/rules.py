"""Regras independentes da API e do motor de reconhecimento."""

import math
import re
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


def validate_username(username):
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,40}", username):
        raise ValueError("Usuário: 3 a 40 letras, números, ponto, hífen ou sublinhado.")
    return username.lower()


def validate_schedule(start_time, tolerance):
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", start_time):
        raise ValueError("Horário deve usar HH:MM, entre 00:00 e 23:59.")
    if not 0 <= tolerance <= 180:
        raise ValueError("Tolerância deve estar entre 0 e 180 minutos.")


def distance_m(lat, lon, config):
    if not math.isfinite(lat) or not -90 <= lat <= 90:
        raise ValueError("Latitude inválida.")
    if not math.isfinite(lon) or not -180 <= lon <= 180:
        raise ValueError("Longitude inválida.")
    a, b = math.radians(lat), math.radians(config.latitude)
    delta_lat = b - a
    delta_lon = math.radians(config.longitude - lon)
    haversine = math.sin(delta_lat / 2) ** 2 + math.cos(a) * math.cos(b) * math.sin(delta_lon / 2) ** 2
    return 6_371_008.8 * 2 * math.asin(math.sqrt(min(1, max(0, haversine))))


def arrival_status(now, start_time, tolerance, tz_name):
    local = now.astimezone(ZoneInfo(tz_name))
    hour, minute = map(int, start_time.split(":"))
    expected = local.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if local <= expected + timedelta(minutes=tolerance):
        return "No horário"
    minutes = math.ceil((local - expected).total_seconds() / 60)
    return f"Atrasado ({minutes} min após o horário de entrada)"


class DuplicateAttendance(ValueError):
    pass


def save_attendance(database, user, lat, lon, distance, config, now=None):
    now = now or datetime.now(timezone.utc)
    now = now.astimezone(timezone.utc)
    with database.connect() as connection:
        # Serializa a checagem e a inserção, inclusive entre processos SQLite.
        connection.execute("BEGIN IMMEDIATE")
        last = connection.execute(
            "SELECT recorded_at FROM attendance WHERE user_id = ? ORDER BY id DESC LIMIT 1",
            (user["id"],),
        ).fetchone()
        if last and (now - datetime.fromisoformat(last["recorded_at"])).total_seconds() < config.intervalo_segundos:
            raise DuplicateAttendance("Aguarde antes de registrar outro ponto.")
        status = arrival_status(now, user["start_time"], user["tolerance"], config.timezone)
        cursor = connection.execute(
            "INSERT INTO attendance(user_id, recorded_at, latitude, longitude, distance_m, status) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user["id"], now.isoformat(), lat, lon, round(distance, 2), status),
        )
        return {"id": cursor.lastrowid, "recorded_at": now.isoformat(), "status": status,
                "latitude": lat, "longitude": lon, "distance_m": round(distance, 2)}
