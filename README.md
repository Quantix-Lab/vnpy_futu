# VeighNa Futu Gateway

富途证券交易接口，基于富途开放平台（Futu OpenAPI）开发。

## 说明

本模块基于富途开放平台提供的API接口开发，支持以下功能：

1. 港股、美股、A股的行情数据订阅和拉取
2. 港股、美股、A股的委托下单和成交查询
3. 账户资金和持仓信息的查询
4. 历史K线数据的获取

## 安装前准备

使用该接口前需要先安装并运行富途牛牛客户端，并在客户端中：

1. 登录您的富途账户
2. 启用OpenAPI功能（点击客户端右上角齿轮图标 > 选择其他 > 勾选启用OpenAPI）
3. 记录您的API地址和端口（默认为127.0.0.1和11111）

## 安装

安装环境推荐基于3.7以上版本的【纯净版】Python环境，避免使用Anaconda那些版本会有一些兼容性问题。

### 方法1：使用pip直接安装

```bash
pip install vnpy_futu
```

### 方法2：下载源代码安装

```bash
git clone https://github.com/vnpy/vnpy_futu.git
cd vnpy_futu
pip install -e .
```

### 依赖安装

本模块自动安装以下依赖项：

- futu-api：富途开放平台的Python SDK
- vnpy_trader：VeighNa核心交易模块

## 使用指南

### 在VeighNa Trader中使用

启动VeighNa Trader后，在主界面点击【交易】菜单栏的【连接富途】，在弹出的窗口中输入以下参数后即可登录：

- API地址：富途API服务器地址，默认为127.0.0.1
- API端口：富途API服务器端口，默认为11111
- 市场环境：正式环境或模拟环境
- 牛牛账号：富途牛牛账号
- 密码：账号密码
- 客户号：客户号，默认为1
- 交易服务器：可选择港股、美股、A股，可多选
- 行情服务器：行情服务器地址，可留空

### 直接通过代码使用

```python
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_futu import FutuGateway


def main():
    """主入口函数"""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)
    main_engine.add_gateway(FutuGateway)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
```

### 示例程序

在`examples`目录下提供了以下示例程序：

1. `futu_stock_trading.py`: 演示如何使用API进行股票交易
2. `futu_data_download.py`: 演示如何下载历史数据
3. `futu_trader_ui.py`: 演示如何启动图形界面

运行示例前确保富途牛牛客户端已启动并开启了OpenAPI功能。

## 常见问题

### 1. 连接失败

确保富途牛牛客户端已启动并开启了OpenAPI功能，API地址和端口配置正确。

### 2. 订阅行情失败

检查您的富途账户是否有相应市场的行情权限，可能需要在富途牛牛客户端中购买相应的行情数据权限。

### 3. 交易失败

- 检查账户是否有足够的资金
- 确认您的账户是否有交易权限
- 验证交易时间是否在目标市场的交易时段内

## 开发者文档

如需了解模块的详细API文档和开发指南，请访问[VeighNa官方文档](https://www.vnpy.com/docs)。

## 相关链接

- [VeighNa官网](https://www.vnpy.com)
- [富途开放平台](https://openapi.futunn.com/)
- [富途API文档](https://openapi.futunn.com/futu-api-doc/)

## 版权说明

MIT License
