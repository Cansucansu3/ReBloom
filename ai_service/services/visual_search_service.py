from functools import lru_cache

import numpy as np

from services.compatibility_service import (
    get_clip_embedding,
    load_clip_artifact,
    load_image_from_value,
)


CATEGORY_PROMPTS = {
    "tops": ["a shirt", "a t-shirt", "a blouse", "a top", "a sweatshirt"],
    "pants": ["a pair of long pants", "jeans", "trousers", "full length pants"],
    "shorts": ["a pair of shorts", "short pants with two leg openings", "athletic shorts"],
    "skirts": [
        "a skirt",
        "a denim mini skirt",
        "a short skirt",
        "a women's denim skirt",
        "a skirt without separated leg openings",
    ],
    "dresses": ["a dress", "a gown"],
    "shoes": ["a pair of shoes", "sandals", "heels", "sneakers"],
    "bags": ["a handbag", "a bag", "a backpack"],
}

CATEGORY_ALIASES = {
    "top": "tops",
    "shirt": "tops",
    "shirts": "tops",
    "tshirt": "tops",
    "tshirts": "tops",
    "t-shirt": "tops",
    "t-shirts": "tops",
    "sweater": "tops",
    "sweatshirt": "tops",
    "jacket": "tops",
    "jean": "pants",
    "jeans": "pants",
    "trouser": "pants",
    "trousers": "pants",
    "short": "shorts",
    "shorts": "shorts",
    "track pants": "pants",
    "skirt": "skirts",
    "skirts": "skirts",
    "dress": "dresses",
    "dresses": "dresses",
    "shoe": "shoes",
    "shoes": "shoes",
    "heels": "shoes",
    "flats": "shoes",
    "sandals": "shoes",
    "flip flops": "shoes",
    "bag": "bags",
    "bags": "bags",
    "handbag": "bags",
    "handbags": "bags",
    "backpack": "bags",
}

COMPLEMENTARY_CATEGORIES = {
    "tops": {"pants", "skirts"},
    "pants": {"tops"},
    "shorts": {"tops"},
    "skirts": {"tops"},
    "dresses": {"bags", "shoes"},
    "shoes": {"pants", "skirts", "dresses"},
    "bags": {"dresses", "tops"},
}

MAX_VISUAL_CANDIDATES = 60
CATEGORY_SCORE_MARGIN = 0.03
CONFUSABLE_CATEGORY_MARGIN = 0.06
CONFUSABLE_CATEGORY_GROUPS = [
    {"pants", "shorts", "skirts"},
]


def cosine_similarity(left, right):
    return float(np.dot(left, right))


@lru_cache(maxsize=512)
def get_product_embedding(product_id, image_url):
    image = load_image_from_value(image_url)
    if image is None:
        return None

    return get_clip_embedding(image)


def normalize_category(value):
    normalized = str(value or "").strip().lower()
    return CATEGORY_ALIASES.get(normalized, normalized)


def category_from_text(value):
    text = str(value or "").strip().lower()
    if not text:
        return None

    aliases = sorted(CATEGORY_ALIASES.items(), key=lambda item: len(item[0]), reverse=True)
    for alias, category in aliases:
        if alias in text:
            return category

    return None


def infer_candidate_category(candidate):
    values = [
        candidate.get("subcategory"),
        candidate.get("title"),
        candidate.get("category"),
    ]

    for value in values:
        category = category_from_text(value)
        if category:
            return category

    return normalize_category(candidate.get("category"))


def infer_gender(text):
    text = str(text or "").lower()
    if any(term in text for term in ["women", "woman", "girl", "girls", "female"]):
        return "women"
    if any(term in text for term in ["men", "man", "boys", "boy", "male"]):
        return "men"
    return None


@lru_cache(maxsize=1)
def get_category_text_embeddings():
    import clip
    import torch

    model, _, device = load_clip_artifact()
    labels = []
    category_embeddings = []

    for label, prompts in CATEGORY_PROMPTS.items():
        tokens = clip.tokenize(prompts).to(device)
        with torch.no_grad():
            text_features = model.encode_text(tokens)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)

        category_embedding = text_features.mean(dim=0, keepdim=True)
        category_embedding = category_embedding / category_embedding.norm(dim=-1, keepdim=True)
        labels.append(label)
        category_embeddings.append(category_embedding.cpu().numpy()[0])

    return labels, np.array(category_embeddings)


def categories_are_confusable(left, right):
    return any(left in group and right in group for group in CONFUSABLE_CATEGORY_GROUPS)


def pick_query_categories(labels, scores, best_index):
    best_category = labels[best_index]
    best_score = float(scores[best_index])
    ranked = sorted(
        ((labels[index], float(score)) for index, score in enumerate(scores)),
        key=lambda item: item[1],
        reverse=True,
    )
    selected = [best_category]

    for category, score in ranked[1:]:
        if score >= best_score - CATEGORY_SCORE_MARGIN:
            selected.append(category)
        elif (
            categories_are_confusable(best_category, category)
            and score >= best_score - CONFUSABLE_CATEGORY_MARGIN
        ):
            selected.append(category)

        if len(selected) >= 3:
            break

    return selected, ranked


def predict_query_category(query_embeddings):
    labels, text_embeddings = get_category_text_embeddings()
    mean_embedding = np.mean([embedding for _, embedding in query_embeddings], axis=0)
    mean_embedding = mean_embedding / np.linalg.norm(mean_embedding)
    scores = text_embeddings @ mean_embedding
    best_index = int(np.argmax(scores))
    query_categories, ranked_scores = pick_query_categories(labels, scores, best_index)
    return labels[best_index], float(scores[best_index]), query_categories, ranked_scores


def select_visual_candidates(candidates, query_categories, limit):
    if not query_categories:
        return list(candidates)[:MAX_VISUAL_CANDIDATES]

    category_matches = []
    other_category = []
    query_category_set = set(query_categories)

    for candidate in candidates:
        if infer_candidate_category(candidate) in query_category_set:
            category_matches.append(candidate)
        else:
            other_category.append(candidate)

    if len(category_matches) >= limit:
        return category_matches[:MAX_VISUAL_CANDIDATES]

    if category_matches:
        remaining = max(0, MAX_VISUAL_CANDIDATES - len(category_matches))
        return category_matches + other_category[:remaining]

    return list(candidates)[:MAX_VISUAL_CANDIDATES]


def rerank_score(clip_score, query_categories, candidate):
    candidate_category = infer_candidate_category(candidate)
    title = candidate.get("title") or ""
    score = clip_score
    primary_category = query_categories[0] if query_categories else None

    if primary_category and candidate_category == primary_category:
        score += 0.14
    elif candidate_category in query_categories:
        score += 0.08
    elif candidate_category in COMPLEMENTARY_CATEGORIES.get(primary_category, set()):
        score -= 0.06
    elif primary_category and candidate_category:
        score -= 0.16

    query_gender = "women" if set(query_categories) & {"skirts", "dresses", "bags"} else None
    candidate_gender = infer_gender(title)
    if query_gender and candidate_gender and candidate_gender != query_gender:
        score -= 0.08

    return score


def rank_visual_candidates(query_image_value, candidates, limit=12):
    query_image = load_image_from_value(query_image_value)
    if query_image is None:
        return [], "unavailable", None

    try:
        query_embeddings = [("original", get_clip_embedding(query_image.convert("RGB")))]
    except Exception:
        query_embeddings = []

    if not query_embeddings:
        return [], "unavailable", None

    preprocessing = "+".join(variant_name for variant_name, _ in query_embeddings)
    predicted_category, category_confidence, query_categories, category_scores = (
        predict_query_category(query_embeddings)
    )
    search_candidates = select_visual_candidates(candidates, query_categories, limit)
    ranked = []

    for candidate in search_candidates:
        product_id = candidate.get("product_id")
        image_url = candidate.get("image_url")
        if product_id is None or not image_url:
            continue

        try:
            product_embedding = get_product_embedding(product_id, image_url)
            if product_embedding is None:
                continue
            score = max(
                cosine_similarity(query_embedding, product_embedding)
                for _, query_embedding in query_embeddings
            )
            final_score = rerank_score(score, query_categories, candidate)
        except Exception:
            continue

        ranked.append(
            {
                "product_id": product_id,
                "score": final_score,
                "clip_score": score,
            }
        )

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:limit], preprocessing, {
        "category": predicted_category,
        "categories": query_categories,
        "confidence": category_confidence,
        "scores": dict(category_scores[:4]),
        "candidate_count": len(search_candidates),
        "total_candidates": len(candidates),
    }
