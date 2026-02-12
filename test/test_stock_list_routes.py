import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestStockListRoutes:
    """测试 stock_list_routes 的接口"""

    # ========== GET 接口测试 ==========

    def test_get_stock_list_success(self, client):
        """测试成功获取股票列表"""
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {
            'code': 'sh600000',
            'name': '浦发银行',
            'industry': '银行'
        }

        with patch('services.stock_list_service.StockListService.get_all_stocks_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_stock, mock_stock]

            response = client.get('/api/stock-list')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['count'] == 2
            assert len(data['data']) == 2
            assert 'timestamp' in data
            mock_get_all.assert_called_once()

    def test_get_stock_list_empty(self, client):
        """测试获取股票列表，没有数据时"""
        with patch('services.stock_list_service.StockListService.get_all_stocks_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []

            response = client.get('/api/stock-list')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['count'] == 0
            assert data['data'] == []

    def test_get_stock_count_success(self, client):
        """测试成功获取股票总数"""
        with patch('services.stock_list_service.StockListService.get_stock_count_async', new_callable=AsyncMock) as mock_get_count:
            mock_get_count.return_value = 5000

            response = client.get('/api/stock-list/count')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['count'] == 5000
            assert 'timestamp' in data
            mock_get_count.assert_called_once()

    def test_get_stock_by_code_success(self, client):
        """测试成功根据代码获取股票"""
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {
            'code': 'sh600000',
            'name': '浦发银行',
            'industry': '银行'
        }

        with patch('services.stock_list_service.StockListService.get_stock_by_code_async', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_stock

            response = client.get('/api/stock-list/sh600000')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data']['code'] == 'sh600000'
            assert 'timestamp' in data
            mock_get.assert_called_once_with('sh600000')

    def test_get_stock_by_code_not_found(self, client):
        """测试根据代码获取股票，股票不存在"""
        with patch('services.stock_list_service.StockListService.get_stock_by_code_async', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.get('/api/stock-list/sh999999')

            assert response.status_code == 404
            assert '股票不存在' in response.json()['detail']
            mock_get.assert_called_once_with('sh999999')

    def test_search_stocks_success(self, client):
        """测试成功搜索股票"""
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {
            'code': 'sh600000',
            'name': '浦发银行',
            'industry': '银行'
        }

        with patch('services.stock_list_service.StockListService.search_stocks_async', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [mock_stock]

            response = client.get('/api/stock-list/search/银行')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['count'] == 1
            assert len(data['data']) == 1
            assert 'timestamp' in data
            mock_search.assert_called_once_with('银行')

    def test_search_stocks_no_results(self, client):
        """测试搜索股票，没有匹配结果"""
        with patch('services.stock_list_service.StockListService.search_stocks_async', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []

            response = client.get('/api/stock-list/search/不存在')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['count'] == 0
            assert data['data'] == []

    # ========== POST 接口测试 ==========

    def test_update_stock_list_success(self, client):
        """测试成功更新股票列表"""
        with patch('services.stock_list_service.StockListService.update_stock_list_async', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (True, '更新成功，共更新5000条记录')

            response = client.post('/api/stock-list/update')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '更新成功，共更新5000条记录'
            assert 'timestamp' in data
            mock_update.assert_called_once()

    def test_update_stock_list_failure(self, client):
        """测试更新股票列表失败"""
        with patch('services.stock_list_service.StockListService.update_stock_list_async', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (False, '更新失败：网络错误')

            response = client.post('/api/stock-list/update')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert data['message'] == '更新失败：网络错误'
            assert 'timestamp' in data

    def test_update_stock_list_exception(self, client):
        """测试更新股票列表，发生异常"""
        with patch('services.stock_list_service.StockListService.update_stock_list_async', new_callable=AsyncMock) as mock_update:
            mock_update.side_effect = Exception('数据库连接失败')

            response = client.post('/api/stock-list/update')

            assert response.status_code == 500
            assert '数据库连接失败' in response.json()['detail']