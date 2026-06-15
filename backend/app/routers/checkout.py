from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app import models, auth, schemas
from app.database import get_db
from app.services.impact_service import (
    apply_impact_milestones,
    ensure_user_impact,
    estimate_product_water_saved,
    get_or_create_legacy_certificate,
    get_tree_stage_payload,
    serialize_certificate,
)

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/", response_model=schemas.CheckoutResponse)
def checkout(
    seller_id: Optional[int] = None,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user.user_id
    ).all()
    
    if not cart_items:
        raise HTTPException(
            status_code=409,
            detail="This item was purchased by another user. Your cart has been updated.",
        )

    checkout_items = []
    stale_items = []

    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.product_id == item.product_id
        ).first()

        if not product or not product.is_active:
            stale_items.append(item)
            continue

        if seller_id is None or product.seller_id == seller_id:
            checkout_items.append((item, product))

    if stale_items:
        for item in stale_items:
            db.delete(item)
        db.commit()
        raise HTTPException(
            status_code=409,
            detail="Some items are no longer available. Your cart was updated."
        )

    if not checkout_items:
        raise HTTPException(status_code=400, detail="No available items selected for checkout")

    seller_ids = {product.seller_id for _, product in checkout_items}
    if seller_id is None and len(seller_ids) > 1:
        raise HTTPException(
            status_code=400,
            detail="Cart contains items from multiple sellers. Please checkout one seller at a time."
        )
    
    total_amount = 0
    total_water_saved = 0
    orders = []
    purchased_product_ids = []
    
    for item, product in checkout_items:
        total_amount += product.price
        
        water_saved = estimate_product_water_saved(product)
        total_water_saved += water_saved
        
        # Create order
        order = models.Orders(
            buyer_id=current_user.user_id,
            product_id=product.product_id,
            price=product.price,
            status="completed"
        )
        db.add(order)
        orders.append(order)
        purchased_product_ids.append(product.product_id)

        # Mark item as sold so it disappears from active marketplace/search/recommendations.
        product.is_active = False

        if product.seller:
            product.seller.total_sales = (product.seller.total_sales or 0) + 1
        
        # Record interaction
        interaction = models.UserInteraction(
            user_id=current_user.user_id,
            product_id=product.product_id,
            interaction_type="purchased"
        )
        db.add(interaction)

    if purchased_product_ids:
        db.query(models.Cart).filter(
            models.Cart.product_id.in_(purchased_product_ids)
        ).delete(synchronize_session=False)
    
    # Update user impact
    impact = ensure_user_impact(db, current_user.user_id)
    
    impact.total_water_saved_liters = (impact.total_water_saved_liters or 0) + total_water_saved
    impact.total_items_reused = (impact.total_items_reused or 0) + len(checkout_items)
    impact.impact_points = (impact.impact_points or 0) + int(total_water_saved // 100)

    apply_impact_milestones(impact)
    impact.updated_at = datetime.now()
    certificate = get_or_create_legacy_certificate(db, current_user, impact)

    db.flush()
    order_ids = [order.order_id for order in orders]
    
    db.commit()
    
    # Determine tree stage
    tree_stage = get_tree_stage(impact.total_water_saved_liters)
    
    return {
        "message": "Order completed successfully!",
        "order_id": orders[0].order_id if orders else 0,
        "order_ids": order_ids,
        "total_amount": total_amount,
        "water_saved_liters": total_water_saved,
        "points_earned": int(total_water_saved // 100),
        "total_water_saved_all_time": impact.total_water_saved_liters,
        "tree_stage": tree_stage,
        "legacy_certificate": serialize_certificate(certificate),
    }

@router.get("/orders", response_model=list[schemas.OrderResponse])
def get_my_orders(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    orders = db.query(models.Orders).filter(
        models.Orders.buyer_id == current_user.user_id
    ).order_by(models.Orders.ordered_at.desc()).all()

    result = []
    for order in orders:
        product = order.product
        seller_name = None
        if product and product.seller and product.seller.user:
            seller_name = product.seller.user.name

        result.append({
            "order_id": order.order_id,
            "product_id": order.product_id,
            "seller_id": product.seller_id if product else 0,
            "seller_name": seller_name,
            "price": order.price,
            "status": order.status,
            "ordered_at": order.ordered_at,
            "product": {
                "product_id": product.product_id if product else order.product_id,
                "seller_id": product.seller_id if product else 0,
                "title": product.title if product else "Unavailable item",
                "brand": product.brand if product else None,
                "size": product.size if product else None,
                "color": product.color if product else None,
                "category": product.category if product else None,
                "subcategory": product.subcategory if product else None,
                "gender": product.gender if product else None,
                "occasion": product.occasion if product else None,
                "condition": product.condition if product else None,
                "material": product.material if product else None,
                "weight_kg": product.weight_kg if product else None,
                "image_url": product.image_url if product else None,
                "water_saved_liters": product.water_saved_liters if product else None,
            },
        })

    return result

def get_tree_stage(water_saved: float):
    return get_tree_stage_payload(water_saved)["stage"]
