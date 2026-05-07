from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models, auth
from app.database import get_db
from app.services.impact_service import (
    add_listing_impact,
    estimate_water_saved_liters,
)

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=schemas.ProductResponse)
def create_product(
    product_data: schemas.ProductCreate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    seller = db.query(models.SellerProfile).filter(
        models.SellerProfile.user_id == current_user.user_id
    ).first()
    
    if not seller:
        raise HTTPException(status_code=403, detail="User is not a seller")

    water_saved_liters = estimate_water_saved_liters(
        product_data.material,
        product_data.weight_kg,
        product_data.category,
    )
    
    product = models.Product(
        seller_id=seller.seller_id,
        title=product_data.title,
        description=product_data.description,
        category=product_data.category,
        subcategory=product_data.subcategory,
        brand=product_data.brand,
        color=product_data.color,
        size=product_data.size,
        condition=product_data.condition,
        material=product_data.material,
        weight_kg=product_data.weight_kg,
        water_saved_liters=water_saved_liters,
        price=product_data.price,
        image_url=product_data.image_url,
        source_platform=product_data.source_platform,
        is_second_hand=True
    )
    
    db.add(product)
    if product_data.source_platform == "lens":
        add_listing_impact(db, current_user.user_id, water_saved_liters)

    db.commit()
    db.refresh(product)
    
    return product

@router.get("/", response_model=List[schemas.ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    q: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    
    if category:
        query = query.filter(models.Product.category == category)

    if q:
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                models.Product.title.ilike(search_term),
                models.Product.description.ilike(search_term),
                models.Product.brand.ilike(search_term),
                models.Product.category.ilike(search_term),
                models.Product.subcategory.ilike(search_term),
                models.Product.material.ilike(search_term),
                models.Product.color.ilike(search_term),
            )
        )
    
    products = query.offset(skip).limit(limit).all()
    return products

@router.get("/mine", response_model=List[schemas.ProductResponse])
def get_my_products(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    seller = db.query(models.SellerProfile).filter(
        models.SellerProfile.user_id == current_user.user_id
    ).first()

    if not seller:
        return []

    return db.query(models.Product).filter(
        models.Product.seller_id == seller.seller_id,
        models.Product.source_platform == "lens",
        models.Product.is_active == True
    ).order_by(models.Product.created_at.desc()).all()

@router.get("/{product_id}", response_model=schemas.ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(
        models.Product.product_id == product_id,
        models.Product.is_active == True
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.put("/{product_id}", response_model=schemas.ProductResponse)
def update_product(
    product_id: int,
    product_data: schemas.ProductUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    seller = db.query(models.SellerProfile).filter(
        models.SellerProfile.seller_id == product.seller_id
    ).first()
    
    if seller.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    update_data = product_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    if "material" in update_data or "weight_kg" in update_data:
        product.water_saved_liters = estimate_water_saved_liters(
            product.material,
            product.weight_kg,
            product.category,
        )
    
    db.commit()
    db.refresh(product)
    return product

@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db)
):
    product = db.query(models.Product).filter(models.Product.product_id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    seller = db.query(models.SellerProfile).filter(
        models.SellerProfile.seller_id == product.seller_id
    ).first()
    
    if seller.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    product.is_active = False
    db.commit()
    
    return {"message": "Product deleted successfully"}
