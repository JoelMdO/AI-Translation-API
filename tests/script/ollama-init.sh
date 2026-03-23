#!/bin/bash

set -e

# Start Ollama in the background
ollama serve &

# Wait until Ollama CLI is responsive (timeout ~60s)
for i in {1..60}; do
	if ollama ls >/dev/null 2>&1; then
		echo "Ollama is ready"
		break
	fi
	echo "Waiting for Ollama to become available... ($i)"
	sleep 1
done

# Ensure primary and fallback models are available locally.
# Pulling is idempotent — it's safe to run on each container start.
MODELS=("aya" "nomic-embed-text" "llama3.2")
for m in "${MODELS[@]}"; do
	echo "Pulling model: $m"
	ollama pull "$m" || echo "Warning: failed to pull $m"
done

# Wait for background processes to keep container alive
wait
