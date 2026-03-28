from pydantic import BaseModel, Field


class CustomHoldingCreate(BaseModel):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=80)
    cost_price: float = Field(ge=0)
    shares: int = Field(gt=0)


class CustomPortfolioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    notes: str = Field(default='', max_length=1000)
    holdings: list[CustomHoldingCreate] = Field(min_length=1)
