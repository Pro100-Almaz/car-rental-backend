#!/bin/bash
set -e

PORT=${2:-8000}
RELOAD_FLAG=""
if [ "${UVICORN_RELOAD:-false}" = "true" ]; then
    RELOAD_FLAG="--reload"
fi

case "$1" in
    start)
        alembic upgrade head
        exec uvicorn app.main.run:make_app --factory --host 0.0.0.0 --port "$PORT" $RELOAD_FLAG
        ;;
    pytest)
        alembic upgrade head
        shift
        exec pytest "$@"
        ;;
    *)
        exec "$@"
        ;;
esac
