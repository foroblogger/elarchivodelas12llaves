from datetime import datetime, timedelta, timezone

from game_engine import GameEngine, calculate_final_score, normalize_answer, rank_for_score


def test_normalize_answer_ignores_case_accents_punctuation_and_spaces():
    assert normalize_answer("UNIÓN") == normalize_answer(" union ")
    assert normalize_answer("La   unión, abre!!!") == "LA UNION ABRE"


def test_final_score_applies_bonuses_and_penalties():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana", "Luis", "Marta"]
    state.started_at = datetime.now(timezone.utc).isoformat()
    state.finished_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    state.score = 100

    assert calculate_final_score(state) == 145
    assert rank_for_score(145) == "Leyendas del Archivo"


def test_final_score_over_sixty_minutes_penalty():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.started_at = datetime.now(timezone.utc).isoformat()
    state.finished_at = (datetime.now(timezone.utc) + timedelta(minutes=61)).isoformat()
    state.score = 100
    state.hints_used = 1

    assert calculate_final_score(state) == 80


def test_correct_answer_advances_stage_and_updates_inventory():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    engine.begin_game(state)

    result = engine.resolve(state, " puerta ")

    assert result.correct is True
    assert state.current_stage == 2
    assert "🗝️ Llave del Umbral" in state.inventory


def test_detects_correct_answer_with_accents():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.current_stage = 10

    assert engine.is_correct_answer(engine.current_stage(state), "unión")


def test_incorrect_answer_penalizes_without_advancing():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    engine.begin_game(state)

    result = engine.resolve(state, "llave")

    assert result.correct is False
    assert state.current_stage == 1
    assert state.wrong_answers == 1
    assert state.score == 98
