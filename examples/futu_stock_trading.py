"""
使用富途网关进行股票交易的示例
"""

import sys
from datetime import datetime
from time import sleep

from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import (
    SubscribeRequest,
    OrderRequest,
    Direction,
    Exchange,
    OrderType,
    Product,
    Offset,
    Status
)

# 导入富途网关
from vnpy_futu import FutuGateway


def run():
    """
    运行富途股票交易示例
    """
    # 创建事件引擎和主引擎
    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    # 添加富途网关
    main_engine.add_gateway(FutuGateway)

    # 连接富途网关
    main_engine.connect({
        "gateway_name": "FUTU",
        "API地址": "127.0.0.1",
        "API端口": 11111,
        "市场环境": "模拟环境",     # 可选：正式环境 或 模拟环境
        "交易服务器": ["港股", "美股", "A股"],   # 可选多个
    })

    # 等待连接成功
    sleep(5)

    # 订阅行情
    req = SubscribeRequest(
        symbol="700",         # 腾讯股票
        exchange=Exchange.HKEX
    )
    main_engine.subscribe(req, "FUTU")

    sleep(3)

    # 获取当前股票价格
    symbol = "700.HKEX"
    tick = main_engine.get_tick(symbol)
    if tick:
        print(f"当前行情 - 股票: {symbol}, 最新价: {tick.last_price}, 买一价: {tick.bid_price_1}, 卖一价: {tick.ask_price_1}")

        # 委托下单 (限价单-买入)
        price = tick.bid_price_1  # 以买一价格买入
        volume = 100              # 买入100股

        order_req = OrderRequest(
            symbol="700",
            exchange=Exchange.HKEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=volume,
            price=price,
            offset=Offset.NONE,   # 股票无需指定开平
            reference="demo"      # 引用信息
        )

        # 提交委托
        vt_orderid = main_engine.send_order(order_req, "FUTU")
        print(f"委托提交成功, vt_orderid: {vt_orderid}")

        # 等待委托成功
        sleep(2)

        # 获取委托状态
        order = main_engine.get_order(vt_orderid)
        if order:
            print(f"委托状态: {order.status.value}")

            # 如果委托未全部成交，则撤单
            if order.status != Status.ALLTRADED:
                main_engine.cancel_order(vt_orderid, "FUTU")
                print(f"已发送撤单请求: {vt_orderid}")
    else:
        print(f"未能获取行情数据: {symbol}")

    # 查询账户资金和持仓
    sleep(2)

    accounts = main_engine.get_all_accounts()
    for account in accounts:
        print(f"账户: {account.accountid}, 余额: {account.balance}, 可用: {account.available}")

    positions = main_engine.get_all_positions()
    for position in positions:
        print(f"持仓: {position.vt_symbol}, 方向: {position.direction.value}, 数量: {position.volume}, 可平: {position.available}, 成本: {position.price}, 市值: {position.pnl}")

    # 等待10秒，让用户查看结果
    print("等待10秒后退出...")
    sleep(10)

    # 关闭引擎
    main_engine.close()
    sys.exit(0)


if __name__ == "__main__":
    run()