from unittest.mock import AsyncMock, patch

import numpy as np


class TestPortfolioRoutes:
    def test_get_portfolio_success(self, client):
        mock_rows = [{'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000, 'current_price': 12.0, 'market_value': 12000.0}]
        mock_summary = {'total_cost': 10500.0, 'total_market_value': 12000.0, 'total_profit_loss': 1500.0, 'total_profit_loss_pct': 14.29}

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (mock_rows, mock_summary)
            response = client.get('/api/portfolio')

        assert response.status_code == 200
        assert response.json()['summary']['total_cost'] == 10500.0

    def test_get_portfolio_empty(self, client):
        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = ([], {'total_cost': 0, 'total_market_value': 0, 'total_profit_loss': 0, 'total_profit_loss_pct': 0})
            response = client.get('/api/portfolio')

        assert response.status_code == 200
        assert response.json()['rows'] == []

    def test_get_portfolio_multiple_stocks(self, client):
        rows = [
            {'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000, 'current_price': 12.0, 'market_value': 12000.0},
            {'code': 'sz000001', 'name': 'PingAn', 'cost_price': 15.0, 'shares': 500, 'current_price': 16.5, 'market_value': 8250.0},
        ]
        summary = {'total_cost': 18000.0, 'total_market_value': 20250.0, 'total_profit_loss': 2250.0, 'total_profit_loss_pct': 12.5}

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (rows, summary)
            response = client.get('/api/portfolio')

        assert response.status_code == 200
        assert len(response.json()['rows']) == 2

    def test_get_portfolio_with_nan_values(self, client):
        rows = [{'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000, 'current_price': np.nan, 'market_value': 12000.0}]
        summary = {'total_cost': 10500.0, 'total_market_value': 12000.0, 'total_profit_loss': 1500.0, 'total_profit_loss_pct': np.nan}

        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = (rows, summary)
            response = client.get('/api/portfolio')

        assert response.status_code == 200
        assert response.json()['rows'][0]['current_price'] is None

    def test_get_portfolio_failure(self, client):
        with patch('services.portfolio_service.PortfolioService.get_portfolio_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.side_effect = RuntimeError('portfolio failed')
            response = client.get('/api/portfolio')

        assert response.status_code == 500

    def test_create_stock_success(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, 'created')
            response = client.post('/api/portfolio', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_create_stock_failure(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (False, 'exists')
            response = client.post('/api/portfolio', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_update_stock_all_fields(self, client):
        stock_data = {'name': 'PF Bank', 'cost_price': 11.0, 'shares': 1500}

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/portfolio/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_update_stock_partial_fields(self, client):
        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/portfolio/sh600000', json={'cost_price': 12.0})

        assert response.status_code == 200
        args = mock_update.call_args[0]
        assert args[1] is None and args[2] == 12.0 and args[3] is None

    def test_update_stock_failure(self, client):
        stock_data = {'name': 'PF Bank', 'cost_price': 11.0, 'shares': 1500}

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = False
            response = client.put('/api/portfolio/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_delete_stock_success(self, client):
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/portfolio/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_delete_stock_failure(self, client):
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/api/portfolio/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'
