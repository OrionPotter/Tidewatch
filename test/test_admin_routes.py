from unittest.mock import AsyncMock, MagicMock, patch


class TestAdminRoutes:
    def test_list_stocks_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_stock]
            response = client.get('/api/admin/stocks')

        assert response.status_code == 200

    def test_list_monitor_stocks_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {'code': 'sh600000', 'name': 'PF Bank', 'timeframe': 'daily', 'enabled': True}

        with patch('repositories.monitor_repository.MonitorStockRepository.get_all', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_stock]
            response = client.get('/api/admin/monitor-stocks')

        assert response.status_code == 200

    def test_create_stock_success(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, 'created')
            response = client.post('/api/admin/stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_create_stock_failure(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'cost_price': 10.5, 'shares': 1000}

        with patch('repositories.portfolio_repository.StockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (False, 'create failed')
            response = client.post('/api/admin/stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_update_stock_success(self, client):
        stock_data = {'name': 'PF Bank', 'cost_price': 11.0, 'shares': 1500}

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/admin/stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_update_stock_failure(self, client):
        stock_data = {'name': 'PF Bank', 'cost_price': 11.0, 'shares': 1500}

        with patch('repositories.portfolio_repository.StockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = False
            response = client.put('/api/admin/stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_delete_stock_success(self, client):
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/admin/stocks/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_delete_stock_failure(self, client):
        with patch('repositories.portfolio_repository.StockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/api/admin/stocks/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_create_monitor_stock_success(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'timeframe': 'daily', 'reasonable_pe_min': 15, 'reasonable_pe_max': 20}

        with patch('repositories.monitor_repository.MonitorStockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (True, 'created')
            response = client.post('/api/admin/monitor-stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_create_monitor_stock_failure(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'timeframe': 'daily', 'reasonable_pe_min': 15, 'reasonable_pe_max': 20}

        with patch('repositories.monitor_repository.MonitorStockRepository.add', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = (False, 'create failed')
            response = client.post('/api/admin/monitor-stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_update_monitor_stock_success(self, client):
        stock_data = {'name': 'PF Bank', 'timeframe': 'weekly', 'reasonable_pe_min': 18, 'reasonable_pe_max': 25}

        with patch('repositories.monitor_repository.MonitorStockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = True
            response = client.put('/api/admin/monitor-stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_update_monitor_stock_failure(self, client):
        stock_data = {'name': 'PF Bank', 'timeframe': 'weekly', 'reasonable_pe_min': 18, 'reasonable_pe_max': 25}

        with patch('repositories.monitor_repository.MonitorStockRepository.update', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = False
            response = client.put('/api/admin/monitor-stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_delete_monitor_stock_success(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = True
            response = client.delete('/api/admin/monitor-stocks/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_delete_monitor_stock_failure(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.delete', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = False
            response = client.delete('/api/admin/monitor-stocks/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_toggle_monitor_stock_success(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.toggle_enabled', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = True
            response = client.post('/api/admin/monitor-stocks/sh600000/toggle', json={'enabled': True})

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_toggle_monitor_stock_failure(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.toggle_enabled', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = False
            response = client.post('/api/admin/monitor-stocks/sh600000/toggle', json={'enabled': True})

        assert response.status_code == 200
        assert response.json()['status'] == 'error'
