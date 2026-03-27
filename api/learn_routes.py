import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from utils.api_helpers import current_timestamp, success_response
from utils.logger import get_logger

logger = get_logger('learn_routes')
learn_router = APIRouter()

LEARN_DIR = Path('learn')
ARTICLES_DIR = LEARN_DIR / 'articles'
INDEX_PATH = LEARN_DIR / 'index.json'


def load_learn_index() -> list[dict]:
    if not INDEX_PATH.exists():
        return []
    return json.loads(INDEX_PATH.read_text(encoding='utf-8'))


def get_article_meta(slug: str) -> dict | None:
    for item in load_learn_index():
        if item['slug'] == slug:
            return item
    return None


@learn_router.get('')
async def get_learn_articles():
    logger.info('GET /api/learn')
    return success_response(
        timestamp=current_timestamp(),
        data={'articles': load_learn_index()},
    )


@learn_router.get('/{slug}')
async def get_learn_article(slug: str):
    logger.info(f'GET /api/learn/{slug}')
    article = get_article_meta(slug)
    if article is None:
        raise HTTPException(status_code=404, detail='文章不存在')

    article_path = ARTICLES_DIR / f'{slug}.md'
    if not article_path.exists():
        raise HTTPException(status_code=404, detail='文章内容不存在')

    return success_response(
        timestamp=current_timestamp(),
        data={
            'article': article,
            'content': article_path.read_text(encoding='utf-8'),
        },
    )
