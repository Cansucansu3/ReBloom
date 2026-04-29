from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/impact", tags=["Impact"])

@router.get("/me")
def get_my_impact(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    
    if not impact:
        return {
            "total_water_saved_liters": 0,
            "total_co2_saved_kg": 0,
            "total_items_reused": 0,
            "virtual_trees": 0,
            "real_trees_earned": 0,
            "impact_points": 0
        }
    
    return impact

@router.get("/tree")
def get_tree_status(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    
    water_saved = impact.total_water_saved_liters if impact else 0
    
    if water_saved < 100:
        stage = "seed"
        next_threshold = 100
        emoji = "🌱"
    elif water_saved < 1000:
        stage = "sprout"
        next_threshold = 1000
        emoji = "🌿"
    elif water_saved < 5000:
        stage = "sapling"
        next_threshold = 5000
        emoji = "🌳"
    elif water_saved < 10000:
        stage = "young_tree"
        next_threshold = 10000
        emoji = "🍃"
    else:
        stage = "ancient_oak"
        next_threshold = None
        emoji = "🏆"
    
    return {
        "stage": stage,
        "emoji": emoji,
        "water_saved": water_saved,
        "next_stage_threshold": next_threshold,
        "remaining_to_next": next_threshold - water_saved if next_threshold else 0
    }

@router.get("/milestones")
def get_milestones(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    milestones = db.query(models.TreeMilestones).all()
    
    return [
        {
            "required_points": m.required_points,
            "virtual_tree_reward": m.virtual_tree_reward,
            "real_tree_reward": m.real_tree_reward,
            "badge_name": m.badge_name
        }
        for m in milestones
    ]
