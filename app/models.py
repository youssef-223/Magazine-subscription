from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Date
from sqlalchemy.orm import relationship
from db.base import Base
from sqlalchemy.orm import validates
from fastapi import HTTPException

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=True)

    subscriptions = relationship("Subscription", back_populates="user")
class Magazine(Base):
    __tablename__ = 'magazines'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    base_price = Column(Float, nullable=False)

    subscriptions = relationship("Subscription", back_populates="magazine")

class Plan(Base):
    __tablename__ = 'plans'

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    renewal_period = Column(Integer, nullable=False)
    tier = Column(Integer, nullable=False)
    discount = Column(Float, nullable=False)

    subscriptions = relationship("Subscription", back_populates="plan")

class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)  # Add ForeignKey here
    magazine_id = Column(Integer, ForeignKey('magazines.id'), nullable=False)
    plan_id = Column(Integer, ForeignKey('plans.id'), nullable=False)
    price = Column(Float, nullable=False)
    renewal_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="subscriptions")  # Add relationship here
    magazine = relationship("Magazine", back_populates="subscriptions")
    plan = relationship("Plan", back_populates="subscriptions")

    @validates("price")
    def validate_price(self, key, price):
        if price <= 0:
            raise HTTPException(status_code=422, detail="Price must be greater than zero")
        return price