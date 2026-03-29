from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd


class TestToolsRoutes:
    def test_get_export_stocks_success(self, client):
        mock_monitor_stock = MagicMock()
        mock_monitor_stock.code = 'sh600000'
        mock_monitor_stock.name = 'PF Bank'

        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled, \
             patch('repositories.kline_repository.KlineRepository.get_latest_date', new_callable=AsyncMock) as mock_get_latest:
            mock_get_enabled.return_value = [mock_monitor_stock]
            mock_get_latest.return_value = '2026-02-10'
            response = client.get('/api/tools/export-kline/stocks')

        assert response.status_code == 200
        assert response.json()['data'][0]['latest_date'] == '2026-02-10'

    def test_get_export_stocks_empty(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled:
            mock_get_enabled.return_value = []
            response = client.get('/api/tools/export-kline/stocks')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_get_export_stocks_with_nan_date(self, client):
        mock_monitor_stock = MagicMock()
        mock_monitor_stock.code = 'sh600000'
        mock_monitor_stock.name = 'PF Bank'

        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled, \
             patch('repositories.kline_repository.KlineRepository.get_latest_date', new_callable=AsyncMock) as mock_get_latest:
            mock_get_enabled.return_value = [mock_monitor_stock]
            mock_get_latest.return_value = None
            response = client.get('/api/tools/export-kline/stocks')

        assert response.status_code == 200
        assert response.json()['data'][0]['latest_date'] is None

    def test_get_export_stocks_multiple(self, client):
        mock_stock1 = MagicMock()
        mock_stock1.code = 'sh600000'
        mock_stock1.name = 'PF Bank'
        mock_stock2 = MagicMock()
        mock_stock2.code = 'sz000001'
        mock_stock2.name = 'PingAn'

        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled, \
             patch('repositories.kline_repository.KlineRepository.get_latest_date', new_callable=AsyncMock) as mock_get_latest:
            mock_get_enabled.return_value = [mock_stock1, mock_stock2]
            mock_get_latest.side_effect = ['2026-02-10', '2026-02-09']
            response = client.get('/api/tools/export-kline/stocks')

        assert response.status_code == 200
        assert len(response.json()['data']) == 2

    def test_get_export_stocks_failure(self, client):
        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled:
            mock_get_enabled.side_effect = RuntimeError('export stocks failed')
            response = client.get('/api/tools/export-kline/stocks')

        assert response.status_code == 500

    def test_calculate_cost_success(self, client):
        response = client.post(
            '/api/tools/calculate-cost',
            json={'positions': [{'price': 10.5, 'shares': 1000}, {'price': 11.0, 'shares': 500}]},
        )

        assert response.status_code == 200
        assert response.json()['data']['average_cost'] == 10.67

    def test_calculate_cost_empty_positions(self, client):
        response = client.post('/api/tools/calculate-cost', json={'positions': []})
        assert response.status_code == 400

    def test_calculate_cost_invalid_price(self, client):
        response = client.post('/api/tools/calculate-cost', json={'positions': [{'price': -10.5, 'shares': 1000}]})
        assert response.status_code == 400

    def test_calculate_cost_invalid_shares(self, client):
        response = client.post('/api/tools/calculate-cost', json={'positions': [{'price': 10.5, 'shares': -1000}]})
        assert response.status_code == 400

    def test_export_kline_csv_success(self, client):
        mock_stock = MagicMock()
        mock_stock.name = 'PF Bank'
        mock_df = pd.DataFrame({
            '日期': ['2026-02-10', '2026-02-09'],
            '开盘': [10.5, 10.3],
            '收盘': [10.8, 10.5],
            '最高': [11.0, 10.8],
            '最低': [10.3, 10.2],
            '成交量': [1000000, 800000],
            '成交额': [10800000, 8400000],
        })
        export_data = {'code': 'sh600000', 'format': 'csv', 'start_date': '2026-02-09', 'end_date': '2026-02-10'}

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:
            mock_get_stock.return_value = mock_stock
            mock_export.return_value = mock_df
            response = client.post('/api/tools/export-kline', json=export_data)

        assert response.status_code == 200
        assert 'text/csv' in response.headers['content-type']

    def test_export_kline_no_code(self, client):
        response = client.post('/api/tools/export-kline', json={'format': 'csv', 'start_date': '2026-02-09', 'end_date': '2026-02-10'})
        assert response.status_code == 422

    def test_export_kline_no_data(self, client):
        mock_stock = MagicMock()
        mock_stock.name = 'PF Bank'
        export_data = {'code': 'sh600000', 'format': 'csv', 'start_date': '2026-02-09', 'end_date': '2026-02-10'}

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:
            mock_get_stock.return_value = mock_stock
            mock_export.return_value = None
            response = client.post('/api/tools/export-kline', json=export_data)

        assert response.status_code == 400

    def test_export_kline_excel_success(self, client):
        mock_stock = MagicMock()
        mock_stock.name = 'PF Bank'
        mock_df = pd.DataFrame({
            '日期': ['2026-02-10'],
            '开盘': [10.5],
            '收盘': [10.8],
            '最高': [11.0],
            '最低': [10.3],
            '成交量': [1000000],
            '成交额': [10800000],
        })
        export_data = {'code': 'sh600000', 'format': 'excel', 'start_date': '2026-02-09', 'end_date': '2026-02-10'}

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:
            mock_get_stock.return_value = mock_stock
            mock_export.return_value = mock_df
            response = client.post('/api/tools/export-kline', json=export_data)

        assert response.status_code == 200
        assert 'spreadsheetml.sheet' in response.headers['content-type']

    def test_export_kline_invalid_format(self, client):
        response = client.post('/api/tools/export-kline', json={'code': 'sh600000', 'format': 'pdf', 'start_date': '2026-02-09', 'end_date': '2026-02-10'})
        assert response.status_code == 400

    def test_export_kline_failure(self, client):
        export_data = {'code': 'sh600000', 'format': 'csv', 'start_date': '2026-02-09', 'end_date': '2026-02-10'}

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:
            mock_get_stock.return_value = None
            mock_export.side_effect = RuntimeError('export failed')
            response = client.post('/api/tools/export-kline', json=export_data)

        assert response.status_code == 500
