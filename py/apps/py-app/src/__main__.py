import sys
import uvicorn
from typing import Optional

from src.state import AppState
from src.server import create_app
from src.config import Config


def init_state(config: Config) -> Optional[AppState]:
    try:
        state = AppState.from_config(config)
        print("✓ Application state initialized")
        return state
    except Exception as e:
        print(f"✗ Failed to initialize application state: {e}")
        return None


config = Config()
print(f"config: {config}")
state = init_state(config)
app = create_app(state) if state else None


def main() -> int:
    try:
        if not state or not app:
            print("✗ Failed to initialize application")
            return 1

        print("✓ Configuration loaded from environment")
        print("✓ FastAPI application created")
        print(f"Starting server on {config.listen_address}:{config.listen_port}")

        if config.dev_mode:
            uvicorn.run(
                "src.__main__:app",
                host=config.listen_address,
                port=config.listen_port,
                proxy_headers=True,
                reload=True,
                reload_dirs=[
                    "src",
                    "templates",
                    "static",
                    "../../packages/py-core/src",
                ],
            )
        else:
            uvicorn.run(
                app,
                host=config.listen_address,
                port=config.listen_port,
                proxy_headers=True,
            )
        return 0
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
