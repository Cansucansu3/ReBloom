-- 1. Users
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR NOT NULL,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    profile_image VARCHAR,
    location VARCHAR,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- 2. SellerProfile
CREATE TABLE seller_profiles (
    seller_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    rating FLOAT DEFAULT 0,
    total_sales INTEGER DEFAULT 0,
    verified BOOLEAN DEFAULT 0,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 3. Product
CREATE TABLE products (
    product_id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    title VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR,
    subcategory VARCHAR,
    brand VARCHAR,
    color VARCHAR,
    size VARCHAR,
    condition VARCHAR,
    material VARCHAR,
    price FLOAT NOT NULL,
    image_url VARCHAR,
    source_platform VARCHAR,
    is_second_hand BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1,
    FOREIGN KEY (seller_id) REFERENCES seller_profiles(seller_id)
);

-- 4. ProductEmbedding
CREATE TABLE product_embeddings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER UNIQUE NOT NULL,
    embedding_vector TEXT,
    model_name VARCHAR DEFAULT 'CLIP',
    updated_at TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 5. UserInteraction
CREATE TABLE user_interactions (
    interaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    interaction_type VARCHAR NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 6. UserPreferenceProfile
CREATE TABLE user_preference_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    top_categories TEXT,
    preferred_colors TEXT,
    preferred_brands TEXT,
    avg_price_range VARCHAR,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 7. OutfitCompatibility
CREATE TABLE outfit_compatibility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_category VARCHAR NOT NULL,
    target_category VARCHAR NOT NULL,
    score FLOAT DEFAULT 0,
    rule_type VARCHAR DEFAULT 'ml'
);

-- 8. SearchHistory
CREATE TABLE search_history (
    search_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    query_text VARCHAR,
    query_type VARCHAR DEFAULT 'text',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 9. UserImpact
CREATE TABLE user_impacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    total_water_saved_liters FLOAT DEFAULT 0,
    total_co2_saved_kg FLOAT DEFAULT 0,
    total_items_reused INTEGER DEFAULT 0,
    virtual_trees INTEGER DEFAULT 0,
    real_trees_earned INTEGER DEFAULT 0,
    impact_points INTEGER DEFAULT 0,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- 10. ProductImpactFactors
CREATE TABLE product_impact_factors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR UNIQUE NOT NULL,
    avg_water_liters FLOAT DEFAULT 0,
    avg_co2_kg FLOAT DEFAULT 0,
    avg_waste_kg FLOAT DEFAULT 0,
    points_reward INTEGER DEFAULT 0
);

-- 11. TreeMilestones
CREATE TABLE tree_milestones (
    milestone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    required_points INTEGER NOT NULL,
    virtual_tree_reward INTEGER DEFAULT 0,
    real_tree_reward INTEGER DEFAULT 0,
    badge_name VARCHAR
);

-- 12. Cart
CREATE TABLE carts (
    cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- 13. Orders
CREATE TABLE orders (
    order_id INTEGER PRIMARY KEY AUTOINCREMENT,
    buyer_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    price FLOAT NOT NULL,
    status VARCHAR DEFAULT 'pending',
    ordered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (buyer_id) REFERENCES users(user_id),
    FOREIGN KEY (product_id) REFERENCES products(product_id)
);

-- INDEXES
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_products_category ON products(category);
CREATE INDEX idx_products_seller ON products(seller_id);
CREATE INDEX idx_interactions_user ON user_interactions(user_id);
CREATE INDEX idx_interactions_product ON user_interactions(product_id);
CREATE INDEX idx_search_user ON search_history(user_id);
CREATE INDEX idx_cart_user ON carts(user_id);
CREATE INDEX idx_orders_buyer ON orders(buyer_id);

-- INSERT DEFAULT IMPACT FACTORS
INSERT INTO product_impact_factors (category, avg_water_liters, avg_co2_kg, points_reward) VALUES
('jeans', 7500, 33, 100),
('tshirt', 2700, 8, 50),
('trench coat', 5000, 20, 80),
('dress', 4000, 15, 70),
('jacket', 6000, 25, 90),
('shirt', 3000, 10, 60);

-- INSERT TREE MILESTONES
INSERT INTO tree_milestones (required_points, virtual_tree_reward, real_tree_reward, badge_name) VALUES
(100, 1, 0, 'Seed Saver'),
(1000, 3, 0, 'Tree Planter'),
(5000, 5, 1, 'Forest Maker'),
(10000, 10, 2, 'Eco Warrior');
