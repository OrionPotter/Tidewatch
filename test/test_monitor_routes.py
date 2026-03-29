from unittest.mock import AsyncMock, patch


class TestMonitorRoutes:
    def test_get_monitor_success(self, client):
        mock_stocks = [{'code': 'sh600000', 'name': 'PF Bank', 'score': 82, 'risk_level': 'low'}]

        with patch('services.monitor_service.MonitorService.get_enriched_monitor_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_stocks
            response = client.get('/api/monitor')

        assert response.status_code == 200
        assert response.json()['stocks'][0]['score'] == 82

    def test_get_monitor_uses_cache(self, client):
        with patch('services.monitor_service.MonitorService.get_enriched_monitor_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = [{'code': 'sh600000'}]
            client.get('/api/monitor')
            client.get('/api/monitor')

        mock_get_data.assert_called_once()

    def test_get_monitor_failure(self, client):
        with patch('services.monitor_service.MonitorService.get_enriched_monitor_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.side_effect = RuntimeError('monitor failed')
            response = client.get('/api/monitor')

        assert response.status_code == 500

    def test_list_monitor_stocks_success(self, client):
        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [{'code': 'sh600000', 'enabled': True}]
            response = client.get('/api/monitor/stocks')

        assert response.status_code == 200
        assert len(response.json()['data']) == 1

    def test_list_monitor_stocks_empty(self, client):
        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []
            response = client.get('/api/monitor/stocks')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_list_monitor_stocks_failure(self, client):
        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.side_effect = RuntimeError('list failed')
            response = client.get('/api/monitor/stocks')

        assert response.status_code == 500

    def test_create_monitor_stock_success(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'timeframe': '1d', 'reasonable_pe_min': 15, 'reasonable_pe_max': 20}

        with patch('services.monitor_service.MonitorService.create_monitor_stock', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = (True, 'created')
            response = client.post('/api/monitor/stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_create_monitor_stock_failure(self, client):
        stock_data = {'code': 'sh600000', 'name': 'PF Bank', 'timeframe': '1d', 'reasonable_pe_min': 15, 'reasonable_pe_max': 20}

        with patch('services.monitor_service.MonitorService.create_monitor_stock', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = (False, 'exists')
            response = client.post('/api/monitor/stocks', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_update_monitor_stock_success(self, client):
        stock_data = {'name': 'PF Bank', 'timeframe': '2d', 'reasonable_pe_min': 18, 'reasonable_pe_max': 25}

        with patch('services.monitor_service.MonitorService.update_monitor_stock', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (True, 'updated')
            response = client.put('/api/monitor/stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_update_monitor_stock_failure(self, client):
        stock_data = {'name': 'PF Bank', 'timeframe': '2d', 'reasonable_pe_min': 18, 'reasonable_pe_max': 25}

        with patch('services.monitor_service.MonitorService.update_monitor_stock', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (False, 'update failed')
            response = client.put('/api/monitor/stocks/sh600000', json=stock_data)

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_delete_monitor_stock_success(self, client):
        with patch('services.monitor_service.MonitorService.delete_monitor_stock', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = (True, 'deleted')
            response = client.delete('/api/monitor/stocks/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_delete_monitor_stock_failure(self, client):
        with patch('services.monitor_service.MonitorService.delete_monitor_stock', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = (False, 'delete failed')
            response = client.delete('/api/monitor/stocks/sh600000')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_toggle_monitor_stock_enable(self, client):
        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (True, 'done')
            response = client.post('/api/monitor/stocks/sh600000/toggle', json={'enabled': True})

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_toggle_monitor_stock_disable(self, client):
        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (True, 'done')
            response = client.post('/api/monitor/stocks/sh600000/toggle', json={'enabled': False})

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_toggle_monitor_stock_failure(self, client):
        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (False, 'toggle failed')
            response = client.post('/api/monitor/stocks/sh600000/toggle', json={'enabled': False})

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_update_kline_success(self, client):
        with patch('asyncio.create_task') as mock_create_task:
            mock_create_task.return_value = None
            response = client.post('/api/monitor/update-kline', json={'force_update': True})

        assert response.status_code == 200

    def test_update_kline_no_force(self, client):
        with patch('asyncio.create_task') as mock_create_task:
            mock_create_task.return_value = None
            response = client.post('/api/monitor/update-kline', json={'force_update': False})
        assert response.status_code == 200

    def test_update_kline_failure(self, client):
        with patch('asyncio.create_task') as mock_create_task:
            mock_create_task.side_effect = RuntimeError('create task failed')
            response = client.post('/api/monitor/update-kline', json={'force_update': False})

        assert response.status_code == 500
