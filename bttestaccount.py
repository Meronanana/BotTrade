

class TestAccount:
    def __init__(self):
        # 현금, 보유 암호화폐
        self.balance = 1000000
        self.wallet = {}

    # order = {'currency': self.ticker, 'balance': amount, 'avg_buy_price': price, 'created_at': time.ctime(), 'status': 'Testing', 'side': 'bid'}
    def buy_order(self, order):
        self.wallet[order['currency']] = order
        self.balance = self.balance - (order['balance'] * order['avg_buy_price'] * 1.0005)

    # order = {'currency': self.ticker, 'balance': amount, 'avg_sell_price': price, 'created_at': time.ctime(), 'status': 'Testing', 'side': 'ask'}
    def sell_order(self, order):
        del self.wallet[order['currency']]
        self.balance = self.balance + (order['balance'] * order['avg_sell_price'] * 0.9995)

    def get_test_account(self):
        print(self.balance)
        print(self.wallet)
