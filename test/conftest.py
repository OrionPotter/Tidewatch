import pytest
import asyncio
from fastapi.testclient import TestClient
from fastapi import FastAPI
from unittest.mock import AsyncMock, patch
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 配置 pytest-asyncio
pytest_plugins = ('pytest_asyncio',)


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_db_conn():
    """模拟数据库连接"""
    mock_conn = AsyncMock()
    mock_conn.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_conn.__aexit__ = AsyncMock(return_value=None)
    return mock_conn


@pytest.fixture
def client(mock_db_conn):
    """创建测试客户端"""
    # Mock 所有可能的依赖
    with patch('utils.db.init_db_pool', new_callable=AsyncMock), \
         patch('utils.db.close_db_pool', new_callable=AsyncMock), \
         patch('utils.db.get_db_conn', return_value=mock_db_conn):
        
        # 创建一个新的 FastAPI app，不带 lifespan
        app = FastAPI()
        
        # 注册路由
        from api.portfolio_routes import portfolio_router
        from api.monitor_routes import monitor_router
        from api.admin_routes import admin_router
        from api.tools_routes import tools_router
        from api.xueqiu_routes import xueqiu_router
        from api.stock_list_routes import stock_list_router
        from api.industry_board_routes import industry_board_router

        app.include_router(portfolio_router, prefix='/api/portfolio', tags=['portfolio'])
        app.include_router(monitor_router, prefix='/api/monitor', tags=['monitor'])
        app.include_router(admin_router, prefix='/api/admin', tags=['admin'])
        app.include_router(tools_router, prefix='/api/tools', tags=['tools'])
        app.include_router(xueqiu_router, prefix='/api/xueqiu', tags=['xueqiu'])
        app.include_router(stock_list_router, prefix='/api/stock-list', tags=['stock-list'])
        app.include_router(industry_board_router, prefix='/api/industry-board', tags=['industry-board'])

        with TestClient(app) as test_client:
            yield test_client