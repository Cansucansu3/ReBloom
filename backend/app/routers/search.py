from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db
from app.services.image_similarity import find_visually_similar_products, image_from_bytes

router = APIRouter(prefix="/search", tags=["Search"])


def product_to_dict(product, score=None):
    data = {
        "product_id": product.product_id,
        "seller_id": product.seller_id,
        "title": product.title,
        "description": product.description,
        "category": product.category,
        "subcategory": product.subcategory,
        "brand": product.brand,
        "color": product.color,
        "size": product.size,
        "condition": product.condition,
        "material": product.material,
        "price": product.price,
        "image_url": product.image_url,
        "is_second_hand": product.is_second_hand,
        "created_at": product.created_at,
    }

    if score is not None:
        data["similarity_score"] = score

    return data

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


@router.post("/visual")
async def visual_search_products(
    file: UploadFile = File(...),
    limit: int = 12,
    db: Session = Depends(get_db)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Please upload an image file")

    try:
        query_image = image_from_bytes(await file.read())
    except Exception:
        raise HTTPException(status_code=400, detail="Image could not be processed")

    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    scored_products = find_visually_similar_products(query_image, products, limit=limit)

    if not scored_products:
        fallback_products = (
            db.query(models.Product)
            .filter(models.Product.is_active == True)
            .order_by(models.Product.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            "title": "Visual search results",
            "algorithm": "image embedding fallback",
            "products": [product_to_dict(product, score=0) for product in fallback_products],
        }

    return {
        "title": "Visual search results",
        "algorithm": "image embedding + cosine similarity",
        "products": [
            product_to_dict(product, score=score)
            for score, product in scored_products
        ],
    }

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
