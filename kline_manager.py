import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import os
from db import save_kline_data, get_kline_data_from_db, get_latest_kline_date, get_stocks_need_update
import time

# 清除代理设置
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)
os.environ.pop('all_proxy', None)

def update_stock_kline_data(code, force_update=False):
    """
    更新单只股票的K线数据
    force_update: 是否强制更新所有数据（False时只增量更新）
    """
    try:
        # 转换股票代码格式为腾讯API格式
        if code.startswith('sh'):
            symbol = 'sh' + code[2:]
        elif code.startswith('sz'):
            symbol = 'sz' + code[2:]
        else:
            # 如果没有前缀，根据代码判断市场
            if code.startswith('6'):  # 上交所
                symbol = 'sh' + code
            elif code.startswith('0') or code.startswith('3'):  # 深交所
                symbol = 'sz' + code
            else:
                symbol = code
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 开始更新 {code} 的K线数据...")
        
        # 确定数据获取范围
        if force_update:
            # 强制更新：获取近三年数据
            start_date = "20200101"
        else:
            # 增量更新：从最新日期的下一天开始
            latest_date = get_latest_kline_date(code)
            if latest_date:
                # 将最新日期加一天作为开始日期
                next_day = (datetime.strptime(latest_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y%m%d')
                start_date = next_day
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 增量更新，从 {start_date} 开始")
            else:
                # 没有历史数据，获取近三年数据
                start_date = "20200101"
        
        # 获取当前日期作为结束日期
        end_date = datetime.now().strftime('%Y%m%d')
        
        # 如果开始日期已经大于等于结束日期，说明数据是最新的
        if start_date >= end_date:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 数据已是最新，跳过更新")
            return True
        
        # 使用腾讯API获取K线数据
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 调用腾讯API获取 {symbol} 的历史数据 ({start_date} 到 {end_date})...")
        df = ak.stock_zh_a_hist_tx(symbol=symbol, start_date=start_date, end_date=end_date, adjust="qfq")
        
        if df is None or df.empty:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 没有获取到新数据")
            return True
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 腾讯API返回 {len(df)} 条新数据")
        
        # 转换列名以保持兼容性
        if 'date' in df.columns and 'close' in df.columns:
            df = df.rename(columns={'date': '日期', 'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低'})
        
        # 保存到数据库
        success = save_kline_data(code, df)
        if success:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} K线数据更新完成")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} K线数据保存失败")
            return False
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 更新 {code} K线数据失败: {str(e)}")
        return False

def batch_update_kline_data(force_update=False, max_workers=3):
    """
    批量更新所有监控股票的K线数据
    force_update: 是否强制更新所有数据
    max_workers: 最大并发数
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # 获取需要更新的股票列表
    if force_update:
        from db import get_enabled_monitor_stocks
        stocks = get_enabled_monitor_stocks()
        stock_codes = [stock[1] for stock in stocks]  # stock[1] 是股票代码
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 强制更新所有 {len(stock_codes)} 只股票的K线数据")
    else:
        stock_codes = get_stocks_need_update(days=1)  # 获取超过1天未更新的股票
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 增量更新 {len(stock_codes)} 只股票的K线数据")
    
    if not stock_codes:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 没有股票需要更新")
        return True
    
    success_count = 0
    total_count = len(stock_codes)
    
    # 使用线程池并发更新
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_code = {executor.submit(update_stock_kline_data, code, force_update): code for code in stock_codes}
        
        # 收集结果
        for future in as_completed(future_to_code):
            code = future_to_code[future]
            try:
                success = future.result()
                if success:
                    success_count += 1
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 更新完成 ({success_count}/{total_count})")
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} 更新异常: {e}")
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] K线数据批量更新完成，成功: {success_count}/{total_count}")
    return success_count == total_count

def get_kline_data_with_cache(code, period='daily', count=250):
    """
    获取股票K线数据（优先从本地数据库读取）
    code: 股票代码
    period: 周期 ('daily'=日K, '2d'=2日, '3d'=3日)
    count: 获取的数据条数
    """
    try:
        # 从本地数据库获取近三年的日K线数据
        df = get_kline_data_from_db(code, limit=1000)  # 获取足够的数据
        
        if df is None or df.empty:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 本地数据库中没有 {code} 的K线数据")
            return None
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 从本地数据库获取到 {code} 的 {len(df)} 条K线数据")
        
        # 根据周期重新采样数据
        if period == '2d':
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 重新采样为2日K线...")
            # 2日K线，重新采样
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.set_index('日期')
            df_2d = df.resample('2B').agg({
                '开盘': 'first',
                '收盘': 'last',
                '最高': 'max',
                '最低': 'min',
                'amount': 'sum'
            }).dropna()
            df = df_2d.reset_index()
            df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 2日K线重采样完成，数据量: {len(df)}")
        elif period == '3d':
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 重新采样为3日K线...")
            # 3日K线，重新采样
            df['日期'] = pd.to_datetime(df['日期'])
            df = df.set_index('日期')
            df_3d = df.resample('3B').agg({
                '开盘': 'first',
                '收盘': 'last',
                '最高': 'max',
                '最低': 'min',
                'amount': 'sum'
            }).dropna()
            df = df_3d.reset_index()
            df['日期'] = df['日期'].dt.strftime('%Y-%m-%d')
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 3日K线重采样完成，数据量: {len(df)}")
        # 默认日K线不需要重新采样
        
        # 取最近count条数据
        if len(df) > count:
            df = df.tail(count)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 数据截取为最近 {count} 条")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {code} K线数据准备完成，最终数据量: {len(df)}")
        return df
        
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 获取 {code} K线数据失败: {str(e)}")
        return None

# 可以直接运行此文件进行测试
if __name__ == '__main__':
    print("开始批量更新K线数据...")
    success = batch_update_kline_data(force_update=True)
    if success:
        print("K线数据更新成功")
    else:
        print("K线数据更新失败")