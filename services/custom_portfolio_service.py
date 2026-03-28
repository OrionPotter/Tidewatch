import asyncio

import aiohttp

from repositories.custom_portfolio_repository import CustomPortfolioRepository
from services.portfolio_service import PortfolioService
from utils.logger import get_logger

logger = get_logger('custom_portfolio_service')


class CustomPortfolioService:
    @staticmethod
    async def get_portfolio_page_data() -> dict:
        portfolios = await CustomPortfolioRepository.list_portfolios()
        holdings = await CustomPortfolioRepository.list_holdings()

        holdings_by_portfolio: dict[int, list] = {}
        stock_codes: list[str] = []
        for holding in holdings:
            holdings_by_portfolio.setdefault(holding.portfolio_id, []).append(holding)
            if holding.code not in stock_codes:
                stock_codes.append(holding.code)

        price_map = await CustomPortfolioService._get_price_map(stock_codes)

        portfolio_cards = []
        overview = {
            'portfolio_count': len(portfolios),
            'holding_count': len(holdings),
            'total_cost': 0.0,
            'total_market_value': 0.0,
            'total_profit': 0.0,
            'total_profit_rate': 0.0,
        }

        for portfolio in portfolios:
            portfolio_holdings, summary = CustomPortfolioService._build_holding_rows(
                holdings_by_portfolio.get(portfolio.id, []),
                price_map,
            )

            overview['total_cost'] += summary['cost']
            overview['total_market_value'] += summary['market_value']
            overview['total_profit'] += summary['profit']

            portfolio_cards.append(
                {
                    **portfolio.to_dict(),
                    'summary': summary,
                    'holdings': portfolio_holdings,
                }
            )

        overview['total_cost'] = round(overview['total_cost'], 2)
        overview['total_market_value'] = round(overview['total_market_value'], 2)
        overview['total_profit'] = round(overview['total_profit'], 2)
        overview['total_profit_rate'] = round((overview['total_profit'] / overview['total_cost']) * 100, 2) if overview['total_cost'] else 0.0

        return {'portfolios': portfolio_cards, 'overview': overview}

    @staticmethod
    async def get_portfolio_detail(portfolio_id: int) -> dict | None:
        portfolio = await CustomPortfolioRepository.get_portfolio_by_id(portfolio_id)
        if not portfolio:
            return None

        holdings = await CustomPortfolioRepository.list_holdings_by_portfolio(portfolio_id)
        price_map = await CustomPortfolioService._get_price_map([holding.code for holding in holdings])
        holding_rows, summary = CustomPortfolioService._build_holding_rows(holdings, price_map)
        return {
            **portfolio.to_dict(),
            'summary': summary,
            'holdings': holding_rows,
        }

    @staticmethod
    def _build_holding_rows(holdings: list, price_map: dict[str, float]) -> tuple[list[dict], dict]:
        rows = []
        summary = {
            'cost': 0.0,
            'market_value': 0.0,
            'profit': 0.0,
            'profit_rate': 0.0,
            'position_count': 0,
        }
        for holding in holdings:
            current_price = price_map.get(holding.code, holding.cost_price)
            cost_amount = round(holding.cost_price * holding.shares, 2)
            market_value = round(current_price * holding.shares, 2)
            profit = round(market_value - cost_amount, 2)
            profit_rate = round((profit / cost_amount) * 100, 2) if cost_amount else 0.0
            rows.append(
                {
                    **holding.to_dict(),
                    'current_price': round(current_price, 2),
                    'cost_amount': cost_amount,
                    'market_value': market_value,
                    'profit': profit,
                    'profit_rate': profit_rate,
                }
            )
            summary['cost'] += cost_amount
            summary['market_value'] += market_value
            summary['profit'] += profit

        summary['cost'] = round(summary['cost'], 2)
        summary['market_value'] = round(summary['market_value'], 2)
        summary['profit'] = round(summary['profit'], 2)
        summary['profit_rate'] = round((summary['profit'] / summary['cost']) * 100, 2) if summary['cost'] else 0.0
        summary['position_count'] = len(rows)
        return rows, summary

    @staticmethod
    async def _get_price_map(stock_codes: list[str]) -> dict[str, float]:
        if not stock_codes:
            return {}

        headers = PortfolioService._get_headers()
        connector = aiohttp.TCPConnector(limit=10, ttl_dns_cache=300)

        async with aiohttp.ClientSession(headers=headers, connector=connector, trust_env=False) as session:
            tasks = [PortfolioService._fetch_stock_price(session, code) for code in stock_codes]
            fetched = await asyncio.gather(*tasks, return_exceptions=True)

        price_map = {}
        for item in fetched:
            if isinstance(item, Exception):
                logger.warning(f'获取组合行情失败: {item}')
                continue
            code, current_price, _, _ = item
            if code and current_price:
                price_map[code] = float(current_price)
        return price_map
