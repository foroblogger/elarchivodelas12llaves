from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import random
import re
import unicodedata

from database import GameState, utc_now_iso
from game_data import CASE_PROFILES, STAGES, CaseProfile, GameStage, VoteOption


INITIAL_SCORE = 100
HINT_PENALTY = 5
WRONG_ANSWER_PENALTY = 2
FALSE_LEAD_PENALTY = 3
OVER_TIME_PENALTY = 20
FAST_COMPLETION_BONUS = 15
NO_HINTS_BONUS = 20
GROUP_BONUS = 10

ROOM_NAMES = [stage.room_name for stage in STAGES]


@dataclass(frozen=True)
class VoteResult:
    accepted: bool
    message: str
    state: GameState
    majority_reached: bool = False
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
    def __init__(self, stages: list[GameStage] | None = None, cases: list[CaseProfile] | None = None) -> None:
        self.stages = stages or STAGES
        self.cases = cases or CASE_PROFILES

    def create_game(self, chat_id: int) -> GameState:
        case = random.choice(self.cases)
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
            case_id=case.id,
            votes={},
            discovered_clues=[],
            false_clues=[],
            expected_players=None,
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
        return self.stage_message(state)

    def set_expected_players(self, state: GameState, count: int) -> str:
        state.expected_players = max(1, count)
        joined = len(state.players)
        if joined >= state.expected_players:
            return self.begin_game(state)
        remaining = state.expected_players - joined
        return (
            f"Perfecto. Entonces sois {state.expected_players} detectives.\n\n"
            f"Ahora necesito que cada detective diga 'me uno'. "
            f"Faltan {remaining} por presentarse y, cuando estéis todos, empiezo a narrar la primera sala."
        )

    def should_auto_begin(self, state: GameState) -> bool:
        return (
            state.game_active
            and state.started_at is None
            and state.expected_players is not None
            and len(state.players) >= state.expected_players
        )

    def current_stage(self, state: GameState) -> GameStage:
        return self.stages[state.current_stage - 1]

    def current_case(self, state: GameState) -> CaseProfile:
        for case in self.cases:
            if case.id == state.case_id:
                return case
        return self.cases[0]

    def options_for_stage(self, state: GameState) -> list[VoteOption]:
        stage = self.current_stage(state)
        if stage.id == len(self.stages):
            return self.current_case(state).final_options
        return stage.options

    def stage_message(self, state: GameState) -> str:
        stage = self.current_stage(state)
        options = "\n".join(f"{option.code}) {option.label}" for option in self.options_for_stage(state))
        return f"""{stage.story}

Opciones de investigación:
{options}

Podéis votar hablando en lenguaje natural, por ejemplo: 'investiguemos el paraguas' o 'voto A'."""

    def vote(self, state: GameState, player_name: str, option_code: str) -> VoteResult:
        if player_name not in state.players:
            return VoteResult(False, "Antes de votar, únete a la investigación diciendo 'me uno'.", state)
        option = self._find_option(state, option_code)
        if option is None:
            return VoteResult(False, "Esa opción no existe. Decid A, B, C o mencionad la opción.", state)
        stage_key = str(state.current_stage)
        state.votes = state.votes or {}
        state.votes.setdefault(stage_key, {})
        state.votes[stage_key][player_name] = option.code
        counts = self.vote_counts(state)
        if counts[option.code] < self.majority_needed(state):
            return VoteResult(True, self.vote_progress_message(state, option.code), state)
        return self._resolve_majority(state, option)

    def vote_by_text(self, state: GameState, player_name: str, text: str) -> VoteResult:
        option = self._find_option_by_text(state, text)
        if option is None:
            options = ", ".join(f"{opt.code}) {opt.label}" for opt in self.options_for_stage(state))
            return VoteResult(False, f"No he entendido la opción. Podéis decir algo como 'voto A' o mencionar una opción:\n{options}", state)
        return self.vote(state, player_name, option.code)

    def _resolve_majority(self, state: GameState, option: VoteOption) -> VoteResult:
        stage = self.current_stage(state)
        if option.is_true_clue:
            state.discovered_clues = state.discovered_clues or []
            if option.clue and option.clue not in state.discovered_clues:
                state.discovered_clues.append(option.clue)
        else:
            state.false_clues = state.false_clues or []
            if option.clue and option.clue not in state.false_clues:
                state.false_clues.append(option.clue)
            state.score = max(0, state.score - FALSE_LEAD_PENALTY)
        if stage.key_item not in state.inventory:
            state.inventory.append(stage.key_item)
        if stage.id == len(self.stages):
            return self._finish_game(state, option)
        result_type = "Pista firme" if option.is_true_clue else "Pista dudosa"
        message = f"""{option.result}

{result_type}: {option.clue}

🎁 Llave encontrada: {stage.key_item}

La mayoría ha decidido. Se abre la siguiente sala.

{self._advance_to_next_stage(state)}"""
        return VoteResult(True, message, state, majority_reached=True)

    def _finish_game(self, state: GameState, option: VoteOption) -> VoteResult:
        case = self.current_case(state)
        state.completed = True
        state.game_active = False
        state.finished_at = utc_now_iso()
        if not option.is_true_clue:
            state.wrong_answers += 1
            state.score = max(0, state.score - 15)
        state.score = calculate_final_score(state)
        verdict = "✅ Acusación correcta." if option.is_true_clue else "❌ Acusación incorrecta."
        message = f"""{verdict}

La mayoría ha señalado:
{option.label}

🎁 Llave encontrada: {self.current_stage(state).key_item}

{case.confession if option.is_true_clue else "El verdadero culpable escucha en silencio. Eso, en esta familia, ya es casi una confesión."}"""
        return VoteResult(True, message, state, majority_reached=True, completed=True)

    def _advance_to_next_stage(self, state: GameState) -> str:
        state.current_stage += 1
        return self.stage_message(state)

    def _find_option(self, state: GameState, option_code: str) -> VoteOption | None:
        normalized = normalize_answer(option_code)
        for option in self.options_for_stage(state):
            if normalize_answer(option.code) == normalized:
                return option
        return None

    def _find_option_by_text(self, state: GameState, text: str) -> VoteOption | None:
        normalized = normalize_answer(text)
        options = self.options_for_stage(state)
        for option in options:
            if re.search(rf"\b{re.escape(normalize_answer(option.code))}\b", normalized):
                return option
        best_option = None
        best_score = 0
        ignored = {"VOTO", "VOTAR", "ELIJO", "ESCOJO", "QUIERO", "INVESTIGAR", "REVISAR", "EXAMINAR", "ACUSAR", "ACUSO", "A", "AL", "LA", "EL", "LOS", "LAS", "DE", "DEL", "POR", "QUE"}
        text_words = {word for word in normalized.split() if word not in ignored and len(word) > 2}
        for option in options:
            label_words = {word for word in normalize_answer(option.label).split() if word not in ignored and len(word) > 2}
            score = len(text_words & label_words)
            if score > best_score:
                best_option = option
                best_score = score
        return best_option if best_score > 0 else None

    def majority_needed(self, state: GameState) -> int:
        return max(1, len(state.players) // 2 + 1)

    def vote_counts(self, state: GameState) -> dict[str, int]:
        votes = (state.votes or {}).get(str(state.current_stage), {})
        counts = {option.code: 0 for option in self.options_for_stage(state)}
        for code in votes.values():
            if code in counts:
                counts[code] += 1
        return counts

    def vote_progress_message(self, state: GameState, voted_code: str | None = None) -> str:
        counts = self.vote_counts(state)
        lines = [f"🗳️ Voto registrado{f' para {voted_code}' if voted_code else ''}.", f"Mayoría necesaria: {self.majority_needed(state)}"]
        lines.extend(f"{code}: {count}" for code, count in counts.items())
        return "\n".join(lines)

    def get_hint(self, state: GameState) -> str:
        stage = self.current_stage(state)
        index = min(state.hints_used, len(stage.hints) - 1)
        state.hints_used += 1
        state.score = max(0, state.score - HINT_PENALTY)
        return f"💡 Pista {index + 1}/{len(stage.hints)}:\n{stage.hints[index]}\n\nPenalización: -5 puntos."

    def resolve(self, state: GameState, answer: str) -> VoteResult:
        return self.vote(state, " ".join(state.players[:1]) if state.players else "", answer)

    def final_message(self, state: GameState) -> str:
        case = self.current_case(state)
        return f"""🏆 ESCAPE ROOM COMPLETADO

Aventura: El Archivo de las Doce Llaves

Tiempo total: {human_duration(state.started_at, state.finished_at)}
Jugadores: {', '.join(state.players) if state.players else 'Sin jugadores registrados'}
Pistas usadas: {state.hints_used}
Errores cometidos: {state.wrong_answers}
Pistas falsas seguidas: {len(state.false_clues or [])}
Puntuación final: {state.score}

Rango obtenido: {rank_for_score(state.score)}

INFORME FINAL

Culpable: {case.culprit}

Móvil:
{case.motive}

Método:
{case.method}

Pista decisiva:
{case.decisive_clue}

Pistas falsas:
{self._format_list(case.false_leads)}

Pistas reales encontradas:
{self._format_list(state.discovered_clues or [])}

Gracias por jugar."""

    def status_message(self, state: GameState) -> str:
        stage = self.current_stage(state) if not state.completed else self.stages[-1]
        return f"""📖 Estado del Archivo

Sala actual: {state.current_stage} - {stage.room_name}
Capítulo: {stage.title}
Jugadores: {', '.join(state.players) if state.players else 'Nadie se ha unido todavía'}
Mayoría necesaria: {self.majority_needed(state)}
Votos actuales:
{self.vote_progress_message(state)}
Pistas usadas: {state.hints_used}
Errores: {state.wrong_answers}
Tiempo: {human_duration(state.started_at, state.finished_at)}
Puntuación actual: {state.score}"""

    def inventory_message(self, state: GameState) -> str:
        if not state.inventory:
            return "🎒 El llavero aún está vacío."
        return "🎒 Llaves encontradas:\n" + "\n".join(f"- {item}" for item in state.inventory)

    @staticmethod
    def _format_list(items: list[str]) -> str:
        if not items:
            return "- Ninguna"
        return "\n".join(f"- {item}" for item in items)
