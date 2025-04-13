"""
富途网关单元测试
"""

import unittest
from unittest.mock import MagicMock, patch

from vnpy.event import EventEngine
from vnpy.trader.constant import Exchange, Interval
from vnpy.trader.object import SubscribeRequest, HistoryRequest, OrderRequest, Direction, OrderType

from vnpy_futu import FutuGateway
from vnpy_futu.vnpy_futu.futu_gateway import FutuQuoteApi, FutuTradeApi


class TestFutuGateway(unittest.TestCase):
    """
    测试富途网关
    """

    def setUp(self):
        """
        测试前准备
        """
        self.event_engine = EventEngine()
        self.gateway = FutuGateway(self.event_engine, "FUTU")

        # Mock API对象
        self.gateway.quote_api = MagicMock()
        self.gateway.trade_api = MagicMock()

    def test_connect(self):
        """
        测试连接
        """
        setting = {
            "API地址": "127.0.0.1",
            "API端口": 11111,
            "市场环境": "模拟环境",
            "交易服务器": ["港股", "美股", "A股"],
        }

        self.gateway.connect(setting)

        self.gateway.quote_api.connect.assert_called_once_with("127.0.0.1", 11111)
        self.gateway.trade_api.connect.assert_called_once_with(
            "127.0.0.1", 11111, "模拟环境", ["港股", "美股", "A股"], setting
        )

    def test_close(self):
        """
        测试关闭
        """
        self.gateway.close()

        self.gateway.quote_api.close.assert_called_once()
        self.gateway.trade_api.close.assert_called_once()

    def test_subscribe(self):
        """
        测试订阅行情
        """
        req = SubscribeRequest(
            symbol="700",
            exchange=Exchange.HKEX
        )

        self.gateway.subscribe(req)

        self.gateway.quote_api.subscribe.assert_called_once_with(req)

    def test_send_order(self):
        """
        测试发送委托
        """
        req = OrderRequest(
            symbol="700",
            exchange=Exchange.HKEX,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=500,
        )

        self.gateway.trade_api.send_order.return_value = "FUTU.1"

        orderid = self.gateway.send_order(req)

        self.gateway.trade_api.send_order.assert_called_once_with(req)
        self.assertEqual(orderid, "FUTU.1")

    def test_query_history(self):
        """
        测试查询历史数据
        """
        req = HistoryRequest(
            symbol="700",
            exchange=Exchange.HKEX,
            interval=Interval.DAILY,
            start=None,
            end=None,
        )

        self.gateway.query_history(req)

        self.gateway.quote_api.query_history.assert_called_once_with(req)


class TestFutuQuoteApi(unittest.TestCase):
    """
    测试富途行情API
    """

    @patch('vnpy_futu.vnpy_futu.futu_gateway.OpenQuoteContext')
    def setUp(self, mock_quote_context):
        """
        测试前准备
        """
        self.event_engine = EventEngine()
        self.gateway = FutuGateway(self.event_engine, "FUTU")
        self.gateway.write_log = MagicMock()
        self.gateway.on_contract = MagicMock()

        # 创建API对象
        self.quote_api = FutuQuoteApi(self.gateway)

        # Mock OpenQuoteContext
        self.mock_context = mock_quote_context.return_value
        self.mock_context.set_handler = MagicMock()
        self.mock_context.start = MagicMock()

    def test_connect(self):
        """
        测试连接
        """
        self.quote_api.connect("127.0.0.1", 11111)

        self.mock_context.set_handler.assert_called()
        self.mock_context.start.assert_called_once()
        self.gateway.write_log.assert_called_with("富途行情接口连接成功")

    def test_close(self):
        """
        测试关闭
        """
        self.quote_api.connect("127.0.0.1", 11111)
        self.quote_api.close()

        self.mock_context.close.assert_called_once()
        self.assertIsNone(self.quote_api.quote_ctx)


if __name__ == '__main__':
    unittest.main()