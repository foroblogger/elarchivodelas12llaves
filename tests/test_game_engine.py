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


def test_game_starts_with_random_case_and_stage_message_options():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    message = engine.begin_game(state)

    assert state.case_id
    assert "Opciones de investigación" in message
    assert "lenguaje natural" in message


def test_expected_players_gate_can_auto_begin():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana"]

    response = engine.set_expected_players(state, 2)

    assert state.expected_players == 2
    assert "Faltan 1" in response
    assert engine.should_auto_begin(state) is False

    state.players.append("Luis")

    assert engine.should_auto_begin(state) is True


def test_vote_waits_until_majority():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana", "Luis", "Marta"]
    engine.begin_game(state)

    result = engine.vote(state, "Ana", "A")

    assert result.accepted is True
    assert result.majority_reached is False
    assert state.current_stage == 1


def test_majority_vote_advances_stage_and_adds_key():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana", "Luis", "Marta"]
    engine.begin_game(state)

    engine.vote(state, "Ana", "A")
    result = engine.vote(state, "Luis", "A")

    assert result.majority_reached is True
    assert state.current_stage == 2
    assert "🗝️ Llave de hierro del Salón" in state.inventory
    assert state.discovered_clues


def test_natural_language_vote_matches_option_label():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana"]
    engine.begin_game(state)

    result = engine.vote_by_text(state, "Ana", "investiguemos el paraguas mojado")

    assert result.majority_reached is True
    assert state.current_stage == 2
    assert "Barro rojo de la capilla" in state.discovered_clues


def test_natural_language_vote_matches_final_accusation_name():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana"]
    state.started_at = datetime.now(timezone.utc).isoformat()
    state.current_stage = 12
    correct_option = next(option for option in engine.options_for_stage(state) if option.is_true_clue)
    accused_text = f"acuso a {correct_option.label}"

    result = engine.vote_by_text(state, "Ana", accused_text)

    assert result.completed is True
    assert state.completed is True


def test_false_vote_penalizes_but_still_advances():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana"]
    engine.begin_game(state)

    result = engine.vote(state, "Ana", "B")

    assert result.majority_reached is True
    assert state.current_stage == 2
    assert state.score == 97
    assert state.false_clues


def test_final_vote_completes_game():
    engine = GameEngine()
    state = engine.create_game(chat_id=1)
    state.players = ["Ana"]
    state.started_at = datetime.now(timezone.utc).isoformat()
    state.current_stage = 12
    correct = next(option.code for option in engine.options_for_stage(state) if option.is_true_clue)

    result = engine.vote(state, "Ana", correct)

    assert result.completed is True
    assert state.completed is True
    assert state.game_active is False
    assert "Culpable:" in engine.final_message(state)
