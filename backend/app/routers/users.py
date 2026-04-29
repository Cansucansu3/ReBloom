from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, models, auth
from app.database import get_db

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if user exists
    existing = db.query(models.User).filter(
        (models.User.email == user_data.email)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create user
    hashed = auth.get_password_hash(user_data.password)
    db_user = models.User(
        name=user_data.name,
        email=user_data.email,
        password_hash=hashed,
        location=user_data.location
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create seller profile (optional, can be upgraded later)
    seller_profile = models.SellerProfile(
        user_id=db_user.user_id,
        verified=False
    )
    db.add(seller_profile)
    
    # Create user impact profile
    impact = models.UserImpact(user_id=db_user.user_id)
    db.add(impact)
    
    db.commit()
    
    return db_user

@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == user_data.email).first()
    if not user or not auth.verify_password(user_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = auth.create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=schemas.UserResponse)
def get_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user
