from collections import Counter


def recommend_based_on_interests(products, searches=None, interactions=None, limit=8):
    searches = searches or []
    interactions = interactions or []
    interacted_ids = {
        str(item.get("product_id"))
        for item in interactions
        if item.get("product_id") is not None
    }
    category_weights = Counter(item.get("category") for item in interactions if item.get("category"))
    brand_weights = Counter(item.get("brand") for item in interactions if item.get("brand"))
    search_terms = [str(term).lower() for term in searches if term]
    scored = []

    for product in products:
        product_id = str(product.get("product_id") or product.get("id"))
        if product_id in interacted_ids:
            continue

        score = 0
        score += category_weights.get(product.get("category"), 0) * 3
        score += brand_weights.get(product.get("brand"), 0)

        searchable = " ".join(
            str(product.get(field) or "")
            for field in ["title", "description", "category", "subcategory", "brand", "material", "color"]
        ).lower()
        score += sum(2 for term in search_terms if term in searchable)

        if score > 0:
            scored.append({"score": score, "product": product})

    if not scored:
        scored = [{"score": 0, "product": product} for product in products]

    return sorted(scored, key=lambda item: item["score"], reverse=True)[:limit]
