import sqlite3

conn = sqlite3.connect('portfolio.db')
cursor = conn.cursor()

# 检查不同时间维度的EMA数据
cursor.execute('SELECT code, timeframe, ema5, ema10, ema20 FROM monitor_data_cache WHERE timeframe = "1d" LIMIT 3')
rows = cursor.fetchall()
print('日K线的EMA数据:')
for row in rows:
    print(f'{row[0]}: ema5={row[2]}, ema10={row[3]}, ema20={row[4]}')

cursor.execute('SELECT code, timeframe, ema10, ema30, ema60 FROM monitor_data_cache WHERE timeframe = "2d" LIMIT 3')
rows = cursor.fetchall()
print('\n2日K线的EMA数据:')
for row in rows:
    print(f'{row[0]}: ema10={row[2]}, ema30={row[3]}, ema60={row[4]}')

cursor.execute('SELECT code, timeframe, ema7, ema21, ema42 FROM monitor_data_cache WHERE timeframe = "3d" LIMIT 3')
rows = cursor.fetchall()
print('\n3日K线的EMA数据:')
for row in rows:
    print(f'{row[0]}: ema7={row[2]}, ema21={row[3]}, ema42={row[4]}')

conn.close()