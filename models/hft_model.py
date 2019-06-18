import time
import datetime as dt
import pandas as pd
from threading import Thread

from ib_insync import IB, Stock, Forex
from ib_insync.util import df
from dateutil import tz


class HftModel(object):

	def __init__(
		self,
		host='localhost', port=4001, client_id=101,
		is_use_gateway=False, evaluation_time_secs=20,
		resample_interval_secs='30s',
		moving_window_period=dt.timedelta(hours=1)
	):
		self.host = host
		self.port = port
		self.client_id = client_id

		self.ib = IB()

		self.utc_timezone = tz.tzutc()
		self.local_timezone = tz.tzlocal()

		self.symbol_map = {}
		self.historical_data = {}  # of mid prices
		self.df_hist = None

		self.symbols = []

		self.volatility_ratio = 1
		self.beta = 0
		self.moving_window_period = dt.timedelta(hours=1)
		self.is_buy_signal, self.is_sell_signal = False, False

	def run(self, to_trade=[]):
		self.ib.connect('127.0.0.1', 7497, clientId=101)

		self.symbol_map = {str(contract): ident for (ident, contract) in to_trade}
		contracts = [contract for (_, contract) in to_trade]
		symbols = list(self.symbol_map.values())
		self.symbols = symbols

		self.df_hist = pd.DataFrame(columns=symbols)

		self.request_historical_data(contracts)
		self.request_market_data(contracts)

		while self.ib.waitOnUpdate():
			self.ib.sleep(1)
			self.calculate_strategy_params()

	def request_market_data(self, contracts):
		for contract in contracts:
			self.ib.reqMktData(contract)

		self.ib.pendingTickersEvent += self.on_tick

	def on_tick(self, tickers):
		for ticker in tickers:
			self.get_incoming_tick_data(ticker)

		self.perform_trade_logic()

	def perform_trade_logic(self):
		"""
		This part is the 'secret-sauce' where actual trades takes place.
        My take is that great experience, good portfolio construction,
        and together with robust backtesting will make your strategy viable.
        GOOD PORTFOLIO CONTRUCTION CAN SAVE YOU FROM BAD RESEARCH,
        BUT BAD PORTFOLIO CONSTRUCTION CANNOT SAVE YOU FROM GREAT RESEARCH

        This trade logic uses volatility ratio and beta as our indicators.
        - volatility ratio > 1 :: uptrend, volatility ratio < 1 :: downtrend
        - beta is calculated as: mean(price A) / mean(price B)
        We use the assumption that prive levels will mean-revert.
        Expected price A = beta x price B

        Consider other methods of identifying our trade logic:
        - current trend
        - current regime
        - detect structural breaks
        """
		self.calculate_signals()
		self.calculate_positions()
		self.check_and_enter_orders()

	def check_and_enter_orders(self):
		# if is_position_closed and is_sell_signal:
		# 	print
		# 	"=================================="
		# 	print
		# 	"OPEN SHORT POSIITON: SELL A BUY B"
		# 	print
		# 	"=================================="
		# 	self.__place_spread_order(-self.trade_qty)
		#
		# elif is_position_closed and is_buy_signal:
		# 	print
		# 	"=================================="
		# 	print
		# 	"OPEN LONG POSIITON: BUY A SELL B"
		# 	print
		# 	"=================================="
		# 	self.__place_spread_order(self.trade_qty)
		#
		# elif is_short and is_buy_signal:
		# 	print
		# 	"=================================="
		# 	print
		# 	"CLOSE SHORT POSITION: BUY A SELL B"
		# 	print
		# 	"=================================="
		# 	self.__place_spread_order(self.trade_qty)
		#
		# elif is_long and is_sell_signal:
		# 	print
		# 	"=================================="
		# 	print
		# 	"CLOSE LONG POSITION: SELL A BUY B"
		# 	print
		# 	"=================================="
		# 	self.__place_spread_order(-self.trade_qty)
		pass

	def calculate_positions(self):
		# Use account position details
		pass

	# symbol_a = self.symbols[0]
	# position = self.stocks_data[symbol_a].position
	# is_position_closed, is_short, is_long = \
	# 	(position == 0), (position < 0), (position > 0)
	#
	# upnl, rpnl = self.__calculate_pnls()
	#
	# # Display to terminal dynamically
	# signal_text = \
	# 	"BUY" if is_buy_signal else "SELL" if is_sell_signal else "NONE"
	# console_output = '\r[%s] signal=%s, position=%s UPnL=%s RPnL=%s\r' % \
	# 				 (dt.datetime.now(), signal_text, position, upnl, rpnl)
	# sys.stdout.write(console_output)
	# sys.stdout.flush()

	def calculate_strategy_params(self):
		"""
		Here, we are calculating beta and volatility ratio
		for our signal indicators.

		Consider calculating other statistics here:
		- stddevs of errs
		- correlations
		- co-integration
		"""
		[symbol_a, symbol_b] = self.symbols

		resampled = self.df_hist.resample('30s').ffill().dropna()
		mean = resampled.mean()
		self.beta = mean[symbol_a] / mean[symbol_b]

		stddevs = resampled.pct_change().dropna().std()
		self.volatility_ratio = stddevs[symbol_a] / stddevs[symbol_b]

		print('beta:', self.beta, 'vr:', self.volatility_ratio)

	def calculate_signals(self):
		self.trim_historical_data()

		is_up_trend, is_down_trend = self.volatility_ratio > 1, self.volatility_ratio < 1
		is_overbought, is_oversold = self.is_overbought_or_oversold()

		# Our final trade signals
		self.is_buy_signal = is_up_trend and is_oversold
		self.is_sell_signal = is_down_trend and is_overbought

	def trim_historical_data(self):
		cutoff_time = dt.datetime.now(tz=self.local_timezone) - self.moving_window_period
		self.df_hist = self.df_hist[self.df_hist.index >= cutoff_time]

	def is_overbought_or_oversold(self):
		[symbol_a, symbol_b] = self.symbols
		leg_a_last_price = self.df_hist[symbol_a].dropna().values[-1]
		leg_b_last_price = self.df_hist[symbol_b].dropna().values[-1]

		expected_leg_a_price = leg_b_last_price * self.beta

		is_overbought = leg_a_last_price < expected_leg_a_price  # Cheaper than expected
		is_oversold = leg_a_last_price > expected_leg_a_price  # Higher than expected

		return is_overbought, is_oversold

	def get_incoming_tick_data(self, ticker):
		symbol = self.get_symbol(ticker.contract)

		dt_obj = self.convert_utc_datetime(ticker.time)
		bid = ticker.bid
		ask = ticker.ask
		mid = (bid + ask) / 2

		self.df_hist.loc[dt_obj, symbol] = mid

	def request_historical_data(self, contracts):
		for contract in contracts:
			self.set_historical_data(contract)

	def set_historical_data(self, contract):
		symbol = self.get_symbol(contract)

		bars = self.ib.reqHistoricalData(
			contract,
			endDateTime=time.strftime('%Y%m%d %H:%M:%S'),
			durationStr='3600 S',
			barSizeSetting='5 secs',
			whatToShow='MIDPOINT',
			useRTH=True,
			formatDate=1
		)
		for bar in bars:
			dt_obj = self.convert_local_datetime(bar.date)
			self.df_hist.loc[dt_obj, symbol] = bar.close

	def get_symbol(self, contract):
		return self.symbol_map.get(str(contract))

	def convert_utc_datetime(self, datetime):
		utc = datetime.replace(tzinfo=self.utc_timezone)
		local_time = utc.astimezone(self.local_timezone)
		return pd.to_datetime(local_time)

	def convert_local_datetime(self, datetime):
		local_time = datetime.replace(tzinfo=self.local_timezone)
		return pd.to_datetime(local_time)
