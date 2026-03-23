# Isolated API Container Testing Instructions

This guide helps you run only the API (and its dependencies) in a container for real integration testing, using Postman or Python.

---

## 1. Prerequisites

- Docker and Docker Compose installed
- `.env` file present at `API/app/.env` (copy from `.env.production` if needed)

## 2. Start API and Dependencies

```sh
chmod +x run-api-only.sh
./run-api-only.sh
```

- This starts only the API, `ollama`, and `chroma` containers.
- The API will be available at: `https://localhost:443`

## 3. Test the API

### a) Using Postman

- Import the provided `postman_collection.json` file.
- Use the `Translate` request in the collection, or create a new POST request:
  - **URL:** `https://localhost:443/api/translate`
  - **Headers:**
    - `Authorization: Bearer devtoken` (if required)
    - `Content-Type: application/json`
  - **Body (JSON):**
    ```json
    {
      "title": "Hello",
      "body": "This is a test.",
      "section": "Intro",
      "target_language": "Spanish",
      "model": "llama2"
    }
    ```
- Accept self-signed certificate warnings if prompted.

### b) Using Python

```python
import requests

url = "https://localhost:443/api/translate"
payload = {
    "title": "Hello",
    "body": "This is a test.",
    "section": "Intro",
    "target_language": "Spanish",
    "model": "llama2"
}
headers = {
    "Authorization": "Bearer devtoken",
    "Content-Type": "application/json"
}

response = requests.post(url, json=payload, headers=headers, verify=False)
print(response.status_code)
print(response.json())
```

## 4. Stopping and Cleaning Up

```sh
docker compose down
```

## 5. Troubleshooting

- If the API is not healthy, check logs:
  - `docker compose logs api`
  - `docker compose logs ollama`
  - `docker compose logs chroma`
- Ensure `.env` is correct and ports are not in use.

---

## Files Provided

- `run-api-only.sh` — Script to start only the API and dependencies
- `postman_collection.json` — Sample Postman collection (import into Postman)
