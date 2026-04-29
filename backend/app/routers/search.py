from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db

router = APIRouter(prefix="/search", tags=["Search"])

@router.post("/")
def search_products(
    query: str,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    if not query:
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    search_record = models.SearchHistory(
        user_id=current_user.user_id,
        query_text=query,
        query_type="text"
    )
    db.add(search_record)
    db.commit()
    
    products = db.query(models.Product).filter(
        models.Product.title.contains(query) | models.Product.description.contains(query),
        models.Product.is_active == True
    ).limit(20).all()
    
    return [
        {
            "product_id": p.product_id,
            "title": p.title,
            "price": p.price,
            "image_url": p.image_url
        }
        for p in products
    ]

@router.get("/history")
def get_search_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    history = db.query(models.SearchHistory).filter(
        models.SearchHistory.user_id == current_user.user_id
    ).order_by(models.SearchHistory.timestamp.desc()).limit(20).all()
    
    return [
        {
            "query_text": h.query_text,
            "query_type": h.query_type,
            "timestamp": h.timestamp
        }
        for h in history
    ]
