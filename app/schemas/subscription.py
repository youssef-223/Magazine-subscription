from pydantic import BaseModel, Field
from datetime import date


class SubscriptionCreate(BaseModel):
    user_id: int
    magazine_id: int
    plan_id: int
    renewal_date: date

    class Config:
        from_attributes = True


class SubscriptionUpdate(BaseModel):
    user_id: int
    magazine_id: int
    plan_id: int
    renewal_date: date


class Subscription(BaseModel):
    id: int
    user_id: int
    magazine_id: int
    plan_id: int
    renewal_date: date
    price: float = Field(..., gt=0)
    is_active: bool

    class Config:
        from_attributes = True

