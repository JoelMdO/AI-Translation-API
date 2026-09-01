const BASE_URL = process.env.API_BASE_URL || "http://localhost:8444";

jest.setTimeout(180000);

async function getJson(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, options);
  const text = await response.text();
  let body;
  try {
    body = JSON.parse(text);
  } catch {
    body = text;
  }
  return { response, body };
}

test("AI Translation API health is live", async () => {
  const { response, body } = await getJson("/health");

  expect(response.status).toBe(200);
  expect(body).toEqual(expect.objectContaining({
    status: expect.any(String),
    ollama_connected: true,
    api_version: expect.any(String),
  }));
});

test("AI Translation API translates through the live Ollama container", async () => {
  const { response, body } = await getJson("/api/translate", {
    method: "POST",
    headers: {
      Authorization: "Bearer standalone-jest-token",
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      title: "Airport slots",
      body: "Airport slots help coordinate demand and capacity.",
      section: "Technology",
      target_language: "Spanish",
      model: "aya",
    }),
  });

  expect(response.status).toBe(200);
  expect(body.status).toBe(200);
  expect(body.model_used).toEqual(expect.any(String));
  expect(body.translated_text).toEqual(expect.objectContaining({
    title: expect.any(String),
    body: expect.any(String),
    section: expect.any(String),
  }));
});
