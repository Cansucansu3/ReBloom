from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app import models, auth, schemas
from app.database import get_db
from app.services.impact_service import estimate_product_water_saved

router = APIRouter(prefix="/checkout", tags=["Checkout"])

@router.post("/", response_model=schemas.CheckoutResponse)
def checkout(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    cart_items = db.query(models.Cart).filter(
        models.Cart.user_id == current_user.user_id
    ).all()
    
    if not cart_items:
        raise HTTPException(status_code=400, detail="Cart is empty")
    
    total_amount = 0
    total_water_saved = 0
    orders = []
    
    for item in cart_items:
        product = db.query(models.Product).filter(
            models.Product.product_id == item.product_id
        ).first()
        
        if not product:
            continue
        
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
        
        # Record interaction
        interaction = models.UserInteraction(
            user_id=current_user.user_id,
            product_id=product.product_id,
            interaction_type="purchased"
        )
        db.add(interaction)
        
        # Delete from cart
        db.delete(item)
    
    # Update user impact
    impact = db.query(models.UserImpact).filter(
        models.UserImpact.user_id == current_user.user_id
    ).first()
    
    if impact:
        impact.total_water_saved_liters = (impact.total_water_saved_liters or 0) + total_water_saved
        impact.total_items_reused = (impact.total_items_reused or 0) + len(cart_items)
        impact.impact_points = (impact.impact_points or 0) + int(total_water_saved // 100)
        
        # Calculate virtual trees (every 1000L = 1 tree)
        impact.virtual_trees = int(impact.total_water_saved_liters // 1000)
        impact.updated_at = datetime.now()
    
    db.commit()
    
    # Determine tree stage
    if impact:
        tree_stage = get_tree_stage(impact.total_water_saved_liters)
    else:
        tree_stage = "seed"
    
    return {
        "message": "Order completed successfully!",
        "order_id": orders[0].order_id if orders else 0,
        "total_amount": total_amount,
        "water_saved_liters": total_water_saved,
        "points_earned": int(total_water_saved // 100),
        "total_water_saved_all_time": impact.total_water_saved_liters if impact else total_water_saved,
        "tree_stage": tree_stage
    }

def get_tree_stage(water_saved: float):
    if water_saved < 100:
        return "seed"
    elif water_saved < 5000:
        return "sapling"
    elif water_saved < 20000:
        return "young_tree"
    elif water_saved < 100000:
        return "mature_oak"
    else:
        return "ancient_oak"
