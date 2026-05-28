from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from typing import Any


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class GameState:
    chat_id: int
    game_active: bool
    current_stage: int
    players: list[str]
    inventory: list[str]
    hints_used: int
    wrong_answers: int
    started_at: str | None
    finished_at: str | None
    completed: bool
    score: int
    case_id: str | None = None
    votes: dict[str, dict[str, str]] | None = None
    discovered_clues: list[str] | None = None
    false_clues: list[str] | None = None
    expected_players: int | None = None


class Database:
    def __init__(self, path: str = "escape_room.sqlite3") -> None:
        self.path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True) if Path(path).parent != Path(".") else None
        self.init_db()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS games (
                    chat_id INTEGER PRIMARY KEY,
                    game_active INTEGER NOT NULL,
                    current_stage INTEGER NOT NULL,
                    players TEXT NOT NULL,
                    inventory TEXT NOT NULL,
                    hints_used INTEGER NOT NULL,
                    wrong_answers INTEGER NOT NULL,
                    started_at TEXT,
                    finished_at TEXT,
                    completed INTEGER NOT NULL,
                    score INTEGER NOT NULL
                )
                """
            )
            self._ensure_column(conn, "case_id", "TEXT")
            self._ensure_column(conn, "votes", "TEXT NOT NULL DEFAULT '{}'")
            self._ensure_column(conn, "discovered_clues", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(conn, "false_clues", "TEXT NOT NULL DEFAULT '[]'")
            self._ensure_column(conn, "expected_players", "INTEGER")

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, column: str, definition: str) -> None:
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(games)").fetchall()}
        if column not in columns:
            conn.execute(f"ALTER TABLE games ADD COLUMN {column} {definition}")

    def get_game(self, chat_id: int) -> GameState | None:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM games WHERE chat_id = ?", (chat_id,)).fetchone()
        if row is None:
            return None
        return self._row_to_state(row)

    def save_game(self, state: GameState) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO games (
                    chat_id, game_active, current_stage, players, inventory, hints_used,
                    wrong_answers, started_at, finished_at, completed, score, case_id,
                    votes, discovered_clues, false_clues, expected_players
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chat_id) DO UPDATE SET
                    game_active = excluded.game_active,
                    current_stage = excluded.current_stage,
                    players = excluded.players,
                    inventory = excluded.inventory,
                    hints_used = excluded.hints_used,
                    wrong_answers = excluded.wrong_answers,
                    started_at = excluded.started_at,
                    finished_at = excluded.finished_at,
                    completed = excluded.completed,
                    score = excluded.score,
                    case_id = excluded.case_id,
                    votes = excluded.votes,
                    discovered_clues = excluded.discovered_clues,
                    false_clues = excluded.false_clues,
                    expected_players = excluded.expected_players
                """,
                self._state_to_tuple(state),
            )

    def delete_game(self, chat_id: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM games WHERE chat_id = ?", (chat_id,))

    def list_completed_games(self) -> list[GameState]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM games WHERE completed = 1 ORDER BY score DESC, finished_at ASC"
            ).fetchall()
        return [self._row_to_state(row) for row in rows]

    @staticmethod
    def _row_to_state(row: sqlite3.Row) -> GameState:
        return GameState(
            chat_id=row["chat_id"],
            game_active=bool(row["game_active"]),
            current_stage=row["current_stage"],
            players=json.loads(row["players"]),
            inventory=json.loads(row["inventory"]),
            hints_used=row["hints_used"],
            wrong_answers=row["wrong_answers"],
            started_at=row["started_at"],
            finished_at=row["finished_at"],
            completed=bool(row["completed"]),
            score=row["score"],
            case_id=row["case_id"],
            votes=json.loads(row["votes"] or "{}"),
            discovered_clues=json.loads(row["discovered_clues"] or "[]"),
            false_clues=json.loads(row["false_clues"] or "[]"),
            expected_players=row["expected_players"],
        )

    @staticmethod
    def _state_to_tuple(state: GameState) -> tuple[Any, ...]:
        return (
            state.chat_id,
            int(state.game_active),
            state.current_stage,
            json.dumps(state.players, ensure_ascii=False),
            json.dumps(state.inventory, ensure_ascii=False),
            state.hints_used,
            state.wrong_answers,
            state.started_at,
            state.finished_at,
            int(state.completed),
            state.score,
            state.case_id,
            json.dumps(state.votes or {}, ensure_ascii=False),
            json.dumps(state.discovered_clues or [], ensure_ascii=False),
            json.dumps(state.false_clues or [], ensure_ascii=False),
            state.expected_players,
        )
