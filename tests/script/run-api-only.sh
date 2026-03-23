#!/bin/bash
# Starts only the API and its direct dependencies (ollama, chroma) for isolated local testing.
# Uses docker-compose.ci.yml at the workspace root — no Editor, Proxy, or CMS services are started.
set -e

# Resolve workspace root (3 levels up from API/tests/script/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
COMPOSE_FILE="$WORKSPACE_ROOT/docker-compose.ci.yml"

if [ ! -f "$COMPOSE_FILE" ]; then
  echo "[ERROR] docker-compose.ci.yml not found at: $COMPOSE_FILE"
  echo "        Make sure you are running this from within the API/tests/script directory"
  echo "        or that docker-compose.ci.yml exists at the workspace root."
  exit 1
fi

echo "[INFO] Using $COMPOSE_FILE"
echo "[INFO] Starting fastapi, ollama, and chroma containers only..."
docker compose -f "$COMPOSE_FILE" up -d --build fastapi ollama chroma

# Wait for API health
API_URL="http://localhost:443/health"
echo "[INFO] Waiting for API to become healthy at $API_URL..."

for i in {1..30}; do
  if curl -s --fail "$API_URL" > /dev/null; then
    echo "[SUCCESS] API is healthy and ready at http://localhost:443"
    echo "[INFO]    To run integration tests:"
    echo "          pytest API/tests/integration/ -m integration -v"
    echo "[INFO]    To stop containers:"
    echo "          docker compose -f $COMPOSE_FILE down"
    exit 0
  fi
  echo "[INFO]    Waiting... attempt $i/30 (sleeping 10s)"
  sleep 10
done

echo "[ERROR] API did not become healthy after 5 minutes."
echo "        Check container logs with: docker compose -f $COMPOSE_FILE logs fastapi"
exit 1
