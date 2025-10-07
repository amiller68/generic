# NOTE: Run 'make styles-py' before building this image
# This Dockerfile expects pre-built static assets in py/static/

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS app

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    make \
    && rm -rf /var/lib/apt/lists/*

# Copy the bin scripts from platform root (scripts expect to be 2 levels deep)
COPY bin/ ../bin/
COPY py/bin/ ./bin/

# Make sure the scripts are executable (including subdirectories)
RUN chmod +x ../bin/* && \
    find ./bin -type f -name "*.sh" -exec chmod +x {} \;

# Copy the requirements file into the container
COPY py/uv.lock .
COPY py/pyproject.toml .

# Install the Python dependencies
RUN uv sync

# Copy the application code
COPY py/src/ ./src/

# Copy the alembic artifacts
COPY py/alembic/ ./alembic/
COPY py/alembic.ini ./alembic.ini

# Copy pre-built static assets (run 'make styles-py' first)
COPY py/static/ ./static/

# Copy the html templates
COPY py/templates/ ./templates/

# Create a startup script
RUN echo '#!/bin/bash' > /app/start.sh && \
    echo '/app/bin/db.sh migrate' >> /app/start.sh && \
    echo '/app/bin/app/run.sh' >> /app/start.sh && \
    chmod +x /app/start.sh

# Expose the port the app runs on
EXPOSE 8000

# Set the entrypoint to our startup script
ENTRYPOINT ["/app/start.sh"]
