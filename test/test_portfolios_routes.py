from unittest.mock import AsyncMock, patch


class TestPortfolioRoutes:
    def test_get_custom_portfolios_success(self, client):
        payload = {
            'overview': {
                'portfolio_count': 1,
                'holding_count': 2,
                'total_cost': 10000.0,
                'total_market_value': 10800.0,
                'total_profit': 800.0,
                'total_profit_rate': 8.0,
            },
            'portfolios': [
                {
                    'id': 1,
                    'name': '趋势仓',
                    'notes': '主仓位',
                    'updated_at': '2026-03-28 10:00:00',
                    'created_at': '2026-03-20 10:00:00',
                    'summary': {
                        'cost': 10000.0,
                        'market_value': 10800.0,
                        'profit': 800.0,
                        'profit_rate': 8.0,
                        'position_count': 2,
                    },
                    'holdings': [],
                }
            ],
        }

        with patch('services.custom_portfolio_service.CustomPortfolioService.get_portfolio_page_data', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = payload

            response = client.get('/api/portfolios')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data']['overview']['portfolio_count'] == 1
            assert data['data']['portfolios'][0]['name'] == '趋势仓'

    def test_create_custom_portfolio_success(self, client):
        body = {
            'name': '防守仓',
            'notes': '低波动',
            'holdings': [
                {'code': 'sh600519', 'name': '贵州茅台', 'cost_price': 1500.0, 'shares': 100}
            ],
        }

        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.create_portfolio', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = 9

            response = client.post('/api/portfolios', json=body)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['portfolio_id'] == 9
            mock_create.assert_called_once()

    def test_add_custom_holding_success(self, client):
        body = {'code': 'sz000001', 'name': '平安银行', 'cost_price': 12.5, 'shares': 200}

        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.add_holding', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, 'Holding added')

            response = client.post('/api/portfolios/3/holdings', json=body)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            mock_add.assert_called_once_with(3, 'sz000001', '平安银行', 12.5, 200)

    def test_get_custom_portfolio_detail_success(self, client):
        payload = {
            'id': 3,
            'name': '防守仓',
            'summary': {
                'cost': 1000.0,
                'market_value': 1100.0,
                'profit': 100.0,
                'profit_rate': 10.0,
                'position_count': 1,
            },
            'holdings': [],
        }

        with patch('services.custom_portfolio_service.CustomPortfolioService.get_portfolio_detail', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = payload

            response = client.get('/api/portfolios/3')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data']['id'] == 3
            mock_get.assert_called_once_with(3)

    def test_delete_custom_portfolio_success(self, client):
        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.delete_portfolio', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            response = client.delete('/api/portfolios/5')

            assert response.status_code == 200
            assert response.json()['status'] == 'success'
            mock_delete.assert_called_once_with(5)

    def test_delete_custom_holding_success(self, client):
        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.delete_holding', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True

            response = client.delete('/api/portfolios/5/holdings/11')

            assert response.status_code == 200
            assert response.json()['status'] == 'success'
            mock_delete.assert_called_once_with(5, 11)
