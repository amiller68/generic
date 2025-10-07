from dotenv import load_dotenv
import os
from enum import Enum as PyEnum

# TODO: storage
# TODO: task manager
# TODO: llm
# TODO: redis

MIN_SECRET_LENGTH = 16


class ConfigExceptionType(PyEnum):
    missing_env_var = "missing_env_var"


class ConfigException(Exception):
    def __init__(self, type: ConfigExceptionType, message: str):
        self.message = message
        self.type = type


def empty_to_none(field):
    value = os.getenv(field)
    if value is None or len(value) == 0:
        return None
    return value


class Secrets:
    # generic service secret
    service_secret: str

    # google sso credentials
    google_client_id: str
    google_client_secret: str

    def __str__(self):
        # show *** hidden values interleaved with first and last 3 chars
        #  of the actual value
        def mask_secret(secret: str | None) -> str:
            secret_str = str(secret)
            return f"{secret_str[:3]}...{secret_str[-3:]}"

        return f"Secrets(service_secret={mask_secret(self.service_secret)}, google_client_id={self.google_client_id}, google_client_secret={mask_secret(self.google_client_secret)})"

    def __init__(self):
        self.service_secret = empty_to_none("SERVICE_SECRET")
        if not self.service_secret:
            # Generate a random secret if not provided
            import secrets

            self.service_secret = secrets.token_urlsafe(32)
            print(f"Generated SERVICE_SECRET: {self.service_secret[:8]}...")
        elif len(self.service_secret) < MIN_SECRET_LENGTH:
            raise ConfigException(
                ConfigExceptionType.invalid_env_var,
                f"SERVICE_SECRET environment variable must be at least {MIN_SECRET_LENGTH} characters long",
            )

        # google sso credentials
        self.google_client_id = empty_to_none("GOOGLE_O_AUTH_CLIENT_ID")
        self.google_client_secret = empty_to_none("GOOGLE_O_AUTH_CLIENT_SECRET")

        # throw if GOOGLE_O_AUTH_CLIENT_ID or GOOGLE_O_AUTH_CLIENT_SECRET is not set
        if not self.google_client_id:
            raise ConfigException(
                ConfigExceptionType.missing_env_var,
                "GOOGLE_O_AUTH_CLIENT_ID environment variable must be set",
            )
        if not self.google_client_secret:
            raise ConfigException(
                ConfigExceptionType.missing_env_var,
                "GOOGLE_O_AUTH_CLIENT_SECRET environment variable must be set",
            )


# TODO: getopt() for cmd line arguments
class Config:
    # whether we're in dev mode -- controls
    #  whether to enable dev features like hot reloading
    #  + http enabled for google sso
    dev_mode: bool

    # listening
    host_name: str
    listen_address: str
    listen_port: int
    auth_redirect_uri: str

    # marketing site URL (for linking back from login page)
    marketing_site_url: str

    # database
    # TODO (amiller68): ... what do we use this for?
    postgres_url: str
    postgres_async_url: str

    # logging
    debug: bool
    log_path: str | None

    # nest secrets in their own object
    secrets: Secrets

    def __str__(self):
        return f"Config(dev_mode={self.dev_mode}, host_name={self.host_name}, listen_address={self.listen_address}, listen_port={self.listen_port}, auth_redirect_uri={self.auth_redirect_uri}, marketing_site_url={self.marketing_site_url}, postgres_url={self.postgres_url}, postgres_async_url={self.postgres_async_url}, debug={self.debug}, log_path={self.log_path}, secrets={self.secrets})"

    def __init__(self):
        # Load the environment variables
        load_dotenv()

        self.dev_mode = os.getenv("DEV_MODE", "False") == "True"

        self.host_name = os.getenv("HOST_NAME", "http://localhost:8000")
        self.listen_address = os.getenv("LISTEN_ADDRESS", "0.0.0.0")
        self.listen_port = int(os.getenv("LISTEN_PORT", 8000))
        self.auth_redirect_uri = os.getenv(
            "AUTH_REDIRECT_URI", f"{self.host_name}/auth/google/callback"
        )

        # Marketing site URL with safe default
        self.marketing_site_url = os.getenv(
            "MARKETING_SITE_URL", "http://localhost:3000"
        )

        # TODO (amiller68): is this the correct way to handle postgres urls?
        #  i.e. what if we're pooling?
        self.postgres_url = empty_to_none("POSTGRES_URL")
        if not self.postgres_url:
            raise ConfigException(
                ConfigExceptionType.missing_env_var,
                "POSTGRES_URL environment variable must be set",
            )
        self.postgres_async_url = self.postgres_url.replace(
            "postgresql://", "postgresql+asyncpg://"
        )

        # Set the log path
        self.log_path = empty_to_none("LOG_PATH")

        # Determine if the DEBUG mode is set
        debug = os.getenv("DEBUG", "True")
        self.debug = debug == "True"

        self.secrets = Secrets()

    def show(self, deep: bool = False):
        if deep:
            print(self.__dict__)
            print(self.secrets.__dict__)
        else:
            print(self.__dict__)
