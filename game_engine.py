from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import random
import re
import unicodedata

from database import GameState, utc_now_iso
from game_data import STAGES, GameStage


INITIAL_SCORE = 100
HINT_PENALTY = 5
WRONG_ANSWER_PENALTY = 2
OVER_TIME_PENALTY = 20
FAST_COMPLETION_BONUS = 15
NO_HINTS_BONUS = 20
GROUP_BONUS = 10

ERROR_MESSAGES = [
    "❌ El Archivo no reconoce esa respuesta. Una grieta aparece en la pared, pero aún no se abre.",
    "❌ El Bucle Negro se ríe. 'Esa no es la llave.' Error registrado: -2 puntos.",
    "❌ La puerta permanece cerrada. Tal vez debáis pensar de otra manera.",
]


@dataclass(frozen=True)
class ResolveResult:
    correct: bool
    message: str
    state: GameState
    completed: bool = False


def normalize_answer(text: str) -> str:
    without_accents = "".join(
        char
        for char in unicodedata.normalize("NFD", text.casefold())
        if unicodedata.category(char) != "Mn"
    )
    without_punctuation = re.sub(r"[^\w\s]", " ", without_accents, flags=re.UNICODE)
    normalized_spaces = re.sub(r"\s+", " ", without_punctuation).strip()
    return normalized_spaces.upper()


def parse_iso_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def human_duration(started_at: str | None, finished_at: str | None = None) -> str:
    start = parse_iso_datetime(started_at)
    if start is None:
        return "0 min"
    end = parse_iso_datetime(finished_at) or datetime.now(timezone.utc)
    total_seconds = max(0, int((end - start).total_seconds()))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours} h {minutes} min {seconds} s"
    if minutes:
        return f"{minutes} min {seconds} s"
    return f"{seconds} s"


def calculate_final_score(state: GameState) -> int:
    score = state.score
    started = parse_iso_datetime(state.started_at)
    finished = parse_iso_datetime(state.finished_at)
    if started and finished:
        elapsed_minutes = (finished - started).total_seconds() / 60
        if elapsed_minutes > 60:
            score -= OVER_TIME_PENALTY
        if elapsed_minutes < 40:
            score += FAST_COMPLETION_BONUS
    if state.hints_used == 0:
        score += NO_HINTS_BONUS
    if len(state.players) >= 3:
        score += GROUP_BONUS
    return max(0, score)


def rank_for_score(score: int) -> str:
    if score >= 120:
        return "Leyendas del Archivo"
    if score >= 100:
        return "Guardianes de las Llaves"
    if score >= 80:
        return "Compañía Heroica"
    if score >= 60:
        return "Aprendices del Umbral"
    return "Atrapados parcialmente en el Bucle"


class GameEngine:
    def __init__(self, stages: list[GameStage] | None = None) -> None:
        self.stages = stages or STAGES

    def create_game(self, chat_id: int) -> GameState:
        return GameState(
            chat_id=chat_id,
            game_active=True,
            current_stage=1,
            players=[],
            inventory=[],
            hints_used=0,
            wrong_answers=0,
            started_at=None,
            finished_at=None,
            completed=False,
            score=INITIAL_SCORE,
        )

    def add_player(self, state: GameState, player_name: str) -> bool:
        clean_name = player_name.strip()
        if clean_name and clean_name not in state.players:
            state.players.append(clean_name)
            return True
        return False

    def begin_game(self, state: GameState) -> str:
        if state.started_at is None:
            state.started_at = utc_now_iso()
        return self.current_stage(state).story

    def current_stage(self, state: GameState) -> GameStage:
        return self.stages[state.current_stage - 1]

    def is_correct_answer(self, stage: GameStage, answer: str) -> bool:
        normalized = normalize_answer(answer)
        return any(normalized == normalize_answer(valid) for valid in stage.valid_answers)

    def get_hint(self, state: GameState) -> str:
        stage = self.current_stage(state)
        index = min(state.hints_used, len(stage.hints) - 1)
        state.hints_used += 1
        state.score = max(0, state.score - HINT_PENALTY)
        return f"💡 Pista {index + 1}/{len(stage.hints)}:\n{stage.hints[index]}\n\nPenalización: -5 puntos."

    def resolve(self, state: GameState, answer: str) -> ResolveResult:
        stage = self.current_stage(state)
        if not self.is_correct_answer(stage, answer):
            state.wrong_answers += 1
            state.score = max(0, state.score - WRONG_ANSWER_PENALTY)
            return ResolveResult(False, random.choice(ERROR_MESSAGES), state)

        if stage.reward_item not in state.inventory:
            state.inventory.append(stage.reward_item)

        if state.current_stage >= len(self.stages):
            state.completed = True
            state.game_active = False
            state.finished_at = utc_now_iso()
            state.score = calculate_final_score(state)
            message = f"{stage.success_message}\n\n🎁 Objeto conseguido: {stage.reward_item}"
            return ResolveResult(True, message, state, completed=True)

        state.current_stage += 1
        next_story = self.current_stage(state).story
        message = f"{stage.success_message}\n\n🎁 Objeto conseguido: {stage.reward_item}\n\n{next_story}"
        return ResolveResult(True, message, state)

    def final_message(self, state: GameState) -> str:
        return f"""🏆 ESCAPE ROOM COMPLETADO

Aventura: El Archivo de las Doce Llaves

Tiempo total: {human_duration(state.started_at, state.finished_at)}
Jugadores: {', '.join(state.players) if state.players else 'Sin jugadores registrados'}
Pistas usadas: {state.hints_used}
Errores cometidos: {state.wrong_answers}
Puntuación final: {state.score}

Rango obtenido: {rank_for_score(state.score)}

El Archivista os entrega el Elixir:

'Un grupo que piensa unido puede abrir puertas que una persona sola ni siquiera ve.'

Gracias por jugar."""

    def status_message(self, state: GameState) -> str:
        stage = self.current_stage(state) if not state.completed else self.stages[-1]
        return f"""📖 Estado del Archivo

Fase actual: {state.current_stage} - {stage.title}
Viaje del héroe: {stage.hero_journey_stage}
Jugadores: {', '.join(state.players) if state.players else 'Nadie se ha unido todavía'}
Pistas usadas: {state.hints_used}
Errores: {state.wrong_answers}
Tiempo: {human_duration(state.started_at, state.finished_at)}
Puntuación actual: {state.score}"""

    def inventory_message(self, state: GameState) -> str:
        if not state.inventory:
            return "🎒 El inventario aún está vacío."
        return "🎒 Inventario del grupo:\n" + "\n".join(f"- {item}" for item in state.inventory)
