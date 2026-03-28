from models.custom_portfolio import CustomPortfolio, CustomPortfolioHolding
from utils.db import get_db_conn
from utils.logger import get_logger

logger = get_logger('custom_portfolio_repository')


class CustomPortfolioRepository:
    _tables_ready = False

    @classmethod
    async def ensure_tables(cls) -> None:
        if cls._tables_ready:
            return

        async with get_db_conn() as conn:
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS custom_portfolios (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(120) NOT NULL,
                    notes TEXT DEFAULT '',
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            await conn.execute(
                '''
                CREATE TABLE IF NOT EXISTS custom_portfolio_holdings (
                    id SERIAL PRIMARY KEY,
                    portfolio_id INTEGER NOT NULL REFERENCES custom_portfolios(id) ON DELETE CASCADE,
                    code VARCHAR(20) NOT NULL,
                    name VARCHAR(80) NOT NULL,
                    cost_price NUMERIC(12, 3) NOT NULL CHECK (cost_price >= 0),
                    shares INTEGER NOT NULL CHECK (shares > 0),
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                '''
            )
            await conn.execute(
                '''
                CREATE INDEX IF NOT EXISTS idx_custom_portfolio_holdings_portfolio_id
                ON custom_portfolio_holdings(portfolio_id)
                '''
            )
            await conn.execute(
                '''
                CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_portfolio_holdings_unique
                ON custom_portfolio_holdings(portfolio_id, code)
                '''
            )
        cls._tables_ready = True

    @staticmethod
    def _normalize_timestamp(value) -> str:
        return value.strftime('%Y-%m-%d %H:%M:%S')

    @classmethod
    async def list_portfolios(cls) -> list[CustomPortfolio]:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            rows = await conn.fetch(
                '''
                SELECT id, name, notes, created_at, updated_at
                FROM custom_portfolios
                ORDER BY updated_at DESC, id DESC
                '''
            )
        return [
            CustomPortfolio(
                id=row['id'],
                name=row['name'],
                notes=row['notes'],
                created_at=cls._normalize_timestamp(row['created_at']),
                updated_at=cls._normalize_timestamp(row['updated_at']),
            )
            for row in rows
        ]

    @classmethod
    async def list_holdings(cls) -> list[CustomPortfolioHolding]:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            rows = await conn.fetch(
                '''
                SELECT id, portfolio_id, code, name, cost_price, shares, created_at, updated_at
                FROM custom_portfolio_holdings
                ORDER BY portfolio_id ASC, id ASC
                '''
            )
        return [
            CustomPortfolioHolding(
                id=row['id'],
                portfolio_id=row['portfolio_id'],
                code=row['code'],
                name=row['name'],
                cost_price=float(row['cost_price']),
                shares=row['shares'],
                created_at=cls._normalize_timestamp(row['created_at']),
                updated_at=cls._normalize_timestamp(row['updated_at']),
            )
            for row in rows
        ]

    @classmethod
    async def get_portfolio_by_id(cls, portfolio_id: int) -> CustomPortfolio | None:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            row = await conn.fetchrow(
                '''
                SELECT id, name, notes, created_at, updated_at
                FROM custom_portfolios
                WHERE id = $1
                ''',
                portfolio_id,
            )
        if not row:
            return None
        return CustomPortfolio(
            id=row['id'],
            name=row['name'],
            notes=row['notes'],
            created_at=cls._normalize_timestamp(row['created_at']),
            updated_at=cls._normalize_timestamp(row['updated_at']),
        )

    @classmethod
    async def list_holdings_by_portfolio(cls, portfolio_id: int) -> list[CustomPortfolioHolding]:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            rows = await conn.fetch(
                '''
                SELECT id, portfolio_id, code, name, cost_price, shares, created_at, updated_at
                FROM custom_portfolio_holdings
                WHERE portfolio_id = $1
                ORDER BY id ASC
                ''',
                portfolio_id,
            )
        return [
            CustomPortfolioHolding(
                id=row['id'],
                portfolio_id=row['portfolio_id'],
                code=row['code'],
                name=row['name'],
                cost_price=float(row['cost_price']),
                shares=row['shares'],
                created_at=cls._normalize_timestamp(row['created_at']),
                updated_at=cls._normalize_timestamp(row['updated_at']),
            )
            for row in rows
        ]

    @classmethod
    async def create_portfolio(cls, name: str, notes: str, holdings: list[dict]) -> int:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            async with conn.transaction():
                portfolio_id = await conn.fetchval(
                    '''
                    INSERT INTO custom_portfolios (name, notes)
                    VALUES ($1, $2)
                    RETURNING id
                    ''',
                    name,
                    notes,
                )
                for holding in holdings:
                    await conn.execute(
                        '''
                        INSERT INTO custom_portfolio_holdings (portfolio_id, code, name, cost_price, shares)
                        VALUES ($1, $2, $3, $4, $5)
                        ''',
                        portfolio_id,
                        holding['code'],
                        holding['name'],
                        holding['cost_price'],
                        holding['shares'],
                    )
        return portfolio_id

    @classmethod
    async def add_holding(cls, portfolio_id: int, code: str, name: str, cost_price: float, shares: int) -> tuple[bool, str]:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            async with conn.transaction():
                exists = await conn.fetchval('SELECT 1 FROM custom_portfolios WHERE id = $1', portfolio_id)
                if not exists:
                    return False, 'Portfolio not found'
                try:
                    await conn.execute(
                        '''
                        INSERT INTO custom_portfolio_holdings (portfolio_id, code, name, cost_price, shares)
                        VALUES ($1, $2, $3, $4, $5)
                        ''',
                        portfolio_id,
                        code,
                        name,
                        cost_price,
                        shares,
                    )
                except Exception as exc:
                    message = str(exc).lower()
                    if 'unique' in message or 'duplicate' in message:
                        return False, 'Duplicate stock code in this portfolio'
                    raise
                await conn.execute(
                    'UPDATE custom_portfolios SET updated_at = CURRENT_TIMESTAMP WHERE id = $1',
                    portfolio_id,
                )
        return True, 'Holding added'

    @classmethod
    async def delete_portfolio(cls, portfolio_id: int) -> bool:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            result = await conn.execute('DELETE FROM custom_portfolios WHERE id = $1', portfolio_id)
        return 'DELETE 1' in result

    @classmethod
    async def delete_holding(cls, portfolio_id: int, holding_id: int) -> bool:
        await cls.ensure_tables()
        async with get_db_conn() as conn:
            async with conn.transaction():
                result = await conn.execute(
                    'DELETE FROM custom_portfolio_holdings WHERE id = $1 AND portfolio_id = $2',
                    holding_id,
                    portfolio_id,
                )
                if 'DELETE 1' not in result:
                    return False
                await conn.execute(
                    'UPDATE custom_portfolios SET updated_at = CURRENT_TIMESTAMP WHERE id = $1',
                    portfolio_id,
                )
        return True
