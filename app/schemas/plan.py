from pydantic import BaseModel, Field
from enum import Enum




class PlanCreate(BaseModel):
    title: str
    description: str
    renewal_period: int = Field(..., gt=0)
    tier: int
    discount: float = Field(..., ge=0, le=1)


class PlanUpdate(BaseModel):
    title: str
    description: str
    renewal_period: int = Field(..., gt=0)
    tier: int
    discount: float = Field(..., ge=0, le=1)


class Plan(BaseModel):
    id: int
    title: str
    description: str
    renewal_period: int
    tier: int
    discount: float = Field(..., ge=0, le=1)

    class Config:
        from_attributes = True


class PlanEnum(Enum):
    SILVER = {
        "title": "Silver Plan",
        "description": "Basic plan which renews monthly",
        "renewal_period": 1,
        "tier": 1,
        "discount": 0.0,
    }
    GOLD = {
        "title": "Gold Plan",
        "description": "Standard plan which renews every 3 months",
        "renewal_period": 3,
        "tier": 2,
        "discount": 0.05,
    }
    PLATINUM = {
        "title": "Platinum Plan",
        "description": "Premium plan which renews every 6 months",
        "renewal_period": 6,
        "tier": 3,
        "discount": 0.10,
    }
    DIAMOND = {
        "title": "Diamond Plan",
        "description": "Exclusive plan which renews annually",
        "renewal_period": 12,
        "tier": 4,
        "discount": 0.25,
    }