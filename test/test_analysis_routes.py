from unittest.mock import AsyncMock, patch


class TestAnalysisRoutes:
    def test_list_analysis_reports_success(self, client):
        reports = [{'id': 1, 'code': 'sh600000'}]

        with patch('services.price_action_service.PriceActionService.list_reports', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = reports

            response = client.get('/api/analysis')

        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'success'
        assert data['data']['reports'] == reports

    def test_get_analysis_report_success(self, client):
        report = {'id': 3, 'code': 'sh600519', 'summary': 'ok'}

        with patch('services.price_action_service.PriceActionService.get_report', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = report

            response = client.get('/api/analysis/3')

        assert response.status_code == 200
        assert response.json()['data']['report'] == report
        mock_get.assert_called_once_with(3)

    def test_get_analysis_report_not_found(self, client):
        with patch('services.price_action_service.PriceActionService.get_report', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.get('/api/analysis/99')

        assert response.status_code == 404
        mock_get.assert_called_once_with(99)

    def test_create_analysis_report_success(self, client):
        payload = {'code': 'sh600000', 'count': 80, 'period': 'daily'}
        result = {'report_id': 5, 'report': {'code': 'sh600000'}}

        with patch(
            'services.price_action_service.PriceActionService.generate_analysis',
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.return_value = result

            response = client.post('/api/analysis', json=payload)

        assert response.status_code == 200
        assert response.json()['data'] == result
        mock_generate.assert_called_once_with(code='sh600000', count=80, period='daily')

    def test_create_analysis_report_value_error(self, client):
        payload = {'code': 'sh600000', 'count': 80, 'period': 'daily'}

        with patch(
            'services.price_action_service.PriceActionService.generate_analysis',
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.side_effect = ValueError('bad input')

            response = client.post('/api/analysis', json=payload)

        assert response.status_code == 400
        assert response.json()['detail'] == 'bad input'

    def test_create_analysis_report_failure(self, client):
        payload = {'code': 'sh600000', 'count': 80, 'period': 'daily'}

        with patch(
            'services.price_action_service.PriceActionService.generate_analysis',
            new_callable=AsyncMock,
        ) as mock_generate:
            mock_generate.side_effect = RuntimeError('analysis failed')

            response = client.post('/api/analysis', json=payload)

        assert response.status_code == 500
        assert response.json()['detail'] == 'analysis failed'

    def test_delete_analysis_report_success(self, client):
        with patch('services.price_action_service.PriceActionService.get_report', new_callable=AsyncMock) as mock_get, \
             patch('services.price_action_service.PriceActionService.delete_report', new_callable=AsyncMock) as mock_delete:
            mock_get.return_value = {'id': 8}
            mock_delete.return_value = True

            response = client.delete('/api/analysis/8')

        assert response.status_code == 200
        assert response.json()['status'] == 'success'
        mock_get.assert_called_once_with(8)
        mock_delete.assert_called_once_with(8)

    def test_delete_analysis_report_not_found_before_delete(self, client):
        with patch('services.price_action_service.PriceActionService.get_report', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.delete('/api/analysis/8')

        assert response.status_code == 404
        mock_get.assert_called_once_with(8)

    def test_delete_analysis_report_not_found_after_delete(self, client):
        with patch('services.price_action_service.PriceActionService.get_report', new_callable=AsyncMock) as mock_get, \
             patch('services.price_action_service.PriceActionService.delete_report', new_callable=AsyncMock) as mock_delete:
            mock_get.return_value = {'id': 8}
            mock_delete.return_value = False

            response = client.delete('/api/analysis/8')

        assert response.status_code == 404
        mock_delete.assert_called_once_with(8)
