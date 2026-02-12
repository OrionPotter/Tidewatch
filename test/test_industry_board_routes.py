import pytest
from unittest.mock import AsyncMock, patch


class TestIndustryBoardRoutes:
    """测试 industry_board_routes 的 GET 接口"""

    def test_get_latest_boards_success(self, client):
        """测试成功获取板块最新数据"""
        mock_boards = [
            {
                'name': '银行',
                'code': 'BK0001',
                'current_price': 1000.5,
                'change_pct': 1.2,
                'turnover': 1000000000
            },
            {
                'name': '证券',
                'code': 'BK0002',
                'current_price': 950.3,
                'change_pct': -0.5,
                'turnover': 800000000
            }
        ]

        with patch('services.industry_board_service.IndustryBoardService.fetch_board_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_boards

            response = client.get('/api/industry-board/latest')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert 'timestamp' in data
            assert data['count'] == 2
            assert len(data['data']) == 2
            assert data['data'][0]['name'] == '银行'
            assert data['data'][1]['name'] == '证券'
            mock_fetch.assert_called_once()

    def test_get_latest_boards_empty(self, client):
        """测试获取板块最新数据，没有数据时"""
        with patch('services.industry_board_service.IndustryBoardService.fetch_board_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = []

            response = client.get('/api/industry-board/latest')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['count'] == 0
            assert data['data'] == []

    def test_get_latest_boards_single(self, client):
        """测试获取板块最新数据，只有一个板块时"""
        mock_boards = [
            {
                'name': '银行',
                'code': 'BK0001',
                'current_price': 1000.5,
                'change_pct': 1.2,
                'turnover': 1000000000
            }
        ]

        with patch('services.industry_board_service.IndustryBoardService.fetch_board_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_boards

            response = client.get('/api/industry-board/latest')

            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 1
            assert len(data['data']) == 1
            assert data['data'][0]['name'] == '银行'

    def test_get_latest_boards_many(self, client):
        """测试获取板块最新数据，多个板块时"""
        mock_boards = [
            {
                'name': f'板块{i}',
                'code': f'BK{i:04d}',
                'current_price': 1000.0 + i,
                'change_pct': i * 0.1,
                'turnover': i * 100000000
            }
            for i in range(10)
        ]

        with patch('services.industry_board_service.IndustryBoardService.fetch_board_data', new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = mock_boards

            response = client.get('/api/industry-board/latest')

            assert response.status_code == 200
            data = response.json()
            assert data['count'] == 10
            assert len(data['data']) == 10