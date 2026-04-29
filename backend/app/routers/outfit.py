from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/outfit", tags=["Outfit"])

@router.get("/suggest/{product_id}")
def suggest_outfit(
    product_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    compatibility = db.query(models.OutfitCompatibility).filter(
        models.OutfitCompatibility.source_category == product.category
    ).order_by(models.OutfitCompatibility.score.desc()).limit(5).all()
    
    suggestions = []
    for comp in compatibility:
        matches = db.query(models.Product).filter(
            models.Product.category == comp.target_category,
            models.Product.is_active == True,
            models.Product.product_id != product_id
        ).limit(3).all()
        
        for match in matches:
            suggestions.append({
                "product_id": match.product_id,
                "title": match.title,
                "price": match.price,
                "category": match.category,
                "compatibility_score": comp.score,
                "image_url": match.image_url
            })
    
    return suggestions[:10]
