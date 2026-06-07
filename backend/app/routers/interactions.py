from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(prefix="/interactions", tags=["Interactions"])


def make_username(name: str | None):
    slug = "".join(
        char.lower() if char.isalnum() else "-"
        for char in str(name or "rebloom-user").strip()
    )
    slug = "-".join(part for part in slug.split("-") if part)
    return f"@{slug or 'rebloom-user'}"


def comment_to_response(comment):
    user_name = comment.user.name if comment.user else "ReBloom user"
    return {
        "comment_id": comment.comment_id,
        "product_id": comment.product_id,
        "user_id": comment.user_id,
        "username": make_username(user_name),
        "user_name": user_name,
        "text": comment.text,
        "created_at": comment.created_at,
    }

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


@router.get("/comments/{product_id}", response_model=list[schemas.ProductCommentResponse])
def get_product_comments(
    product_id: int,
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    comments = (
        db.query(models.ProductComment)
        .filter(models.ProductComment.product_id == product_id)
        .order_by(models.ProductComment.created_at.asc())
        .all()
    )

    return [comment_to_response(comment) for comment in comments]


@router.post("/comments/{product_id}", response_model=schemas.ProductCommentResponse)
def add_product_comment(
    product_id: int,
    payload: schemas.ProductCommentCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    text = payload.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Comment cannot be empty")

    comment = models.ProductComment(
        product_id=product_id,
        user_id=current_user.user_id,
        text=text,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)

    return comment_to_response(comment)
