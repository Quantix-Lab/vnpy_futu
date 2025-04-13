"""
使用富途接口下载历史数据的示例
"""

import sys
from datetime import datetime, timedelta
from time import sleep
import csv

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import (
    HistoryRequest,
    Exchange,
    Interval
)
from vnpy.trader.utility import load_json, save_json

# 导入富途接口
from vnpy_futu import FutuGateway


def run():
    """
    运行富途历史数据下载示例
    """
    # 创建事件引擎和主引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    # 添加富途接口
    main_engine.add_gateway(FutuGateway)

    # 连接富途接口
    main_engine.connect({
        "gateway_name": "FUTU",
        "API地址": "127.0.0.1",
        "API端口": 11111,
        "市场环境": "正式环境",
        "交易服务器": ["港股"],
    })

    # 等待连接成功
    sleep(5)

    # 设置下载参数
    symbol = "700"
    exchange = Exchange.HKEX
    interval = Interval.DAILY

    end = datetime.now()
    start = end - timedelta(days=365)  # 下载过去一年的数据

    # 创建历史数据请求
    req = HistoryRequest(
        symbol=symbol,
        exchange=exchange,
        interval=interval,
        start=start,
        end=end
    )

    # 获取历史数据
    bars = main_engine.query_history(req, "FUTU")

    if not bars:
        print("获取历史数据失败")
    else:
        print(f"成功获取历史数据: {len(bars)}条")

        # 将数据保存到CSV文件
        filename = f"{symbol}_{exchange.value}_{interval.value}.csv"
        with open(filename, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["datetime", "open", "high", "low", "close", "volume"])

            for bar in bars:
                writer.writerow([
                    bar.datetime.strftime("%Y-%m-%d %H:%M:%S"),
                    bar.open_price,
                    bar.high_price,
                    bar.low_price,
                    bar.close_price,
                    bar.volume
                ])

        print(f"历史数据已保存到文件: {filename}")

    # 关闭引擎
    main_engine.close()
    sys.exit(0)


if __name__ == "__main__":
    run()