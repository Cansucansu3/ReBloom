import base64
import json
import os
import urllib.error
import urllib.request

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from app import models, auth
from app.database import get_db
from app.services.image_similarity import find_visually_similar_products, image_from_bytes

router = APIRouter(prefix="/search", tags=["Search"])

AI_VISUAL_SEARCH_TIMEOUT = float(os.getenv("REBLOOM_AI_VISUAL_TIMEOUT", "20"))


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
        "weight_kg": product.weight_kg,
        "water_saved_liters": product.water_saved_liters,
        "price": product.price,
        "image_url": product.image_url,
        "is_second_hand": product.is_second_hand,
        "created_at": product.created_at,
    }

    if score is not None:
        data["similarity_score"] = score

    return data


def ai_product_payload(product):
    return {
        "product_id": product.product_id,
        "title": product.title,
        "category": product.category,
        "subcategory": product.subcategory,
        "color": product.color,
        "image_url": product.image_url,
    }


def image_bytes_to_data_url(content, content_type):
    encoded = base64.b64encode(content).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


def get_ai_visual_scores(image_content, content_type, candidates, limit=12):
    service_url = os.getenv("REBLOOM_AI_SERVICE_URL", "http://127.0.0.1:8010").rstrip("/")
    payload = {
        "query_image": image_bytes_to_data_url(image_content, content_type),
        "candidates": [ai_product_payload(candidate) for candidate in candidates],
        "limit": limit,
    }

    try:
        request = urllib.request.Request(
            f"{service_url}/visual-search",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=AI_VISUAL_SEARCH_TIMEOUT) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return {}, "unavailable", None

    return (
        {
            item["product_id"]: float(item["score"])
            for item in data.get("ranked", [])
            if item.get("product_id") is not None
        },
        data.get("preprocessing") or "original",
        data.get("predicted"),
    )


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

    image_content = await file.read()

    try:
        query_image = image_from_bytes(image_content)
    except Exception:
        raise HTTPException(status_code=400, detail="Image could not be processed")

    products = db.query(models.Product).filter(models.Product.is_active == True).all()
    ai_scores, preprocessing, predicted = await run_in_threadpool(
        get_ai_visual_scores,
        image_content,
        file.content_type,
        products,
        limit,
    )

    if ai_scores:
        product_by_id = {product.product_id: product for product in products}
        scored_products = [
            (score, product_by_id[product_id])
            for product_id, score in ai_scores.items()
            if product_id in product_by_id
        ]
    else:
        scored_products = await run_in_threadpool(
            find_visually_similar_products,
            query_image,
            products,
            limit,
        )

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
            "preprocessing": "original",
            "predicted": None,
            "products": [product_to_dict(product, score=0) for product in fallback_products],
        }

    return {
        "title": "Visual search results",
        "algorithm": "clip-ai-service" if ai_scores else "histogram-fallback",
        "preprocessing": preprocessing if ai_scores else "original",
        "predicted": predicted if ai_scores else None,
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
