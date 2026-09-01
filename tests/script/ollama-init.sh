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

# Preload the primary model so the first real translation does not pay the
# model-load cost. OLLAMA_KEEP_ALIVE keeps it resident after this request.
echo "Warming model: aya"
ollama run aya "" >/dev/null || echo "Warning: failed to warm aya"

# Wait for background processes to keep container alive
wait
