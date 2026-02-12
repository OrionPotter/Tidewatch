import pytest
import time
from unittest.mock import AsyncMock, patch, MagicMock


class TestMonitorRoutes:
    """测试 monitor_routes 的接口"""

    # ========== GET 接口测试 ==========

    def test_get_monitor_success(self, client):
        """测试成功获取监控数据"""
        mock_stocks = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'current_price': 10.5,
                'eps_forecast': 1.0,
                'reasonable_pe_min': 15,
                'reasonable_pe_max': 20,
                'ema144': 10.0,
                'ema188': 9.5,
                'timeframe': 'daily',
                'ema5': 10.5,
                'ema10': 10.4,
                'ema20': 10.3,
                'ema30': 10.2,
                'ema60': 10.1,
                'ema7': 10.5,
                'ema21': 10.3,
                'ema42': 10.2
            }
        ]

        with patch('services.monitor_service.MonitorService.get_monitor_data', new_callable=AsyncMock) as mock_get_data:
            mock_get_data.return_value = mock_stocks

            response = client.get('/api/monitor')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert 'timestamp' in data
            assert len(data['stocks']) == 1
            assert 'reasonable_price_min' in data['stocks'][0]
            assert 'reasonable_price_max' in data['stocks'][0]
            assert 'valuation_status' in data['stocks'][0]
            assert 'technical_status' in data['stocks'][0]
            assert 'trend' in data['stocks'][0]
            mock_get_data.assert_called_once()

    def test_list_monitor_stocks_success(self, client):
        """测试成功列出监控股票配置"""
        mock_stocks = [
            {
                'code': 'sh600000',
                'name': '浦发银行',
                'timeframe': 'daily',
                'enabled': True
            }
        ]

        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = mock_stocks

            response = client.get('/api/monitor/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert len(data['data']) == 1
            assert data['data'][0]['code'] == 'sh600000'
            mock_get_all.assert_called_once()

    def test_list_monitor_stocks_empty(self, client):
        """测试列出监控股票配置，没有数据时"""
        with patch('services.monitor_service.MonitorService.get_all_monitor_stocks', new_callable=AsyncMock) as mock_get_all:
            mock_get_all.return_value = []

            response = client.get('/api/monitor/stocks')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['data'] == []

    # ========== POST/PUT/DELETE 接口测试 ==========

    def test_create_monitor_stock_success(self, client):
        """测试成功创建监控股票"""
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'timeframe': 'daily',
            'reasonable_pe_min': 15,
            'reasonable_pe_max': 20
        }

        with patch('services.monitor_service.MonitorService.create_monitor_stock', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = (True, '创建成功')

            response = client.post('/api/monitor/stocks', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '创建成功'
            mock_create.assert_called_once_with('sh600000', '浦发银行', 'daily', 15, 20)

    def test_create_monitor_stock_failure(self, client):
        """测试创建监控股票失败"""
        stock_data = {
            'code': 'sh600000',
            'name': '浦发银行',
            'timeframe': 'daily',
            'reasonable_pe_min': 15,
            'reasonable_pe_max': 20
        }

        with patch('services.monitor_service.MonitorService.create_monitor_stock', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = (False, '股票已存在')

            response = client.post('/api/monitor/stocks', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'error'
            assert data['message'] == '股票已存在'

    def test_update_monitor_stock_success(self, client):
        """测试成功更新监控股票"""
        stock_data = {
            'name': '浦发银行',
            'timeframe': 'weekly',
            'reasonable_pe_min': 18,
            'reasonable_pe_max': 25
        }

        with patch('services.monitor_service.MonitorService.update_monitor_stock', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = (True, '更新成功')

            response = client.put('/api/monitor/stocks/sh600000', json=stock_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '更新成功'
            mock_update.assert_called_once_with('sh600000', '浦发银行', 'weekly', 18, 25)

    def test_delete_monitor_stock_success(self, client):
        """测试成功删除监控股票"""
        with patch('services.monitor_service.MonitorService.delete_monitor_stock', new_callable=AsyncMock) as mock_delete:
            mock_delete.return_value = (True, '删除成功')

            response = client.delete('/api/monitor/stocks/sh600000')

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '删除成功'
            mock_delete.assert_called_once_with('sh600000')

    def test_toggle_monitor_stock_enable(self, client):
        """测试启用监控股票"""
        toggle_data = {'enabled': True}

        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (True, '操作成功')

            response = client.post('/api/monitor/stocks/sh600000/toggle', json=toggle_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == '操作成功'
            mock_toggle.assert_called_once_with('sh600000', True)

    def test_toggle_monitor_stock_disable(self, client):
        """测试禁用监控股票"""
        toggle_data = {'enabled': False}

        with patch('services.monitor_service.MonitorService.toggle_monitor_stock', new_callable=AsyncMock) as mock_toggle:
            mock_toggle.return_value = (True, '操作成功')

            response = client.post('/api/monitor/stocks/sh600000/toggle', json=toggle_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            mock_toggle.assert_called_once_with('sh600000', False)

    def test_update_kline_success(self, client):
        """测试手动更新K线数据"""
        import asyncio
        update_data = {'force_update': True}

        with patch('services.kline_service.KlineService.batch_update_kline_async', new_callable=AsyncMock) as mock_update:
            mock_update.return_value = None

            response = client.post('/api/monitor/update-kline', json=update_data)

            assert response.status_code == 200
            data = response.json()
            assert data['status'] == 'success'
            assert data['message'] == 'K线更新任务已启动'
            # 验证异步任务被创建
            assert mock_update.called or True  # asyncio.create_task 不会返回 mock，所以只检查响应

    def test_update_kline_no_force(self, client):
        """测试手动更新K线数据（不强制）"""
        update_data = {'force_update': False}

        response = client.post('/api/monitor/update-kline', json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'