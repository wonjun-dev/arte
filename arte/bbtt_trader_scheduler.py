import traceback
from apscheduler.schedulers.blocking import BlockingScheduler

from arte.data.data_manager import DataManager
from arte.system.strategy_manager import StrategyManager
from arte.system.account import Account
from arte.system import OrderHandler
from arte.system.telegram_bot import SimonManager


from arte.indicator.core.indicator_manager import IndicatorManager
from arte.indicator.bollinger import Bollinger
from arte.strategy.bollinger_touch import BollingerTouch


class BBTTTrader:
    """
    Class BBTTTrader
        실시간 트레이딩 모듈

    Attributes:
        client: API를 사용하는 client 정보
        data_manager: 데이터 관리 모듈
    """

    def __init__(self, client, symbol):
        """초기화 함수"""
        self.symbol = symbol
        self.client = client
        self.data_manager = DataManager(self.client)
        self.scheduler = BlockingScheduler()

        # init bot manager
        self.bot_manager = SimonManager()
        self.bot_manager.trader = self

        # Init Order Handler
        self.account = Account(client.request_client)
        self.oh = OrderHandler(client.request_client, self.account, symbol=self.symbol.upper())

        # Init strategy
        INDICATORS = [Bollinger()]
        self.im = IndicatorManager(indicator_instance=INDICATORS)
        self.strategy = BollingerTouch(indicator_manager=self.im)
        self.strategy_manager = StrategyManager(
            self.oh, self.strategy, self.bot_manager, max_order_count=3, verbose_bot=False
        )

    def mainloop(self):
        """주기적으로 실행되는 함수"""
        try:
            # 여기에 로직을 넣으시오
            # print(self.data_manager.candlestick.close)
            data = self.data_manager.candlestick
            self.strategy_manager.run(data)

        except Exception:
            traceback.print_exc()

    def run(self, maxlen: int = 21, interval: str = "1m", watch_interval: int = 2):
        """
        mainloop를 watch_interval마다 실행시켜주는 함수
        """
        self.data_manager.open_candlestick_socket(
            symbol=self.symbol.lower(), maxlen=maxlen, interval=interval
        )
        self.runner = self.scheduler.add_job(
            self.mainloop, "interval", seconds=watch_interval, id="mainloop"
        )
        self.bot_runner = self.scheduler.add_job(self.bot_manager.bot_manager_setting)
        self.scheduler.start()
