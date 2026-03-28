from fastapi import APIRouter

from api.route_helpers import bool_status_response, list_response
from repositories.monitor_repository import MonitorStockRepository
from repositories.portfolio_repository import StockRepository
from schemas.admin import (
    AdminMonitorStockCreate,
    AdminMonitorStockUpdate,
    AdminStockCreate,
    AdminStockUpdate,
    ToggleEnabled,
)
from utils.logger import get_logger

logger = get_logger('admin_routes')

admin_router = APIRouter()


@admin_router.get('/stocks')
async def list_stocks():
    logger.info('GET /api/admin/stocks')
    stocks = await StockRepository.get_all()
    return list_response(stocks)


@admin_router.post('/stocks')
async def create_stock(data: AdminStockCreate):
    success, msg = await StockRepository.add(data.code, data.name, data.cost_price, data.shares)
    return bool_status_response(success, msg, msg)


@admin_router.put('/stocks/{code}')
async def update_stock(code: str, data: AdminStockUpdate):
    success = await StockRepository.update(code, data.name, data.cost_price, data.shares)
    return bool_status_response(success, '更新成功', '更新失败')


@admin_router.delete('/stocks/{code}')
async def delete_stock(code: str):
    success = await StockRepository.delete(code)
    return bool_status_response(success, '删除成功', '删除失败')


@admin_router.get('/monitor-stocks')
async def list_monitor_stocks():
    logger.info('GET /api/admin/monitor-stocks')
    stocks = await MonitorStockRepository.get_all()
    return list_response(stocks)


@admin_router.post('/monitor-stocks')
async def create_monitor_stock(data: AdminMonitorStockCreate):
    success, msg = await MonitorStockRepository.add(
        data.code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return bool_status_response(success, msg, msg)


@admin_router.put('/monitor-stocks/{code}')
async def update_monitor_stock(code: str, data: AdminMonitorStockUpdate):
    success = await MonitorStockRepository.update(
        code,
        data.name,
        data.timeframe,
        data.reasonable_pe_min,
        data.reasonable_pe_max,
    )
    return bool_status_response(success, '更新成功', '更新失败')


@admin_router.delete('/monitor-stocks/{code}')
async def delete_monitor_stock(code: str):
    success = await MonitorStockRepository.delete(code)
    return bool_status_response(success, '删除成功', '删除失败')


@admin_router.post('/monitor-stocks/{code}/toggle')
async def toggle_monitor_stock(code: str, data: ToggleEnabled):
    success = await MonitorStockRepository.toggle_enabled(code, data.enabled)
    return bool_status_response(success, '操作成功', '操作失败')
