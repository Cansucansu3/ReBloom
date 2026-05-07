from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# =====================================================
# USER SCHEMAS
# =====================================================

class UserCreate(BaseModel):
    name: str
    email: str
    password: str
    location: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    email: str
    location: Optional[str]
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# =====================================================
# PRODUCT SCHEMAS
# =====================================================

class ProductCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    condition: Optional[str] = None
    material: Optional[str] = None
    weight_kg: Optional[float] = None
    price: float
    image_url: Optional[str] = None
    source_platform: Optional[str] = None

class ProductUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    material: Optional[str] = None
    weight_kg: Optional[float] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    product_id: int
    seller_id: int
    title: str
    description: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    brand: Optional[str]
    color: Optional[str]
    size: Optional[str]
    condition: Optional[str]
    material: Optional[str]
    weight_kg: Optional[float] = None
    water_saved_liters: Optional[float] = None
    price: float
    image_url: Optional[str]
    is_second_hand: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

# =====================================================
# CART SCHEMAS
# =====================================================

class AddToCartRequest(BaseModel):
    quantity: int = 1

class CartItemResponse(BaseModel):
    cart_id: int
    product_id: int
    title: str
    price: float
    added_at: datetime

class CartResponse(BaseModel):
    items: List[CartItemResponse]
    total: float

# =====================================================
# CHECKOUT SCHEMAS
# =====================================================

class CheckoutResponse(BaseModel):
    message: str
    order_id: int
    total_amount: float
    water_saved_liters: float
    points_earned: int
    total_water_saved_all_time: float
    tree_stage: str

# =====================================================
# IMPACT SCHEMAS
# =====================================================

class ImpactResponse(BaseModel):
    user_id: int
    total_water_saved_liters: float
    total_co2_saved_kg: float
    total_items_reused: int
    virtual_trees: int
    real_trees_earned: int
    impact_points: int

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    water_saved_liters: float
    tree_stage: str

class MyRankResponse(BaseModel):
    rank: Optional[int]
    water_saved: float
    tree_stage: str
    next_stage: Optional[dict] = None
