from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import auth, models
from app.database import get_db
from app.services.impact_service import get_tree_stage_payload


router = APIRouter(prefix="/impact", tags=["Impact"])


def impact_payload(impact):
    if not impact:
        return {
            "total_water_saved_liters": 0,
            "total_co2_saved_kg": 0,
            "total_items_reused": 0,
            "virtual_trees": 0,
            "real_trees_earned": 0,
            "impact_points": 0,
        }

    return impact


@router.get("/me")
def get_my_impact(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()

    return impact_payload(impact)


@router.get("/tree")
def get_tree_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()

    water_saved = impact.total_water_saved_liters if impact else 0

    payload = get_tree_stage_payload(water_saved)
    payload["emoji"] = payload["label"]
    return payload


@router.get("/milestones")
def get_milestones(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    milestones = db.query(models.TreeMilestones).all()

    return [
        {
            "required_points": milestone.required_points,
            "virtual_tree_reward": milestone.virtual_tree_reward,
            "real_tree_reward": milestone.real_tree_reward,
            "badge_name": milestone.badge_name,
        }
        for milestone in milestones
    ]
