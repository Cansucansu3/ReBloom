import json
import math
from pathlib import Path

from .extract_embeddings import DEFAULT_OUTPUT_PATH, text_to_embedding


def cosine_similarity(left, right):
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (left_norm * right_norm)


def load_embeddings(path=DEFAULT_OUTPUT_PATH):
    with Path(path).open(encoding="utf-8") as file:
        return json.load(file)


def search_similar_products(query, records, limit=5):
    query_embedding = text_to_embedding(query)
    scored = []

    for record in records:
        scored.append(
            {
                "score": cosine_similarity(query_embedding, record["embedding"]),
                "product": record["metadata"],
            }
        )

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
