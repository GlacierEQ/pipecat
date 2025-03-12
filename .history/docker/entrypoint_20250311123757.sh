#!/bin/bash
# Docker entry point script for Pipecat

set -e

# Create cache directory if it doesn't exist
if [ ! -d "${PIPECAT_CACHE_DIR}" ]; then
    mkdir -p "${PIPECAT_CACHE_DIR}"
    chmod 777 "${PIPECAT_CACHE_DIR}"
fi

# Handle special command cases
case "$1" in
    dashboard)
        exec python -m pipecat.cli dashboard --host "${2:-0.0.0.0}" --port "${3:-8080}" "${@:4}"
        ;;
    api)
        exec python -m pipecat.cli api --host "${2:-0.0.0.0}" --port "${3:-8000}" "${@:4}"
        ;;
    shell)
        exec /bin/bash
        ;;
    python)
        exec python "${@:2}"
        ;;
    *)
        # If the first argument looks like a flag, assume we want to run the dashboard
        if [ "${1:0:1}" = "-" ]; then
            exec python -m pipecat.cli dashboard "$@"
        else
            exec python -m pipecat.cli "$@"
        fi
        ;;
esac
