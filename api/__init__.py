# api/__init__.py
from .portfolio_routes import portfolio_router
from .monitor_routes import monitor_router
from .admin_routes import admin_router
from .tools_routes import tools_router
from .xueqiu_routes import xueqiu_router

__all__ = ['portfolio_router', 'monitor_router', 'admin_router', 'tools_router', 'xueqiu_router']