from unittest.mock import AsyncMock, MagicMock, patch


class TestStockListRoutes:
    def test_get_stock_list_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {'code': 'sh600000', 'name': 'PF Bank', 'industry': 'Bank'}

        with patch('services.stock_list_service.StockListService.get_all_stocks_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = [mock_stock, mock_stock]
            response = client.get('/api/stock-list')

        assert response.status_code == 200
        assert response.json()['count'] == 2

    def test_get_stock_list_empty(self, client):
        with patch('services.stock_list_service.StockListService.get_all_stocks_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []
            response = client.get('/api/stock-list')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_get_stock_list_failure(self, client):
        with patch('services.stock_list_service.StockListService.get_all_stocks_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.side_effect = RuntimeError('list failed')
            response = client.get('/api/stock-list')

        assert response.status_code == 500

    def test_get_stock_count_success(self, client):
        with patch('services.stock_list_service.StockListService.get_stock_count_async', new_callable=AsyncMock) as mock_get_count:
            mock_get_count.return_value = 5000
            response = client.get('/api/stock-list/count')

        assert response.status_code == 200
        assert response.json()['count'] == 5000

    def test_get_stock_count_failure(self, client):
        with patch('services.stock_list_service.StockListService.get_stock_count_async', new_callable=AsyncMock) as mock_get_count:
            mock_get_count.side_effect = RuntimeError('count failed')
            response = client.get('/api/stock-list/count')

        assert response.status_code == 500

    def test_get_stock_by_code_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {'code': 'sh600000', 'name': 'PF Bank', 'industry': 'Bank'}

        with patch('services.stock_list_service.StockListService.get_stock_by_code_async', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_stock
            response = client.get('/api/stock-list/sh600000')

        assert response.status_code == 200
        assert response.json()['data']['code'] == 'sh600000'

    def test_get_stock_by_code_not_found(self, client):
        with patch('services.stock_list_service.StockListService.get_stock_by_code_async', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None
            response = client.get('/api/stock-list/sh999999')

        assert response.status_code == 404

    def test_get_stock_by_code_failure(self, client):
        with patch('services.stock_list_service.StockListService.get_stock_by_code_async', new_callable=AsyncMock) as mock_get:
            mock_get.side_effect = RuntimeError('get failed')
            response = client.get('/api/stock-list/sh600000')

        assert response.status_code == 500

    def test_search_stocks_success(self, client):
        mock_stock = MagicMock()
        mock_stock.to_dict.return_value = {'code': 'sh600000', 'name': 'PF Bank', 'industry': 'Bank'}

        with patch('services.stock_list_service.StockListService.search_stocks_async', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = [mock_stock]
            response = client.get('/api/stock-list/search/bank')

        assert response.status_code == 200
        assert response.json()['count'] == 1

    def test_search_stocks_no_results(self, client):
        with patch('services.stock_list_service.StockListService.search_stocks_async', new_callable=AsyncMock) as mock_search:
            mock_search.return_value = []
            response = client.get('/api/stock-list/search/missing')

        assert response.status_code == 200
        assert response.json()['data'] == []

    def test_search_stocks_failure(self, client):
        with patch('services.stock_list_service.StockListService.search_stocks_async', new_callable=AsyncMock) as mock_search:
            mock_search.side_effect = RuntimeError('search failed')
            response = client.get('/api/stock-list/search/test')

        assert response.status_code == 500

    def test_update_stock_list_success(self, client):
        with patch('services.stock_list_service.StockListService.update_stock_list_async', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (True, 'updated')
            response = client.post('/api/stock-list/update')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'

    def test_update_stock_list_failure(self, client):
        with patch('services.stock_list_service.StockListService.update_stock_list_async', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (False, 'update failed')
            response = client.post('/api/stock-list/update')

        assert response.status_code == 200
        assert response.json()['status'] == 'error'

    def test_update_stock_list_exception(self, client):
        with patch('services.stock_list_service.StockListService.update_stock_list_async', new_callable=AsyncMock) as mock_update:
            mock_update.side_effect = Exception('db failed')
            response = client.post('/api/stock-list/update')

        assert response.status_code == 500
