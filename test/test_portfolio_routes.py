import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestPortfolioRoutes:
    """测试 portfolio_routes 的接口"""

    # ========== GET 接口测试 ==========

    def test_get_portfolio_success(self, client):
        """测试成功获取投资组合数据"""
        mock_rows = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'cost_price': 10.5,
                'shares': 1000,
                'current_price': 12.0,
                'market_value': 12000.0,
                'profit_loss': 1500.0,
                'profit_loss_pct': 14.29
            }
        ]

        mock_summary = {
            'total_cost': 10500.0,
            'total_market_value': 12000.0,
            'total_profit_loss': 1500.0,
            'total_profit_loss_pct': 14.29
        }

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (mock_rows, mock_summary)

            response = client.get('/api/portfolio')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert 'timestamp' in data
            assert len(data['rows']) == 1
            assert data['summary']['total_cost'] == 10500.0
            mock_get_data.assert_called_once()

    def test_get_portfolio_empty(self, client):
        """测试获取投资组合数据，没有持仓时"""
        mock_rows = []
        mock_summary = {
            'total_cost': 0,
            'total_market_value': 0,
            'total_profit_loss': 0,
            'total_profit_loss_pct': 0
        }

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (mock_rows, mock_summary)

            response = client.get('/api/portfolio')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['rows'] == []
            assert data['summary']['total_cost'] == 0

    def test_get_portfolio_multiple_stocks(self, client):
        """测试获取投资组合数据，多只股票时"""
        mock_rows = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'cost_price': 10.5,
                'shares': 1000,
                'current_price': 12.0,
                'market_value': 12000.0
            },
            {
                'code': 'sz000001',
                'name': '平安银行',
                'cost_price': 15.0,
                'shares': 500,
                'current_price': 16.5,
                'market_value': 8250.0
            }
        ]

        mock_summary = {
            'total_cost': 18000.0,
            'total_market_value': 20250.0,
            'total_profit_loss': 2250.0,
            'total_profit_loss_pct': 12.5
        }

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (mock_rows, mock_summary)

            response = client.get('/api/portfolio')

            assert response.status_code == 200
            data = response.json()
            assert len(data['rows']) == 2
            assert data['summary']['total_market_value'] == 20250.0

    def test_get_portfolio_with_nan_values(self, client):
        """测试获取投资组合数据，包含 NaN 值时"""
        import numpy as np
        mock_rows = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'cost_price': 10.5,
                'shares': 1000,
                'current_price': np.nan,  # NaN 值
                'market_value': 12000.0
            }
        ]

        mock_summary = {
            'total_cost': 10500.0,
            'total_market_value': 12000.0,
            'total_profit_loss': 1500.0,
            'total_profit_loss_pct': np.nan  # NaN 值
        }

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (mock_rows, mock_summary)

            response = client.get('/api/portfolio')

            assert response.status_code == 200
            data = response.json()
            # NaN 值应该被清理为 None
            assert data['rows'][0]['current_price'] is None

    # ========== POST/PUT/DELETE 接口测试 ==========

    def test_create_stock_success(self, client):
        """测试成功创建股票"""
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'cost_price': 10.5,
            'shares': 1000
        }

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, '创建成功')

            response = client.post('/api/portfolio', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '创建成功'
            mock_add.assert_called_once_with('sh600000', '浦发银行', 10.5, 1000)

    def test_create_stock_failure(self, client):
        """测试创建股票失败"""
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'cost_price': 10.5,
            'shares': 1000
        }

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (False, '股票已存在')

            response = client.post('/api/portfolio', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert data['message'] == '股票已存在'

    def test_update_stock_all_fields(self, client):
        """测试更新股票所有字段"""
        stock_data = {
            'name': '浦发银行',
            'cost_price': 11.0,
            'shares': 1500
        }

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True

            response = client.put('/api/portfolio/sh600000', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '更新成功'
            mock_update.assert_called_once_with('sh600000', '浦发银行', 11.0, 1500)

    def test_update_stock_partial_fields(self, client):
        """测试更新股票部分字段"""
        stock_data = {
            'cost_price': 12.0
        }

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True

            response = client.put('/api/portfolio/sh600000', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            # 验证只更新提供的字段
            call_args = mock_update.call_args
            assert call_args[0][1] is None  # name
            assert call_args[0][2] == 12.0  # cost_price
            assert call_args[0][3] is None  # shares

    def test_update_stock_failure(self, client):
        """测试更新股票失败"""
        stock_data = {
            'name': '浦发银行',
            'cost_price': 11.0,
            'shares': 1500
        }

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = False

            response = client.put('/api/portfolio/sh600000', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert data['message'] == '更新失败'

    def test_delete_stock_success(self, client):
        """测试成功删除股票"""
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            response = client.delete('/api/portfolio/sh600000')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '删除成功'
            mock_delete.assert_called_once_with('sh600000')

    def test_delete_stock_failure(self, client):
        """测试删除股票失败"""
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False

            response = client.delete('/api/portfolio/sh600000')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert data['message'] == '删除失败'