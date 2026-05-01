from collections import Counter

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db


router = APIRouter(prefix="/recommendations", tags=["Recommendations"])
product_router = APIRouter(prefix="/products", tags=["Recommendations"])


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
    compatible_categories = {
        "tops": ["pants", "skirts", "outerwear"],
        "pants": ["tops", "outerwear"],
        "skirts": ["tops", "outerwear"],
        "dresses": ["outerwear", "bags"],
        "outerwear": ["tops", "dresses", "pants", "skirts"],
        "bags": ["dresses", "tops", "pants", "skirts"],
        "clothing": ["outerwear", "pants", "skirts", "tops"],
    }
    target_categories = compatible_categories.get(base_product.category, [])

    query = db.query(models.Product).filter(
        models.Product.product_id != product_id,
        models.Product.is_active == True,
    )

    if target_categories:
        query = query.filter(models.Product.category.in_(target_categories))

    candidates = query.all()
    scored = [
        (score_product_similarity(base_product, candidate), candidate)
        for candidate in candidates
    ]
    scored.sort(key=lambda item: item[0], reverse=True)

    return {
        "title": "Complete the Look",
        "base_product": product_to_dict(base_product),
        "products": [product_to_dict(product) for _, product in scored[:6]],
    }
