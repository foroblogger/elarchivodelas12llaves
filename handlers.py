from __future__ import annotations

import logging

from aiogram import Bot, Router
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from database import Database
from game_engine import GameEngine, rank_for_score


logger = logging.getLogger(__name__)
router = Router()
db: Database | None = None
engine = GameEngine()

ROOM_NAMES = [
    "Vestíbulo del Archivo",
    "Sala 01 - Mundo ordinario",
    "Sala 02 - Llamada a la aventura",
    "Sala 03 - Rechazo de la llamada",
    "Sala 04 - Encuentro con el mentor",
    "Sala 05 - Cruce del umbral",
    "Sala 06 - Pruebas y aliados",
    "Sala 07 - El Bucle Negro",
    "Sala 08 - Cámara del Silencio",
    "Sala 09 - Prueba suprema",
    "Sala 10 - Recompensa",
    "Sala 11 - Camino de regreso",
    "Sala 12 - Decisión final",
    "Ranking - Salón de los Héroes",
]


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
        "Partida creada. Que los jugadores usen /unirse y luego /comenzar."
    )


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
        await message.answer(f"✅ {name} se une a la Compañía de las Doce Llaves.")
    else:
        await message.answer(f"✅ {name} ya forma parte de la partida.")


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

    answer = (command.args or "").strip()
    if not answer:
        await message.answer("Escribid la respuesta así: /resolver vuestra respuesta")
        return

    result = engine.resolve(state, answer)
    database.save_game(state)
    logger.info(
        "Respuesta en chat_id=%s correct=%s stage=%s score=%s",
        message.chat.id,
        result.correct,
        state.current_stage,
        state.score,
    )
    await message.answer(result.message)
    if result.completed:
        await message.answer(engine.final_message(state))


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
