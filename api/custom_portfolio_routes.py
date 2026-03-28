from fastapi import APIRouter, HTTPException

from api.route_helpers import bool_status_response
from repositories.custom_portfolio_repository import CustomPortfolioRepository
from schemas.custom_portfolio import CustomHoldingCreate, CustomPortfolioCreate
from services.custom_portfolio_service import CustomPortfolioService
from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('custom_portfolio_routes')

custom_portfolio_router = APIRouter()


@custom_portfolio_router.get('')
async def get_custom_portfolios():
    try:
        data = await CustomPortfolioService.get_portfolio_page_data()
        return success_response(timestamp=current_timestamp(), data=data, clean_nan=True)
    except Exception as exc:
        logger.error(f'GET /api/portfolios failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@custom_portfolio_router.get('/{portfolio_id}')
async def get_custom_portfolio_detail(portfolio_id: int):
    try:
        data = await CustomPortfolioService.get_portfolio_detail(portfolio_id)
        if not data:
            raise HTTPException(status_code=404, detail='Portfolio not found')
        return success_response(timestamp=current_timestamp(), data=data, clean_nan=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f'GET /api/portfolios/{portfolio_id} failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@custom_portfolio_router.post('')
async def create_custom_portfolio(payload: CustomPortfolioCreate):
    try:
        portfolio_id = await CustomPortfolioRepository.create_portfolio(
            payload.name.strip(),
            payload.notes.strip(),
            [
                {
                    'code': item.code.strip().lower(),
                    'name': item.name.strip(),
                    'cost_price': item.cost_price,
                    'shares': item.shares,
                }
                for item in payload.holdings
            ],
        )
        return success_response(
            timestamp=current_timestamp(),
            message='Portfolio created',
            portfolio_id=portfolio_id,
        )
    except Exception as exc:
        logger.error(f'POST /api/portfolios failed: {exc}')
        raise HTTPException(status_code=500, detail=str(exc))


@custom_portfolio_router.post('/{portfolio_id}/holdings')
async def add_custom_holding(portfolio_id: int, payload: CustomHoldingCreate):
    success, message = await CustomPortfolioRepository.add_holding(
        portfolio_id,
        payload.code.strip().lower(),
        payload.name.strip(),
        payload.cost_price,
        payload.shares,
    )
    return bool_status_response(success, message, message)


@custom_portfolio_router.delete('/{portfolio_id}')
async def delete_custom_portfolio(portfolio_id: int):
    success = await CustomPortfolioRepository.delete_portfolio(portfolio_id)
    return bool_status_response(success, 'Portfolio deleted', 'Portfolio delete failed')


@custom_portfolio_router.delete('/{portfolio_id}/holdings/{holding_id}')
async def delete_custom_holding(portfolio_id: int, holding_id: int):
    success = await CustomPortfolioRepository.delete_holding(portfolio_id, holding_id)
    return bool_status_response(success, 'Holding deleted', 'Holding delete failed')
