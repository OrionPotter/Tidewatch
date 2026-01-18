import asyncio
from typing import List, Dict
import logging
import akshare as ak
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)

# 使用独立的线程池
_executor = ThreadPoolExecutor(max_workers=2)


class IndustryBoardService:
    """行业板块数据服务 - 使用 akshare 获取数据"""

    @staticmethod
    async def fetch_board_data() -> List[Dict]:
        """从 akshare 获取行业板块资金流向数据
        
        Returns:
            list: 行业板块数据列表
        """
        try:
            logger.info("开始获取行业板块资金流向数据...")
            
            # 使用独立线程池执行，设置20秒超时
            df = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    _executor,
                    lambda: ak.stock_sector_fund_flow_rank(indicator="今日")
                ),
                timeout=20
            )
            
            if df is None or df.empty:
                logger.warning("获取行业板块数据失败：返回数据为空")
                return []
            
            # 使用列表推导式优化转换速度
            board_data_list = []
            for idx in range(len(df)):
                try:
                    row = df.iloc[idx]
                    
                    # 净流入金额（单位：元，转换为亿元）
                    net_inflow = row.get('今日主力净流入-净额', 0)
                    net_inflow_yi = net_inflow / 100000000 if net_inflow else 0
                    
                    # 超大单净流入
                    super_inflow = row.get('今日超大单净流入-净额', 0)
                    super_inflow_yi = super_inflow / 100000000 if super_inflow else 0
                    
                    # 大单净流入
                    big_inflow = row.get('今日大单净流入-净额', 0)
                    big_inflow_yi = big_inflow / 100000000 if big_inflow else 0
                    
                    # 计算流入和流出
                    if net_inflow_yi >= 0:
                        inflow = net_inflow_yi
                        outflow = 0
                    else:
                        inflow = 0
                        outflow = abs(net_inflow_yi)
                    
                    board_data = {
                        'rank': idx + 1,
                        'board_code': None,
                        'board_name': str(row.get('名称', '')),
                        'change_percent': float(row.get('今日涨跌幅', 0)),
                        'inflow': inflow,
                        'outflow': outflow,
                        'net_amount': net_inflow_yi,
                        'super_inflow': super_inflow_yi,
                        'big_inflow': big_inflow_yi,
                    }
                    board_data_list.append(board_data)
                except Exception as e:
                    logger.warning(f"解析板块数据失败（行 {idx}）: {str(e)}")
                    continue
            
            logger.info(f"成功获取 {len(board_data_list)} 个行业板块数据")
            return board_data_list
            
        except asyncio.TimeoutError:
            logger.error("获取行业板块数据超时（20秒）")
            return []
        except Exception as e:
            logger.error(f"获取行业板块数据失败: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []