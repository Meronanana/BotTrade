import pyupbit as pu
import time


class TestAccount:
    def __init__(self, balance: int = 1000000, wallet: dict = None):
        self.balance = balance
        if wallet is None:
            self.wallet = {}
        else:
            self.wallet = wallet

    def get_acc_data(self):
        return [self.balance, self.wallet]

    # order = {'currency': self.ticker, 'balance': amount, 'avg_buy_price': price, 'created_at': time.ctime(), 'status': 'Testing', 'side': 'bid'}
    def buy_order(self, order):
        self.wallet[order['currency']] = order
        self.balance = self.balance - (order['balance'] * order['avg_buy_price'] * 1.0005)
        print(order)

    # order = {'currency': self.ticker, 'balance': amount, 'avg_sell_price': price, 'created_at': time.ctime(), 'status': 'Testing', 'side': 'ask'}
    def sell_order(self, order):
        del self.wallet[order['currency']]
        self.balance = self.balance + (order['balance'] * order['avg_sell_price'] * 0.9995)
        print(order)

    def get_test_account(self):
        total_bought = 0
        total_evaluate = 0
        for order in self.wallet.values():
            total_bought = total_bought + order['balance'] * order['avg_buy_price']
            try:
                total_evaluate = total_evaluate + order['balance'] * pu.get_current_price(order['currency'])
            except:
                time.sleep(1)
                return self.get_test_account
            time.sleep(0.1)

        total_balance = self.balance + total_evaluate
        difference = total_evaluate - total_bought
        try:
            difference_rate = difference / total_bought * 100
        except:
            difference_rate = 0.00

        return (int(total_balance), int(total_bought), int(total_evaluate), int(difference), round(difference_rate, 2))
