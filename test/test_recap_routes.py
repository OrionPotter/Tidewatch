from types import SimpleNamespace
from unittest.mock import AsyncMock, patch


class TestRecapRoutes:
    def _form_data(self):
        return {
            'review_date': '2026-03-28T10:30',
            'stock_name': 'Test Stock',
            'stock_code': 'sh600000',
            'take_profit': '12.5',
            'stop_loss': '9.8',
            'risk_reward_ratio': '2.0',
            'profit_amount': '1000',
            'is_success': 'true',
            'failure_reason': '  ',
            'strategy_tag': 'breakout',
            'summary': 'good',
            'lessons_learned': 'keep',
            'notes': 'note',
        }

    def test_list_recaps_success(self, client):
        record = SimpleNamespace(to_dict=lambda: {'id': 1, 'stock_name': 'Test Stock'})

        with patch('repositories.recap_repository.RecapRepository.list_records', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = [record]

            response = client.get('/api/recaps')

        assert response.status_code == 200
        assert response.json()['data']['records'] == [{'id': 1, 'stock_name': 'Test Stock'}]

    def test_get_recap_success(self, client):
        record = SimpleNamespace(to_dict=lambda: {'id': 3, 'stock_name': 'Test Stock'})

        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = record

            response = client.get('/api/recaps/3')

        assert response.status_code == 200
        assert response.json()['data']['record']['id'] == 3

    def test_get_recap_not_found(self, client):
        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.get('/api/recaps/3')

        assert response.status_code == 404

    def test_create_recap_success(self, client):
        with patch('api.recap_routes._save_image', new_callable=AsyncMock) as mock_save, \
             patch('repositories.recap_repository.RecapRepository.create_record', new_callable=AsyncMock) as mock_create:
            mock_save.return_value = '/static/uploads/recaps/test.png'
            mock_create.return_value = 7

            response = client.post('/api/recaps', data=self._form_data())

        assert response.status_code == 200
        data = response.json()['data']
        assert data['id'] == 7
        assert data['image_path'] == '/static/uploads/recaps/test.png'
        call_kwargs = mock_create.call_args.kwargs
        assert call_kwargs['stock_name'] == 'Test Stock'
        assert call_kwargs['stock_code'] == 'sh600000'
        assert call_kwargs['failure_reason'] is None
        assert call_kwargs['is_success'] is True

    def test_create_recap_invalid_datetime(self, client):
        form_data = self._form_data()
        form_data['review_date'] = 'bad-date'

        response = client.post('/api/recaps', data=form_data)

        assert response.status_code == 400

    def test_create_recap_invalid_image_type(self, client):
        response = client.post(
            '/api/recaps',
            data=self._form_data(),
            files={'image': ('test.txt', b'bad', 'text/plain')},
        )

        assert response.status_code == 400

    def test_update_recap_success_replace_image(self, client):
        existing = SimpleNamespace(image_path='/static/uploads/recaps/old.png')

        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get, \
             patch('api.recap_routes._save_image', new_callable=AsyncMock) as mock_save, \
             patch('api.recap_routes._delete_image') as mock_delete, \
             patch('repositories.recap_repository.RecapRepository.update_record', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = existing
            mock_save.return_value = '/static/uploads/recaps/new.png'
            mock_update.return_value = True

            response = client.put('/api/recaps/5', data=self._form_data())

        assert response.status_code == 200
        assert response.json()['data']['image_path'] == '/static/uploads/recaps/new.png'
        mock_delete.assert_called_once_with('/static/uploads/recaps/old.png')
        assert mock_update.call_args.kwargs['image_path'] == '/static/uploads/recaps/new.png'

    def test_update_recap_success_remove_existing_image(self, client):
        existing = SimpleNamespace(image_path='/static/uploads/recaps/old.png')
        form_data = self._form_data()
        form_data['keep_existing_image'] = 'false'

        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get, \
             patch('api.recap_routes._save_image', new_callable=AsyncMock) as mock_save, \
             patch('api.recap_routes._delete_image') as mock_delete, \
             patch('repositories.recap_repository.RecapRepository.update_record', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = existing
            mock_save.return_value = None
            mock_update.return_value = True

            response = client.put('/api/recaps/5', data=form_data)

        assert response.status_code == 200
        assert response.json()['data']['image_path'] is None
        mock_delete.assert_called_once_with('/static/uploads/recaps/old.png')

    def test_update_recap_not_found(self, client):
        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.put('/api/recaps/5', data=self._form_data())

        assert response.status_code == 404

    def test_update_recap_update_failure(self, client):
        existing = SimpleNamespace(image_path=None)

        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get, \
             patch('api.recap_routes._save_image', new_callable=AsyncMock) as mock_save, \
             patch('repositories.recap_repository.RecapRepository.update_record', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = existing
            mock_save.return_value = None
            mock_update.return_value = False

            response = client.put('/api/recaps/5', data=self._form_data())

        assert response.status_code == 404

    def test_delete_recap_success(self, client):
        existing = SimpleNamespace(image_path='/static/uploads/recaps/test.png')

        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get, \
             patch('repositories.recap_repository.RecapRepository.delete_record', new_callable=AsyncMock) as mock_delete, \
             patch('api.recap_routes._delete_image') as mock_delete_image:
            mock_get.return_value = existing
            mock_delete.return_value = True

            response = client.delete('/api/recaps/5')

        assert response.status_code == 200
        mock_delete_image.assert_called_once_with('/static/uploads/recaps/test.png')

    def test_delete_recap_not_found(self, client):
        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = None

            response = client.delete('/api/recaps/5')

        assert response.status_code == 404

    def test_delete_recap_delete_failure(self, client):
        existing = SimpleNamespace(image_path=None)

        with patch('repositories.recap_repository.RecapRepository.get_record', new_callable=AsyncMock) as mock_get, \
             patch('repositories.recap_repository.RecapRepository.delete_record', new_callable=AsyncMock) as mock_delete:
            mock_get.return_value = existing
            mock_delete.return_value = False

            response = client.delete('/api/recaps/5')

        assert response.status_code == 404
