from dataclasses import dataclass


@dataclass
class CustomPortfolio:
    id: int
    name: str
    notes: str | None
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'notes': self.notes,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class CustomPortfolioHolding:
    id: int
    portfolio_id: int
    code: str
    name: str
    cost_price: float
    shares: int
    created_at: str
    updated_at: str

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'portfolio_id': self.portfolio_id,
            'code': self.code,
            'name': self.name,
            'cost_price': round(self.cost_price, 2),
            'shares': self.shares,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
