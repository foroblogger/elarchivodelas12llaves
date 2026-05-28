from __future__ import annotations

import logging

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
        except TelegramAPIError as exc:
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
    await message.answer(
        "🗄️ El Archivo de las Doce Llaves despierta.\n\n"
        "Caso abierto: asesinato de Javi, heredero de la familia Valcárcel.\n\n"
        "Que los detectives digan 'me uno' y luego 'empezamos'."
    )


@router.message(Command("unirse"))
async def join_game(message: Message) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("Aún no hay una partida activa. Decid 'abrir caso' para abrir el Archivo.")
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


@router.message(Command("comenzar"))
async def begin_game(message: Message) -> None:
    database = require_db()
    state = database.get_game(message.chat.id)
    if not state or not state.game_active:
        await message.answer("No hay partida activa. Decid 'abrir caso' primero.")
        return
    if state.started_at is not None:
        await message.answer("La investigación ya ha comenzado. Decid 'cómo vamos' para consultar la sala actual.")
        return
    if not state.players:
        await message.answer("Antes de comenzar, al menos un detective debe decir 'me uno'.")
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
        await message.answer("La investigación todavía no ha comenzado. Decid 'empezamos'.")
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
        await message.answer("No hay una investigación activa. Decid 'abrir caso'.")
        return
    if state.started_at is None:
        await message.answer("Aún no podéis votar: primero decid 'empezamos'.")
        return

    option = (command.args or "").strip()
    if not option:
        await message.answer("Podéis votar diciendo 'voto A' o mencionando la opción que queréis investigar.")
        return

    result = engine.vote_by_text(state, player_display_name(message), option)
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
    await message.answer(
        "Esta versión del caso se juega hablando: 'investiguemos la vitrina', 'voto A' o 'acuso a Elena'."
    )


@router.message(Command("reset_escape"))
async def reset_escape(message: Message, bot: Bot) -> None:
    if not await require_admin_message(message, bot):
        return

    require_db().delete_game(message.chat.id)
    logger.info("Partida reiniciada en chat_id=%s", message.chat.id)
    await message.answer("♻️ El Archivo ha sido reiniciado. Decid 'abrir caso' para empezar de nuevo.")


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

    if any(phrase in normalized for phrase in ["crear partida", "empezar partida", "abrir caso", "nuevo caso"]):
        await start_escape(message)
        return

    if any(phrase in normalized for phrase in ["me uno", "quiero unirme", "me apunto", "soy detective"]):
        await join_game(message)
        return

    if any(phrase in normalized for phrase in ["comenzar", "empezamos", "empezar", "iniciar", "abrir la mansión"]):
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
        "voto", "votamos", "elijo", "elegimos", "escojo", "investiguemos",
        "investigar", "revisar", "examinar", "acuso", "acusamos",
    ]
    if normalized in {"a", "b", "c"}:
        return True
    return any(word in normalized for word in vote_words)
