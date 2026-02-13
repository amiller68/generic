# NOTE: Run 'make styles-py' before building this image
# This Dockerfile expects pre-built static assets
# Build context is the repository root

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS runtime

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy bin scripts from root (needed by db.sh)
COPY bin/ ../bin/

# Copy project configuration (needed by bin/config)
COPY .env.project ../.env.project
COPY .env.vault ../.env.vault

# Copy Python workspace files
COPY py/uv.lock ./uv.lock
COPY py/pyproject.toml ./pyproject.toml

# Copy Python packages
COPY py/packages/py-core/ ./packages/py-core/

# Copy Python app code
COPY py/apps/py-app/pyproject.toml ./apps/py-app/pyproject.toml
COPY py/apps/py-app/src/ ./apps/py-app/src/

# Copy templates and static assets
COPY py/apps/py-app/templates/ ./apps/py-app/templates/
COPY py/apps/py-app/static/ ./apps/py-app/static/

# Sync uv workspace to install all Python packages
RUN uv sync --all-packages

# Make all shell scripts executable
RUN find ../bin -type f -name "*.sh" -exec chmod +x {} \;

# Create startup script that runs migrations then starts the server
RUN echo '#!/bin/bash\n\
set -ex\n\
echo "Starting application..."\n\
echo "Running migrations..."\n\
cd /app/packages/py-core\n\
uv run alembic upgrade head\n\
echo "Starting server..."\n\
cd /app\n\
export LISTEN_ADDRESS=0.0.0.0\n\
export LISTEN_PORT=8000\n\
export DEBUG=False\n\
export STATIC_DIR=/app/apps/py-app/static\n\
export TEMPLATES_DIR=/app/apps/py-app/templates\n\
uv run python apps/py-app/src/__main__.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE 8000

# Using CMD instead of ENTRYPOINT allows Kamal to override for worker/scheduler roles
CMD ["/app/start.sh"]
