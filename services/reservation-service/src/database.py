"""
SQLite database initialization for Reservation Service
"""

import sqlite3
import os

DB_PATH = os.getenv("RESERVATION_DB_PATH", "reservation.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            slot_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            slot_type TEXT NOT NULL DEFAULT 'standard',
            capacity INTEGER NOT NULL DEFAULT 4,
            table_number TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            store_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            resv_date TEXT NOT NULL,
            time_slot TEXT NOT NULL,
            guest_count INTEGER NOT NULL DEFAULT 1,
            bring_cat INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'PENDING',
            buffer_expires_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (slot_id) REFERENCES slots(id)
        );

        CREATE TABLE IF NOT EXISTS queue_tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id INTEGER NOT NULL,
            queue_number INTEGER NOT NULL,
            estimated_wait_minutes INTEGER NOT NULL DEFAULT 15,
            ahead_count INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'WAITING',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_reservations_user ON reservations(user_id);
        CREATE INDEX IF NOT EXISTS idx_reservations_date ON reservations(resv_date, store_id);
        CREATE INDEX IF NOT EXISTS idx_queue_store ON queue_tickets(store_id, status);
    """)
    conn.commit()

    # seed slots if empty
    row = conn.execute("SELECT COUNT(*) FROM slots").fetchone()
    if row[0] == 0:
        _seed_slots(conn)

    conn.close()


def _seed_slots(conn: sqlite3.Connection):
    import itertools

    stores = [1, 2]
    dates = ["2026-06-15", "2026-06-16", "2026-06-17"]
    times = [
        "10:00-12:00",
        "12:00-14:00",
        "14:00-16:00",
        "16:00-18:00",
        "18:00-20:00",
        "20:00-22:00",
    ]
    table_num = 1
    for store, d, t in itertools.product(stores, dates, times):
        for slot_type in ["standard", "standard", "cat-friendly", "window"]:
            conn.execute(
                "INSERT INTO slots (store_id, slot_date, time_slot, slot_type, capacity, table_number) VALUES (?, ?, ?, ?, ?, ?)",
                (store, d, t, slot_type, 4, f"T{table_num:03d}"),
            )
            table_num += 1
    conn.commit()
