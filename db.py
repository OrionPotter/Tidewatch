import sqlite3
import os
from datetime import datetime

# 数据库文件路径
DB_PATH = 'portfolio.db'

def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 创建股票持仓表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            cost_price REAL NOT NULL,
            shares INTEGER NOT NULL
        )
    ''')
    
    # 创建监控股票表
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS monitor_stocks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            timeframe TEXT NOT NULL,
            enabled INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 创建索引以提高查询性能
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_code ON portfolio(code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitor_code ON monitor_stocks(code)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_monitor_enabled ON monitor_stocks(enabled)')
    
    conn.commit()
    conn.close()

def get_all_stocks():
    """获取所有股票数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM portfolio ORDER BY code')
    stocks = cursor.fetchall()
    
    conn.close()
    return stocks

def get_stock_by_code(code):
    """根据代码获取单个股票数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM portfolio WHERE code = ?', (code,))
    stock = cursor.fetchone()
    
    conn.close()
    return stock

def add_stock(code, name, cost_price, shares):
    """添加股票"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO portfolio (code, name, cost_price, shares)
            VALUES (?, ?, ?, ?)
        ''', (code, name, cost_price, shares))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 如果股票代码已存在，返回False
        return False
    finally:
        conn.close()

def update_stock(code, name, cost_price, shares):
    """更新股票信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE portfolio
        SET name = ?, cost_price = ?, shares = ?
        WHERE code = ?
    ''', (name, cost_price, shares, code))
    
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return changed

def delete_stock(code):
    """删除股票"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM portfolio WHERE code = ?', (code,))
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return changed

# ========== 监控股票相关操作 ==========

def get_all_monitor_stocks():
    """获取所有监控股票数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM monitor_stocks ORDER BY code')
    stocks = cursor.fetchall()
    
    conn.close()
    return stocks

def get_enabled_monitor_stocks():
    """获取所有启用的监控股票数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM monitor_stocks WHERE enabled = 1 ORDER BY code')
    stocks = cursor.fetchall()
    
    conn.close()
    return stocks

def get_monitor_stock_by_code(code):
    """根据代码获取单个监控股票数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM monitor_stocks WHERE code = ?', (code,))
    stock = cursor.fetchone()
    
    conn.close()
    return stock

def add_monitor_stock(code, name, timeframe):
    """添加监控股票"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO monitor_stocks (code, name, timeframe)
            VALUES (?, ?, ?)
        ''', (code, name, timeframe))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # 如果股票代码已存在，返回False
        return False
    finally:
        conn.close()

def update_monitor_stock(code, name, timeframe, enabled=None):
    """更新监控股票信息"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    if enabled is not None:
        cursor.execute('''
            UPDATE monitor_stocks
            SET name = ?, timeframe = ?, enabled = ?, updated_at = CURRENT_TIMESTAMP
            WHERE code = ?
        ''', (name, timeframe, enabled, code))
    else:
        cursor.execute('''
            UPDATE monitor_stocks
            SET name = ?, timeframe = ?, updated_at = CURRENT_TIMESTAMP
            WHERE code = ?
        ''', (name, timeframe, code))
    
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return changed

def delete_monitor_stock(code):
    """删除监控股票"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM monitor_stocks WHERE code = ?', (code,))
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return changed

def toggle_monitor_stock(code, enabled):
    """启用/禁用监控股票"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        UPDATE monitor_stocks
        SET enabled = ?, updated_at = CURRENT_TIMESTAMP
        WHERE code = ?
    ''', (enabled, code))
    
    changed = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return changed

def populate_initial_data():
    """从config.py导入初始数据（仅在数据库为空时）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查portfolio表是否为空
    cursor.execute('SELECT COUNT(*) FROM portfolio')
    count = cursor.fetchone()[0]
    
    if count == 0:
        # 从config.py导入初始数据
        try:
            from config import PORTFOLIO_CONFIG
            for code, info in PORTFOLIO_CONFIG.items():
                cursor.execute('''
                    INSERT INTO portfolio (code, name, cost_price, shares)
                    VALUES (?, ?, ?, ?)
                ''', (code, info['name'], info['cost_price'], info['shares']))
            
            conn.commit()
            print(f"已从config.py导入 {len(PORTFOLIO_CONFIG)} 条初始数据")
        except ImportError:
            print("未找到config.py文件，跳过portfolio初始数据导入")
    
    # 检查monitor_stocks表是否为空
    cursor.execute('SELECT COUNT(*) FROM monitor_stocks')
    monitor_count = cursor.fetchone()[0]
    
    if monitor_count == 0:
        # 导入默认监控股票数据
        default_monitor_stocks = [
            ('sh601919', '中远海控', '1d'),
            ('sz000895', '双汇发展', '1d'),
            ('sh600938', '中国海油', '2d'),
            ('sh600886', '国投电力', '3d'),
            ('sh601169', '北京银行', '2d')
        ]
        
        for code, name, timeframe in default_monitor_stocks:
            cursor.execute('''
                INSERT INTO monitor_stocks (code, name, timeframe)
                VALUES (?, ?, ?)
            ''', (code, name, timeframe))
        
        conn.commit()
        print(f"已导入 {len(default_monitor_stocks)} 条默认监控股票数据")
    
    conn.close()

# 初始化数据库
if __name__ == '__main__':
    init_db()
    populate_initial_data()
    print("数据库初始化完成")
    print("当前股票数据:")
    for stock in get_all_stocks():
        print(stock)