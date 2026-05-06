from services.similarity_service import cosine_similarity


COMPATIBLE_CATEGORIES = {
    "Shirts": ["Jeans", "Handbags"],
    "Tshirts": ["Jeans", "Handbags"],
    "Jeans": ["Shirts", "Tshirts", "Handbags"],
    "Dresses": ["Handbags"],
    "Handbags": ["Dresses", "Shirts", "Tshirts", "Jeans"],
    "tops": ["pants", "skirts", "outerwear"],
    "pants": ["tops", "outerwear"],
    "skirts": ["tops", "outerwear"],
    "dresses": ["outerwear", "bags"],
    "outerwear": ["tops", "dresses", "pants", "skirts"],
    "bags": ["dresses", "tops", "pants", "skirts"],
}

COLOR_RULES = {
    "White": ["Blue", "Black", "Grey", "Navy Blue", "Beige"],
    "Black": ["White", "Grey", "Red", "Blue", "Beige"],
    "Blue": ["White", "Black", "Grey", "Navy Blue"],
    "Navy Blue": ["White", "Grey", "Blue"],
    "Grey": ["White", "Black", "Blue", "Navy Blue"],
    "Beige": ["White", "Brown", "Black", "Blue"],
    "Brown": ["Beige", "White", "Black"],
    "Red": ["Black", "White", "Grey"],
    "Green": ["White", "Black", "Brown"],
    "Pink": ["White", "Grey", "Beige"],
    "Purple": ["White", "Black", "Grey"],
}


def color_score(base_color, candidate_color):
    base_color = str(base_color or "").strip()
    candidate_color = str(candidate_color or "").strip()

    if base_color.lower() == candidate_color.lower():
        return 0.8

    if candidate_color.title() in COLOR_RULES.get(base_color.title(), []):
        return 1.0

    return 0.4


def recommend_outfit(base_product, products, embeddings=None, metadata=None, top_k_per_category=1):
    base_id = str(base_product.get("product_id") or base_product.get("id"))
    base_category = base_product.get("category")
    base_color = base_product.get("color")
    base_usage = base_product.get("usage")
    target_categories = COMPATIBLE_CATEGORIES.get(base_category, [])
    embedding_by_id = {}

    if embeddings is not None and metadata is not None:
        for index, product in enumerate(metadata):
            product_id = str(product.get("product_id") or product.get("id"))
            embedding_by_id[product_id] = embeddings[index]

    base_embedding = embedding_by_id.get(base_id)
    outfit_results = []

    for target_category in target_categories:
        candidates = [
            product for product in products
            if product.get("category") == target_category
            and str(product.get("product_id") or product.get("id")) != base_id
        ]
        scored_candidates = []

        for candidate in candidates:
            candidate_id = str(candidate.get("product_id") or candidate.get("id"))
            candidate_embedding = embedding_by_id.get(candidate_id)
            visual_similarity = 0.0

            if base_embedding is not None and candidate_embedding is not None:
                visual_similarity = cosine_similarity(base_embedding, candidate_embedding)

            usage_score = 1.0 if base_usage and base_usage == candidate.get("usage") else 0.6
            final_score = (
                0.4 * color_score(base_color, candidate.get("color"))
                + 0.3 * usage_score
                + 0.3 * visual_similarity
            )
            scored_candidates.append(
                {
                    "score": final_score,
                    "visual_similarity": visual_similarity,
                    "product": candidate,
                }
            )

        scored_candidates.sort(key=lambda item: item["score"], reverse=True)
        outfit_results.extend(scored_candidates[:top_k_per_category])

    return outfit_results
