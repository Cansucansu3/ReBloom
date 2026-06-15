from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

# =====================================================
# USER SCHEMAS
# =====================================================

class UserCreate(BaseModel):
    name: str
    username: Optional[str] = None
    email: str
    password: str
    location: Optional[str] = None

class UserLogin(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    user_id: int
    name: str
    username: str
    email: str
    location: Optional[str]
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=80)
    username: Optional[str] = Field(None, min_length=3, max_length=30)
    location: Optional[str] = Field(None, max_length=100)
    profile_image: Optional[str] = None
    bio: Optional[str] = Field(None, max_length=500)

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
    gender: Optional[str] = "Unisex"
    occasion: Optional[str] = None
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
    subcategory: Optional[str] = None
    brand: Optional[str] = None
    color: Optional[str] = None
    size: Optional[str] = None
    price: Optional[float] = None
    condition: Optional[str] = None
    material: Optional[str] = None
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    occasion: Optional[str] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None

class ProductResponse(BaseModel):
    product_id: int
    seller_id: int
    seller_name: Optional[str] = None
    title: str
    description: Optional[str]
    category: Optional[str]
    subcategory: Optional[str]
    brand: Optional[str]
    color: Optional[str]
    size: Optional[str]
    gender: Optional[str] = "Unisex"
    occasion: Optional[str] = "Casual"
    condition: Optional[str]
    material: Optional[str]
    weight_kg: Optional[float] = None
    water_saved_liters: Optional[float] = None
    price: float
    image_url: Optional[str]
    is_second_hand: bool
    is_active: bool
    is_sold: bool = False
    created_at: datetime
    
    class Config:
        from_attributes = True

class ProductCommentCreate(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)

class ProductCommentResponse(BaseModel):
    comment_id: int
    product_id: int
    user_id: int
    username: str
    user_name: str
    text: str
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
    seller_id: int
    seller_name: Optional[str] = None
    title: str
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    gender: Optional[str] = "Unisex"
    occasion: Optional[str] = "Casual"
    condition: Optional[str] = None
    material: Optional[str] = None
    weight_kg: Optional[float] = None
    image_url: Optional[str] = None
    water_saved_liters: Optional[float] = None
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
    order_ids: List[int] = Field(default_factory=list)
    total_amount: float
    water_saved_liters: float
    points_earned: int
    total_water_saved_all_time: float
    tree_stage: str
    legacy_certificate: Optional["LegacyCertificateResponse"] = None

class OrderProductResponse(BaseModel):
    product_id: int
    seller_id: int
    title: str
    brand: Optional[str] = None
    size: Optional[str] = None
    color: Optional[str] = None
    category: Optional[str] = None
    subcategory: Optional[str] = None
    gender: Optional[str] = "Unisex"
    occasion: Optional[str] = "Casual"
    condition: Optional[str] = None
    material: Optional[str] = None
    weight_kg: Optional[float] = None
    image_url: Optional[str] = None
    water_saved_liters: Optional[float] = None

class OrderResponse(BaseModel):
    order_id: int
    product_id: int
    seller_id: int
    seller_name: Optional[str] = None
    price: float
    status: str
    ordered_at: datetime
    product: OrderProductResponse

class LegacyCertificateResponse(BaseModel):
    certificate_id: str
    certificate_hash: str
    total_water_saved_liters: float
    status: str
    partner_name: Optional[str] = None
    planting_location: Optional[str] = None
    gps_location: Optional[str] = None
    issued_at: datetime
    confirmed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class PublicImpactResponse(BaseModel):
    total_water_saved_liters: float
    total_items_reused: int
    virtual_trees: int
    real_trees_earned: int = 0
    impact_points: int
    legacy_certificate: Optional[LegacyCertificateResponse] = None

class PublicTreeResponse(BaseModel):
    stage: str
    label: str
    description: Optional[str] = None
    water_saved: float
    total_water_saved_liters: Optional[float] = None
    current_tree_liters: float = 0
    current_tree_goal_liters: float = 10000
    real_tree_goal_liters: float = 100000
    legacy_goal_liters: float = 100000
    next_stage_threshold: Optional[float] = None
    remaining_to_next: float
    remaining_to_next_tree: float = 10000
    virtual_trees: int = 0
    real_trees_earned: int = 0
    legacy_milestone_reached: bool = False

class PublicProfileResponse(BaseModel):
    user_id: int
    seller_id: Optional[int] = None
    name: str
    username: str
    location: Optional[str] = None
    profile_image: Optional[str] = None
    bio: Optional[str] = None
    rating: Optional[float] = None
    total_sales: Optional[int] = None
    verified: Optional[bool] = None
    joined_at: datetime
    impact: PublicImpactResponse
    tree: PublicTreeResponse
    active_products: List[ProductResponse]


class PublicProfileSearchResult(BaseModel):
    user_id: int
    seller_id: Optional[int] = None
    name: str
    username: str
    location: Optional[str] = None
    profile_image: Optional[str] = None
    verified: bool = False
    total_sales: int = 0
    virtual_trees: int = 0
    active_listing_count: int = 0

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
    legacy_certificate: Optional[LegacyCertificateResponse] = None

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
