import json
import os
from typing import Dict
from utils.translation.vocabulary_match import VocabularyMatch, find_exact_matches, normalize_text
class RagVocabulary:
    def __init__(self, language: str):
        self.language = language
        self.vocabulary = self.load_vocabulary()

    def load_vocabulary(self) -> Dict[str, str]:
        """Load vocabulary from the JSON file based on the specified language."""
        vocab_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vocabulary.json")
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("vocabulary", {}).get(self.language, {})
        except Exception as e:
            print(f"⚠️  Could not load vocabulary.json: {e}")
            return {}

    def get_vocabulary(self):
        return self.vocabulary

    async def query_vocabulary_semantically(
        self,
        text: str,
        n_results: int = 5,
    ) -> list[VocabularyMatch]:
        collection_id = self.get_vocabulary()
        embedding = await embed(text)

        if not collection_id or not embedding:
            return []

        tenant, database = await get_v2_context()

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                (
                    f"{_CHROMA_BASE}/api/v2/tenants/{tenant}"
                    f"/databases/{database}"
                    f"/collections/{collection_id}/query"
                ),
                json={
                    "query_embeddings": [embedding],
                    "n_results": n_results,
                    "include": ["metadatas", "distances"],
                },
            )
            response.raise_for_status()
            data = response.json()

        metadatas = data.get("metadatas", [[]])[0]
        distances = data.get("distances", [[]])[0]

        results: list[VocabularyMatch] = []

        for metadata, distance in zip(metadatas, distances):
            similarity = 1.0 - float(distance)

            # Starting value only; calibrate with real articles.
            if similarity < 0.78:
                continue

            results.append(
                VocabularyMatch(
                    source=metadata["source"],
                    target=metadata["target"],
                    score=similarity,
                    match_type="semantic",
                )
            )

        return results

    async def retrieve_relevant_vocabulary(
    text: str,
    target_language: str,
    max_terms: int = 15,
) -> list[VocabularyMatch]:
    exact = find_exact_matches(
        text=text,
        target_language=target_language,
        max_terms=max_terms,
    )

    semantic = await query_vocabulary_semantically(
        text=text,
        target_language=target_language,
        n_results=5,
    )

    # Exact matches always win.
    selected = {
        normalize_text(match.source): match
        for match in exact
    }

    remaining_capacity = max_terms - len(selected)

    for match in sorted(semantic, key=lambda item: item.score, reverse=True):
        key = normalize_text(match.source)

        if key in selected:
            continue

        if remaining_capacity <= 0:
            break

        selected[key] = match
        remaining_capacity -= 1

    return list(selected.values())