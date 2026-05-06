from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text, ForeignKey, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


# ENUMS


class InteractionType(str, enum.Enum):
    VIEWED = "viewed"
    LIKED = "liked"
    PURCHASED = "purchased"
    SEARCHED = "searched"
    ADDED_TO_CART = "added_to_cart"

class QueryType(str, enum.Enum):
    TEXT = "text"
    VISUAL = "visual"
    VOICE = "voice"


# USER MANAGEMENT 

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    profile_image = Column(String, nullable=True)
    location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    seller_profile = relationship("SellerProfile", back_populates="user", uselist=False)
    interactions = relationship("UserInteraction", back_populates="user")
    impact = relationship("UserImpact", back_populates="user", uselist=False)
    searches = relationship("SearchHistory", back_populates="user")
    cart_items = relationship("Cart", back_populates="user")
    orders = relationship("Orders", back_populates="buyer")

class SellerProfile(Base):
    __tablename__ = "seller_profiles"
    
    seller_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    rating = Column(Float, default=0.0)
    total_sales = Column(Integer, default=0)
    verified = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="seller_profile")
    products = relationship("Product", back_populates="seller")


# PRODUCT & MARKETPLACE 


class Product(Base):
    __tablename__ = "products"
    
    product_id = Column(Integer, primary_key=True, index=True)
    seller_id = Column(Integer, ForeignKey("seller_profiles.seller_id"))
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String)
    subcategory = Column(String)
    brand = Column(String)
    color = Column(String)
    size = Column(String)
    condition = Column(String)
    material = Column(String)
    price = Column(Float, nullable=False)
    image_url = Column(String)
    source_platform = Column(String)  # Zara, Mango, User Listing, Vintage Shop
    is_second_hand = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    seller = relationship("SellerProfile", back_populates="products")
    embedding = relationship("ProductEmbedding", back_populates="product", uselist=False)
    interactions = relationship("UserInteraction", back_populates="product")
    cart_entries = relationship("Cart", back_populates="product")
    order_entries = relationship("Orders", back_populates="product")


# AI SYSTEM (4-6)

class ProductEmbedding(Base):
    __tablename__ = "product_embeddings"
    
    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.product_id"), unique=True)
    embedding_vector = Column(Text, nullable=True)  # Store as JSON string or pickle
    model_name = Column(String, default="CLIP")  # CLIP, ResNet50, FineTunedFashionModel
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    product = relationship("Product", back_populates="embedding")

class UserInteraction(Base):
    __tablename__ = "user_interactions"
    
    interaction_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    interaction_type = Column(String)  # viewed, liked, purchased, searched, added_to_cart
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="interactions")
    product = relationship("Product", back_populates="interactions")

class UserPreferenceProfile(Base):
    __tablename__ = "user_preference_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    top_categories = Column(Text, nullable=True)  # JSON array
    preferred_colors = Column(Text, nullable=True)  # JSON array
    preferred_brands = Column(Text, nullable=True)  # JSON array
    avg_price_range = Column(String, nullable=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


# OUTFIT SYSTEM 


class OutfitCompatibility(Base):
    __tablename__ = "outfit_compatibility"
    
    id = Column(Integer, primary_key=True, index=True)
    source_category = Column(String, nullable=False)
    target_category = Column(String, nullable=False)
    score = Column(Float, default=0.0)
    rule_type = Column(String, default="ml")


# SEARCH SYSTEM (8)


class SearchHistory(Base):
    __tablename__ = "search_history"
    
    search_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    query_text = Column(String, nullable=True)
    query_type = Column(String, default="text")  # text, visual, voice
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="searches")


# IMPACT / TREE SYSTEM 


class UserImpact(Base):
    __tablename__ = "user_impacts"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), unique=True)
    total_water_saved_liters = Column(Float, default=0.0)
    total_co2_saved_kg = Column(Float, default=0.0)
    total_items_reused = Column(Integer, default=0)
    virtual_trees = Column(Integer, default=0)
    real_trees_earned = Column(Integer, default=0)
    impact_points = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="impact")

class ProductImpactFactors(Base):
    __tablename__ = "product_impact_factors"
    
    id = Column(Integer, primary_key=True, index=True)
    category = Column(String, unique=True)
    avg_water_liters = Column(Float, default=0.0)
    avg_co2_kg = Column(Float, default=0.0)
    avg_waste_kg = Column(Float, default=0.0)
    points_reward = Column(Integer, default=0)

class TreeMilestones(Base):
    __tablename__ = "tree_milestones"
    
    milestone_id = Column(Integer, primary_key=True, index=True)
    required_points = Column(Integer, nullable=False)
    virtual_tree_reward = Column(Integer, default=0)
    real_tree_reward = Column(Integer, default=0)
    badge_name = Column(String)


# CART & ORDERS (12-13)

class Cart(Base):
    __tablename__ = "carts"
    
    cart_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    added_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="cart_items")
    product = relationship("Product", back_populates="cart_entries")

class Orders(Base):
    __tablename__ = "orders"
    
    order_id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"))
    price = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, completed, cancelled
    ordered_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    buyer = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="order_entries")
class PlantProgress(Base):
    __tablename__ = "plant_progress"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    product_id = Column(Integer, ForeignKey("products.product_id"), nullable=True)
    water_level = Column(Integer, default=0)
    streak_days = Column(Integer, default=0)
    total_points = Column(Integer, default=0)
    last_watered_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    user = relationship("User", foreign_keys=[user_id])
    product = relationship("Product")
