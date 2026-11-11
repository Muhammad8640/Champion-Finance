# Champion Transactions — Phase 1

Local Python + Streamlit + SQLite app for Champion Restoration & Construction.

## Quick start (Windows)

1. Install Python 3.10 or newer from python.org (select **Add Python to PATH** during installation).
2. Extract the ZIP.
3. Double-click `start_windows.bat`. It installs Streamlit and starts the app.
4. Browser opens at `http://localhost:8501` (or navigate there manually).
5. Keep the terminal window open while using the app.

## Quick start (Mac/Linux)

From the extracted directory, run:

```sh
sh start_mac_linux.sh
```

Or manually:

```sh
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Features

- Add outgoing **expenses** and incoming **expected deposits** with name, amount, first due date, and notes.
- Frequency: one-time, weekly, every two weeks, monthly, quarterly, yearly.
- Browse scheduled occurrences within selectable ranges.
- Mark each *individual due date* as paid/unpaid or received/not received, without affecting future occurrences.
- Edit and delete transaction schedules.
- See simple outstanding-expense and expected-deposit totals for the selected date range.

## Storage and privacy

Transactions are stored in `data/champion.db`, a SQLite database **on this computer**. It is created the first time the app starts. There is no cloud sync, authentication, bank integration, or contractor-sheet import in this phase. To back up, close the app and copy `data/champion.db` to a safe location. Do not put confidential company transaction data in a public shared folder. All editing on a single machine is recommended until a shared backend is built.

## Notes

- The amounts are cash-flow estimates; clicking Paid/Received **does not send money** or verify bank activity.
- Monthly recurrences anchored on the 29th/30th/31st fall on the last valid day of shorter months, then return to their original calendar day when possible.
- If a recurring transaction changes, its old paid statuses may remain in the database but no longer appear if their due dates are no longer part of its new schedule. For audit/history in a later release, we'll add immutable transaction events.
- Bank balances, contractor import and full cash-flow dashboards are intentionally deferred to later phases.
