import re
import hashlib
import uuid
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

VIRTUAL_TREE_GOAL_LITERS = 10000
LEGACY_GOAL_LITERS = 100000
REAL_TREE_GOAL_LITERS = LEGACY_GOAL_LITERS
LEGACY_PARTNER_NAME = "ReBloom Legacy Forest Partner"
LEGACY_PLANTING_LOCATION = "Antalya ReBloom Demo Forest"
LEGACY_GPS_LOCATION = "36.8969, 30.7133"


TREE_STAGE_THRESHOLDS = [
    {
        "stage": "seed",
        "label": "Seed",
        "next": 1000,
        "description": "Your garden has started.",
    },
    {
        "stage": "sapling",
        "label": "Sapling",
        "next": 4000,
        "description": "Your first leaves are growing.",
    },
    {
        "stage": "young_tree",
        "label": "Young Tree",
        "next": 7000,
        "description": "Your impact is becoming visible.",
    },
    {
        "stage": "mature_oak",
        "label": "Mature Oak",
        "next": VIRTUAL_TREE_GOAL_LITERS,
        "description": "Your garden is getting stronger.",
    },
]


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


def get_current_tree_liters(total_water_saved_liters):
    total = max(0, float(total_water_saved_liters or 0))
    return total % VIRTUAL_TREE_GOAL_LITERS


def get_impact_milestones(total_water_saved_liters):
    total = max(0, float(total_water_saved_liters or 0))
    return {
        "virtual_trees": int(total // VIRTUAL_TREE_GOAL_LITERS),
        "real_trees_earned": int(total // REAL_TREE_GOAL_LITERS),
        "legacy_milestone_reached": total >= LEGACY_GOAL_LITERS,
    }


def apply_impact_milestones(impact):
    milestones = get_impact_milestones(impact.total_water_saved_liters)
    impact.virtual_trees = milestones["virtual_trees"]
    impact.real_trees_earned = milestones["real_trees_earned"]
    return impact


def serialize_certificate(certificate):
    if not certificate:
        return None

    return {
        "certificate_id": certificate.certificate_id,
        "certificate_hash": certificate.certificate_hash,
        "total_water_saved_liters": certificate.total_water_saved_liters,
        "status": certificate.status,
        "partner_name": certificate.partner_name,
        "planting_location": certificate.planting_location,
        "gps_location": certificate.gps_location,
        "issued_at": certificate.issued_at,
        "confirmed_at": certificate.confirmed_at,
    }


def get_or_create_legacy_certificate(db, user, impact):
    if not user or not impact:
        return None

    total = float(impact.total_water_saved_liters or 0)
    if total < LEGACY_GOAL_LITERS:
        return None

    existing = db.query(models.Certificate).filter(
        models.Certificate.user_id == user.user_id
    ).order_by(models.Certificate.issued_at.desc()).first()

    if existing:
        return existing

    certificate_id = str(uuid.uuid4())
    certificate_hash = hashlib.sha256(
        f"{certificate_id}:{user.user_id}:{user.email}:{round(total, 2)}".encode("utf-8")
    ).hexdigest()[:24].upper()

    certificate = models.Certificate(
        certificate_id=certificate_id,
        user_id=user.user_id,
        certificate_hash=certificate_hash,
        total_water_saved_liters=total,
        status="generated",
        partner_name=LEGACY_PARTNER_NAME,
        planting_location=LEGACY_PLANTING_LOCATION,
        gps_location=LEGACY_GPS_LOCATION,
        confirmed_at=datetime.now(),
    )
    db.add(certificate)
    db.flush()

    partner_log = models.PartnerRequestLog(
        certificate_id=certificate.certificate_id,
        partner_name=LEGACY_PARTNER_NAME,
        request_status="demo_generated",
        request_payload=(
            f"user_id={user.user_id}; total_water_saved_liters={round(total, 2)}; "
            f"location={LEGACY_PLANTING_LOCATION}"
        ),
        response_payload="Demo certificate generated locally; external partner API pending.",
    )
    db.add(partner_log)

    return certificate


def get_tree_stage_payload(total_water_saved_liters):
    total = max(0, float(total_water_saved_liters or 0))
    current_tree_liters = get_current_tree_liters(total)
    milestones = get_impact_milestones(total)

    for stage in TREE_STAGE_THRESHOLDS:
        if current_tree_liters < stage["next"]:
            selected = stage
            break
    else:
        selected = TREE_STAGE_THRESHOLDS[-1]

    return {
        "stage": selected["stage"],
        "label": selected["label"],
        "description": selected["description"],
        "water_saved": total,
        "total_water_saved_liters": total,
        "current_tree_liters": current_tree_liters,
        "current_tree_goal_liters": VIRTUAL_TREE_GOAL_LITERS,
        "real_tree_goal_liters": REAL_TREE_GOAL_LITERS,
        "legacy_goal_liters": LEGACY_GOAL_LITERS,
        "next_stage_threshold": selected["next"],
        "remaining_to_next": max(0, selected["next"] - current_tree_liters),
        "remaining_to_next_tree": (
            VIRTUAL_TREE_GOAL_LITERS
            if current_tree_liters == 0
            else max(0, VIRTUAL_TREE_GOAL_LITERS - current_tree_liters)
        ),
        **milestones,
    }


def add_listing_impact(db, user_id, water_saved_liters):
    impact = ensure_user_impact(db, user_id)
    water_saved = float(water_saved_liters or 0)

    impact.total_water_saved_liters = (impact.total_water_saved_liters or 0) + water_saved
    impact.total_items_reused = (impact.total_items_reused or 0) + 1
    impact.impact_points = (impact.impact_points or 0) + int(water_saved // 100)
    apply_impact_milestones(impact)
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
