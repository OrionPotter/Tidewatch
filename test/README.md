# 单元测试

本项目包含针对所有 GET 接口的单元测试。

## 测试文件结构

```
test/
├── __init__.py                    # 测试包初始化文件
├── conftest.py                    # pytest 配置和 fixtures
├── test_admin_routes.py           # admin_routes GET 接口测试
├── test_stock_list_routes.py      # stock_list_routes GET 接口测试
├── test_monitor_routes.py         # monitor_routes GET 接口测试
├── test_tools_routes.py           # tools_routes GET 接口测试
├── test_xueqiu_routes.py          # xueqiu_routes GET 接口测试
├── test_portfolio_routes.py       # portfolio_routes GET 接口测试
└── test_industry_board_routes.py  # industry_board_routes GET 接口测试
```

## 安装测试依赖

```bash
pip install pytest pytest-asyncio
```

## 运行测试

### 运行所有测试

```bash
pytest
```

### 运行指定测试文件

```bash
pytest test/test_admin_routes.py
```

### 运行指定测试类

```bash
pytest test/test_admin_routes.py::TestAdminRoutes
```

### 运行指定测试方法

```bash
pytest test/test_admin_routes.py::TestAdminRoutes::test_list_stocks_success
```

### 显示详细输出

```bash
pytest -v
```

### 显示打印语句

```bash
pytest -s
```

## 测试覆盖的接口

| 模块 | GET 接口 |
|------|----------|
| admin_routes | `/api/admin/stocks`, `/api/admin/monitor-stocks`, `/api/admin/xueqiu-cubes` |
| stock_list_routes | `/api/stock-list`, `/api/stock-list/count`, `/api/stock-list/{code}`, `/api/stock-list/search/{keyword}` |
| monitor_routes | `/api/monitor`, `/api/monitor/stocks` |
| tools_routes | `/api/tools/export-kline/stocks` |
| xueqiu_routes | `/api/xueqiu`, `/api/xueqiu/{cube_symbol}` |
| portfolio_routes | `/api/portfolio` |
| industry_board_routes | `/api/industry-board/latest` |