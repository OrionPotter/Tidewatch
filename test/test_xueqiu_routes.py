import pytest
from unittest.mock import AsyncMock, patch, MagicMock


class TestXueqiuRoutes:
    """测试 xueqiu_routes 的 GET 接口"""

    def test_get_xueqiu_data_success(self, client):
        """测试成功获取所有雪球组合数据"""
        mock_data = [
            {
                'cube_symbol': 'ZH123456',
                'cube_name': '测试组合1',
                'rebalancing': []
            },
            {
                'cube_symbol': 'ZH789012',
                'cube_name': '测试组合2',
                'rebalancing': []
            }
        ]

        with patch('services.xueqiu_service.XueqiuService.get_all_formatted_data_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = mock_data

            response = client.get('/api/xueqiu')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert 'timestamp' in data
            assert len(data['data']) == 2
            assert data['data'][0]['cube_symbol'] == 'ZH123456'
            mock_get_all.assert_called_once()

    def test_get_xueqiu_data_empty(self, client):
        """测试获取雪球组合数据，没有数据时"""
        with patch('services.xueqiu_service.XueqiuService.get_all_formatted_data_async', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []

            response = client.get('/api/xueqiu')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data'] == []

    def test_get_cube_data_success(self, client):
        """测试成功获取指定雪球组合数据"""
        mock_history = []
        mock_cube = MagicMock()
        mock_cube.cube_name = '测试组合'

        with patch('services.xueqiu_service.XueqiuService._get_headers') as mock_headers, \
             patch('aiohttp.ClientSession') as mock_session_class, \
             patch('repositories.xueqiu_repository.XueqiuCubeRepository.get_by_symbol', new_callable=AsyncMock) as mock_get_cube, \
             patch('services.xueqiu_service.XueqiuService.format_rebalancing_data') as mock_format:

            mock_headers.return_value = {}
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session_instance

            with patch('services.xueqiu_service.XueqiuService._fetch_cube_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_history
                mock_get_cube.return_value = mock_cube
                mock_format.return_value = []

                response = client.get('/api/xueqiu/ZH123456')

                assert response.status_code == 200
                data = response.json()
                assert data['status'] == 'success'
                assert 'timestamp' in data
                assert data['cube_symbol'] == 'ZH123456'
                mock_get_cube.assert_called_once_with('ZH123456')
                mock_format.assert_called_once()

    def test_get_cube_data_not_found(self, client):
        """测试获取指定雪球组合数据，组合不存在时"""
        mock_history = []

        with patch('services.xueqiu_service.XueqiuService._get_headers') as mock_headers, \
             patch('aiohttp.ClientSession') as mock_session_class, \
             patch('repositories.xueqiu_repository.XueqiuCubeRepository.get_by_symbol', new_callable=AsyncMock) as mock_get_cube:

            mock_headers.return_value = {}
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session_instance

            with patch('services.xueqiu_service.XueqiuService._fetch_cube_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = mock_history
                mock_get_cube.return_value = None

                with patch('services.xueqiu_service.XueqiuService.format_rebalancing_data') as mock_format:
                    mock_format.return_value = []

                    response = client.get('/api/xueqiu/ZH999999')

                    assert response.status_code == 200
                    data = response.json()
                    assert data['cube_symbol'] == 'ZH999999'
                    # 当组合不存在时，cube_name 应该使用 cube_symbol
                    mock_format.assert_called_once_with('ZH999999', 'ZH999999', mock_history)

    def test_get_cube_data_fetch_failure(self, client):
        """测试获取指定雪球组合数据，获取失败时"""
        with patch('services.xueqiu_service.XueqiuService._get_headers') as mock_headers, \
             patch('aiohttp.ClientSession') as mock_session_class:

            mock_headers.return_value = {}
            mock_session_instance = AsyncMock()
            mock_session_instance.__aenter__ = AsyncMock(return_value=mock_session_instance)
            mock_session_instance.__aexit__ = AsyncMock(return_value=None)
            mock_session_class.return_value = mock_session_instance

            with patch('services.xueqiu_service.XueqiuService._fetch_cube_data', new_callable=AsyncMock) as mock_fetch:
                mock_fetch.return_value = None

                response = client.get('/api/xueqiu/ZH123456')

                assert response.status_code == 500
                assert '获取数据失败' in response.json()['detail']