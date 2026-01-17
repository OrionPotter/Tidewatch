# api/portfolio_routes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from repositories.portfolio_repository import StockRepository
from services.portfolio_service import PortfolioService
from datetime import datetime

portfolio_router = APIRouter()


class StockCreate(BaseModel):
    code: str
    name: str
    cost_price: float
    shares: int


class StockUpdate(BaseModel):
    name: Optional[str] = None
    cost_price: Optional[float] = None
    shares: Optional[int] = None


@portfolio_router.get('')
def get_portfolio():
    """获取投资组合数据"""
    try:
        rows, summary = PortfolioService.get_portfolio_data()
        return {
            'status': 'success',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'rows': rows,
            'summary':  summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@portfolio_router.post('')
def create_stock(data: StockCreate):
    """创建股票"""
    success, msg = StockRepository.add(
        data.code,
        data.name,
        data.cost_price,
        data.shares
    )
    
    return {
        'status':  'success' if success else 'error',
        'message': msg
    }


@portfolio_router.put('/{code}')
def update_stock(code: str, data: StockUpdate):
    """更新股票"""
    success = StockRepository.update(
        code,
        data.name,
        data.cost_price,
        data.shares
    )
    
    return {
        'status':  'success' if success else 'error',
        'message':  '更新成功' if success else '更新失败'
    }


@portfolio_router.delete('/{code}')
def delete_stock(code: str):
    """删除股票"""
    success = StockRepository.delete(code)
    
    return {
        'status': 'success' if success else 'error',
        'message': '删除成功' if success else '删除失败'
    }