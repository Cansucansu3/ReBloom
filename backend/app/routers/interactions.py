from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/interactions", tags=["Interactions"])

@router.post("/view/{product_id}")
def record_view(
    product_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    interaction = models.UserInteraction(
        user_id=current_user.user_id,
        product_id=product_id,
        interaction_type="viewed"
    )
    db.add(interaction)
    db.commit()
    
    return {"message": "View recorded"}

@router.post("/like/{product_id}")
def like_product(
    product_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    existing = db.query(models.UserInteraction).filter(
        models.UserInteraction.user_id == current_user.user_id,
        models.UserInteraction.product_id == product_id,
        models.UserInteraction.interaction_type == "liked"
    ).first()
    
    if existing:
        return {"message": "Already liked"}
    
    interaction = models.UserInteraction(
        user_id=current_user.user_id,
        product_id=product_id,
        interaction_type="liked"
    )
    db.add(interaction)
    db.commit()
    
    return {"message": "Product liked"}

@router.get("/liked")
def get_liked_products(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    liked = db.query(models.UserInteraction).filter(
        models.UserInteraction.user_id == current_user.user_id,
        models.UserInteraction.interaction_type == "liked"
    ).all()
    
    products = []
    for item in liked:
        product = db.query(models.Product).filter(
            models.Product.product_id == item.product_id
        ).first()
        if product:
            products.append({
                "product_id": product.product_id,
                "title": product.title,
                "price": product.price,
                "image_url": product.image_url
            })
    
    return products
