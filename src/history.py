"""Conversation history in SQLite (stdlib only).

SqliteStore(path)      -> persistent, local single-user use.
SqliteStore(":memory:") -> per-session store, used for public deployments (nothing is written to disk).
"""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "chat_history.sqlite3"

SCHEMA = """
CREATE TABLE IF NOT EXISTS conversations(
  id TEXT PRIMARY KEY, title TEXT NOT NULL,
  created_at REAL NOT NULL, updated_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS messages(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  conv_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
  role TEXT NOT NULL CHECK(role IN ('user','assistant')),
  content TEXT NOT NULL DEFAULT '',
  comparison INTEGER NOT NULL DEFAULT 0,
  result_json TEXT, elapsed REAL, created_at REAL NOT NULL);
CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conv_id, id);
CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
"""


def make_title(question, limit=60):
    t = " ".join(str(question).split())
    if len(t) <= limit:
        return t or "New conversation"
    cut = t[:limit].rsplit(" ", 1)[0] or t[:limit]
    return cut.rstrip(" ,;:-") + "…"


def _jsonable(o):
    try:
        return float(o)
    except (TypeError, ValueError):
        return str(o)


class SqliteStore:
    def __init__(self, path=DEFAULT_DB):
        self.memory = str(path) == ":memory:"
        self.path = str(path)
        if self.memory:
            self._mem = sqlite3.connect(":memory:", check_same_thread=False)
            self._mem.row_factory = sqlite3.Row
        else:
            Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            if not self.memory:
                c.execute("PRAGMA journal_mode=WAL")
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        if self.memory:
            c = self._mem
        else:
            c = sqlite3.connect(self.path, timeout=10)
            c.row_factory = sqlite3.Row
        c.execute("PRAGMA foreign_keys=ON")
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
        finally:
            if not self.memory:
                c.close()

    # ---- conversations
    def create_conversation(self, title):
        cid, now = uuid.uuid4().hex, time.time()
        with self._conn() as c:
            c.execute("INSERT INTO conversations(id,title,created_at,updated_at) VALUES(?,?,?,?)",
                      (cid, title or "New conversation", now, now))
        return cid

    def list_conversations(self, limit=50):
        with self._conn() as c:
            rows = c.execute("SELECT id,title,created_at,updated_at FROM conversations "
                             "ORDER BY updated_at DESC LIMIT ?", (int(limit),)).fetchall()
        return [dict(r) for r in rows]

    def get_conversation(self, cid):
        if not cid:
            return None
        with self._conn() as c:
            r = c.execute("SELECT id,title,created_at,updated_at FROM conversations WHERE id=?", (cid,)).fetchone()
        return dict(r) if r else None

    def rename(self, cid, title):
        with self._conn() as c:
            c.execute("UPDATE conversations SET title=? WHERE id=?", (title.strip()[:120], cid))

    def delete_conversation(self, cid):
        with self._conn() as c:
            c.execute("DELETE FROM conversations WHERE id=?", (cid,))

    def delete_all(self):
        with self._conn() as c:
            c.execute("DELETE FROM messages")
            c.execute("DELETE FROM conversations")

    # ---- messages
    def add_message(self, cid, role, content="", comparison=False, result=None, elapsed=None):
        now = time.time()
        rj = json.dumps(result, default=_jsonable) if result is not None else None
        with self._conn() as c:
            cur = c.execute("INSERT INTO messages(conv_id,role,content,comparison,result_json,elapsed,created_at) "
                            "VALUES(?,?,?,?,?,?,?)", (cid, role, content, int(bool(comparison)), rj, elapsed, now))
            c.execute("UPDATE conversations SET updated_at=? WHERE id=?", (now, cid))
            return cur.lastrowid

    def get_messages(self, cid):
        with self._conn() as c:
            rows = c.execute("SELECT id,role,content,comparison,result_json,elapsed,created_at "
                             "FROM messages WHERE conv_id=? ORDER BY id", (cid,)).fetchall()
        out = []
        for r in rows:
            try:
                result = json.loads(r["result_json"]) if r["result_json"] else None
            except ValueError:
                result = None
            out.append({"id": r["id"], "role": r["role"], "content": r["content"],
                        "comparison": bool(r["comparison"]), "result": result,
                        "elapsed": r["elapsed"], "created_at": r["created_at"]})
        return out

    def delete_message(self, mid):
        with self._conn() as c:
            c.execute("DELETE FROM messages WHERE id=?", (mid,))

    # ---- settings
    def get_setting(self, key, default=None):
        with self._conn() as c:
            r = c.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return r["value"] if r else default

    def set_setting(self, key, value):
        with self._conn() as c:
            c.execute("INSERT INTO settings(key,value) VALUES(?,?) "
                      "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (key, str(value)))