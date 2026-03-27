import asyncio
import json
import os
from datetime import datetime

import aiohttp
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from repositories.kline_repository import KlineRepository
from repositories.analysis_repository import AnalysisRepository
from utils.logger import get_logger

logger = get_logger('price_action_service')


class PriceActionService:
    EMA_WARMUP = 40
    VALID_PERIODS = {'daily': '101', 'weekly': '102', 'monthly': '103'}

    @staticmethod
    def _build_session() -> requests.Session:
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36',
            'Referer': 'https://quote.eastmoney.com/',
            'Connection': 'close',
        })
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)
        return session

    @staticmethod
    def _strip_prefix(code: str) -> str:
        for prefix in ('sh', 'sz', 'bj'):
            if code.lower().startswith(prefix):
                return code[len(prefix):]
        return code

    @staticmethod
    def _get_market_code(code: str) -> int:
        return 1 if code.startswith('6') else 0

    @staticmethod
    def _normalize_code_candidates(code: str) -> list[str]:
        raw = PriceActionService._strip_prefix(code)
        candidates = [code, raw]
        if not raw.startswith(('sh', 'sz', 'bj')):
            if raw.startswith(('6', '5')):
                candidates.append(f'sh{raw}')
            elif raw.startswith(('0', '3')):
                candidates.append(f'sz{raw}')
            elif raw.startswith(('4', '8', '9')):
                candidates.append(f'bj{raw}')
        deduped = []
        for item in candidates:
            if item and item not in deduped:
                deduped.append(item)
        return deduped

    @staticmethod
    def _compute_ema(series: pd.Series, span: int = 20) -> pd.Series:
        return series.ewm(span=span, adjust=False).mean()

    @staticmethod
    def _compute_bar_metrics(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['bar_range'] = df['high'] - df['low']
        df['body'] = (df['close'] - df['open']).abs()
        safe_range = df['bar_range'].replace(0, float('nan'))
        df['body_ratio'] = (df['body'] / safe_range).round(2).fillna(0)
        df['upper_wick'] = df['high'] - df[['open', 'close']].max(axis=1)
        df['lower_wick'] = df[['open', 'close']].min(axis=1) - df['low']
        df['upper_wick_ratio'] = (df['upper_wick'] / safe_range).round(2).fillna(0)
        df['lower_wick_ratio'] = (df['lower_wick'] / safe_range).round(2).fillna(0)
        df['close_position'] = ((df['close'] - df['low']) / safe_range).round(2).fillna(0.5)
        return df

    @staticmethod
    def _classify_bar_type(df: pd.DataFrame) -> pd.Series:
        types = pd.Series('neutral', index=df.index)
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        is_bull = df['close'] > df['open']
        is_bear = df['close'] < df['open']
        types[df['body_ratio'] < 0.1] = 'doji'
        types[(df['upper_wick'] > df['body']) & (df['close_position'] < 0.6)] = 'signal_bear'
        types[(df['lower_wick'] > df['body']) & (df['close_position'] > 0.4)] = 'signal_bull'
        types[is_bear & (df['body_ratio'] >= 0.6) & (df['close_position'] <= 0.5)] = 'trend_bear'
        types[is_bull & (df['body_ratio'] >= 0.6) & (df['close_position'] >= 0.5)] = 'trend_bull'
        types[(df['high'] < prev_high) & (df['low'] > prev_low)] = 'inside_bar'
        types[(df['high'] > prev_high) & (df['low'] < prev_low)] = 'outside_bar'
        return types

    @staticmethod
    def _detect_gaps(df: pd.DataFrame) -> pd.Series:
        prev_high = df['high'].shift(1)
        prev_low = df['low'].shift(1)
        gaps = pd.Series(None, index=df.index, dtype=object)
        gaps[df['low'] > prev_high] = 'gap_up'
        gaps[df['high'] < prev_low] = 'gap_down'
        return gaps

    @staticmethod
    def _resample_from_daily(df: pd.DataFrame, period: str) -> pd.DataFrame:
        if period == 'daily':
            return df

        rule = 'W-FRI' if period == 'weekly' else 'ME'
        agg = {
            'open': 'first',
            'close': 'last',
            'high': 'max',
            'low': 'min',
            'volume': 'sum',
            'amount': 'sum',
        }
        resampled = (
            df.set_index('date')
            .resample(rule)
            .agg(agg)
            .dropna()
            .reset_index()
        )
        return resampled

    @staticmethod
    def _build_analysis_payload(df: pd.DataFrame, code: str, stock_name: str, period: str, count: int) -> dict:
        df = df.copy()
        df['ema20'] = PriceActionService._compute_ema(df['close'], span=20).round(2)
        df['ema20_slope'] = (df['ema20'].pct_change() * 100).round(3).fillna(0)
        ema_safe = df['ema20'].replace(0, float('nan'))
        df['ema20_distance'] = (((df['close'] - df['ema20']) / ema_safe) * 100).round(2).fillna(0)
        df = PriceActionService._compute_bar_metrics(df)
        df['bar_type'] = PriceActionService._classify_bar_type(df)
        df['gap'] = PriceActionService._detect_gaps(df)
        if len(df) > count:
            df = df.tail(count).reset_index(drop=True)

        klines = []
        for _, row in df.iterrows():
            item = {
                'date': row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else str(row['date']),
                'open': round(float(row['open']), 2),
                'high': round(float(row['high']), 2),
                'low': round(float(row['low']), 2),
                'close': round(float(row['close']), 2),
                'volume': round(float(row.get('volume', 0))),
                'amount': round(float(row.get('amount', 0)), 2),
                'change_pct': round(float(row.get('change_pct', 0)), 2) if 'change_pct' in row else 0,
                'turnover': round(float(row.get('turnover', 0)), 2) if 'turnover' in row else 0,
                'amplitude': round(float(row.get('amplitude', 0)), 2) if 'amplitude' in row else round(((row['high'] - row['low']) / row['close']) * 100, 2) if row['close'] else 0,
                'ema20': float(row['ema20']),
                'ema20_slope': float(row['ema20_slope']),
                'ema20_distance': float(row['ema20_distance']),
                'body_ratio': float(row['body_ratio']),
                'upper_wick_ratio': float(row['upper_wick_ratio']),
                'lower_wick_ratio': float(row['lower_wick_ratio']),
                'close_position': float(row['close_position']),
                'bar_type': row['bar_type'],
            }
            if pd.notna(row.get('gap')):
                item['gap'] = row['gap']
            klines.append(item)

        return {
            'code': PriceActionService._strip_prefix(code),
            'name': stock_name,
            'period': period,
            'count': len(klines),
            'klines': klines,
        }

    @staticmethod
    async def _fetch_kline_from_db(code: str, count: int, period: str) -> dict | None:
        for candidate in PriceActionService._normalize_code_candidates(code):
            df = await KlineRepository.get_by_code(candidate, limit=max(count * 6, 300))
            if df is None or df.empty:
                continue

            renamed = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
            }).copy()
            if 'date' not in renamed.columns:
                continue
            renamed['date'] = pd.to_datetime(renamed['date'], errors='coerce')
            renamed = renamed.dropna(subset=['date']).sort_values('date')
            if renamed.empty:
                continue

            resampled = PriceActionService._resample_from_daily(renamed, period)
            if resampled.empty:
                continue

            return PriceActionService._build_analysis_payload(
                resampled,
                code=candidate,
                stock_name=PriceActionService._strip_prefix(candidate),
                period=period,
                count=count,
            )
        return None

    @staticmethod
    def _fetch_kline_sync(code: str, count: int, period: str) -> dict | None:
        session = PriceActionService._build_session()
        raw_code = PriceActionService._strip_prefix(code)
        fetch_count = count + PriceActionService.EMA_WARMUP
        market_code = PriceActionService._get_market_code(raw_code)

        try:
            name_response = session.get(
                'https://push2.eastmoney.com/api/qt/stock/get',
                params={
                    'fltt': '2',
                    'invt': '2',
                    'fields': 'f57,f58',
                    'secid': f'{market_code}.{raw_code}',
                },
                timeout=10,
            )
            name_data = name_response.json()
            stock_name = (name_data.get('data') or {}).get('f58', raw_code)
        except Exception:
            stock_name = raw_code

        response = session.get(
            'https://push2his.eastmoney.com/api/qt/stock/kline/get',
            params={
                'secid': f'{market_code}.{raw_code}',
                'ut': 'fa5fd1943c7b386f172d6893dbfba10b',
                'fields1': 'f1,f2,f3,f4,f5,f6',
                'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116',
                'klt': PriceActionService.VALID_PERIODS[period],
                'fqt': '1',
                'beg': '19700101',
                'end': datetime.now().strftime('%Y%m%d'),
                'lmt': fetch_count,
            },
            timeout=15,
        )
        payload = response.json()
        rows = ((payload.get('data') or {}).get('klines')) or []
        if not rows:
            return None

        df = pd.DataFrame([
            {
                'date': arr[0],
                'open': float(arr[1]),
                'close': float(arr[2]),
                'high': float(arr[3]),
                'low': float(arr[4]),
                'volume': float(arr[5]),
                'amount': float(arr[6]),
                'amplitude': float(arr[7]),
                'change_pct': float(arr[8]),
                'change': float(arr[9]),
                'turnover': float(arr[10]),
            }
            for arr in (line.split(',') for line in rows)
        ])

        df['ema20'] = PriceActionService._compute_ema(df['close'], span=20).round(2)
        df['ema20_slope'] = (df['ema20'].pct_change() * 100).round(3).fillna(0)
        ema_safe = df['ema20'].replace(0, float('nan'))
        df['ema20_distance'] = (((df['close'] - df['ema20']) / ema_safe) * 100).round(2).fillna(0)
        df = PriceActionService._compute_bar_metrics(df)
        df['bar_type'] = PriceActionService._classify_bar_type(df)
        df['gap'] = PriceActionService._detect_gaps(df)
        if len(df) > count:
            df = df.tail(count).reset_index(drop=True)

        klines = []
        for _, row in df.iterrows():
            item = {
                'date': str(row['date']),
                'open': round(float(row['open']), 2),
                'high': round(float(row['high']), 2),
                'low': round(float(row['low']), 2),
                'close': round(float(row['close']), 2),
                'volume': round(float(row.get('volume', 0))),
                'amount': round(float(row.get('amount', 0)), 2),
                'change_pct': round(float(row.get('change_pct', 0)), 2),
                'turnover': round(float(row.get('turnover', 0)), 2),
                'amplitude': round(float(row.get('amplitude', 0)), 2),
                'ema20': float(row['ema20']),
                'ema20_slope': float(row['ema20_slope']),
                'ema20_distance': float(row['ema20_distance']),
                'body_ratio': float(row['body_ratio']),
                'upper_wick_ratio': float(row['upper_wick_ratio']),
                'lower_wick_ratio': float(row['lower_wick_ratio']),
                'close_position': float(row['close_position']),
                'bar_type': row['bar_type'],
            }
            if pd.notna(row['gap']):
                item['gap'] = row['gap']
            klines.append(item)

        return {
            'code': raw_code,
            'name': stock_name,
            'period': period,
            'count': len(klines),
            'klines': klines,
        }

    @staticmethod
    async def fetch_kline_data(code: str, count: int, period: str) -> dict | None:
        db_data = await PriceActionService._fetch_kline_from_db(code, count, period)
        if db_data:
            logger.info(f'Price action analysis using database kline data for {code} ({period})')
            return db_data

        if os.getenv('ANALYSIS_ALLOW_NETWORK_FALLBACK', 'false').lower() != 'true':
            logger.warning(f'No local kline data found for {code}, and network fallback is disabled')
            return None

        logger.warning(f'Falling back to remote kline fetch for {code} ({period})')
        return await asyncio.to_thread(PriceActionService._fetch_kline_sync, code, count, period)

    @staticmethod
    def _build_prompt(kline_data: dict) -> str:
        return f"""你是 A 股价格行为分析师，分析框架参考 Al Brooks Price Action。

硬性要求：
1. 只给 A 股做多方向建议，不提供做空建议。
2. 必须基于提供的 K 线数据判断：市场周期、关键 K 线、结构、支撑阻力、入场机会、风险点。
3. 如果没有清晰做多机会，要明确写“观望”，不要勉强给买入建议。
4. 所有结论必须和提供的数据对应，不要空泛。
5. 用中文输出，输出为 Markdown。

请严格按以下结构输出：
# {kline_data['name']}（{kline_data['code']}）价格行为分析
## 1. 当前市场周期
## 2. 关键K线与结构判断
## 3. 支撑位与阻力位
## 4. 做多机会评估
## 5. 风险提示与无效条件
## 6. 操作建议

操作建议部分必须包含：
- 结论：做多 / 观望 / 减仓观察
- 理由：
- 关注价位：
- 失效条件：

下面是待分析的 K 线 JSON：
{json.dumps(kline_data, ensure_ascii=False, indent=2)}
"""

    @staticmethod
    def _build_base_url_candidates(base_url: str) -> list[str]:
        normalized = base_url.rstrip('/')
        candidates = [normalized]
        if not normalized.endswith('/v1'):
            candidates.append(f'{normalized}/v1')
        deduped = []
        for item in candidates:
            if item and item not in deduped:
                deduped.append(item)
        return deduped

    @staticmethod
    async def _call_llm_once(base_url: str, api_style: str, model_name: str, api_key: str, prompt: str) -> tuple[str, str]:
        if api_style == 'responses':
            url = f'{base_url}/responses'
            payload = {
                'model': model_name,
                'temperature': 0.2,
                'input': [
                    {'role': 'system', 'content': [{'type': 'text', 'text': '你是专业的 A 股价格行为分析师。'}]},
                    {'role': 'user', 'content': [{'type': 'text', 'text': prompt}]},
                ],
            }
        else:
            url = f'{base_url}/chat/completions'
            payload = {
                'model': model_name,
                'temperature': 0.2,
                'messages': [
                    {'role': 'system', 'content': '你是专业的 A 股价格行为分析师。'},
                    {'role': 'user', 'content': prompt},
                ],
            }

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, headers=headers, json=payload, timeout=aiohttp.ClientTimeout(total=120)) as response:
                text = await response.text()
                if response.status >= 400:
                    raise RuntimeError(f'{api_style} {url} -> HTTP {response.status} - {text[:500]}')
                data = json.loads(text)
                if api_style == 'responses':
                    content = data.get('output_text')
                    if not content:
                        chunks = []
                        for item in data.get('output', []):
                            for content_item in item.get('content', []):
                                if content_item.get('type') in {'output_text', 'text'}:
                                    chunks.append(content_item.get('text', ''))
                        content = '\n'.join(chunk for chunk in chunks if chunk).strip()
                else:
                    content = data['choices'][0]['message']['content']
                if not content:
                    raise RuntimeError(f'{api_style} {url} -> 模型返回内容为空')
                return model_name, content

    @staticmethod
    async def _call_llm(prompt: str) -> tuple[str, str]:
        base_url = os.getenv('OPENAI_BASE_URL', '').rstrip('/')
        api_key = os.getenv('OPENAI_API_KEY', '')
        model_name = os.getenv('OPENAI_MODEL', '')
        api_style = os.getenv('OPENAI_API_STYLE', 'chat_completions').strip().lower()
        if not base_url or not api_key or not model_name:
            raise ValueError('OpenAI 模型配置不完整，请检查 .env 中的 OPENAI_BASE_URL / OPENAI_API_KEY / OPENAI_MODEL')
        if api_style not in {'chat_completions', 'responses'}:
            raise ValueError('OPENAI_API_STYLE 仅支持 chat_completions 或 responses')

        styles = [api_style, 'responses' if api_style == 'chat_completions' else 'chat_completions']
        tried = []
        for candidate_base_url in PriceActionService._build_base_url_candidates(base_url):
            for candidate_style in styles:
                key = (candidate_base_url, candidate_style)
                if key in tried:
                    continue
                tried.append(key)
                try:
                    logger.info(f'Calling LLM via {candidate_style} at {candidate_base_url}')
                    return await PriceActionService._call_llm_once(
                        candidate_base_url,
                        candidate_style,
                        model_name,
                        api_key,
                        prompt,
                    )
                except Exception as exc:
                    logger.warning(f'LLM call failed via {candidate_style} at {candidate_base_url}: {exc}')

        raise RuntimeError('模型调用失败：已尝试 chat_completions / responses 以及 base_url 和 base_url/v1 组合，仍未成功')

    @staticmethod
    async def generate_analysis(code: str, count: int = 60, period: str = 'daily') -> dict:
        if period not in PriceActionService.VALID_PERIODS:
            raise ValueError('period 仅支持 daily / weekly / monthly')

        kline_data = await PriceActionService.fetch_kline_data(code, count, period)
        if not kline_data:
            raise ValueError('未获取到可分析的 K 线数据')

        prompt = PriceActionService._build_prompt(kline_data)
        model_name, analysis_markdown = await PriceActionService._call_llm(prompt)

        report_id = await AnalysisRepository.create_report(
            code=kline_data['code'],
            stock_name=kline_data['name'],
            period=period,
            kline_count=kline_data['count'],
            model_name=model_name,
            prompt_text=prompt,
            input_payload=kline_data,
            analysis_markdown=analysis_markdown,
        )

        return {
            'id': report_id,
            'code': kline_data['code'],
            'stock_name': kline_data['name'],
            'period': period,
            'kline_count': kline_data['count'],
            'model_name': model_name,
            'analysis_markdown': analysis_markdown,
            'input_payload': kline_data,
        }

    @staticmethod
    async def list_reports(limit: int = 50) -> list[dict]:
        return await AnalysisRepository.list_reports(limit=limit)

    @staticmethod
    async def get_report(report_id: int) -> dict | None:
        return await AnalysisRepository.get_report(report_id)
