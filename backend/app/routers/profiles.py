from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.services.impact_service import (
    apply_impact_milestones,
    get_or_create_legacy_certificate,
    get_tree_stage_payload,
    serialize_certificate,
)


router = APIRouter(prefix="/profiles", tags=["Public Profiles"])


@router.get("/seller/{seller_id}", response_model=schemas.PublicProfileResponse)
def get_seller_profile(seller_id: int, db: Session = Depends(get_db)):
    seller = db.query(models.SellerProfile).filter(
        models.SellerProfile.seller_id == seller_id
    ).first()

    if not seller or not seller.user:
        raise HTTPException(status_code=404, detail="Seller profile not found")

    return build_public_profile(db, seller.user, seller)


@router.get("/user/{user_id}", response_model=schemas.PublicProfileResponse)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(
        models.User.user_id == user_id,
        models.User.is_active == True,
    ).first()

    if not user:
        raise HTTPException(status_code=404, detail="User profile not found")

    return build_public_profile(db, user, user.seller_profile)


def build_public_profile(db: Session, user: models.User, seller: models.SellerProfile | None):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == user.user_id
    ).first()

    active_products = []
    if seller:
        active_products = db.query(models.Product).filter(
            models.Product.seller_id == seller.seller_id,
            models.Product.is_active == True,
        ).order_by(models.Product.created_at.desc()).limit(24).all()

    water_saved = impact.total_water_saved_liters if impact else 0
    tree = get_tree_payload(water_saved)
    certificate = None
    if impact:
        apply_impact_milestones(impact)
        tree["real_trees_earned"] = impact.real_trees_earned or 0
        certificate = get_or_create_legacy_certificate(db, user, impact)
        db.commit()

    return {
        "user_id": user.user_id,
        "seller_id": seller.seller_id if seller else None,
        "name": user.name,
        "location": user.location,
        "rating": seller.rating if seller else None,
        "total_sales": seller.total_sales if seller else None,
        "verified": seller.verified if seller else None,
        "joined_at": seller.joined_at if seller else user.created_at,
        "impact": {
            "total_water_saved_liters": water_saved,
            "total_items_reused": impact.total_items_reused if impact else 0,
            "virtual_trees": impact.virtual_trees if impact else 0,
            "real_trees_earned": impact.real_trees_earned if impact else 0,
            "impact_points": impact.impact_points if impact else 0,
            "legacy_certificate": serialize_certificate(certificate),
        },
        "tree": tree,
        "active_products": active_products,
    }


def get_tree_payload(water_saved: float):
    return get_tree_stage_payload(water_saved)
