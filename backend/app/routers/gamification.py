from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/gamification", tags=["Gamification"])

def get_tree_stage(water_level: int):
    if water_level < 20:
        return {"stage": "seed", "emoji": "🌰", "name": "Seed"}
    elif water_level < 40:
        return {"stage": "sprout", "emoji": "🌱", "name": "Sprout"}
    elif water_level < 60:
        return {"stage": "sapling", "emoji": "🌿", "name": "Sapling"}
    elif water_level < 80:
        return {"stage": "young_tree", "emoji": "🌳", "name": "Young Tree"}
    elif water_level < 100:
        return {"stage": "mature_tree", "emoji": "🍃", "name": "Mature Tree"}
    else:
        return {"stage": "ancient_oak", "emoji": "🏆", "name": "Ancient Oak"}

@router.post("/water")
def water_plant(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(models.PlantProgress).filter(
        models.PlantProgress.user_id == current_user.user_id
    ).first()
    
    if not progress:
        progress = models.PlantProgress(user_id=current_user.user_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    today = datetime.now().date()
    points_earned = 10
    
    if progress.last_watered_date:
        last_date = progress.last_watered_date.date()
        days_diff = (today - last_date).days
        
        if days_diff == 0:
            raise HTTPException(status_code=400, detail="Already watered today!")
        elif days_diff == 1:
            progress.streak_days += 1
            points_earned += progress.streak_days // 7 * 5
        else:
            progress.streak_days = 1
    else:
        progress.streak_days = 1
    
    progress.water_level = min(100, progress.water_level + 15)
    progress.total_points += points_earned
    progress.last_watered_date = datetime.now()
    
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    
    if impact:
        impact.impact_points = (impact.impact_points or 0) + points_earned
    
    db.commit()
    
    tree_stage = get_tree_stage(progress.water_level)
    
    return {
        "message": "💧 Plant watered!",
        "water_level": progress.water_level,
        "streak_days": progress.streak_days,
        "points_earned": points_earned,
        "total_points": progress.total_points,
        "tree_stage": tree_stage["stage"],
        "tree_emoji": tree_stage["emoji"],
        "tree_name": tree_stage["name"]
    }

@router.get("/my-tree")
def get_my_tree(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    progress = db.query(models.PlantProgress).filter(
        models.PlantProgress.user_id == current_user.user_id
    ).first()
    
    if not progress:
        progress = models.PlantProgress(user_id=current_user.user_id)
        db.add(progress)
        db.commit()
        db.refresh(progress)
    
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    water_saved = impact.total_water_saved_liters if impact else 0
    
    tree_stage = get_tree_stage(progress.water_level)
    
    next_water_time = None
    if progress.last_watered_date:
        next_water_time = progress.last_watered_date + timedelta(days=1)
    
    return {
        "tree": {
            "name": tree_stage["name"],
            "stage": tree_stage["stage"],
            "emoji": tree_stage["emoji"],
            "water_level": progress.water_level,
            "image_url": f"/static/trees/{tree_stage['stage']}.png"
        },
        "stats": {
            "streak_days": progress.streak_days,
            "total_points": progress.total_points,
            "water_saved_liters": water_saved,
            "virtual_trees": impact.virtual_trees if impact else 0,
            "real_trees_earned": impact.real_trees_earned if impact else 0
        },
        "next_watering": {
            "available_at": next_water_time.isoformat() if next_water_time else None,
            "hours_remaining": round((next_water_time - datetime.now()).total_seconds() / 3600, 1) if next_water_time and next_water_time > datetime.now() else 0
        }
    }

@router.post("/claim-points/{action}")
def claim_points(
    action: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    points_map = {
        "daily_login": 5,
        "share": 20,
        "review": 15,
        "invite_friend": 50,
        "complete_profile": 25
    }
    
    if action not in points_map:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    progress = db.query(models.PlantProgress).filter(
        models.PlantProgress.user_id == current_user.user_id
    ).first()
    
    if not progress:
        progress = models.PlantProgress(user_id=current_user.user_id)
        db.add(progress)
    
    points = points_map[action]
    progress.total_points += points
    
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    if impact:
        impact.impact_points = (impact.impact_points or 0) + points
    
    db.commit()
    
    return {
        "message": f"+{points} points earned!",
        "action": action,
        "points_earned": points,
        "total_points": progress.total_points
    }

@router.get("/leaderboard/points")
def get_points_leaderboard(
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    top_users = db.query(
        models.User.user_id,
        models.User.name,
        models.PlantProgress.total_points,
        models.PlantProgress.streak_days
    ).join(
        models.PlantProgress, models.User.user_id == models.PlantProgress.user_id
    ).order_by(
        models.PlantProgress.total_points.desc()
    ).limit(limit).all()
    
    result = []
    for i, user in enumerate(top_users):
        result.append({
            "rank": i + 1,
            "user_id": user.user_id,
            "username": user.name,
            "total_points": user.total_points or 0,
            "streak_days": user.streak_days or 0
        })
    
    return result
