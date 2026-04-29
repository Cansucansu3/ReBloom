from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import schemas, models, auth
from app.database import get_db

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
        price=product_data.price,
        image_url=product_data.image_url,
        source_platform=product_data.source_platform,
        is_second_hand=True
    )
    
    db.add(product)
    db.commit()
    db.refresh(product)
    
    return product

@router.get("/", response_model=List[schemas.ProductResponse])
def get_products(
    skip: int = 0,
    limit: int = 100,
    category: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Product).filter(models.Product.is_active == True)
    
    if category:
        query = query.filter(models.Product.category == category)
    
    products = query.offset(skip).limit(limit).all()
    return products

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
    
    for key, value in product_data.dict(exclude_unset=True).items():
        setattr(product, key, value)
    
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
