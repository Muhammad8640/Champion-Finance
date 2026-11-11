"""SQLite storage for Champion Transactions (no external packages required)."""
import os
import sqlite3
from pathlib import Path

DB_PATH = Path(os.environ.get('CHAMPION_DB_PATH', str(Path(__file__).resolve().parent / 'data' / 'champion.db')))


def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute('PRAGMA foreign_keys = ON')
    connection.execute('PRAGMA busy_timeout = 5000')
    return connection


def init_db():
    with connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('Expense','Deposit')),
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            due_date TEXT NOT NULL,
            frequency TEXT NOT NULL CHECK(frequency IN ('One-time','Weekly','Every 2 weeks','Monthly','Quarterly','Yearly')),
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS occurrence_status (
            transaction_id INTEGER NOT NULL,
            due_date TEXT NOT NULL,
            paid INTEGER NOT NULL DEFAULT 0 CHECK(paid IN (0,1)),
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (transaction_id, due_date),
            FOREIGN KEY (transaction_id) REFERENCES transactions(id) ON DELETE CASCADE
        );
        ''')


def get_transactions():
    with connect() as con:
        return [dict(r) for r in con.execute('SELECT * FROM transactions ORDER BY due_date ASC, id DESC')]


def add_transaction(name, kind, amount_cents, due_date, frequency, notes):
    with connect() as con:
        con.execute('INSERT INTO transactions (name,kind,amount_cents,due_date,frequency,notes) VALUES (?,?,?,?,?,?)',
                    (name, kind, amount_cents, due_date, frequency, notes))


def update_transaction(tx_id, name, kind, amount_cents, due_date, frequency, notes):
    with connect() as con:
        con.execute('UPDATE transactions SET name=?,kind=?,amount_cents=?,due_date=?,frequency=?,notes=? WHERE id=?',
                    (name, kind, amount_cents, due_date, frequency, notes, tx_id))


def delete_transaction(tx_id):
    with connect() as con:
        con.execute('DELETE FROM transactions WHERE id=?', (tx_id,))


def get_statuses():
    with connect() as con:
        return {(r['transaction_id'],r['due_date']):bool(r['paid']) for r in con.execute('SELECT transaction_id,due_date,paid FROM occurrence_status')}


def set_status(tx_id, date_iso, paid):
    with connect() as con:
        con.execute('''INSERT INTO occurrence_status (transaction_id,due_date,paid,updated_at)
            VALUES (?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(transaction_id,due_date) DO UPDATE SET paid=excluded.paid, updated_at=CURRENT_TIMESTAMP''',
            (tx_id, date_iso, int(paid)))
