from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, auth, schemas
from app.database import get_db

router = APIRouter(prefix="/cart", tags=["Cart"])

@router.post("/add/{product_id}")
def add_to_cart(
    product_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    # Check if product exists and is active
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if already in cart
    existing = db.query(models.Cart).filter(
        models.Cart.user_id == current_user.user_id,
        models.Cart.product_id == product_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Product already in cart")
    
    cart_item = models.Cart(
        user_id=current_user.user_id,
        product_id=product_id
    )
    db.add(cart_item)
    db.commit()
    
    return {"message": "Added to cart", "cart_id": cart_item.cart_id}

@router.get("/", response_model=schemas.CartResponse)
def view_cart(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user.user_id
    ).all()
    
    items = []
    total = 0
    
    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.product_id == item.product_id
        ).first()
        
        if product:
            items.append({
                "cart_id": item.cart_id,
                "product_id": product.product_id,
                "title": product.title,
                "price": product.price,
                "added_at": item.added_at
            })
            total += product.price
    
    return {"items": items, "total": total}

@router.delete("/remove/{cart_id}")
def remove_from_cart(
    cart_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    cart_item = db.query(models.Cart).filter(
        models.Cart.cart_id == cart_id,
        models.Cart.user_id == current_user.user_id
    ).first()
    
    if not cart_item:
        raise HTTPException(status_code=404, detail="Item not found in cart")
    
    db.delete(cart_item)
    db.commit()
    
    return {"message": "Removed from cart"}
