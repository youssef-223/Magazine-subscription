from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from typing import List, Annotated
from schemas import *
import auth as auth
from auth import (
    authenticate_user,
    create_access_token,
    bcrypt_context,
    oauth2_bearer,
    create_refresh_token,
)
from fastapi_mail import FastMail, MessageSchema
from datetime import datetime, timedelta, UTC
from config import conf
import secrets
from jose import jwt


import models as models
from db.session import SessionLocal, engine
from sqlalchemy.orm import Session
from schemas.user import UserCreate, UserOut, UserLogin
from schemas.magazine import Magazine, MagazineCreate, MagazineUpdate
from schemas.plan import Plan, PlanCreate, PlanUpdate
from schemas.subscription import (
    Subscription,
    SubscriptionCreate,
    SubscriptionUpdate,
)
from schemas.tokens import Token

app = FastAPI()
app.include_router(auth.router)
models.Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Calculate subscription price
def calculate_price(magazine_base_price: float, plan_discount: float) -> float:
    return magazine_base_price * (1 - plan_discount)


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(auth.get_current_user)]


##############################################################################################################
# Users


# Register user
@app.post(
    "/users/register",
    response_model=UserOut,
    status_code=status.HTTP_200_OK,
    tags=["users"],
)
def register_user(user: UserCreate, db: db_dependency):
    db_user = (
        db.query(models.User)
        .filter(
            (models.User.username == user.username) | (models.User.email == user.email)
        )
        .first()
    )
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    new_user = models.User(
        username=user.username,
        hashed_password=bcrypt_context.hash(user.password),
        email=user.email,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"id": new_user.id, "username": new_user.username, "email": new_user.email}


# Login user
@app.post("/users/login", response_model=Token, tags=["users"])
async def login_user(login_request: UserLogin, db: db_dependency):
    user = authenticate_user(db, login_request.username, login_request.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
        )

    # Create tokens
    access_token = create_access_token(
        user.username, user.id, expires_delta=timedelta(minutes=15)
    )
    refresh_token = create_access_token(
        user.username, user.id, expires_delta=timedelta(days=7)
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


# Reset password
@app.post("/users/reset-password", status_code=status.HTTP_200_OK, tags=["users"])
async def reset_password(
    background_tasks: BackgroundTasks,
    db: db_dependency,
    email: str = Query(..., description="User's email address"),
):
    # Check if the user exists
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate a secure token
    reset_token = secrets.token_urlsafe(32)

    # Send email with token
    print(f"Mock email sent with token: {reset_token}")

    return {"message": "Password reset process initiated"}


# Deactivate a user
@app.delete(
    "/users/deactivate/{username}", status_code=status.HTTP_200_OK, tags=["users"]
)
def deactivate_user(username: str, db: db_dependency, current_user: user_dependency):
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    db.commit()
    return {"message": "User deactivated successfully"}


# Refresh token
@app.post("/users/token/refresh", response_model=Token, tags=["users"])
async def refresh_token(
    token: Annotated[str, Depends(oauth2_bearer)], db: db_dependency
):
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        # Verify user exists and is active
        user = (
            db.query(models.User)
            .filter(models.User.username == username, models.User.id == user_id)
            .first()
        )
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found or inactive",
            )

        # Create new tokens
        access_token = create_access_token(
            username, user_id, expires_delta=timedelta(minutes=15)
        )
        refresh_token = create_refresh_token(
            username, user_id, expires_delta=timedelta(days=7)
        )

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        }
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        )
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


# Get current user
@app.get(
    "/users/me", response_model=UserOut, status_code=status.HTTP_200_OK, tags=["users"]
)
def user(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication Failed")
    user_id = user["user_id"]
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    return {"id": db_user.id, "username": db_user.username, "email": db_user.email}


##############################################################################################################
# Magazines


# Get all magazines
@app.get("/magazines/", response_model=List[Magazine], tags=["magazines"])
def get_magazines(db: db_dependency):
    magazines = db.query(models.Magazine).all()
    if magazines is None:
        raise HTTPException(status_code=404, detail="Magazines not found")
    return magazines


# Create a new magazine
@app.post("/magazines/", response_model=Magazine, tags=["magazines"])
def create_magazine(magazine: MagazineCreate, db: db_dependency):
    db_magazine = models.Magazine(
        name=magazine.name,
        description=magazine.description,
        base_price=magazine.base_price,
    )
    db.add(db_magazine)
    db.commit()
    db.refresh(db_magazine)
    return db_magazine


# Get a specific magazine
@app.get("/magazines/{magazine_id}", response_model=Magazine, tags=["magazines"])
def get_magazine(magazine_id: int, db: db_dependency):
    magazine = (
        db.query(models.Magazine).filter(models.Magazine.id == magazine_id).first()
    )
    if magazine is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    return magazine


# Update a magazine
@app.put("/magazines/{magazine_id}", response_model=Magazine, tags=["magazines"])
def update_magazine(magazine_id: int, magazine: MagazineUpdate, db: db_dependency):
    db_magazine = (
        db.query(models.Magazine).filter(models.Magazine.id == magazine_id).first()
    )
    if db_magazine is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    db_magazine.name = magazine.name
    db_magazine.description = magazine.description
    db_magazine.base_price = magazine.base_price
    db.commit()
    db.refresh(db_magazine)
    return db_magazine


# Delete a magazine
@app.delete("/magazines/{magazine_id}", tags=["magazines"])
def delete_magazine(magazine_id: int, db: db_dependency):
    db_magazine = (
        db.query(models.Magazine).filter(models.Magazine.id == magazine_id).first()
    )
    if db_magazine is None:
        raise HTTPException(status_code=404, detail="Magazine not found")
    db.delete(db_magazine)
    db.commit()
    return {"message": "Magazine deleted successfully"}


##############################################################################################################
# Plans


# Get all plans
@app.get("/plans/", response_model=List[Plan], tags=["plans"])
def get_plans(db: db_dependency):
    plans = db.query(models.Plan).all()
    if plans is None:
        raise HTTPException(status_code=404, detail="Plans not found")
    return plans


# Create a new plan
@app.post("/plans/", response_model=Plan, tags=["plans"])
def create_plan(plan: PlanCreate, db: db_dependency):
    db_plan = models.Plan(
        title=plan.title,
        description=plan.description,
        renewal_period=plan.renewal_period,
        tier=plan.tier,
        discount=plan.discount,
    )
    db.add(db_plan)
    db.commit()
    db.refresh(db_plan)
    return db_plan


# Get a specific plan
@app.get("/plans/{plan_id}", response_model=Plan, tags=["plans"])
def get_plan(plan_id: int, db: db_dependency):
    plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan


# Update a plan
@app.put("/plans/{plan_id}", response_model=Plan, tags=["plans"])
def update_plan(plan_id: int, plan: PlanUpdate, db: db_dependency):
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    db_plan.title = plan.title
    db_plan.description = plan.description
    db_plan.renewal_period = plan.renewal_period
    db_plan.tier = plan.tier
    db_plan.discount = plan.discount
    db.commit()
    db.refresh(db_plan)
    return db_plan


# Delete a plan
@app.delete("/plans/{plan_id}", tags=["plans"])
def delete_plan(plan_id: int, db: db_dependency):
    db_plan = db.query(models.Plan).filter(models.Plan.id == plan_id).first()
    if db_plan is None:
        raise HTTPException(status_code=404, detail="Plan not found")
    db.delete(db_plan)
    db.commit()
    return {"message": "Plan deleted successfully"}


##############################################################################################################
# Subscriptions


# Get all subscriptions for the current user
@app.get("/subscriptions/", response_model=List[Subscription], tags=["subscriptions"])
def get_subscriptions(db: db_dependency, current_user: user_dependency):
    subscriptions = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id
            == current_user["user_id"]
            # models.Subscription.is_active == True,
        )
        .all()
    )
    return subscriptions


# Create a new subscription for the current user
@app.post("/subscriptions/", response_model=None, tags=["subscriptions"])
def create_subscription(
    subscription: SubscriptionCreate, db: db_dependency, current_user: user_dependency
):
    existing_subscription = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.user_id == current_user["user_id"],
            models.Subscription.magazine_id == subscription.magazine_id,
            models.Subscription.plan_id == subscription.plan_id,
            models.Subscription.is_active == True,
        )
        .first()
    )

    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Active subscription already exists",
        )

    magazine = (
        db.query(models.Magazine)
        .filter(models.Magazine.id == subscription.magazine_id)
        .first()
    )
    plan = db.query(models.Plan).filter(models.Plan.id == subscription.plan_id).first()

    if not magazine or not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Magazine or Plan not found"
        )

    price = calculate_price(magazine.base_price, plan.discount)

    new_subscription = models.Subscription(
        user_id=current_user["user_id"],
        magazine_id=subscription.magazine_id,
        plan_id=subscription.plan_id,
        price=price,
        renewal_date=subscription.renewal_date,
        is_active=True,
    )

    db.add(new_subscription)
    db.commit()
    db.refresh(new_subscription)
    return new_subscription


# Get a specific subscription for the current user
@app.get("/subscriptions/{id}", response_model=Subscription, tags=["subscriptions"])
def get_subscription(id: int, db: db_dependency):
    subscription = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.id
            == id
            #  models.Subscription.is_active == True
        )
        .first()
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )
    return subscription


# Update a subscription for the current user
@app.put(
    "/subscriptions/{subscription_id}",
    response_model=Subscription,
    tags=["subscriptions"],
)
def update_subscription(
    subscription_id: int,
    subscription_update: SubscriptionUpdate,
    db: db_dependency,
    current_user: user_dependency,
):
    subscription = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.id
            == subscription_id
            # models.Subscription.user_id == current_user["user_id"],
        )
        .first()
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    subscription.magazine_id = subscription_update.magazine_id
    subscription.plan_id = subscription_update.plan_id
    subscription.renewal_date = subscription_update.renewal_date

    db.commit()
    db.refresh(subscription)
    return subscription


# Deactivate a subscription for the current user
@app.delete(
    "/subscriptions/{subscription_id}",
    response_model=Subscription,
    tags=["subscriptions"],
)
def delete_subscription(
    subscription_id: int, db: db_dependency, current_user: user_dependency
):
    subscription = (
        db.query(models.Subscription)
        .filter(
            models.Subscription.id == subscription_id,
            models.Subscription.user_id == current_user["user_id"],
        )
        .first()
    )
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Subscription not found"
        )

    subscription.is_active = False
    db.commit()
    db.refresh(subscription)
    return subscription
