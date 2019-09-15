import os

from ib_insync import Forex, Stock

from models.hft_model_1 import HftModel1

if __name__ == '__main__':
	TWS_HOST = os.environ.get('TWS_HOST', '127.0.0.1')
	TWS_PORT = os.environ.get('TWS_PORT', 4002)

	print('Connecting on host:', TWS_HOST, 'port:', TWS_PORT)

	model = HftModel1(
		host=TWS_HOST,
		port=TWS_PORT,
		client_id=1,
	)

	to_trade = [
		('SPY', Stock('SPY','SMART','USD')),
		('QQQ', Stock('QQQ','SMART','USD')),
	]

	# to_trade = [
	# 	Stock('QQQ', 'SMART', 'USD'),
	# 	Stock('SPY', 'SMART', 'USD')
	# ]

	model.run(to_trade=to_trade, trade_qty=100)
