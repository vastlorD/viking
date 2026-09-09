"""SQLite local com transações curtas e consultas parametrizadas."""

import sqlite3
from contextlib import contextmanager

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'employee')),
    photo TEXT,
    start_time TEXT NOT NULL DEFAULT '09:00',
    tolerance INTEGER NOT NULL DEFAULT 10 CHECK(tolerance >= 0)
);
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    recorded_at TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    distance_m REAL NOT NULL,
    status TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS attendance_user_time ON attendance(user_id, recorded_at);
"""


class Database:
    def __init__(self, data_dir):
        self.path = data_dir / "ponto.sqlite3"
        data_dir.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def user(self, username):
        with self.connect() as connection:
            row = connection.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None

    def add_user(self, name, username, password_hash, role, photo=None, start_time="09:00", tolerance=10):
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users(name, username, password_hash, role, photo, start_time, tolerance) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, username, password_hash, role, photo, start_time, tolerance),
            )
            return cursor.lastrowid

    def records(self, user_id=None, limit=100):
        query = "SELECT a.*, u.name FROM attendance a JOIN users u ON u.id = a.user_id"
        params = []
        if user_id is not None:
            query += " WHERE a.user_id = ?"
            params.append(user_id)
        query += " ORDER BY a.recorded_at DESC, a.id DESC LIMIT ?"
        params.append(limit)
        with self.connect() as connection:
            return [dict(row) for row in connection.execute(query, params)]
