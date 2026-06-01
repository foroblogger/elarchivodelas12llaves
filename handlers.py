from __future__ import annotations

import logging
import re

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from database import Database
from game_engine import GameEngine, ROOM_NAMES, rank_for_score


logger = logging.getLogger(__name__)
router = Router()
db: Database | None = None
engine = GameEngine()


def setup_handlers(database: Database) -> Router:
    global db
    db = database
    return router


def require_db() -> Database:
    if db is None:
        raise RuntimeError("La base de datos no se ha inicializado.")
    return db


def player_display_name(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "Jugador sin nombre"
    return user.full_name or user.username or f"Jugador {user.id}"


async def is_group_admin(bot: Bot, chat_id: int, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id, user_id)
    return member.status in {"creator", "administrator"}


async def require_admin_message(message: Message, bot: Bot) -> bool:
    user = message.from_user
    if user is None or not await is_group_admin(bot, message.chat.id, user.id):
        await message.answer("🔒 Solo un administrador del grupo puede usar este comando.")
        return False
    return True


@router.message(Command("crear_salas"))
async def create_rooms(message: Message, bot: Bot) -> None:
    if not await require_admin_message(message, bot):
        return

    chat = await bot.get_chat(message.chat.id)
    if not getattr(chat, "is_forum", False):
        await message.answer(
            "Para crear salas, primero activa los temas del grupo en Telegram "
            "Ajustes del grupo > Temas."
        )
        return

    created: list[str] = []
    failed: list[str] = []
    await message.answer("🛠️ El Archivista empieza a abrir las salas del Archivo...")
    for room_name in ROOM_NAMES:
        try:
            await bot.create_forum_topic(chat_id=message.chat.id, name=room_name)
            created.append(room_name)
        except TelegramBadRequest as exc:
            logger.warning("No se pudo crear la sala %s: %s", room_name, exc)
            failed.append(room_name)
        except TelegramForbiddenError as exc:
            logger.warning("Permisos insuficientes creando salas en chat_id=%s: %s", message.chat.id, exc)
            await message.answer(
                "No tengo permisos suficientes para crear temas. "
                "Hazme administrador y activa el permiso para gestionar temas."
            )
            return
        except TelegramAPIError:
            logger.exception("Error de Telegram creando la sala %s", room_name)
            failed.append(room_name)

    response = [f"✅ Salas creadas: {len(created)}"]
    if created:
        response.extend(f"- {room}" for room in created)
    if failed:
        response.append("")
        response.append(
            "⚠️ Algunas salas no se pudieron crear. Si ya existían, Telegram puede haber rechazado duplicados:"
        )
        response.extend(f"- {room}" for room in failed)
    await message.answer("\n".join(response))


@router.message(Command("start_escape"))
async def start_escape(message: Message) -> None:
    database = require_db()
    current = database.get_game(message.chat.id)
    if current and current.game_active and not current.completed:
        await message.answer("🕯️ Ya hay una partida activa en este grupo. Usad /estado para verla.")
        return

    state = engine.create_game(message.chat.id)
    database.save_game(state)
    logger.info("Nueva partida creada en chat_id=%s", message.chat.id)
    await message.answer(opening_intro())


@router.message(Command("unirse"))
async def join_game(message: Message) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("Aún no hay una partida activa. Usad /start_escape para abrir el Archivo.")
        return
    if state.started_at is not None:
        await message.answer("La puerta ya se ha cerrado tras el grupo. La partida está en marcha.")
        return

    name = player_display_name(message)
    added = engine.add_player(state, name)
    database.save_game(state)
    if added:
        await message.answer(f"✅ {name} se une al equipo de detectives.")
    else:
        await message.answer(f"✅ {name} ya forma parte de la partida.")
    if engine.should_auto_begin(state):
        story = engine.begin_game(state)
        database.save_game(state)
        await message.answer(
            "Ya estáis todos. La mansión cierra sus puertas y empieza la investigación.\n\n"
            f"{story}"
        )
    elif state.expected_players:
        await message.answer(waiting_for_players_message(state))


@router.message(Command("comenzar"))
async def begin_game(message: Message) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("No hay partida activa. Usad /start_escape primero.")
        return
    if state.started_at is not None:
        await message.answer("La aventura ya ha comenzado. Usad /estado para consultar la fase actual.")
        return
    if not state.players:
        await message.answer("Antes de comenzar, al menos un jugador debe usar /unirse.")
        return
    if state.expected_players is None:
        await message.answer("Antes necesito saber cuántos detectives sois. Decid algo como 'somos 5'.")
        return

    story = engine.begin_game(state)
    database.save_game(state)
    logger.info("Partida iniciada en chat_id=%s", message.chat.id)
    await message.answer(story)


@router.message(Command("estado"))
async def status(message: Message) -> None:
    state = require_db().get_game(message.chat.id)
    if not state:
        await message.answer("No hay partida registrada en este grupo.")
        return
    await message.answer(engine.status_message(state))


@router.message(Command("inventario"))
async def inventory(message: Message) -> None:
    state = require_db().get_game(message.chat.id)
    if not state:
        await message.answer("No hay partida registrada en este grupo.")
        return
    await message.answer(engine.inventory_message(state))


@router.message(Command("pista"))
async def hint(message: Message) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("No hay partida activa para pedir una pista.")
        return
    if state.started_at is None:
        await message.answer("La aventura todavía no ha comenzado. Usad /comenzar.")
        return

    hint_text = engine.get_hint(state)
    database.save_game(state)
    logger.info("Pista usada en chat_id=%s total=%s", message.chat.id, state.hints_used)
    await message.answer(hint_text)


@router.message(Command("votar"))
async def vote(message: Message, command: CommandObject) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("No hay una investigación activa. Usad /start_escape.")
        return
    if state.started_at is None:
        await message.answer("Aún no podéis votar: primero usad /comenzar.")
        return

    option = (command.args or "").strip()
    if not option:
        await message.answer("Votad así: /votar A, /votar B o /votar C")
        return

    result = engine.vote(state, player_display_name(message), option)
    database.save_game(state)
    logger.info(
        "Voto en chat_id=%s accepted=%s majority=%s stage=%s score=%s",
        message.chat.id,
        result.accepted,
        result.majority_reached,
        state.current_stage,
        state.score,
    )
    await message.answer(result.message)
    if result.completed:
        await message.answer(engine.final_message(state))


@router.message(Command("resolver"))
async def resolve(message: Message, command: CommandObject) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("No hay partida activa. El Archivo permanece dormido.")
        return
    if state.started_at is None:
        await message.answer("Aún no podéis resolver: primero usad /comenzar.")
        return

    await message.answer(
        "Esta versión del caso avanza por votación. Usad /votar A, /votar B o /votar C."
    )


@router.message(Command("reset_escape"))
async def reset_escape(message: Message, bot: Bot) -> None:
    if not await require_admin_message(message, bot):
        return

    require_db().delete_game(message.chat.id)
    logger.info("Partida reiniciada en chat_id=%s", message.chat.id)
    await message.answer("♻️ El Archivo ha sido reiniciado. Usad /start_escape para empezar de nuevo.")


@router.message(Command("ranking"))
async def ranking(message: Message) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if state and state.completed:
        await message.answer(
            f"🏆 Resultado final\n\n"
            f"Puntuación: {state.score}\n"
            f"Rango: {rank_for_score(state.score)}\n"
            f"Jugadores: {', '.join(state.players) if state.players else 'Sin jugadores registrados'}"
        )
        return

    completed = database.list_completed_games()[:5]
    if not completed:
        await message.answer("Aún no hay partidas completadas en el ranking.")
        return

    lines = ["🏆 Ranking del Archivo"]
    for index, game in enumerate(completed, start=1):
        players = ", ".join(game.players) if game.players else f"Chat {game.chat_id}"
        lines.append(f"{index}. {players} - {game.score} pts - {rank_for_score(game.score)}")
    await message.answer("\n".join(lines))


@router.message()
async def natural_language(message: Message) -> None:
    if not message.text or message.text.startswith("/"):
        return

    text = message.text.strip()
    normalized = text.casefold()
    database = require_db()
    state = database.get_game(message.chat.id)

    if state is None and looks_like_game_start(normalized):
        await start_escape(message)
        return

    if state and state.game_active and state.started_at is None:
        handled = await handle_setup_conversation(message, state, text, normalized)
        if handled:
            return

    if any(phrase in normalized for phrase in ["crear partida", "empezar partida", "abrir caso", "nuevo caso"]):
        await start_escape(message)
        return

    if any(phrase in normalized for phrase in ["me uno", "quiero unirme", "me apunto", "soy detective"]):
        await join_game(message)
        return

    if any(
        phrase in normalized
        for phrase in ["ya estamos", "estamos todos", "estamos listos", "listos", "comenzar", "empezamos", "empezar", "iniciar", "abrir la mansión"]
    ):
        await begin_game(message)
        return

    if any(phrase in normalized for phrase in ["estado", "cómo vamos", "como vamos", "situación", "situacion"]):
        await status(message)
        return

    if any(phrase in normalized for phrase in ["inventario", "llaves", "qué tenemos", "que tenemos"]):
        await inventory(message)
        return

    if any(phrase in normalized for phrase in ["pista", "ayuda", "orientación", "orientacion"]):
        await hint(message)
        return

    if not state or not state.game_active or state.started_at is None:
        return

    if looks_like_vote(text):
        result = engine.vote_by_text(state, player_display_name(message), text)
        database.save_game(state)
        await message.answer(result.message)
        if result.completed:
            await message.answer(engine.final_message(state))


def looks_like_vote(text: str) -> bool:
    normalized = text.casefold().strip()
    vote_words = [
        "voto",
        "votamos",
        "elijo",
        "elegimos",
        "escojo",
        "investiguemos",
        "investigar",
        "revisar",
        "examinar",
        "acuso",
        "acusamos",
    ]
    if normalized in {"a", "b", "c"}:
        return True
    return any(word in normalized for word in vote_words)


async def handle_setup_conversation(
    message: Message,
    state,
    text: str,
    normalized: str,
) -> bool:
    database = require_db()
    player_count = extract_player_count(text)
    if state.expected_players is None:
        if player_count is not None:
            if player_display_name(message) not in state.players:
                engine.add_player(state, player_display_name(message))
            response = engine.set_expected_players(state, player_count)
            database.save_game(state)
            await message.answer(response)
            return True

        await message.answer(
            "Antes de abrir la mansión necesito saber cuántos detectives habéis venido.\n\n"
            "Podéis responder de forma natural, por ejemplo: 'somos 5', 'estamos 4' o 'seremos 3'."
        )
        return True

    if any(
        phrase in normalized
        for phrase in ["ya estamos", "estamos todos", "estamos listos", "listos", "empezamos", "comenzar", "empezar"]
    ):
        if not state.players:
            engine.add_player(state, player_display_name(message))
        story = engine.begin_game(state)
        database.save_game(state)
        await message.answer(
            "Perfecto. Cierro la verja de la mansión. Nadie entra, nadie sale, y alguien va a tener una noche larguísima.\n\n"
            f"{story}"
        )
        return True

    if looks_like_join(normalized) or should_auto_register_setup_message(normalized):
        added = engine.add_player(state, player_display_name(message))
        database.save_game(state)
        if engine.should_auto_begin(state):
            story = engine.begin_game(state)
            database.save_game(state)
            await message.answer(
                "Ya estáis todos. La tormenta corta el camino del pueblo y la mansión cierra sus puertas.\n\n"
                f"{story}"
            )
        elif added:
            await message.answer(f"✅ {player_display_name(message)} queda registrado.\n\n{waiting_for_players_message(state)}")
        else:
            await message.answer(waiting_for_players_message(state))
        return True

    return False


def opening_intro() -> str:
    return (
        "🗄️ El Archivo de las Doce Llaves despierta.\n\n"
        "La tormenta cae sobre una mansión familiar española, de esas donde las paredes tienen humedad, "
        "los retratos tienen mala leche y todo el mundo dice 'familia' como quien dice 'coartada'.\n\n"
        "Javi, heredero de los Valcárcel, ha aparecido muerto en la biblioteca por un disparo de escopeta de postas.\n\n"
        "Antes de abrir la primera sala necesito configurar la investigación.\n\n"
        "¿Cuántos detectives habéis venido esta noche?"
    )


def waiting_for_players_message(state) -> str:
    expected = state.expected_players or 0
    joined = len(state.players)
    remaining = max(0, expected - joined)
    players = ", ".join(state.players) if state.players else "nadie todavía"
    if remaining == 0:
        return "Ya estáis todos. Decid 'estamos listos' si queréis que empiece la narración."
    return (
        f"Detectives registrados: {joined}/{expected}.\n"
        f"Equipo actual: {players}.\n\n"
        f"Faltan {remaining}. Cada detective puede escribir cualquier saludo claro, por ejemplo: "
        "'me uno', 'estoy aquí' o 'soy detective'."
    )


def looks_like_game_start(normalized: str) -> bool:
    starters = [
        "hola",
        "empezar",
        "empecemos",
        "abrir caso",
        "nuevo caso",
        "iniciar juego",
        "jugar",
        "comenzar",
    ]
    return any(starter in normalized for starter in starters)


def looks_like_join(normalized: str) -> bool:
    joiners = [
        "me uno",
        "quiero unirme",
        "me apunto",
        "soy detective",
        "estoy aqui",
        "estoy aquí",
        "presente",
        "entro",
        "aqui",
        "aquí",
    ]
    return any(joiner in normalized for joiner in joiners)


def should_auto_register_setup_message(normalized: str) -> bool:
    blocked = [
        "pista",
        "estado",
        "inventario",
        "llaves",
        "como vamos",
        "cómo vamos",
        "cuantos",
        "cuántos",
        "somos",
        "estamos todos",
        "ya estamos",
        "listos",
        "empezamos",
        "comenzar",
        "empezar",
    ]
    return bool(normalized) and not any(word in normalized for word in blocked)


def extract_player_count(text: str) -> int | None:
    normalized = text.casefold()
    if not any(word in normalized for word in ["somos", "estamos", "seremos", "jugadores", "detectives"]):
        return None
    match = re.search(r"\b(\d{1,2})\b", normalized)
    if not match:
        return None
    count = int(match.group(1))
    if 1 <= count <= 10:
        return count
    return None
