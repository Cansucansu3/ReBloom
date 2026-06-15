SPORTS_TERMS = {
    "athletic",
    "football",
    "gym",
    "jogger",
    "running",
    "sport",
    "sports",
    "track",
    "training",
}

SPECIAL_OCCASION_TERMS = {
    "cocktail",
    "embellished",
    "evening",
    "heel",
    "heels",
    "metallic",
    "party",
    "pump",
    "pumps",
    "prom",
    "satin",
    "sequin",
    "stiletto",
    "tulle",
    "wedding",
}

FORMAL_TERMS = {
    "blazer",
    "business",
    "formal",
    "office",
    "suit",
    "tailored",
}


def infer_occasion(*values):
    text = " ".join(str(value or "").strip().lower() for value in values)

    if any(term in text for term in SPORTS_TERMS):
        return "Sports"
    if any(term in text for term in SPECIAL_OCCASION_TERMS):
        return "Special Occasion"
    if any(term in text for term in FORMAL_TERMS):
        return "Formal"
    return "Casual"


def product_occasion(product):
    stored = str(getattr(product, "occasion", "") or "").strip()
    if stored:
        return stored

    return infer_occasion(
        getattr(product, "title", None),
        getattr(product, "description", None),
        getattr(product, "category", None),
        getattr(product, "subcategory", None),
    )


def occasions_are_compatible(base_occasion, candidate_occasion):
    base = str(base_occasion or "Casual").strip().lower()
    candidate = str(candidate_occasion or "Casual").strip().lower()

    if base == candidate:
        return True

    compatible_groups = (
        {"formal", "special occasion"},
        {"casual", "sports"},
    )
    return any({base, candidate}.issubset(group) for group in compatible_groups)
