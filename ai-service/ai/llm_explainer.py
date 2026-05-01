def explain_match(query, result):
    product = result["product"]
    score = result["score"]
    title = product.get("title", "This item")
    material = product.get("material", "its material")
    category = product.get("category", "category")

    return (
        f"{title} matches your search because it is a {category} item made "
        f"with {material}. Similarity score: {score:.2f}."
    )


def explain_outfit(seed_product, recommendation):
    product = recommendation["product"]
    seed_title = seed_product.get("title", "your selected item")
    title = product.get("title", "this item")

    return (
        f"{title} pairs well with {seed_title} based on category, color, "
        "and material compatibility."
    )
