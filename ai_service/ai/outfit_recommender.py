COMPATIBLE_CATEGORIES = {
    "tops": ["pants", "skirts"],
    "pants": ["tops", "outerwear"],
    "skirts": ["tops", "outerwear"],
    "dresses": ["outerwear"],
    "outerwear": ["tops", "dresses", "pants", "skirts"],
}


def recommend_outfit(seed_product, products, limit=3):
    seed_category = seed_product.get("category")
    compatible = COMPATIBLE_CATEGORIES.get(seed_category, [])
    recommendations = []

    for product in products:
        if product.get("product_id") == seed_product.get("product_id"):
            continue

        score = 0
        if product.get("category") in compatible:
            score += 2
        if product.get("color") == seed_product.get("color"):
            score += 1
        if product.get("material") == seed_product.get("material"):
            score += 1

        if score > 0:
            recommendations.append({"score": score, "product": product})

    return sorted(recommendations, key=lambda item: item["score"], reverse=True)[:limit]
