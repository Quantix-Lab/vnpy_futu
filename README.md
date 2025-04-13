# VeighNa Futu Gateway

[English](README.md) | [简体中文](README_CN.md)

Futu Securities trading gateway for VeighNa trading framework, developed based on Futu Open API.

## Disclaimer

This software is provided for educational and research purposes only and does not constitute investment or trading advice. Users assume all risks associated with real-money trading using this software. The developers of this software bear no responsibility for any direct or indirect losses resulting from the use of this software.

By using this software, you agree that:
1. You will assume all risks and consequences of using this software for trading
2. Any issues with the software (including but not limited to errors, delays, etc.) may lead to trading losses
3. You fully understand the risks of financial markets and have appropriate risk tolerance capacity

## Overview

This module is developed based on the API provided by Futu OpenAPI platform and supports the following features:

1. Market data subscription and retrieval for Hong Kong, US, and A-share stocks
2. Order placement and trade execution for Hong Kong, US, and A-share stocks
3. Account balance and position information queries
4. Historical K-line data retrieval

## Prerequisites

Before using this gateway, you need to install and run the Futu Bullish (FutuNiuNiu) client and:

1. Log in to your Futu account
2. Enable the OpenAPI function (click the gear icon in the upper right corner > select "Others" > check "Enable OpenAPI")
3. Note your API address and port (default is 127.0.0.1 and 11111)

## Installation

We recommend using a clean Python environment based on version 3.7 or higher, avoiding Anaconda distributions as they may cause compatibility issues.

### Installation from Source Code

```bash
git clone https://github.com/Quantix-Lab/vnpy_futu.git
cd vnpy_futu
pip install -e .
```

### Dependencies

This module only depends on:

- futu-api: The Python SDK for Futu OpenAPI platform

**Note:** This module does not automatically install the VeighNa core library, which needs to be installed by the user separately. This design avoids dependency conflicts and allows users to flexibly choose the VeighNa version that suits their environment.

## Usage Guide

### Using in VeighNa Trader

After launching VeighNa Trader, click the [Trade] menu and select [Connect Futu]. Enter the following parameters in the popup window to log in:

- API Address: Futu API server address, default is 127.0.0.1
- API Port: Futu API server port, default is 11111
- Market Environment: Real environment or simulation environment
- Trading Gateway: Select Hong Kong, US, or A-shares stocks, multiple selections allowed
- Quote Server: Quote server address, can be left empty

**Note:** You do not need to enter your username and password in VeighNa as authentication is handled through the Futu Bullish client. Please ensure that the Futu Bullish client is logged in and the OpenAPI function is enabled.

### Direct Code Usage

```python
from vnpy.event import EventEngine
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_futu import FutuGateway


def main():
    """Main entry function"""
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

### Example Programs

The following example programs are provided in the `examples` directory:

1. `futu_stock_trading.py`: Demonstrates how to use the API for stock trading
2. `futu_data_download.py`: Demonstrates how to download historical data
3. `futu_trader_ui.py`: Demonstrates how to launch the graphical interface

Make sure the Futu Bullish client is running and the OpenAPI function is enabled before running the examples.

## Common Issues

### 1. Connection Failure

Ensure that the Futu Bullish client is running with the OpenAPI function enabled, and the API address and port are configured correctly.

### 2. Market Data Subscription Failure

Check if your Futu account has market data permissions for the relevant markets. You may need to purchase market data subscriptions in the Futu Bullish client.

### 3. Trading Failure

- Check if your account has sufficient funds
- Confirm if your account has trading permissions
- Verify if the trading time is within the trading hours of the target market

## Developer Documentation

For detailed API documentation and development guidelines, please visit [VeighNa Official Documentation](https://www.vnpy.com/docs).

## Useful Links

- [VeighNa Official Website](https://www.vnpy.com)
- [Futu Open Platform](https://openapi.futunn.com/)
- [Futu API Documentation](https://openapi.futunn.com/futu-api-doc/)

## License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for the complete license text.

```
MIT License

Copyright (c) 2025 Quantix-Lab

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions...