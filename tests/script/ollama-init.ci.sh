#!/bin/bash
# CI-only Ollama init: pulls only tinyllama and nomic-embed-text (lightweight, fast to pull).
# Full model list (aya, llama3.2) is NOT pulled to keep CI fast.

set -e

# Start Ollama in the background
ollama serve &

# Wait until Ollama CLI is responsive (timeout ~60s)
for i in {1..60}; do
    if ollama ls >/dev/null 2>&1; then
        echo "Ollama is ready"
        break
    fi
    echo "Waiting for Ollama... ($i)"
    sleep 1
done

# Pull lightweight models for CI
MODELS=("tinyllama" "nomic-embed-text")
for m in "${MODELS[@]}"; do
    echo "Pulling model: $m"
    ollama pull "$m" || echo "Warning: failed to pull $m"
done

# Keep container alive
wait
