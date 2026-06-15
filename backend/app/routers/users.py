from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import schemas, models, auth
from app.database import get_db
from app.services.username_service import make_unique_username, validate_username

router = APIRouter(prefix="/users", tags=["Users"])

@router.post("/register", response_model=schemas.UserResponse)
def register(user_data: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(
        (models.User.email == user_data.email)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already exists")

    if user_data.username:
        try:
            username = validate_username(user_data.username)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        username_exists = db.query(models.User).filter(
            models.User.username == username
        ).first()
        if username_exists:
            raise HTTPException(status_code=400, detail="Username already exists")
    else:
        used_usernames = {
            value
            for (value,) in db.query(models.User.username).all()
            if value
        }
        username = make_unique_username(user_data.name, used_usernames)

    hashed = auth.get_password_hash(user_data.password)
    db_user = models.User(
        name=user_data.name,
        username=username,
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


@router.put("/me", response_model=schemas.UserResponse)
def update_me(
    user_data: schemas.UserUpdate,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(get_db),
):
    update_data = user_data.model_dump(exclude_unset=True)

    if "username" in update_data:
        try:
            username = validate_username(update_data["username"])
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        existing = db.query(models.User).filter(
            models.User.username == username,
            models.User.user_id != current_user.user_id,
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Username already exists")
        update_data["username"] = username

    for field in ("name", "location", "bio"):
        if field in update_data and isinstance(update_data[field], str):
            update_data[field] = update_data[field].strip() or None

    if update_data.get("name") is None and "name" in update_data:
        raise HTTPException(status_code=400, detail="Name cannot be empty")

    for key, value in update_data.items():
        setattr(current_user, key, value)

    db.commit()
    db.refresh(current_user)
    return current_user
