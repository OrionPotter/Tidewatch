import json
import shutil
from pathlib import Path
from uuid import uuid4

from api import learn_routes


class TestLearnRoutes:
    def _make_learn_dir(self):
        learn_dir = Path('test') / f'_learn_{uuid4().hex}'
        articles_dir = learn_dir / 'articles'
        articles_dir.mkdir(parents=True, exist_ok=True)
        return learn_dir, articles_dir

    def _patch_paths(self, monkeypatch, learn_dir, articles_dir):
        monkeypatch.setattr(learn_routes, 'LEARN_DIR', learn_dir)
        monkeypatch.setattr(learn_routes, 'ARTICLES_DIR', articles_dir)
        monkeypatch.setattr(learn_routes, 'INDEX_PATH', learn_dir / 'index.json')

    def test_get_learn_articles_success(self, client, monkeypatch):
        learn_dir, articles_dir = self._make_learn_dir()
        try:
            self._patch_paths(monkeypatch, learn_dir, articles_dir)
            (learn_dir / 'index.json').write_text(json.dumps([{'slug': 'intro', 'title': 'Intro'}]), encoding='utf-8')

            response = client.get('/api/learn')

            assert response.status_code == 200
            assert response.json()['data']['articles'][0]['slug'] == 'intro'
        finally:
            shutil.rmtree(learn_dir, ignore_errors=True)

    def test_get_learn_articles_when_index_missing(self, client, monkeypatch):
        learn_dir, articles_dir = self._make_learn_dir()
        try:
            self._patch_paths(monkeypatch, learn_dir, articles_dir)

            response = client.get('/api/learn')

            assert response.status_code == 200
            assert response.json()['data']['articles'] == []
        finally:
            shutil.rmtree(learn_dir, ignore_errors=True)

    def test_get_learn_article_success(self, client, monkeypatch):
        learn_dir, articles_dir = self._make_learn_dir()
        try:
            self._patch_paths(monkeypatch, learn_dir, articles_dir)
            (learn_dir / 'index.json').write_text(json.dumps([{'slug': 'intro', 'title': 'Intro'}]), encoding='utf-8')
            (articles_dir / 'intro.md').write_text('# Intro', encoding='utf-8')

            response = client.get('/api/learn/intro')

            assert response.status_code == 200
            assert response.json()['data']['content'] == '# Intro'
        finally:
            shutil.rmtree(learn_dir, ignore_errors=True)

    def test_get_learn_article_not_found(self, client, monkeypatch):
        learn_dir, articles_dir = self._make_learn_dir()
        try:
            self._patch_paths(monkeypatch, learn_dir, articles_dir)
            (learn_dir / 'index.json').write_text(json.dumps([]), encoding='utf-8')

            response = client.get('/api/learn/missing')

            assert response.status_code == 404
        finally:
            shutil.rmtree(learn_dir, ignore_errors=True)

    def test_get_learn_article_content_missing(self, client, monkeypatch):
        learn_dir, articles_dir = self._make_learn_dir()
        try:
            self._patch_paths(monkeypatch, learn_dir, articles_dir)
            (learn_dir / 'index.json').write_text(json.dumps([{'slug': 'intro', 'title': 'Intro'}]), encoding='utf-8')

            response = client.get('/api/learn/intro')

            assert response.status_code == 404
        finally:
            shutil.rmtree(learn_dir, ignore_errors=True)
