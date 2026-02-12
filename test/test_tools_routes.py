import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import pandas as pd


class TestToolsRoutes:
    """测试 tools_routes 的接口"""

    # ========== GET 接口测试 ==========

    def test_get_export_stocks_success(self, client):
        """测试成功获取可导出的股票列表"""
        mock_monitor_stock = MagicMock()
        mock_monitor_stock.code = 'sh600000'
        mock_monitor_stock.name = '浦发银行'

        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled, \
             patch('repositories.kline_repository.KlineRepository.get_latest_date', new_callable=AsyncMock) as mock_get_latest:

            mock_get_enabled.return_value = [mock_monitor_stock]
            mock_get_latest.return_value = '2026-02-10'

            response = client.get('/api/tools/export-kline/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert len(data['data']) == 1
            assert data['data'][0]['code'] == 'sh600000'
            assert data['data'][0]['name'] == '浦发银行'
            assert data['data'][0]['latest_date'] == '2026-02-10'
            mock_get_enabled.assert_called_once()
            mock_get_latest.assert_called_once_with('sh600000')

    def test_get_export_stocks_empty(self, client):
        """测试获取可导出的股票列表，没有数据时"""
        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled:
            mock_get_enabled.return_value = []

            response = client.get('/api/tools/export-kline/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data'] == []

    def test_get_export_stocks_with_nan_date(self, client):
        """测试获取可导出的股票列表，最新日期为 NaN 时"""
        mock_monitor_stock = MagicMock()
        mock_monitor_stock.code = 'sh600000'
        mock_monitor_stock.name = '浦发银行'

        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled, \
             patch('repositories.kline_repository.KlineRepository.get_latest_date', new_callable=AsyncMock) as mock_get_latest:

            mock_get_enabled.return_value = [mock_monitor_stock]
            mock_get_latest.return_value = None

            response = client.get('/api/tools/export-kline/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert len(data['data']) == 1
            assert data['data'][0]['latest_date'] is None

    def test_get_export_stocks_multiple(self, client):
        """测试获取多个可导出的股票"""
        mock_stock1 = MagicMock()
        mock_stock1.code = 'sh600000'
        mock_stock1.name = '浦发银行'

        mock_stock2 = MagicMock()
        mock_stock2.code = 'sz000001'
        mock_stock2.name = '平安银行'

        with patch('repositories.monitor_repository.MonitorStockRepository.get_enabled', new_callable=AsyncMock) as mock_get_enabled, \
             patch('repositories.kline_repository.KlineRepository.get_latest_date', new_callable=AsyncMock) as mock_get_latest:

            mock_get_enabled.return_value = [mock_stock1, mock_stock2]
            mock_get_latest.side_effect = ['2026-02-10', '2026-02-09']

            response = client.get('/api/tools/export-kline/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert len(data['data']) == 2
            assert data['data'][0]['code'] == 'sh600000'
            assert data['data'][1]['code'] == 'sz000001'

    # ========== POST 接口测试 ==========

    def test_calculate_cost_success(self, client):
        """测试成功计算成本价"""
        positions_data = {
            'positions': [
                {'price': 10.5, 'shares': 1000},
                {'price': 11.0, 'shares': 500}
            ]
        }

        response = client.post('/api/tools/calculate-cost', json=positions_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['total_shares'] == 1500
        assert data['data']['average_cost'] == 10.67
        assert data['data']['total_cost'] == 16000.0

    def test_calculate_cost_empty_positions(self, client):
        """测试计算成本价，没有持仓记录"""
        positions_data = {'positions': []}

        response = client.post('/api/tools/calculate-cost', json=positions_data)

        assert response.status_code == 400
        assert '请提供买入记录' in response.json()['detail']

    def test_calculate_cost_invalid_price(self, client):
        """测试计算成本价，价格为负数"""
        positions_data = {
            'positions': [
                {'price': -10.5, 'shares': 1000}
            ]
        }

        response = client.post('/api/tools/calculate-cost', json=positions_data)

        assert response.status_code == 400
        assert '价格和股数必须大于0' in response.json()['detail']

    def test_calculate_cost_invalid_shares(self, client):
        """测试计算成本价，股数为负数"""
        positions_data = {
            'positions': [
                {'price': 10.5, 'shares': -1000}
            ]
        }

        response = client.post('/api/tools/calculate-cost', json=positions_data)

        assert response.status_code == 400
        assert '价格和股数必须大于0' in response.json()['detail']

    def test_export_kline_csv_success(self, client):
        """测试成功导出K线数据为CSV"""
        mock_stock = MagicMock()
        mock_stock.name = '浦发银行'

        mock_df = pd.DataFrame({
            '日期': ['2026-02-10', '2026-02-09'],
            '开盘': [10.5, 10.3],
            '收盘': [10.8, 10.5],
            '最高': [11.0, 10.8],
            '最低': [10.3, 10.2],
            '成交量': [1000000, 800000],
            '成交额': [10800000, 8400000]
        })

        export_data = {
            'code': 'sh600000',
            'format': 'csv',
            'start_date': '2026-02-09',
            'end_date': '2026-02-10'
        }

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:

            mock_get_stock.return_value = mock_stock
            mock_export.return_value = mock_df

            response = client.post('/api/tools/export-kline', json=export_data)

            assert response.status_code == 200
            assert 'text/csv' in response.headers['content-type']
            assert 'attachment' in response.headers['content-disposition']

    def test_export_kline_no_code(self, client):
        """测试导出K线数据，没有提供股票代码"""
        export_data = {
            'format': 'csv',
            'start_date': '2026-02-09',
            'end_date': '2026-02-10'
        }

        response = client.post('/api/tools/export-kline', json=export_data)

        # Pydantic 验证失败返回 422
        assert response.status_code == 422

    def test_export_kline_no_data(self, client):
        """测试导出K线数据，没有数据"""
        mock_stock = MagicMock()
        mock_stock.name = '浦发银行'

        export_data = {
            'code': 'sh600000',
            'format': 'csv',
            'start_date': '2026-02-09',
            'end_date': '2026-02-10'
        }

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:

            mock_get_stock.return_value = mock_stock
            mock_export.return_value = None

            response = client.post('/api/tools/export-kline', json=export_data)

            assert response.status_code == 400
            assert '没有可导出的数据' in response.json()['detail']

    def test_export_kline_excel_success(self, client):
        """测试成功导出K线数据为Excel"""
        mock_stock = MagicMock()
        mock_stock.name = '浦发银行'

        mock_df = pd.DataFrame({
            '日期': ['2026-02-10'],
            '开盘': [10.5],
            '收盘': [10.8],
            '最高': [11.0],
            '最低': [10.3],
            '成交量': [1000000],
            '成交额': [10800000]
        })

        export_data = {
            'code': 'sh600000',
            'format': 'excel',
            'start_date': '2026-02-09',
            'end_date': '2026-02-10'
        }

        with patch('repositories.monitor_repository.MonitorStockRepository.get_by_code', new_callable=AsyncMock) as mock_get_stock, \
             patch('repositories.kline_repository.KlineRepository.export_kline_data', new_callable=AsyncMock) as mock_export:

            mock_get_stock.return_value = mock_stock
            mock_export.return_value = mock_df

            response = client.post('/api/tools/export-kline', json=export_data)

            assert response.status_code == 200
            assert 'spreadsheetml.sheet' in response.headers['content-type']
            assert 'attachment' in response.headers['content-disposition']

    def test_export_kline_invalid_format(self, client):
        """测试导出K线数据，不支持的格式"""
        export_data = {
            'code': 'sh600000',
            'format': 'pdf',
            'start_date': '2026-02-09',
            'end_date': '2026-02-10'
        }

        response = client.post('/api/tools/export-kline', json=export_data)

        assert response.status_code == 400
        assert '不支持的导出格式' in response.json()['detail']