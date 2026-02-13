#!/bin/bash

export LISTEN_ADDRESS=0.0.0.0
export LISTEN_PORT=8000
export DEBUG=False

uv run src/__main__.py

exit 0
