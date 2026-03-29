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
                    'name': 'Growth',
                    'notes': 'Core',
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
        assert response.json()['data']['overview']['portfolio_count'] == 1

    def test_get_custom_portfolios_failure(self, client):
        with patch('services.custom_portfolio_service.CustomPortfolioService.get_portfolio_page_data', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = RuntimeError('portfolio page failed')
            response = client.get('/api/portfolios')

        assert response.status_code == 500
        assert response.json()['detail'] == 'portfolio page failed'

    def test_create_custom_portfolio_success(self, client):
        body = {
            'name': 'Defensive',
            'notes': 'Low beta',
            'holdings': [{'code': 'sh600519', 'name': 'Moutai', 'cost_price': 1500.0, 'shares': 100}],
        }

        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.create_portfolio', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = 9
            response = client.post('/api/portfolios', json=body)

        assert response.status_code == 200
        assert response.json()['portfolio_id'] == 9

    def test_create_custom_portfolio_failure(self, client):
        body = {
            'name': 'Defensive',
            'notes': 'Low beta',
            'holdings': [{'code': 'sh600519', 'name': 'Moutai', 'cost_price': 1500.0, 'shares': 100}],
        }

        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.create_portfolio', new_callable=AsyncMock) as mock_create:
            mock_create.side_effect = RuntimeError('create failed')
            response = client.post('/api/portfolios', json=body)

        assert response.status_code == 500

    def test_add_custom_holding_success(self, client):
        body = {'code': 'sz000001', 'name': 'PingAn', 'cost_price': 12.5, 'shares': 200}

        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.add_holding', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, 'Holding added')
            response = client.post('/api/portfolios/3/holdings', json=body)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_add_custom_holding_failure(self, client):
        body = {'code': 'sz000001', 'name': 'PingAn', 'cost_price': 12.5, 'shares': 200}

        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.add_holding', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (False, 'Holding add failed')
            response = client.post('/api/portfolios/3/holdings', json=body)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_get_custom_portfolio_detail_success(self, client):
        payload = {'id': 3, 'name': 'Defensive', 'summary': {'cost': 1000.0}, 'holdings': []}

        with patch('services.custom_portfolio_service.CustomPortfolioService.get_portfolio_detail', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = payload
            response = client.get('/api/portfolios/3')

        assert response.status_code == 200
        assert response.json()['data']['id'] == 3

    def test_get_custom_portfolio_detail_not_found(self, client):
        with patch('services.custom_portfolio_service.CustomPortfolioService.get_portfolio_detail', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            response = client.get('/api/portfolios/3')

        assert response.status_code == 404

    def test_get_custom_portfolio_detail_failure(self, client):
        with patch('services.custom_portfolio_service.CustomPortfolioService.get_portfolio_detail', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = RuntimeError('detail failed')
            response = client.get('/api/portfolios/3')

        assert response.status_code == 500

    def test_delete_custom_portfolio_success(self, client):
        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.delete_portfolio', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/portfolios/5')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_delete_custom_portfolio_failure(self, client):
        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.delete_portfolio', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/api/portfolios/5')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_delete_custom_holding_success(self, client):
        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.delete_holding', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/portfolios/5/holdings/11')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_delete_custom_holding_failure(self, client):
        with patch('repositories.custom_portfolio_repository.CustomPortfolioRepository.delete_holding', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/api/portfolios/5/holdings/11')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'
