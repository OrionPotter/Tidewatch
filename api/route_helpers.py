from collections.abc import Iterable
from typing import Any

from services.monitor_service import MonitorService
from utils.api_helpers import status_message_response, success_response


def serialize_items(items: Iterable[Any]) -> list[dict[str, Any]]:
    return [item.to_dict() for item in items]


def list_response(items: Iterable[Any], *, clean_nan: bool = True) -> dict[str, Any]:
    return success_response(data=serialize_items(items), clean_nan=clean_nan)


def bool_status_response(success: bool, success_message: str, error_message: str) -> dict[str, str]:
    return status_message_response(success, success_message, error_message)


def enrich_monitor_stocks(stocks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for stock in stocks:
        min_price, max_price = MonitorService.calculate_reasonable_price(
            stock.get('eps_forecast'),
            stock.get('reasonable_pe_min'),
            stock.get('reasonable_pe_max'),
        )
        stock['reasonable_price_min'] = min_price
        stock['reasonable_price_max'] = max_price
        stock['valuation_status'] = MonitorService.check_valuation_status(
            stock.get('current_price'),
            stock.get('eps_forecast'),
            stock.get('reasonable_pe_min'),
            stock.get('reasonable_pe_max'),
        )
        stock['technical_status'] = MonitorService.check_technical_status(
            stock.get('current_price'),
            stock.get('ema144'),
            stock.get('ema188'),
        )
        stock['trend'] = MonitorService.check_trend(
            {
                'ema5': stock.get('ema5'),
                'ema10': stock.get('ema10'),
                'ema20': stock.get('ema20'),
                'ema30': stock.get('ema30'),
                'ema60': stock.get('ema60'),
                'ema7': stock.get('ema7'),
                'ema21': stock.get('ema21'),
                'ema42': stock.get('ema42'),
            },
            stock.get('timeframe'),
        )
    return stocks
