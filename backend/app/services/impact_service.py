import re
from datetime import datetime

from app import models


WATER_FOOTPRINTS_L_PER_KG = {
    "cotton": 10000,
    "denim": 8000,
    "polyester": 100,
    "recycled polyester": 60,
    "synthetic": 500,
    "faux leather": 900,
    "leather": 17000,
    "canvas": 4000,
    "cotton blend": 5000,
}

DEFAULT_CATEGORY_WEIGHTS_KG = {
    "tops": 0.30,
    "pants": 0.60,
    "shorts": 0.35,
    "skirts": 0.40,
    "dresses": 0.50,
    "outerwear": 0.90,
    "shoes": 0.80,
    "bags": 0.50,
    "clothing": 0.50,
}


def normalize_material_name(value):
    text = str(value or "").strip().lower()
    if not text:
        return ""

    if "recycled" in text and "polyester" in text:
        return "recycled polyester"
    if "faux" in text and "leather" in text:
        return "faux leather"
    if "cotton" in text and "blend" in text:
        return "cotton blend"

    for material in WATER_FOOTPRINTS_L_PER_KG:
        if material in text:
            return material

    return text


def default_weight_for_category(category):
    normalized = str(category or "clothing").strip().lower()
    return DEFAULT_CATEGORY_WEIGHTS_KG.get(normalized, DEFAULT_CATEGORY_WEIGHTS_KG["clothing"])


def parse_material_composition(material):
    text = str(material or "").strip()
    if not text:
        return [("cotton blend", 1.0)]

    matches = re.findall(r"(\d+(?:\.\d+)?)\s*%\s*([A-Za-z ]+)", text)
    if matches:
        composition = []
        for percent, name in matches:
            normalized = normalize_material_name(name)
            if normalized:
                composition.append((normalized, float(percent) / 100))

        total_share = sum(share for _, share in composition)
        if total_share > 0:
            return [(name, share / total_share) for name, share in composition]

    return [(normalize_material_name(text) or "cotton blend", 1.0)]


def estimate_water_saved_liters(material, weight_kg=None, category=None):
    weight = float(weight_kg) if weight_kg not in (None, "") else default_weight_for_category(category)
    if weight <= 0:
        weight = default_weight_for_category(category)

    footprint_per_kg = 0
    for material_name, share in parse_material_composition(material):
        footprint_per_kg += WATER_FOOTPRINTS_L_PER_KG.get(material_name, 1000) * share

    return round(footprint_per_kg * weight)


def ensure_user_impact(db, user_id):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == user_id
    ).first()

    if impact:
        return impact

    impact = models.UserImpact(user_id=user_id)
    db.add(impact)
    db.flush()
    return impact


def add_listing_impact(db, user_id, water_saved_liters):
    impact = ensure_user_impact(db, user_id)
    water_saved = float(water_saved_liters or 0)

    impact.total_water_saved_liters = (impact.total_water_saved_liters or 0) + water_saved
    impact.total_items_reused = (impact.total_items_reused or 0) + 1
    impact.impact_points = (impact.impact_points or 0) + int(water_saved // 100)
    impact.virtual_trees = int((impact.total_water_saved_liters or 0) // 1000)
    impact.updated_at = datetime.now()
    return impact


def estimate_product_water_saved(product):
    existing = getattr(product, "water_saved_liters", None)
    if existing is not None:
        return existing

    return estimate_water_saved_liters(
        product.material,
        getattr(product, "weight_kg", None),
        product.category,
    )
