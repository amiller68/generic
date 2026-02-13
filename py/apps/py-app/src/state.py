from fastapi import (
    Request,
)
from dataclasses import dataclass
from fastapi_sso.sso.google import GoogleSSO
from enum import Enum as PyEnum

from py_core.database import (
    AsyncDatabase,
)
from src.config import Config, Secrets
from py_core.observability import Logger
from redis.asyncio import Redis


class AppStateExceptionType(PyEnum):
    startup_failed = "startup_failed"  # raised when startup fails


class AppStateException(Exception):
    def __init__(self, type: AppStateExceptionType, message: str):
        self.message = message
        self.type = type


@dataclass
class AppState:
    config: Config
    google_sso: GoogleSSO
    database: AsyncDatabase
    logger: Logger
    secrets: Secrets
    redis: Redis

    @classmethod
    def from_config(cls, config: Config):
        state = cls(
            config=config,
            google_sso=GoogleSSO(
                config.secrets.google_client_id,
                config.secrets.google_client_secret,
                redirect_uri=config.auth_redirect_uri,
                allow_insecure_http=config.dev_mode,
            ),
            database=AsyncDatabase(config.postgres_async_url),
            logger=Logger(config.log_path, config.debug),
            secrets=config.secrets,
            redis=Redis.from_url(config.redis_url),
        )
        return state

    async def startup(self):
        """run any startup logic here"""
        try:
            await self.database.initialize()
            await self.redis.ping()  # type: ignore[misc]
        except Exception as e:
            raise AppStateException(AppStateExceptionType.startup_failed, str(e)) from e

    async def shutdown(self):
        """run any shutdown logic here"""
        await self.redis.aclose()

    def set_on_request(self, request: Request):
        """set any request-specific state here"""
        request.state.app_state = self
