from fastapi import APIRouter, HTTPException
from services.industry_board_service import IndustryBoardService
from datetime import datetime
import time
from utils.logger import get_logger

logger = get_logger('industry_board_routes')

industry_board_router = APIRouter()


@industry_board_router.get('/latest')
async def get_latest_boards():
    """获取所有板块的最新数据（从 10jqka 实时获取）"""
    start_time = time.time()
    logger.info("GET /api/industry-board/latest - 请求开始")
    try:
        boards = await IndustryBoardService.fetch_board_data()
        
        elapsed = time.time() - start_time
        result = {
            'status': 'success',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'count': len(boards),
            'data': boards
        }
        logger.info(f"GET /api/industry-board/latest - 返回成功，板块数量: {len(boards)}, 耗时: {elapsed:.2f}秒")
        return result
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"GET /api/industry-board/latest - 请求失败，耗时: {elapsed:.2f}秒，错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))