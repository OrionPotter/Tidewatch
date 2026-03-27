from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Any

templates = Jinja2Templates(directory='templates')


def render_page(template_name: str, request: Request, **context: Any) -> HTMLResponse:
    return templates.TemplateResponse(template_name, {'request': request, **context})
