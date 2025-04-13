"""
Futu Symbol Rules

HSI-HKD-IDX  HKEX
700-HKD-STK  HKEX
AAPL-USD-STK NASDAQ
ES-202212-USD-FUT CME

Futu API 同时支持股票、期货、指数等产品的交易
"""

import pytz
from datetime import datetime
from copy import copy
from typing import Any, Dict, List, Tuple, Optional
from threading import Thread

from futu import (
    OpenQuoteContext,
    OpenHKTradeContext,
    OpenUSTradeContext,
    OpenCNTradeContext,
    TrdEnv,
    Market,
    SecurityType,
    ModifyOrderOp,
    OrderStatus,
    OrderType as FutuOrderType,
    RET_OK,
    RET_ERROR,
    KLType,
    SubType,
    SortDir,
    TrdSide,
    StockQuoteHandlerBase,
    OrderBookHandlerBase,
    TradeOrderHandlerBase,
    TradeDealHandlerBase
)

from vnpy.event import EventEngine
from vnpy.trader.event import EVENT_TIMER
from vnpy.trader.constant import (
    Direction,
    Exchange,
    OrderType,
    Product,
    Status,
    Interval,
    Currency
)
from vnpy.trader.gateway import BaseGateway
from vnpy.trader.object import (
    TickData,
    OrderData,
    TradeData,
    PositionData,
    AccountData,
    ContractData,
    BarData,
    OrderRequest,
    CancelRequest,
    SubscribeRequest,
    HistoryRequest
)

# 交易所映射
EXCHANGE_VT2FUTU: Dict[Exchange, Market] = {
    Exchange.SEHK: Market.HK,
    Exchange.SMART: Market.US,
    Exchange.NYSE: Market.US,
    Exchange.NASDAQ: Market.US,
    Exchange.SSE: Market.SH,
    Exchange.SZSE: Market.SZ,
}
EXCHANGE_FUTU2VT: Dict[str, Exchange] = {
    Market.HK: Exchange.SEHK,
    Market.US: Exchange.SMART,
    Market.SH: Exchange.SSE,
    Market.SZ: Exchange.SZSE,
}

# 产品类型映射
PRODUCT_VT2FUTU: Dict[Product, SecurityType] = {
    Product.EQUITY: SecurityType.STOCK,
    Product.INDEX: SecurityType.IDX,
    Product.ETF: SecurityType.ETF,
    Product.WARRANT: SecurityType.WARRANT,
    Product.BOND: SecurityType.BOND,
    Product.OPTION: SecurityType.DRVT,
    Product.FUTURES: SecurityType.FUTURE,
}
PRODUCT_FUTU2VT: Dict[SecurityType, Product] = {
    SecurityType.STOCK: Product.EQUITY,
    SecurityType.IDX: Product.INDEX,
    SecurityType.ETF: Product.ETF,
    SecurityType.WARRANT: Product.WARRANT,
    SecurityType.BOND: Product.BOND,
    SecurityType.DRVT: Product.OPTION,
    SecurityType.FUTURE: Product.FUTURES,
}

# 委托类型映射
ORDERTYPE_VT2FUTU: Dict[OrderType, FutuOrderType] = {
    OrderType.LIMIT: FutuOrderType.NORMAL,
    OrderType.MARKET: FutuOrderType.MARKET,
    OrderType.STOP: FutuOrderType.STOP,
}
ORDERTYPE_FUTU2VT: Dict[FutuOrderType, OrderType] = {
    FutuOrderType.NORMAL: OrderType.LIMIT,
    FutuOrderType.MARKET: OrderType.MARKET,
    FutuOrderType.STOP: OrderType.STOP,
}

# 委托状态映射
STATUS_FUTU2VT: Dict[OrderStatus, Status] = {
    OrderStatus.NONE: Status.SUBMITTING,
    OrderStatus.SUBMITTED: Status.SUBMITTING,
    OrderStatus.SUBMITTING: Status.SUBMITTING,
    OrderStatus.FILLED_PART: Status.PARTTRADED,
    OrderStatus.FILLED_ALL: Status.ALLTRADED,
    OrderStatus.CANCELLED_ALL: Status.CANCELLED,
    OrderStatus.CANCELLED_PART: Status.CANCELLED,
    OrderStatus.SUBMIT_FAILED: Status.REJECTED,
    OrderStatus.FAILED: Status.REJECTED,
    OrderStatus.DISABLED: Status.REJECTED,
    OrderStatus.DELETED: Status.REJECTED,
}

# 多空方向映射
DIRECTION_VT2FUTU: Dict[Direction, TrdSide] = {
    Direction.LONG: TrdSide.BUY,
    Direction.SHORT: TrdSide.SELL,
}
DIRECTION_FUTU2VT: Dict[TrdSide, Direction] = {
    TrdSide.BUY: Direction.LONG,
    TrdSide.SELL: Direction.SHORT,
    TrdSide.BUY_BACK: Direction.LONG,
    TrdSide.SELL_SHORT: Direction.SHORT,
}

# 数据频率映射
INTERVAL_VT2FUTU: Dict[Interval, KLType] = {
    Interval.MINUTE: KLType.K_1M,
    Interval.HOUR: KLType.K_60M,
    Interval.DAILY: KLType.K_DAY,
    Interval.WEEKLY: KLType.K_WEEK,
}

# 货币类型映射
CURRENCY_MAP: Dict[str, Currency] = {
    "HKD": Currency.HKD,
    "USD": Currency.USD,
    "CNY": Currency.CNY,
}

# 其他常量
JOIN_SYMBOL: str = "-"
CHINA_TZ = pytz.timezone("Asia/Shanghai")

# 替代get_local_datetime函数
def get_local_datetime() -> datetime:
    """获取本地时间"""
    return datetime.now().replace(tzinfo=CHINA_TZ)


class FutuGateway(BaseGateway):
    """
    VeighNa用于对接富途证券的交易接口。
    """

    default_name: str = "FUTU"

    default_setting: Dict[str, Any] = {
        "API地址": "127.0.0.1",
        "API端口": 11111,
        "市场环境": ["正式环境", "模拟环境"],
        "牛牛账号": "",
        "密码": "",
        "客户号": 1,
        "交易服务器": ["港股", "美股", "A股"],
        "行情服务器": ""
    }

    exchanges: List[Exchange] = list(EXCHANGE_VT2FUTU.keys())

    def __init__(self, event_engine: EventEngine, gateway_name: str) -> None:
        """构造函数"""
        super().__init__(event_engine, gateway_name)

        self.quote_api: "FutuQuoteApi" = FutuQuoteApi(self)
        self.trade_api: "FutuTradeApi" = FutuTradeApi(self)

        self.count: int = 0
        self.order_count: int = 0

        self.local_orderids: set = set()
        self.futu_orderids: Dict[str, str] = {}

    def connect(self, setting: dict) -> None:
        """连接交易接口"""
        host: str = setting["API地址"]
        port: int = setting["API端口"]
        trd_env: str = setting["市场环境"]
        market: str = setting["交易服务器"]

        self.quote_api.connect(host, port)
        self.trade_api.connect(host, port, trd_env, market, setting)

        self.init_query()

    def close(self) -> None:
        """关闭接口"""
        self.quote_api.close()
        self.trade_api.close()

    def subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        self.quote_api.subscribe(req)

    def send_order(self, req: OrderRequest) -> str:
        """委托下单"""
        return self.trade_api.send_order(req)

    def cancel_order(self, req: CancelRequest) -> None:
        """委托撤单"""
        self.trade_api.cancel_order(req)

    def query_account(self) -> None:
        """查询资金"""
        self.trade_api.query_account()

    def query_position(self) -> None:
        """查询持仓"""
        self.trade_api.query_position()

    def query_history(self, req: HistoryRequest) -> List[BarData]:
        """查询历史数据"""
        return self.quote_api.query_history(req)

    def init_query(self) -> None:
        """初始化查询任务"""
        self.event_engine.register(EVENT_TIMER, self.process_timer_event)

    def process_timer_event(self, event) -> None:
        """定时事件处理"""
        self.count += 1
        if self.count < 10:
            return
        self.count = 0

        self.query_account()
        self.query_position()


class FutuQuoteHandler(StockQuoteHandlerBase):
    """FUTU行情回调处理类"""

    def __init__(self, api: "FutuQuoteApi") -> None:
        """构造函数"""
        self.api: FutuQuoteApi = api

    def on_recv_rsp(self, rsp_pb) -> None:
        """收到推送数据回调"""
        ret_code, content = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            self.api.gateway.write_log(f"行情推送数据处理失败: {content}")
            return

        for stock_code, data in content.items():
            self.api.process_quote(stock_code, data)


class FutuOrderBookHandler(OrderBookHandlerBase):
    """富途盘口推送处理器"""

    def __init__(self, api: "FutuQuoteApi") -> None:
        """构造函数"""
        self.api: FutuQuoteApi = api

    def on_recv_rsp(self, rsp_pb) -> None:
        """收到推送数据回调"""
        ret_code, content = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            self.api.gateway.write_log(f"盘口推送数据处理失败: {content}")
            return

        self.api.process_orderbook(content)


class FutuQuoteApi:
    """富途行情API"""

    def __init__(self, gateway: FutuGateway) -> None:
        """构造函数"""
        self.gateway: FutuGateway = gateway
        self.gateway_name: str = gateway.gateway_name

        self.quote_ctx: OpenQuoteContext = None

        self.subscribed: set = set()
        self.ticks: Dict[str, TickData] = {}
        self.contracts: Dict[str, ContractData] = {}

        # 创建回调处理对象
        self.quote_handler: FutuQuoteHandler = FutuQuoteHandler(self)
        self.orderbook_handler: FutuOrderBookHandler = FutuOrderBookHandler(self)

    def connect(self, host: str, port: int) -> None:
        """连接服务器"""
        # 如果已经连接则直接返回
        if self.quote_ctx:
            return

        # 创建行情连接
        self.quote_ctx = OpenQuoteContext(host, port)

        # 设置回调处理
        self.quote_ctx.set_handler(self.quote_handler)
        self.quote_ctx.set_handler(self.orderbook_handler)
        self.quote_ctx.start()

        # 初始化并查询合约信息
        self.query_contract()

        self.gateway.write_log("富途行情接口连接成功")

    def close(self) -> None:
        """关闭连接"""
        if self.quote_ctx:
            self.quote_ctx.close()
            self.quote_ctx = None

    def process_quote(self, code: str, data: dict) -> None:
        """处理行情推送"""
        tick = self.get_tick(code)

        # 更新时间
        dt = datetime.now(CHINA_TZ)
        if "data_date" in data and "data_time" in data and data["data_date"]:
            date_str = data["data_date"].replace("-", "")
            time_str = data["data_time"].split(".")[0]
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H:%M:%S")
            dt = CHINA_TZ.localize(dt)

        tick.datetime = dt

        # 更新行情
        tick.open_price = data.get("open_price", 0)
        tick.high_price = data.get("high_price", 0)
        tick.low_price = data.get("low_price", 0)
        tick.pre_close = data.get("prev_close_price", 0)
        tick.last_price = data.get("last_price", 0)
        tick.volume = data.get("volume", 0)

        # 更新涨跌停价格
        if "price_spread" in data:
            spread = data["price_spread"]
            tick.limit_up = tick.last_price + spread * 10
            tick.limit_down = tick.last_price - spread * 10

        self.gateway.on_tick(copy(tick))

    def process_orderbook(self, data: dict) -> None:
        """处理盘口数据推送"""
        symbol = data.get("code", "")
        tick = self.get_tick(symbol)

        # 更新盘口数据
        bid_data = data.get("Bid", [])
        ask_data = data.get("Ask", [])

        for i in range(min(5, len(bid_data), len(ask_data))):
            n = i + 1
            setattr(tick, f"bid_price_{n}", bid_data[i][0])
            setattr(tick, f"bid_volume_{n}", bid_data[i][1])
            setattr(tick, f"ask_price_{n}", ask_data[i][0])
            setattr(tick, f"ask_volume_{n}", ask_data[i][1])

        # 推送Tick数据
        if tick.datetime:
            self.gateway.on_tick(copy(tick))

    def get_tick(self, code: str) -> TickData:
        """获取或创建Tick对象"""
        tick = self.ticks.get(code, None)

        if not tick:
            # 解析富途代码为VeighNa符号和交易所
            symbol, exchange = self.convert_symbol_futu2vt(code)

            # 创建Tick对象
            tick = TickData(
                symbol=symbol,
                exchange=exchange,
                datetime=datetime.now(CHINA_TZ),
                gateway_name=self.gateway_name,
            )
            self.ticks[code] = tick

            # 查找合约名称
            contract = self.contracts.get(tick.vt_symbol, None)
            if contract:
                tick.name = contract.name

        return tick

    def subscribe(self, req: SubscribeRequest) -> None:
        """订阅行情"""
        if not self.quote_ctx:
            return

        # 检查是否已订阅
        if req.vt_symbol in self.subscribed:
            return

        # 转换VeighNa代码为富途代码
        futu_symbol = self.convert_symbol_vt2futu(req.symbol, req.exchange)

        # 发送订阅请求
        ret, data = self.quote_ctx.subscribe(futu_symbol, [SubType.QUOTE, SubType.ORDER_BOOK])
        if ret != RET_OK:
            self.gateway.write_log(f"行情订阅失败: {data}")
            return

        # 记录订阅的合约
        self.subscribed.add(req.vt_symbol)

        # 添加合约对象到缓存
        contract = ContractData(
            symbol=req.symbol,
            exchange=req.exchange,
            name=req.symbol,
            product=Product.EQUITY,  # 默认为股票，后续处理中会更新
            size=1,
            pricetick=0.001,
            gateway_name=self.gateway_name
        )
        self.contracts[req.vt_symbol] = contract
        self.gateway.on_contract(copy(contract))

        self.gateway.write_log(f"{req.vt_symbol}行情订阅成功")

    def query_history(self, req: HistoryRequest) -> List[BarData]:
        """查询历史数据"""
        if not self.quote_ctx:
            return []

        # 转换VeighNa代码为富途代码
        futu_symbol = self.convert_symbol_vt2futu(req.symbol, req.exchange)

        # 转换时间频率
        ktype = INTERVAL_VT2FUTU.get(req.interval)
        if not ktype:
            self.gateway.write_log(f"不支持的时间周期: {req.interval}")
            return []

        # 查询起止时间
        start = req.start.strftime("%Y-%m-%d")
        end = req.end.strftime("%Y-%m-%d")

        # 请求历史数据
        ret, data, page_req_key = self.quote_ctx.request_history_kline(
            futu_symbol,
            start=start,
            end=end,
            ktype=ktype,
            max_count=1000
        )

        if ret != RET_OK:
            self.gateway.write_log(f"历史数据查询失败: {data}")
            return []

        bars = []
        for _, row in data.iterrows():
            # 创建K线数据对象
            dt = datetime.strptime(row["time_key"], "%Y-%m-%d %H:%M:%S")

            bar = BarData(
                symbol=req.symbol,
                exchange=req.exchange,
                interval=req.interval,
                datetime=CHINA_TZ.localize(dt),
                open_price=float(row["open"]),
                high_price=float(row["high"]),
                low_price=float(row["low"]),
                close_price=float(row["close"]),
                volume=float(row["volume"]),
                gateway_name=self.gateway_name
            )
            bars.append(bar)

        return bars

    def query_contract(self) -> None:
        """查询合约信息"""
        if not self.quote_ctx:
            return

        # 查询港股、美股、A股市场的合约信息
        for market in [Market.HK, Market.US, Market.SH, Market.SZ]:
            for security_type in [SecurityType.STOCK, SecurityType.ETF, SecurityType.IDX, SecurityType.WARRANT]:
                ret, data = self.quote_ctx.get_stock_basicinfo(market, security_type)
                if ret != RET_OK:
                    self.gateway.write_log(f"合约信息查询失败: {market} {security_type} {data}")
                    continue

                for _, row in data.iterrows():
                    # 解析代码
                    symbol, exchange = self.convert_symbol_futu2vt(row["code"])

                    # 确定产品类型
                    product = PRODUCT_FUTU2VT.get(security_type, Product.EQUITY)

                    # 创建合约对象
                    contract = ContractData(
                        symbol=symbol,
                        exchange=exchange,
                        name=row["name"],
                        product=product,
                        size=1,
                        pricetick=0.001,  # 默认最小价格变动
                        net_position=True,
                        gateway_name=self.gateway_name
                    )

                    self.contracts[contract.vt_symbol] = contract
                    self.gateway.on_contract(copy(contract))

        self.gateway.write_log("合约信息查询成功")

    def convert_symbol_futu2vt(self, code: str) -> Tuple[str, Exchange]:
        """富途代码转换为VeighNa代码"""
        code_split = code.split(".")
        if len(code_split) == 2:
            futu_exchange = code_split[0]
            futu_symbol = code_split[1]

            exchange = EXCHANGE_FUTU2VT.get(futu_exchange, Exchange.SMART)
            return futu_symbol, exchange

        # 对未识别代码的处理
        return code, Exchange.SMART

    def convert_symbol_vt2futu(self, symbol: str, exchange: Exchange) -> str:
        """VeighNa代码转换为富途代码"""
        futu_exchange = EXCHANGE_VT2FUTU.get(exchange, Market.HK)
        return f"{futu_exchange}.{symbol}"


class FutuOrderHandler(TradeOrderHandlerBase):
    """富途委托回调类"""

    def __init__(self, api: "FutuTradeApi") -> None:
        """构造函数"""
        self.api: FutuTradeApi = api

    def on_recv_rsp(self, rsp_pb) -> None:
        """收到推送数据回调"""
        ret_code, content = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            self.api.gateway.write_log(f"委托状态推送数据处理失败: {content}")
            return

        self.api.process_order(content)


class FutuDealHandler(TradeDealHandlerBase):
    """富途成交回调类"""

    def __init__(self, api: "FutuTradeApi") -> None:
        """构造函数"""
        self.api: FutuTradeApi = api

    def on_recv_rsp(self, rsp_pb) -> None:
        """收到推送数据回调"""
        ret_code, content = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            self.api.gateway.write_log(f"成交状态推送数据处理失败: {content}")
            return

        self.api.process_deal(content)


class FutuTradeApi:
    """富途交易API"""

    def __init__(self, gateway: FutuGateway) -> None:
        """构造函数"""
        self.gateway: FutuGateway = gateway
        self.gateway_name: str = gateway.gateway_name

        # 交易会话管理
        self.trade_ctx: Dict[Market, Any] = {}
        self.env: TrdEnv = TrdEnv.REAL

        # 成交订单记录
        self.trades: set = set()
        self.orders: Dict[str, OrderData] = {}

        # 创建回调处理对象
        self.order_handler: FutuOrderHandler = FutuOrderHandler(self)
        self.deal_handler: FutuDealHandler = FutuDealHandler(self)

    def connect(
        self,
        host: str,
        port: int,
        trd_env: str,
        market: List[str],
        setting: Dict[str, Any]
    ) -> None:
        """连接交易接口"""
        # 设置交易环境
        self.env = TrdEnv.REAL if trd_env == "正式环境" else TrdEnv.SIMULATE

        # 对每个选择的市场创建交易会话
        if "港股" in market:
            trade_ctx = OpenHKTradeContext(host, port)
            if trade_ctx:
                trade_ctx.set_handler(self.order_handler)
                trade_ctx.set_handler(self.deal_handler)
                trade_ctx.start()
                self.trade_ctx[Market.HK] = trade_ctx
                self.gateway.write_log("富途港股交易接口连接成功")

        if "美股" in market:
            trade_ctx = OpenUSTradeContext(host, port)
            if trade_ctx:
                trade_ctx.set_handler(self.order_handler)
                trade_ctx.set_handler(self.deal_handler)
                trade_ctx.start()
                self.trade_ctx[Market.US] = trade_ctx
                self.gateway.write_log("富途美股交易接口连接成功")

        if "A股" in market:
            trade_ctx = OpenCNTradeContext(host, port)
            if trade_ctx:
                trade_ctx.set_handler(self.order_handler)
                trade_ctx.set_handler(self.deal_handler)
                trade_ctx.start()
                self.trade_ctx[Market.SH] = trade_ctx
                self.trade_ctx[Market.SZ] = trade_ctx
                self.gateway.write_log("富途A股交易接口连接成功")

        # 启动交易连接后执行初始化查询
        if self.trade_ctx:
            # 查询委托
            self.query_order()
            # 查询成交
            self.query_trade()
            # 查询持仓
            self.query_position()
            # 查询账户
            self.query_account()

    def close(self) -> None:
        """关闭连接"""
        for ctx in self.trade_ctx.values():
            if ctx:
                ctx.close()
        self.trade_ctx.clear()

    def send_order(self, req: OrderRequest) -> str:
        """委托下单"""
        # 判断合适的交易市场
        if req.exchange == Exchange.SEHK:
            market = Market.HK
        elif req.exchange in [Exchange.NYSE, Exchange.NASDAQ, Exchange.SMART]:
            market = Market.US
        elif req.exchange == Exchange.SSE:
            market = Market.SH
        elif req.exchange == Exchange.SZSE:
            market = Market.SZ
        else:
            self.gateway.write_log(f"不支持的交易所: {req.exchange}")
            return ""

        # 获取对应市场的交易会话
        trade_ctx = self.trade_ctx.get(market, None)
        if not trade_ctx:
            self.gateway.write_log(f"交易会话未创建: {market}")
            return ""

        # 发送委托请求
        futu_order_type = ORDERTYPE_VT2FUTU.get(req.type, FutuOrderType.NORMAL)

        # 将VeighNa代码转换为富途代码
        futu_code = f"{market}.{req.symbol}"

        # 确定买卖方向
        trd_side = DIRECTION_VT2FUTU.get(req.direction, TrdSide.BUY)

        # 发送委托请求
        ret, data = trade_ctx.place_order(
            price=req.price,
            qty=req.volume,
            code=futu_code,
            trd_side=trd_side,
            order_type=futu_order_type,
            trd_env=self.env
        )

        # 处理委托请求结果
        if ret != RET_OK:
            self.gateway.write_log(f"委托失败: {data}")
            return ""

        # 获取富途系统的订单编号
        orderid = str(data["order_id"][0])

        # 推送委托数据
        order = req.create_order_data(orderid, self.gateway_name)
        self.orders[orderid] = order
        self.gateway.on_order(copy(order))

        return order.vt_orderid

    def cancel_order(self, req: CancelRequest) -> None:
        """委托撤单"""
        # 查找委托记录
        order = self.orders.get(req.orderid, None)
        if not order:
            self.gateway.write_log(f"撤单失败，未找到委托: {req.orderid}")
            return

        # 确定交易市场
        if order.exchange == Exchange.SEHK:
            market = Market.HK
        elif order.exchange in [Exchange.NYSE, Exchange.NASDAQ, Exchange.SMART]:
            market = Market.US
        elif order.exchange == Exchange.SSE:
            market = Market.SH
        elif order.exchange == Exchange.SZSE:
            market = Market.SZ
        else:
            self.gateway.write_log(f"不支持的交易所: {order.exchange}")
            return

        # 获取对应市场的交易会话
        trade_ctx = self.trade_ctx.get(market, None)
        if not trade_ctx:
            self.gateway.write_log(f"交易会话未创建: {market}")
            return

        # 发送撤单请求
        ret, data = trade_ctx.modify_order(
            ModifyOrderOp.CANCEL,
            order_id=int(req.orderid),
            qty=0,
            price=0,
            trd_env=self.env
        )

        # 处理撤单请求结果
        if ret != RET_OK:
            self.gateway.write_log(f"撤单失败: {data}")

    def query_account(self) -> None:
        """查询账户资金"""
        for market, ctx in self.trade_ctx.items():
            ret, data = ctx.accinfo_query(trd_env=self.env, acc_id=0)

            if ret != RET_OK:
                self.gateway.write_log(f"账户资金查询失败: {data}")
                continue

            for _, row in data.iterrows():
                # 创建账户对象
                account = AccountData(
                    accountid=f"{self.gateway_name}_{market}",
                    balance=float(row["power"]),
                    frozen=float(row["frozen_cash"]),
                    gateway_name=self.gateway_name
                )
                self.gateway.on_account(account)

    def query_position(self) -> None:
        """查询持仓"""
        for ctx in self.trade_ctx.values():
            ret, data = ctx.position_list_query(trd_env=self.env, acc_id=0)

            if ret != RET_OK:
                self.gateway.write_log(f"持仓查询失败: {data}")
                continue

            if data.empty:
                continue

            for _, row in data.iterrows():
                # 解析代码
                code = row["code"]
                symbol, exchange = self.convert_symbol_futu2vt(code)

                # 创建持仓数据
                pos = PositionData(
                    symbol=symbol,
                    exchange=exchange,
                    direction=Direction.LONG,  # 富途持仓默认为多头
                    volume=row["qty"],
                    frozen=(float(row["qty"]) - float(row["can_sell_qty"])),
                    price=float(row["cost_price"]),
                    pnl=float(row["pl_val"]),
                    gateway_name=self.gateway_name
                )
                self.gateway.on_position(pos)

    def query_order(self) -> None:
        """查询未成交委托"""
        for ctx in self.trade_ctx.values():
            ret, data = ctx.order_list_query("", trd_env=self.env)

            if ret != RET_OK:
                self.gateway.write_log(f"委托查询失败: {data}")
                continue

            if data.empty:
                continue

            self.process_order(data)

        self.gateway.write_log("委托查询成功")

    def query_trade(self) -> None:
        """查询成交"""
        for ctx in self.trade_ctx.values():
            ret, data = ctx.deal_list_query("", trd_env=self.env)

            if ret != RET_OK:
                self.gateway.write_log(f"成交查询失败: {data}")
                continue

            if data.empty:
                continue

            self.process_deal(data)

        self.gateway.write_log("成交查询成功")

    def process_order(self, data: dict) -> None:
        """处理委托数据"""
        for _, row in data.iterrows():
            # 过滤已删除的委托
            if row["order_status"] == OrderStatus.DELETED:
                continue

            # 解析代码
            code = row["code"]
            symbol, exchange = self.convert_symbol_futu2vt(code)

            # 创建委托数据
            orderid = str(row["order_id"])

            order = OrderData(
                symbol=symbol,
                exchange=exchange,
                orderid=orderid,
                direction=DIRECTION_FUTU2VT.get(row["trd_side"], Direction.LONG),
                price=float(row["price"]),
                volume=float(row["qty"]),
                traded=float(row["dealt_qty"]),
                status=STATUS_FUTU2VT.get(row["order_status"], Status.SUBMITTING),
                datetime=self.generate_datetime(row["create_time"]),
                gateway_name=self.gateway_name
            )

            self.orders[orderid] = order
            self.gateway.on_order(copy(order))

    def process_deal(self, data: dict) -> None:
        """处理成交数据"""
        for _, row in data.iterrows():
            # 过滤重复成交推送
            tradeid = str(row["deal_id"])
            if tradeid in self.trades:
                continue

            self.trades.add(tradeid)

            # 解析代码
            code = row["code"]
            symbol, exchange = self.convert_symbol_futu2vt(code)

            # 创建成交数据
            trade = TradeData(
                symbol=symbol,
                exchange=exchange,
                direction=DIRECTION_FUTU2VT.get(row["trd_side"], Direction.LONG),
                tradeid=tradeid,
                orderid=str(row["order_id"]),
                price=float(row["price"]),
                volume=float(row["qty"]),
                datetime=self.generate_datetime(row["create_time"]),
                gateway_name=self.gateway_name
            )

            self.gateway.on_trade(trade)

    def generate_datetime(self, s: str) -> datetime:
        """生成时间戳"""
        if "." in s:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S.%f")
        else:
            dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

        dt = CHINA_TZ.localize(dt)
        return dt

    def convert_symbol_futu2vt(self, code: str) -> Tuple[str, Exchange]:
        """富途代码转换为VeighNa代码"""
        code_split = code.split(".")
        if len(code_split) == 2:
            futu_exchange = code_split[0]
            futu_symbol = code_split[1]

            exchange = EXCHANGE_FUTU2VT.get(futu_exchange, Exchange.SMART)
            return futu_symbol, exchange

        # 对未识别代码的处理
        return code, Exchange.SMART
