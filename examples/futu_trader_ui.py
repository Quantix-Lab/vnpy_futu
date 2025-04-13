"""
使用VeighNa图形界面进行富途交易的示例
"""

import sys
import os

# 添加项目根目录到Python路径
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.append(ROOT_DIR)

try:
    from vnpy.event import EventEngine
    from vnpy.trader.engine import MainEngine
    from vnpy.trader.ui import MainWindow, create_qapp

    # 导入富途网关
    from vnpy_futu.vnpy_futu import FutuGateway
except ImportError as e:
    print(f"导入错误: {e}")
    print(f"当前Python路径: {sys.path}")
    print(f"尝试从以下路径导入vnpy: {ROOT_DIR}")
    try:
        # 如果vnpy不是作为包安装的，尝试直接导入
        sys.path.append(os.path.join(ROOT_DIR, 'vnpy'))
        from vnpy.event import EventEngine
        from vnpy.trader.engine import MainEngine
        from vnpy.trader.ui import MainWindow, create_qapp

        # 直接从相对路径导入富途网关
        from vnpy_futu.vnpy_futu.futu_gateway import FutuGateway
        print("成功通过直接路径导入模块")
    except ImportError as e2:
        print(f"第二次导入尝试也失败: {e2}")
        print("请确保已正确安装vnpy和vnpy_futu")
        sys.exit(1)


def main():
    """
    启动VeighNa交易平台
    """
    print("正在启动VeighNa交易平台...")

    try:
        # 创建Qt应用
        qapp = create_qapp()

        # 创建事件引擎
        event_engine = EventEngine()

        # 创建主引擎
        main_engine = MainEngine(event_engine)

        # 添加富途网关
        main_engine.add_gateway(FutuGateway)
        print("成功添加富途网关")

        # 创建并显示主窗口
        main_window = MainWindow(main_engine, event_engine)
        main_window.showMaximized()
        print("成功启动VeighNa交易平台界面")

        # 在富途网关连接设置中：
        # - API地址: 127.0.0.1
        # - API端口: 11111
        # - 市场环境: 模拟环境或正式环境
        # - 交易服务器: 根据需要选择港股、美股、A股

        # 运行Qt应用
        qapp.exec()
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()