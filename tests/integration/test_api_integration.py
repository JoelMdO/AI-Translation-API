"""
Integration tests for the AI Translation & Summary API.

These tests run against a LIVE API container with DEV_MODE=true.
They do NOT mock any dependencies — Ollama and ChromaDB must be running.

Tests validate HTTP status codes and response schemas only.
LLM output quality is NOT asserted (results vary per model/run).

Prerequisites:
  - API running at https://localhost:443 (or API_BASE_URL env var)
  - DEV_MODE=true set in API environment
  - Ollama running with 'tinyllama' model available
  - ChromaDB running (RAG degrades gracefully if empty)

Run locally:
  ./run-api-only.sh
  pytest API/tests/integration/ -m integration -v

Run in CI (handled automatically by GitHub Actions):
  docker compose -f docker-compose.ci.yml up -d --build
  pytest API/tests/integration/ -m integration -v
"""

import os
import pytest
import httpx

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:443")
AUTH = {"Authorization": "Bearer devtoken"}

TRANSLATE_PAYLOAD = {
    "title": "Hello World",
    "body": "Slot and PPR (Prior Permission Required) are crucial concepts when you are planning a flight or managing air traffic and airport resources. But, What are those?. Slot (Airport slot). It's a permission assigned by a slot coordinator to an aircraft operator (commercial airline or private jet company) where an available \\\"spot\\\" is given to an aircraft to depart or land at a specific time and date, the objective is to manage capacity and congestion at busiest airports. Not all the airports are slots coordinated, only the ones where the demand of flights exceeds the available capacity. These airports are designated as Level 3 (Coordinated) and you can find a complete list of them on the IATA's web portal: How are slots normally allocated? By following the Worldwide Airport Slot Guidelines (WASG), published by the International Air Transport Association (IATA), Airports Council International (ACI), and other industry bodies. Where every calendar year is divided into two seasons, Summer and Winter. Months before each season begins; a neutral and independent slot coordinator allocates slots based on declared airport capacity, which goes on a 80/20 rule, where the 80% is assigned to commercial Airlines based on their \\\"historic precedence\\\" and current schedules, and the 20% remaining, private operators can apply for it. Additionally there is a rule called: \\\"Use-it-or-Lose-it\\\" with the purpose to prevent operators from holding slots without using them. PPR (Prior Permission Required). Is a requirement for specific types of operations or at airfields with unique constraints such as: Limited parking space. Specific security or operational requirements. Flights outside of normal operating hours. Specialized operations (e.g. training flights, cargo, special events). The PPR is issued by the Airport Operator, the designated Ground Handling Agent or FBO, or the local authority depending on the case, for example during the American Football Championship (SuperBowl) FBOs trend to issue PPRs depending on its ramp parking capacity. The Achilles' Heel: Challenges and Solutions. Despite the established systems, managing airport slots and PPRs remains a significant pain point for many in the aviation industry, from major airlines to private operators.",
    "section": "Technology",
    "target_language": "Spanish",
    "model": "tinyllama",
}

TRANSLATE_HTML_PAYLOAD = {
    "title": "<b>Hello World</b>",
    "body": "<div><p>Slot and PPR (Prior Permission Required) are crucial concepts when you are planning a flight or managing air traffic and airport resources.</p><br /><img src=\\\"https://res.cloudinary.com/dc2rrmx5r/image/upload/v1763129958/%22DeCav%22/10-11-25-Article-Slots-DeCAV.webp.webp\\\" alt=\\\"10-11-25-Article-Slots-DeCAV.webp\\\" /><p>10-11-25-Article-Slots-DeCAV.webp</p><br /><p>But, What are those?</p><blockquote>Slot (Airport slot)</blockquote><p>It's a permission assigned by a slot coordinator to an aircraft operator (commercial airline or private jet company) where an available \\\"spot\\\" is given to an aircraft to depart or land at a specific time and date, the objective is to manage capacity and congestion at busiest airports.</p><br /><p>Not all the airports are slots coordinated, only the ones where the demand of flights exceeds the available capacity. These airports are designated as Level 3 (Coordinated) and you can find a complete list of them on the IATA's web portal:</p><br /><img src=\\\"https://res.cloudinary.com/dc2rrmx5r/image/upload/v1763129958/%22DeCav%22/10-11-25-IATA%20Airport%20Levels%20of%20Coordination.webp.webp\\\" alt=\\\"10-11-25-IATA Airport Levels of Coordination.webp\\\" /><p>10-11-25-IATA Airport Levels of Coordination.webp</p><br /><br /><a href=\\\"https://www.iata.org/contentassets/4ede2aabfcc14a55919e468054d714fe/wasg-annex-12.7.xlsx\\\"><em>IATA Coordinated Airport List</em></a><br /><p><strong><em>How are slots normally allocated?</em></strong></p><p>By following the Worldwide Airport Slot Guidelines (WASG), published by the International Air Transport Association (IATA), Airports Council International (ACI), and other industry bodies. Where every calendar year is divided into two seasons, Summer and Winter. Months before each season begins; a neutral and independent slot coordinator allocates slots based on declared airport capacity, which goes on a 80/20 rule, where the 80% is assigned to commercial Airlines based on their \\\"historic precedence\\\" and current schedules, and the 20% remaining, private operators can apply for it. Additionally there is a rule called: \\\"Use-it-or-Lose-it\\\" with the purpose to prevent operators from holding slots without using them.</p><br /><blockquote>PPR (Prior Permission Required).</blockquote><br /><p>Is a requirement for specific types of operations or at airfields with unique constraints such as:</p><br /><ol><li>Limited parking space.</li><li>Specific security or operational requirements.</li><li>Flights outside of normal operating hours.</li><li>Specialized operations (e.g. training flights, cargo, special events).</li></ol><br /><p>The PPR is issued by the Airport Operator, the designated Ground Handling Agent or FBO, or the local authority depending on the case, for example during the American Football Championship (SuperBowl) FBOs trend to issue PPRs depending on its ramp parking capacity.</p><hr /><h2>The Achilles' Heel: Challenges and Solutions.</h2><br /><p>Despite the established systems, managing airport slots and PPRs remains a significant pain point for many in the aviation industry, from major airlines to private operators.</p>}",
    "section": "<strong>Technology</strong>",
    "target_language": "Spanish",
    "model": "tinyllama",
}

SUMMARY_PAYLOAD = {
    "title": "Hello World",
    "body": "Slot and PPR (Prior Permission Required) are crucial concepts when you are planning a flight or managing air traffic and airport resources. But, What are those?. Slot (Airport slot). It's a permission assigned by a slot coordinator to an aircraft operator (commercial airline or private jet company) where an available \\\"spot\\\" is given to an aircraft to depart or land at a specific time and date, the objective is to manage capacity and congestion at busiest airports. Not all the airports are slots coordinated, only the ones where the demand of flights exceeds the available capacity. These airports are designated as Level 3 (Coordinated) and you can find a complete list of them on the IATA's web portal: How are slots normally allocated? By following the Worldwide Airport Slot Guidelines (WASG), published by the International Air Transport Association (IATA), Airports Council International (ACI), and other industry bodies. Where every calendar year is divided into two seasons, Summer and Winter. Months before each season begins; a neutral and independent slot coordinator allocates slots based on declared airport capacity, which goes on a 80/20 rule, where the 80% is assigned to commercial Airlines based on their \\\"historic precedence\\\" and current schedules, and the 20% remaining, private operators can apply for it. Additionally there is a rule called: \\\"Use-it-or-Lose-it\\\" with the purpose to prevent operators from holding slots without using them. PPR (Prior Permission Required). Is a requirement for specific types of operations or at airfields with unique constraints such as: Limited parking space. Specific security or operational requirements. Flights outside of normal operating hours. Specialized operations (e.g. training flights, cargo, special events). The PPR is issued by the Airport Operator, the designated Ground Handling Agent or FBO, or the local authority depending on the case, for example during the American Football Championship (SuperBowl) FBOs trend to issue PPRs depending on its ramp parking capacity. The Achilles' Heel: Challenges and Solutions. Despite the established systems, managing airport slots and PPRs remains a significant pain point for many in the aviation industry, from major airlines to private operators.",
    "language": "en",
}


# ---------------------------------------------------------------------------
# Module-scoped HTTP client (reused across all tests for speed)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    """Synchronous httpx client pointed at the live API container."""
    with httpx.Client(base_url=BASE_URL, verify=False, timeout=120.0) as c:
        yield c


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_health_endpoint_returns_200(client): #type: ignore
    """GET /health is public and must return 200 with required fields."""
    resp = client.get("/health") #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert "status" in data
    assert "ollama_connected" in data
    assert "api_version" in data


@pytest.mark.integration
def test_health_status_is_string(client): #type: ignore
    """GET /health status field must be a non-empty string."""
    resp = client.get("/health") #type: ignore
    assert resp.status_code == 200 #type: ignore
    assert isinstance(resp.json().get("status"), str) #type: ignore


# ---------------------------------------------------------------------------
# RAG status
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_rag_status_returns_200(client): #type: ignore
    """GET /api/rag/status is public and must return 200 with chroma_available field."""
    resp = client.get("/api/rag/status") #type: ignore
    assert resp.status_code == 200 #type: ignore
    assert "chroma_available" in resp.json() #type: ignore


# ---------------------------------------------------------------------------
# POST /api/translate — auth enforcement
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_translate_403_without_auth(client): #type: ignore
    """POST /api/translate without Authorization header returns 403."""
    resp = client.post("/api/translate", json=TRANSLATE_PAYLOAD) #type: ignore
    assert resp.status_code == 403 #type: ignore


@pytest.mark.integration
def test_translate_422_empty_payload(client): #type: ignore
    """POST /api/translate with empty body returns 422 Unprocessable Entity."""
    resp = client.post("/api/translate", json={}, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.integration
def test_translate_omit_target_language_uses_default(client): #type: ignore
    """POST /api/translate without target_language succeeds — field has a default value."""
    payload = {k: v for k, v in TRANSLATE_PAYLOAD.items() if k != "target_language"}
    resp = client.post("/api/translate", json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore


@pytest.mark.integration
def test_translate_422_missing_body(client): #type: ignore
    """POST /api/translate without body returns 422."""
    payload = {k: v for k, v in TRANSLATE_PAYLOAD.items() if k != "body"}
    resp = client.post("/api/translate", json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


# ---------------------------------------------------------------------------
# POST /api/translate — happy path (plain text)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_translate_plain_text_returns_200(client): #type: ignore
    """POST /api/translate with valid plain-text payload returns 200."""
    resp = client.post("/api/translate", json=TRANSLATE_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore


@pytest.mark.integration
def test_translate_plain_text_response_shape(client): #type: ignore
    """POST /api/translate response must contain success, model_used, and translated_text."""
    resp = client.post("/api/translate", json=TRANSLATE_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert "success" in data
    assert "model_used" in data
    assert "translated_text" in data
    assert isinstance(data["model_used"], str) and len(data["model_used"]) > 0 #type: ignore


@pytest.mark.integration
def test_translate_plain_text_translated_text_keys(client): #type: ignore
    """POST /api/translate translated_text must contain title, body, and section."""
    resp = client.post("/api/translate", json=TRANSLATE_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    translated = resp.json().get("translated_text", {}) #type: ignore
    for key in ("title", "body", "section"):
        assert key in translated, f"Missing key '{key}' in translated_text"


# ---------------------------------------------------------------------------
# POST /api/translate — happy path (HTML body)
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_translate_html_body_returns_200(client): #type: ignore
    """POST /api/translate with HTML body returns 200."""
    resp = client.post("/api/translate", json=TRANSLATE_HTML_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore


@pytest.mark.integration
def test_translate_html_body_response_shape(client): #type: ignore
    """POST /api/translate with HTML body returns correct response shape."""
    resp = client.post("/api/translate", json=TRANSLATE_HTML_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert "success" in data
    assert "translated_text" in data
    for key in ("title", "body", "section"):
        assert key in data["translated_text"]


# ---------------------------------------------------------------------------
# POST /api/summary — auth enforcement
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_summary_403_without_auth(client): #type: ignore
    """POST /api/summary without Authorization header returns 403."""
    resp = client.post("/api/summary", json=SUMMARY_PAYLOAD) #type: ignore
    assert resp.status_code == 403 #type: ignore


@pytest.mark.integration
def test_summary_422_empty_payload(client): #type: ignore
    """POST /api/summary with empty body returns 422 Unprocessable Entity."""
    resp = client.post("/api/summary", json={}, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.integration
def test_summary_422_missing_body(client): #type: ignore
    """POST /api/summary without body field returns 422."""
    resp = client.post("/api/summary", json={"title": "Test", "language": "en"}, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.integration
def test_summary_422_missing_title(client): #type: ignore
    """POST /api/summary without title field returns 422."""
    resp = client.post("/api/summary", json={"body": "Long body", "language": "en"}, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


# ---------------------------------------------------------------------------
# POST /api/summary — happy path
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_summary_returns_200(client): #type: ignore
    """POST /api/summary with valid payload returns 200."""
    resp = client.post("/api/summary", json=SUMMARY_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore


@pytest.mark.integration
def test_summary_response_shape(client): #type: ignore
    """POST /api/summary response must contain success and article fields."""
    resp = client.post("/api/summary", json=SUMMARY_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    assert "success" in data
    assert "article" in data


@pytest.mark.integration
def test_summary_article_is_non_empty_on_success(client): #type: ignore
    """On success, POST /api/summary article must be a non-empty string."""
    resp = client.post("/api/summary", json=SUMMARY_PAYLOAD, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    if data.get("success"): #type: ignore
        assert isinstance(data["article"], str) #type: ignore
        assert len(data["article"].strip()) > 0 #type: ignore


@pytest.mark.integration
def test_summary_html_body_returns_200(client): #type: ignore
    """POST /api/summary with HTML body is accepted and returns 200."""
    payload = {**SUMMARY_PAYLOAD, "body": "<div><p>Slot and PPR (Prior Permission Required) are crucial concepts when you are planning a flight or managing air traffic and airport resources.</p><br /><img src=\\\"https://res.cloudinary.com/dc2rrmx5r/image/upload/v1763129958/%22DeCav%22/10-11-25-Article-Slots-DeCAV.webp.webp\\\" alt=\\\"10-11-25-Article-Slots-DeCAV.webp\\\" /><p>10-11-25-Article-Slots-DeCAV.webp</p><br /><p>But, What are those?</p><blockquote>Slot (Airport slot)</blockquote><p>It's a permission assigned by a slot coordinator to an aircraft operator (commercial airline or private jet company) where an available \\\"spot\\\" is given to an aircraft to depart or land at a specific time and date, the objective is to manage capacity and congestion at busiest airports.</p><br /><p>Not all the airports are slots coordinated, only the ones where the demand of flights exceeds the available capacity. These airports are designated as Level 3 (Coordinated) and you can find a complete list of them on the IATA's web portal:</p><br /><img src=\\\"https://res.cloudinary.com/dc2rrmx5r/image/upload/v1763129958/%22DeCav%22/10-11-25-IATA%20Airport%20Levels%20of%20Coordination.webp.webp\\\" alt=\\\"10-11-25-IATA Airport Levels of Coordination.webp\\\" /><p>10-11-25-IATA Airport Levels of Coordination.webp</p><br /><br /><a href=\\\"https://www.iata.org/contentassets/4ede2aabfcc14a55919e468054d714fe/wasg-annex-12.7.xlsx\\\"><em>IATA Coordinated Airport List</em></a><br /><p><strong><em>How are slots normally allocated?</em></strong></p><p>By following the Worldwide Airport Slot Guidelines (WASG), published by the International Air Transport Association (IATA), Airports Council International (ACI), and other industry bodies. Where every calendar year is divided into two seasons, Summer and Winter. Months before each season begins; a neutral and independent slot coordinator allocates slots based on declared airport capacity, which goes on a 80/20 rule, where the 80% is assigned to commercial Airlines based on their \\\"historic precedence\\\" and current schedules, and the 20% remaining, private operators can apply for it. Additionally there is a rule called: \\\"Use-it-or-Lose-it\\\" with the purpose to prevent operators from holding slots without using them.</p><br /><blockquote>PPR (Prior Permission Required).</blockquote><br /><p>Is a requirement for specific types of operations or at airfields with unique constraints such as:</p><br /><ol><li>Limited parking space.</li><li>Specific security or operational requirements.</li><li>Flights outside of normal operating hours.</li><li>Specialized operations (e.g. training flights, cargo, special events).</li></ol><br /><p>The PPR is issued by the Airport Operator, the designated Ground Handling Agent or FBO, or the local authority depending on the case, for example during the American Football Championship (SuperBowl) FBOs trend to issue PPRs depending on its ramp parking capacity.</p><hr /><h2>The Achilles' Heel: Challenges and Solutions.</h2><br /><p>Despite the established systems, managing airport slots and PPRs remains a significant pain point for many in the aviation industry, from major airlines to private operators.</p>}",}
    resp = client.post("/api/summary", json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    assert "article" in resp.json() #type: ignore


@pytest.mark.integration
def test_summary_spanish_language_returns_200(client): #type: ignore
    """POST /api/summary with language=es returns 200."""
    payload = {**SUMMARY_PAYLOAD, "language": "es"}
    resp = client.post("/api/summary", json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    assert "success" in resp.json() #type: ignore


# ---------------------------------------------------------------------------
# Unhappy paths — wrong HTTP method / unknown routes
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_nonexistent_endpoint_returns_404(client): #type: ignore
    """GET /api/nonexistent returns 404."""
    resp = client.get("/api/nonexistent") #type: ignore
    assert resp.status_code == 404 #type: ignore


@pytest.mark.integration
def test_translate_wrong_method_get_returns_405(client): #type: ignore
    """GET /api/translate (wrong method) returns 405 Method Not Allowed."""
    resp = client.get("/api/translate", headers=AUTH) #type: ignore
    assert resp.status_code == 405 #type: ignore


@pytest.mark.integration
def test_summary_wrong_method_get_returns_405(client): #type: ignore
    """GET /api/summary (wrong method) returns 405 Method Not Allowed."""
    resp = client.get("/api/summary", headers=AUTH) #type: ignore
    assert resp.status_code == 405 #type: ignore


# ---------------------------------------------------------------------------
# Unhappy paths — malformed / invalid auth
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_translate_invalid_auth_scheme_returns_403(client): #type: ignore
    """POST /api/translate with Basic auth scheme instead of Bearer returns 403."""
    resp = client.post( #type: ignore
        "/api/translate",
        json=TRANSLATE_PAYLOAD,
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    ) #type: ignore
    assert resp.status_code == 403 #type: ignore


@pytest.mark.integration
def test_summary_invalid_auth_scheme_returns_403(client): #type: ignore
    """POST /api/summary with Basic auth scheme instead of Bearer returns 403."""
    resp = client.post( #type: ignore
        "/api/summary",
        json=SUMMARY_PAYLOAD,
        headers={"Authorization": "Basic dXNlcjpwYXNz"},
    ) #type: ignore
    assert resp.status_code == 403 #type: ignore


# ---------------------------------------------------------------------------
# Unhappy paths — translate: individual required fields missing
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_translate_422_missing_title(client): #type: ignore
    """POST /api/translate without title returns 422."""
    payload = {k: v for k, v in TRANSLATE_PAYLOAD.items() if k != "title"}
    resp = client.post("/api/translate", json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


@pytest.mark.integration
def test_translate_422_missing_section(client): #type: ignore
    """POST /api/translate without section returns 422."""
    payload = {k: v for k, v in TRANSLATE_PAYLOAD.items() if k != "section"}
    resp = client.post("/api/translate", json=payload, headers=AUTH) #type: ignore
    assert resp.status_code == 422 #type: ignore


# ---------------------------------------------------------------------------
# Unhappy paths — XSS / injection payloads must not crash the API
# ---------------------------------------------------------------------------

@pytest.mark.integration
def test_translate_xss_payload_sanitized_and_processed(client): #type: ignore
    """
    XSS injection in translate fields must be sanitized by the service BEFORE
    reaching the LLM. Two things are verified:
      1. The API returns 200 with success=True — proving the sanitized content
         was processed cleanly (not rejected or errored out).
      2. The response output contains no raw injection tags — proving the
         sanitizer stripped malicious content from what the LLM saw.
    """
    xss_payload = {
        **TRANSLATE_PAYLOAD,
        "title": '<script>alert("xss")</script>Hello',
        "body": '<img src=x onerror=alert(1)> Some content about airport slots.',
        "section": '<a href="javascript:evil()">Click</a>',
    }
    resp = client.post("/api/translate", json=xss_payload, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    # success=True proves sanitization allowed clean processing to continue (not reject)
    assert data.get("success") is True, ( #type: ignore
        "Sanitizer should clean the input and allow translation to proceed, not fail"
    )
    # Output must not echo back any injected tags
    translated = data.get("translated_text", {}) #type: ignore
    for field in translated.values(): #type: ignore
        assert "<script>" not in str(field), "Raw <script> tag leaked into translated output" #type: ignore
        assert "onerror" not in str(field).lower(), "onerror handler leaked into translated output" #type: ignore
        assert "javascript:" not in str(field).lower(), "javascript: URI leaked into translated output" #type: ignore


@pytest.mark.integration
def test_summary_xss_payload_sanitized_and_processed(client): #type: ignore
    """
    XSS injection in summary fields must be sanitized by the service BEFORE
    reaching the LLM. Two things are verified:
      1. The API returns 200 with success=True — proving the sanitized content
         was processed cleanly (not rejected or errored out).
      2. The article output contains no raw injection tags — proving the
         sanitizer stripped malicious content from what the LLM saw.
    """
    xss_payload = {
        **SUMMARY_PAYLOAD,
        "title": '<script>alert("xss")</script>Airport Slots',
        "body": '<img src=x onerror=alert(1)><p>Some safe content about aviation.</p>',
    }
    resp = client.post("/api/summary", json=xss_payload, headers=AUTH) #type: ignore
    assert resp.status_code == 200 #type: ignore
    data = resp.json() #type: ignore
    # success=True proves sanitization allowed clean processing to continue (not reject)
    assert data.get("success") is True, ( #type: ignore
        "Sanitizer should clean the input and allow summarization to proceed, not fail"
    )
    # Output must not echo back any injected tags
    article = data.get("article", "") #type: ignore
    assert "<script>" not in str(article), "Raw <script> tag leaked into article output" #type: ignore
    assert "onerror" not in str(article).lower(), "onerror handler leaked into article output" #type: ignore
    assert "javascript:" not in str(article).lower(), "javascript: URI leaked into article output" #type: ignore

