from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app import models, auth, schemas
from app.database import get_db

router = APIRouter(prefix="/leaderboard", tags=["Leaderboard"])

@router.get("/", response_model=list)
def get_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    top_users = db.query(
        models.User.user_id,
        models.User.name,
        models.UserImpact.total_water_saved_liters,
        models.UserImpact.virtual_trees
    ).join(
        models.UserImpact, models.User.user_id == models.UserImpact.user_id
    ).order_by(
        desc(models.UserImpact.total_water_saved_liters)
    ).limit(limit).all()
    
    result = []
    for i, user in enumerate(top_users):
        result.append({
            "rank": i + 1,
            "user_id": user.user_id,
            "username": user.name,
            "water_saved_liters": user.total_water_saved_liters or 0,
            "virtual_trees": user.virtual_trees or 0
        })
    
    return result

@router.get("/me")
def get_my_rank(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    
    if not impact:
        return {"rank": None, "water_saved": 0, "virtual_trees": 0}
    
    higher_count = db.query(models.UserImpact).filter(
        models.UserImpact.total_water_saved_liters > (impact.total_water_saved_liters or 0)
    ).count()
    
    return {
        "rank": higher_count + 1,
        "water_saved": impact.total_water_saved_liters or 0,
        "virtual_trees": impact.virtual_trees or 0
    }
