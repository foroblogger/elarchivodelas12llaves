from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    database_path: str = "escape_room.sqlite3"
    telegram_ssl_verify: bool = True


def get_settings() -> Settings:
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    database_path = os.getenv("DATABASE_PATH", "escape_room.sqlite3").strip()
    ssl_verify = os.getenv("TELEGRAM_SSL_VERIFY", "true").strip().lower() not in {
        "0",
        "false",
        "no",
    }
    if not token:
        raise RuntimeError(
            "TELEGRAM_BOT_TOKEN no está configurado. Copia .env.example a .env y añade tu token."
        )
    return Settings(
        telegram_bot_token=token,
        database_path=database_path,
        telegram_ssl_verify=ssl_verify,
    )
