"""A tiny ticket database (SQLite) for the service desk assistant."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "tickets.db"

CATEGORIES = ["Hardware request", "Account access", "VPN", "Other"]


def connect():
    """Open the database and create the tickets table the first time."""
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute(
        """CREATE TABLE IF NOT EXISTS tickets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee TEXT NOT NULL,
            category TEXT NOT NULL,
            summary TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Open',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )"""
    )
    return connection


def create_ticket(employee, category, summary):
    """Save a new ticket and return it."""
    if category not in CATEGORIES:
        return {"error": f"Category must be one of: {', '.join(CATEGORIES)}"}
    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO tickets (employee, category, summary) VALUES (?, ?, ?)",
            (employee, category, summary),
        )
        ticket_id = cursor.lastrowid
    return get_ticket(ticket_id)


def get_ticket(ticket_id):
    """Look up one ticket by its number."""
    with connect() as connection:
        row = connection.execute("SELECT * FROM tickets WHERE id = ?", (ticket_id,)).fetchone()
    if row is None:
        return {"error": f"No ticket found with number {ticket_id}"}
    return dict(row)


if __name__ == "__main__":
    # Quick test: run "python tickets.py"
    new_ticket = create_ticket("Test User", "Hardware request", "Laptop screen is cracked")
    print("Created:", new_ticket)
    print("Looked up:", get_ticket(new_ticket["id"]))
    print("Missing:", get_ticket(9999))
    print("Bad category:", create_ticket("Test User", "Lunch", "Pizza"))