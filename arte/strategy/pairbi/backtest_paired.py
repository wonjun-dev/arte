import traceback

from tqdm import tqdm

from arte.data.common_symbol_collector import CommonSymbolCollector
from arte.data.test_data_loader import TestDataLoader
from arte.test_system import BackTestUpbitTradeManager
from arte.test_system import BackTestBinanceTradeManager
from arte.test_system import BatchBacktester
from strategy_loop import StrategyLoop

DATA_PATH = "/Volumes/D/data"

class BackTester:
    def __init__(self):
        self.tm_upbit = BackTestUpbitTradeManager(init_krw=400000, max_order_count=3)
        self.tm_binance = BackTestBinanceTradeManager(init_usdt=10000, max_order_count=3)

        self.strategy = StrategyLoop(trade_manager_upbit=self.tm_upbit, trade_manager_binance = self.tm_binance) # need to change!
        self.except_list = []

    def mainloop(self):
        try:
            self.tm_upbit.update(
                test_current_time=self.test_data_manager.current_time,
                trade_prices=self.test_data_manager.upbit_trade.price,
                last_askbid=self.test_data_manager.upbit_last_askbid,
            )
            self.tm_binance.update() # need to change!

            self.strategy.update(
                upbit_price=self.test_data_manager.upbit_trade,
                binance_spot_price=self.test_data_manager.binance_trade,
                exchange_rate=self.test_data_manager.exchange_rate,
                except_list=self.except_list,
                current_time=self.test_data_manager.current_time,
            )
            self.strategy.run()

        except Exception:
            traceback.print_exc()

    def start(self, symbols, date_range):
        self.test_data_manager = TestDataLoader(DATA_PATH)
        self.test_data_manager.init_test_data_loader(symbols, date_range[0], date_range[1], ohlcv_interval=1000)
        self.strategy.initialize(symbols, self.except_list)

        for i in tqdm(range(self.test_data_manager.get_counter()), ncols=100):
            self.test_data_manager.load_next_by_counter(i)
            self.mainloop()

        return {'upbit': self.tm_upbit.end_bt(), 'binance': self.tm_binance.end_bt()}


if __name__ == "__main__":
    selected_assets = "BTC ETH BCH AAVE SOL LTC AXS ETC NEO DOT ATOM LINK QTUM OMG KAVA MANA EOS 1INCH ADA"
    # symbols = selected_assets.split(" ")

    strategy_name = "upbitfollow_converge_nov"
    start_date = "2021-11-01"
    end_date = "2021-11-30"
    symbols = ["AXS"]

    bbt = BatchBacktester(
        BackTester(), DATA_PATH, strategy_name, ["upbit", "binance_spot"], symbols, start_date, end_date
    )

    import timeit
    st = timeit.default_timer()
    bbt.start()
    print(timeit.default_timer() - st)