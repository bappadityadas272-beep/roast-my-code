"""Score history for the line chart.

Every roast is appended to history.json. Each entry carries a session id so
the chart on the website only shows the current visitor's own roasts, even
though the file is shared by everyone using the app.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import pandas as pd

HISTORY_FILE = Path(__file__).parent / "history.json"
MAX_ENTRIES = 500  # keep the file small


def _read() -> list[dict]:
    try:
        data = json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, ValueError):
        return []  # missing or corrupt file: start fresh


def _write(entries: list[dict]) -> None:
    try:
        tmp = HISTORY_FILE.with_suffix(".tmp")
        tmp.write_text(json.dumps(entries, indent=2), encoding="utf-8")
        os.replace(tmp, HISTORY_FILE)
    except OSError:
        pass  # read-only host: the app still works, history just isn't saved


def add_entry(session_id: str, language: str, level: str, score: int) -> None:
    entries = _read()
    entries.append(
        {
            "time": datetime.now().isoformat(timespec="seconds"),
            "session": session_id,
            "language": language,
            "level": level,
            "score": int(score),
        }
    )
    _write(entries[-MAX_ENTRIES:])


def load_history(session_id: str) -> list[dict]:
    return [e for e in _read() if e.get("session") == session_id]


def history_frame(session_id: str) -> pd.DataFrame:
    """Scores in order, indexed 1..n, ready for st.line_chart."""
    rows = load_history(session_id)
    df = pd.DataFrame({"Score": [r["score"] for r in rows]})
    df.index = range(1, len(df) + 1)
    df.index.name = "Roast #"
    return df


def clear_history(session_id: str) -> None:
    """Remove only this session's entries."""
    _write([e for e in _read() if e.get("session") != session_id])
