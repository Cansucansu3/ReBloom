from functools import lru_cache

import numpy as np

from services.compatibility_service import get_clip_embedding, load_image_from_value


def cosine_similarity(left, right):
    return float(np.dot(left, right))


@lru_cache(maxsize=512)
def get_product_embedding(product_id, image_url):
    image = load_image_from_value(image_url)
    if image is None:
        return None

    return get_clip_embedding(image)


def rank_visual_candidates(query_image_value, candidates, limit=12):
    query_image = load_image_from_value(query_image_value)
    if query_image is None:
        return []

    query_embedding = get_clip_embedding(query_image)
    ranked = []

    for candidate in candidates:
        product_id = candidate.get("product_id")
        image_url = candidate.get("image_url")
        if product_id is None or not image_url:
            continue

        try:
            product_embedding = get_product_embedding(product_id, image_url)
            if product_embedding is None:
                continue
            score = cosine_similarity(query_embedding, product_embedding)
        except Exception:
            continue

        ranked.append(
            {
                "product_id": product_id,
                "score": score,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit]
