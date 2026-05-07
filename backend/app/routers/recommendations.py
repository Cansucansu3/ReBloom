from collections import Counter
import json
import os
import urllib.error
import urllib.request

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
product_router = APIRouter(prefix="/products", tags=["Recommendations"])

OUTFIT_SLOT_SIZE = 4
OUTFIT_PREFILTER_LIMIT = 20
AI_OUTFIT_TIMEOUT = float(os.getenv("REBLOOM_AI_OUTFIT_TIMEOUT", "15"))

OUTFIT_CATEGORY_SLOTS = {
    "tops": ["pants", "skirts", "shoes", "bags"],
    "pants": ["tops", "shoes", "bags"],
    "shorts": ["tops", "shoes", "bags"],
    "skirts": ["tops", "shoes", "bags"],
    "dresses": ["shoes", "bags", "outerwear"],
    "outerwear": ["tops", "dresses", "pants", "skirts", "shoes"],
    "shoes": ["tops", "pants", "skirts", "dresses", "bags"],
    "bags": ["dresses", "tops", "pants", "skirts", "shoes"],
    "clothing": ["tops", "pants", "skirts", "shoes", "bags"],
}

OUTFIT_SLOT_TITLES = {
    "tops": "Tops",
    "pants": "Pants",
    "shorts": "Shorts",
    "skirts": "Skirts",
    "dresses": "Dresses",
    "shoes": "Shoes",
    "bags": "Bags",
    "outerwear": "Outerwear",
}

NEUTRAL_COLORS = {
    "black",
    "white",
    "grey",
    "gray",
    "beige",
    "cream",
    "brown",
    "navy",
    "silver",
    "gold",
}

COLOR_PAIRS = {
    frozenset(("blue", "white")),
    frozenset(("blue", "black")),
    frozenset(("blue", "red")),
    frozenset(("blue", "beige")),
    frozenset(("blue", "grey")),
    frozenset(("navy", "white")),
    frozenset(("navy", "beige")),
    frozenset(("black", "white")),
    frozenset(("black", "red")),
    frozenset(("green", "white")),
    frozenset(("green", "brown")),
    frozenset(("pink", "white")),
    frozenset(("purple", "white")),
}


def product_to_dict(product):
    return {
        "product_id": product.product_id,
        "seller_id": product.seller_id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "subcategory": product.subcategory,
        "brand": product.brand,
        "color": product.color,
        "size": product.size,
        "condition": product.condition,
        "material": product.material,
        "weight_kg": product.weight_kg,
        "water_saved_liters": product.water_saved_liters,
        "price": product.price,
        "image_url": product.image_url,
        "is_second_hand": product.is_second_hand,
        "created_at": product.created_at,
    }


def score_product_similarity(base_product, candidate):
    score = 0

    if base_product.category and base_product.category == candidate.category:
        score += 4
    if base_product.subcategory and base_product.subcategory == candidate.subcategory:
        score += 3
    if base_product.material and base_product.material == candidate.material:
        score += 2
    if base_product.brand and base_product.brand == candidate.brand:
        score += 1
    if base_product.color and base_product.color == candidate.color:
        score += 1

    return score


def normalize_category(category):
    value = str(category or "").strip().lower()
    aliases = {
        "top": "tops",
        "shirt": "tops",
        "shirts": "tops",
        "tshirt": "tops",
        "tshirts": "tops",
        "t-shirt": "tops",
        "t-shirts": "tops",
        "jean": "pants",
        "jeans": "pants",
        "trouser": "pants",
        "trousers": "pants",
        "pant": "pants",
        "short": "shorts",
        "shorts": "shorts",
        "dress": "dresses",
        "skirt": "skirts",
        "shoe": "shoes",
        "shoes": "shoes",
        "sneaker": "shoes",
        "sneakers": "shoes",
        "heel": "shoes",
        "heels": "shoes",
        "sandal": "shoes",
        "sandals": "shoes",
        "flat": "shoes",
        "flats": "shoes",
        "handbag": "bags",
        "handbags": "bags",
        "bag": "bags",
        "outwear": "outerwear",
        "jacket": "outerwear",
        "jackets": "outerwear",
    }
    return aliases.get(value, value)


def infer_outfit_category(product):
    normalized = normalize_category(product.category)
    if normalized and normalized != "clothing":
        return normalized

    text = " ".join(
        str(value or "").lower()
        for value in [product.title, product.subcategory, product.description]
    )
    title_aliases = [
        (("t-shirt", "tshirt", "shirt", "tee", "blouse", "top"), "tops"),
        (("shorts",), "shorts"),
        (("skirt",), "skirts"),
        (("jean", "pants", "trouser"), "pants"),
        (("dress",), "dresses"),
        (("shoe", "sneaker", "heel", "sandal", "flat"), "shoes"),
        (("jacket", "coat", "outerwear"), "outerwear"),
        (("bag", "handbag", "purse"), "bags"),
    ]

    for terms, category in title_aliases:
        if any(term in text for term in terms):
            return category

    return normalized


def ai_product_payload(product):
    return {
        "product_id": product.product_id,
        "title": product.title,
        "category": product.category,
        "subcategory": product.subcategory,
        "color": product.color,
        "image_url": product.image_url,
    }


def normalize_color(color):
    value = str(color or "").strip().lower()
    if not value:
        return ""

    if "navy" in value:
        return "navy"
    if "grey" in value or "gray" in value:
        return "grey"
    if "blue" in value:
        return "blue"
    if "black" in value:
        return "black"
    if "white" in value:
        return "white"
    if "beige" in value or "cream" in value:
        return "beige"
    if "brown" in value or "coffee" in value:
        return "brown"
    if "red" in value:
        return "red"
    if "green" in value or "olive" in value:
        return "green"
    if "pink" in value:
        return "pink"
    if "purple" in value or "violet" in value:
        return "purple"
    if "yellow" in value or "gold" in value:
        return "gold"
    if "silver" in value:
        return "silver"

    return value.split()[0]


def score_color_compatibility(base_color, candidate_color):
    base = normalize_color(base_color)
    candidate = normalize_color(candidate_color)

    if not base or not candidate:
        return 0.4
    if base == candidate:
        return 0.8
    if base in NEUTRAL_COLORS or candidate in NEUTRAL_COLORS:
        return 1.4
    if frozenset((base, candidate)) in COLOR_PAIRS:
        return 1.8
    return 0.2


def score_outfit_metadata(base_product, candidate, target_category):
    candidate_category = infer_outfit_category(candidate)
    score = 0.0

    if candidate_category == target_category:
        score += 4.0
    if candidate_category == infer_outfit_category(base_product):
        score -= 4.0

    score += score_color_compatibility(base_product.color, candidate.color)

    if base_product.material and candidate.material:
        if base_product.material == candidate.material:
            score += 0.3
        elif normalize_category(candidate_category) in {"shoes", "bags"}:
            score += 0.2

    if base_product.brand and candidate.brand and base_product.brand == candidate.brand:
        score += 0.2

    return score


def build_outfit_groups(base_product, candidates):
    base_category = infer_outfit_category(base_product)
    target_categories = OUTFIT_CATEGORY_SLOTS.get(base_category, OUTFIT_CATEGORY_SLOTS["clothing"])
    groups = {}
    flat_scored = []
    used_product_ids = set()
    scoring_modes = set()

    for target_category in target_categories:
        slot_candidates = [
            candidate for candidate in candidates
            if infer_outfit_category(candidate) == target_category
        ]
        if not slot_candidates:
            continue

        prefiltered = sorted(
            (
                (score_outfit_metadata(base_product, candidate, target_category), candidate)
                for candidate in slot_candidates
            ),
            key=lambda item: item[0],
            reverse=True,
        )[:OUTFIT_PREFILTER_LIMIT]

        prefilter_products = [candidate for _, candidate in prefiltered]
        ai_scores = get_ai_outfit_scores(
            base_product,
            prefilter_products,
            limit=min(OUTFIT_SLOT_SIZE * 2, len(prefilter_products)),
        )
        scoring_modes.add("ai-service" if ai_scores else "metadata-fallback")

        scored = []
        for metadata_score, candidate in prefiltered:
            ai_score = ai_scores.get(candidate.product_id)
            final_score = metadata_score
            if ai_score is not None:
                final_score += ai_score * 10
            scored.append((final_score, candidate))

        scored.sort(key=lambda item: item[0], reverse=True)
        selected = []

        for score, candidate in scored:
            if candidate.product_id in used_product_ids:
                continue

            selected.append(product_to_dict(candidate))
            used_product_ids.add(candidate.product_id)
            flat_scored.append((score, candidate))

            if len(selected) >= OUTFIT_SLOT_SIZE:
                break

        if selected:
            groups[target_category] = {
                "title": OUTFIT_SLOT_TITLES.get(target_category, target_category.title()),
                "products": selected,
            }

    flat_scored.sort(key=lambda item: item[0], reverse=True)
    scoring = "ai-service" if "ai-service" in scoring_modes else "metadata-fallback"

    return groups, flat_scored, scoring, base_category, target_categories


def get_ai_outfit_scores(base_product, candidates, limit=6):
    service_url = os.getenv("REBLOOM_AI_SERVICE_URL", "http://127.0.0.1:8010").rstrip("/")
    payload = {
        "base_product": ai_product_payload(base_product),
        "candidates": [ai_product_payload(candidate) for candidate in candidates],
        "limit": limit,
    }

    try:
        request = urllib.request.Request(
            f"{service_url}/outfit-rank",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=AI_OUTFIT_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return {}

    return {
        item["product_id"]: float(item["score"])
        for item in data.get("ranked", [])
        if item.get("product_id") is not None
    }


def get_active_product_or_404(product_id, db):
    product = (
        db.query(models.Product)
        .filter(
            models.Product.product_id == product_id,
            models.Product.is_active == True,
        )
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


@router.get("/home")
def recommend_home(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    interactions = (
        db.query(models.UserInteraction)
        .filter(
            models.UserInteraction.user_id == current_user.user_id,
            models.UserInteraction.interaction_type.in_(["viewed", "liked", "added_to_cart"]),
        )
        .order_by(models.UserInteraction.timestamp.desc())
        .limit(30)
        .all()
    )
    product_ids = [interaction.product_id for interaction in interactions]
    interacted_products = (
        db.query(models.Product)
        .filter(models.Product.product_id.in_(product_ids))
        .all()
        if product_ids
        else []
    )

    categories = Counter(
        product.category for product in interacted_products if product.category
    )
    brands = Counter(product.brand for product in interacted_products if product.brand)
    materials = Counter(
        product.material for product in interacted_products if product.material
    )

    searches = (
        db.query(models.SearchHistory)
        .filter(models.SearchHistory.user_id == current_user.user_id)
        .order_by(models.SearchHistory.timestamp.desc())
        .limit(10)
        .all()
    )
    search_terms = [search.query_text for search in searches if search.query_text]

    query = db.query(models.Product).filter(models.Product.is_active == True)

    if product_ids:
        query = query.filter(~models.Product.product_id.in_(product_ids))

    filters = []
    if categories:
        filters.append(models.Product.category.in_([category for category, _ in categories.most_common(3)]))
    if brands:
        filters.append(models.Product.brand.in_([brand for brand, _ in brands.most_common(3)]))
    if materials:
        filters.append(models.Product.material.in_([material for material, _ in materials.most_common(3)]))
    for term in search_terms[:3]:
        like_term = f"%{term}%"
        filters.append(
            or_(
                models.Product.title.ilike(like_term),
                models.Product.description.ilike(like_term),
                models.Product.category.ilike(like_term),
                models.Product.brand.ilike(like_term),
                models.Product.material.ilike(like_term),
            )
        )

    if filters:
        query = query.filter(or_(*filters))

    products = query.limit(12).all()

    if not products:
        products = (
            db.query(models.Product)
            .filter(models.Product.is_active == True)
            .order_by(models.Product.created_at.desc())
            .limit(12)
            .all()
        )

    return {
        "title": "Inspired by your browsing",
        "basis": {
            "categories": [category for category, _ in categories.most_common(3)],
            "brands": [brand for brand, _ in brands.most_common(3)],
            "materials": [material for material, _ in materials.most_common(3)],
            "search_terms": search_terms[:3],
        },
        "products": [product_to_dict(product) for product in products],
    }


@router.get("/products/{product_id}/similar")
@product_router.get("/{product_id}/similar")
def recommend_similar_products(
    product_id: int,
    db: Session = Depends(get_db),
):
    base_product = get_active_product_or_404(product_id, db)
    candidates = (
        db.query(models.Product)
        .filter(
            models.Product.product_id != product_id,
            models.Product.is_active == True,
        )
        .all()
    )

    scored = [
        (score_product_similarity(base_product, candidate), candidate)
        for candidate in candidates
    ]
    scored = [item for item in scored if item[0] > 0]
    scored.sort(key=lambda item: item[0], reverse=True)

    return {
        "title": "Similar items",
        "base_product": product_to_dict(base_product),
        "products": [product_to_dict(product) for _, product in scored[:8]],
    }


@router.get("/liked-similar")
def recommend_similar_to_liked(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    interactions = (
        db.query(models.UserInteraction)
        .filter(
            models.UserInteraction.user_id == current_user.user_id,
            models.UserInteraction.interaction_type.in_(["liked", "viewed"]),
        )
        .order_by(models.UserInteraction.timestamp.desc())
        .limit(10)
        .all()
    )
    seed_ids = []

    for interaction in interactions:
        if interaction.product_id not in seed_ids:
            seed_ids.append(interaction.product_id)

    seed_products = (
        db.query(models.Product)
        .filter(models.Product.product_id.in_(seed_ids))
        .all()
        if seed_ids
        else []
    )
    candidates = (
        db.query(models.Product)
        .filter(
            models.Product.is_active == True,
            ~models.Product.product_id.in_(seed_ids) if seed_ids else True,
        )
        .all()
    )

    scored_by_product = {}
    for seed_product in seed_products:
        for candidate in candidates:
            score = score_product_similarity(seed_product, candidate)
            if score <= 0:
                continue

            current = scored_by_product.get(candidate.product_id)
            if current is None or score > current[0]:
                scored_by_product[candidate.product_id] = (score, candidate)

    scored = sorted(scored_by_product.values(), key=lambda item: item[0], reverse=True)

    if not scored:
        fallback = (
            db.query(models.Product)
            .filter(models.Product.is_active == True)
            .order_by(models.Product.created_at.desc())
            .limit(8)
            .all()
        )
        scored = [(0, product) for product in fallback]

    return {
        "title": "Similar to items you liked",
        "basis_product_ids": seed_ids,
        "products": [product_to_dict(product) for _, product in scored[:8]],
    }


@router.get("/products/{product_id}/outfit")
@product_router.get("/{product_id}/outfit")
def recommend_outfit(
    product_id: int,
    db: Session = Depends(get_db),
):
    base_product = get_active_product_or_404(product_id, db)
    candidates = (
        db.query(models.Product)
        .filter(
            models.Product.product_id != product_id,
            models.Product.is_active == True,
        )
        .all()
    )
    groups, scored, scoring, base_category, target_categories = build_outfit_groups(
        base_product,
        candidates,
    )

    return {
        "title": "Complete the Look",
        "base_product": product_to_dict(base_product),
        "base_category": base_category,
        "target_categories": target_categories,
        "scoring": scoring,
        "groups": groups,
        "products": [product_to_dict(product) for _, product in scored[:6]],
    }
