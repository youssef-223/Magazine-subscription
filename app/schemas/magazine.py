from pydantic import BaseModel, Field

class MagazineCreate(BaseModel):
    name: str
    description: str
    base_price: float = Field(..., gt=0)


class MagazineUpdate(BaseModel):
    name: str
    description: str
    base_price: float = Field(..., gt=0)


class Magazine(BaseModel):
    id: int
    name: str
    description: str
    base_price: float

    class Config:
        from_attributes = True