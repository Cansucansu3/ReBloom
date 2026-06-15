from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from sqlalchemy import inspect, text
from app.database import engine, Base
from app.services.occasion_service import infer_occasion
from app.services.username_service import make_unique_username, normalize_username
from app.routers import users, products, cart, checkout, leaderboard, interactions, impact, search, outfit, gamification, recommendations, profiles


def ensure_product_occasion_column():
    columns = {column["name"] for column in inspect(engine).get_columns("products")}
    if "occasion" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE products ADD COLUMN occasion VARCHAR")
            )

    with engine.begin() as connection:
        rows = connection.execute(
            text(
                """
                SELECT product_id, title, description, category, subcategory
                FROM products
                WHERE occasion IS NULL OR TRIM(occasion) = ''
                """
            )
        ).mappings()
        updates = [
            {
                "product_id": row["product_id"],
                "occasion": infer_occasion(
                    row["title"],
                    row["description"],
                    row["category"],
                    row["subcategory"],
                ),
            }
            for row in rows
        ]
        if updates:
            connection.execute(
                text(
                    """
                    UPDATE products
                    SET occasion = :occasion
                    WHERE product_id = :product_id
                    """
                ),
                updates,
            )


def ensure_user_username_column():
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    if "username" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE users ADD COLUMN username VARCHAR"))

    with engine.begin() as connection:
        rows = connection.execute(
            text(
                """
                SELECT user_id, name, email, username
                FROM users
                ORDER BY user_id
                """
            )
        ).mappings().all()

        used_usernames = set()
        updates = []
        for row in rows:
            current = normalize_username(row["username"])
            source = current or row["name"] or str(row["email"]).split("@", 1)[0]
            username = make_unique_username(source, used_usernames)
            if row["username"] != username:
                updates.append({"user_id": row["user_id"], "username": username})

        if updates:
            connection.execute(
                text(
                    """
                    UPDATE users
                    SET username = :username
                    WHERE user_id = :user_id
                    """
                ),
                updates,
            )

        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS ix_users_username
                ON users (username)
                """
            )
        )


def ensure_user_profile_columns():
    columns = {column["name"] for column in inspect(engine).get_columns("users")}
    with engine.begin() as connection:
        if "profile_image" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN profile_image VARCHAR"))
        if "bio" not in columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN bio TEXT"))


Base.metadata.create_all(bind=engine)
ensure_user_username_column()
ensure_user_profile_columns()
ensure_product_occasion_column()

app = FastAPI(title="ReBloom API", description="Sustainable Circular Fashion Platform", version="4.0.0")

PRODUCT_IMAGES_DIR = Path(__file__).resolve().parents[1] / "static" / "product_images"
TREES_DIR = Path(__file__).resolve().parents[1] / "static" / "trees"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(leaderboard.router)
app.include_router(interactions.router)
app.include_router(impact.router)
app.include_router(search.router)
app.include_router(outfit.router)
app.include_router(gamification.router)
app.include_router(recommendations.router)
app.include_router(recommendations.product_router)
app.include_router(profiles.router)
app.mount(
    "/static/product_images",
    StaticFiles(directory=str(PRODUCT_IMAGES_DIR), check_dir=False),
    name="product_images",
)
app.mount(
    "/static/trees",
    StaticFiles(directory=str(TREES_DIR), check_dir=False),
    name="trees",
)

@app.get("/")
def root():
    return {
        "message": "Welcome to ReBloom API",
        "version": "4.0.0",
        "features": [
            "User authentication",
            "Product management",
            "Shopping cart",
            "Checkout with water savings",
            "Leaderboard",
            "View/Like tracking",
            "Impact tracking with trees",
            "Search history",
            "Outfit suggestions",
            "Gamification - Water your tree daily!"
        ]
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
