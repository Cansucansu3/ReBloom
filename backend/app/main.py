from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import users, products, cart, checkout, leaderboard, interactions, impact, search, outfit, gamification, recommendations

Base.metadata.create_all(bind=engine)

app = FastAPI(title="ReBloom API", description="Sustainable Circular Fashion Platform", version="4.0.0")

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
