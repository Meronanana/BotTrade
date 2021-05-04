import pyupbit as pu
from pandas import DataFrame
from PyQt5.QtCore import *
from bttestaccount import *
from datetime import datetime


# 각 매수 매도결정을 하는 프로젝트들을 모두 관리하는 모듈이다.


# 업비트 계정을 연결해 주는 클래스
class Account:
    my_account = None

    def __init__(self):
        f = open("upbit.txt", "rt")
        lines = f.readlines()

        get_key = ['acc', 'pri']
        for i, line in enumerate(lines):
            get_key[i] = line.strip('\n')

        Account.my_account = pu.Upbit(get_key[0], get_key[1])
        f.close()


# 주문의 자료형을 정하는 클래스, 거래시간-거래프로젝트-티커 로 이루어짐
class Order:
    def __init__(self, tm: datetime, project, ticker: str, status: str, order):
        self.order_time = tm
        self.ordered_project = project
        self.ticker = ticker
        self.status = status
        self.order = order
        print(tm, ticker, status, order)

    # 시간 - 로그내용([프로젝트], 티커, 매수/매도, 수량, 평균단가, 거래총액)
    def order_to_log(self):
        log_time: str
        log_content: str
        if self.status == 'Release':
            # log_time = self.order_time.
            pass
        elif self.status == 'Testing':
            print('ordertoLog')
            log_time = self.order_time.strftime('%y-%m-%d :: %H시 %M분 %S초')
            log_content = self.ordered_project.title + ' / ' + self.ticker + ' / '
            price: float
            if self.order['side'] == 'bid':
                price = self.order['avg_buy_price']
                log_content = log_content + '매수 / '
            elif self.order['side'] == 'ask':
                price = self.order['avg_sell_price']
                log_content = log_content + '매도 / '
            log_content = str(log_content + '수량:' + str(round(self.order['balance'], 8)) + ' / 평단가:' + str(price) + ' / 총액:' + str(round(self.order['balance'] * price, 0)))

        return (log_time, log_content)


# 모든 프로젝트들의 최상위 클래스
class Project:
    # Order(현재시각, 프로젝트 객체, ticker, status, order(upbit or test))
    order_log = []
    runner_amount = 0

    def __init__(self, name: str, title: str, algs: list):  # 인자로 알고리즘 객체의 리스트를 받음
        # self.name = name
        self.title = title
        self.algorithms = algs  # 알고리즘 객체로 이루어진 리스트
        self.tickers = pu.get_tickers(fiat="KRW")  # 티커는 krw시장 전 종목
        self.buy_thread = BuyThread(self)
        self.sell_thread = SellThread(self)
        self.status = 'Off'
        self.balance = 10000  # 프로젝트에서 사용 가능한 현금량
        self.real_holdings = []
        self.test_holdings = []

        self.test_account = TestAccount()

    # 프로젝트가 실제 매매에 사용 중, 현재 테스트중이므로 비활성화
    def project_release(self):
        if self.status != 'Release':
            self.buy_thread.terminate()
            self.sell_thread.terminate()

            self.status = 'Release'
            # self.buy_thread.start()
            # self.sell_thread.start()
            # print('started?')

            Project.runner_amount += 1

    # 프로젝트가 실제 데이터를 활용한 테스트 중
    def project_testing(self):
        if self.status != 'Testing':
            self.buy_thread.terminate()
            self.sell_thread.terminate()

            self.status = 'Testing'
            self.buy_thread.start()
            self.sell_thread.start()

            Project.runner_amount += 1
            print(self.status)

    # 프로젝트가 현재 비활성화
    def project_off(self):
        if self.status != 'Off':
            self.status = 'Off'
            self.buy_thread.terminate()
            self.sell_thread.terminate()
            self.test_account.get_test_account()

            Project.runner_amount -= 1
            print(self.status)


# 티커 관련 알고리즘 수정 필요, 매수량 및 매수가 관련 알고리즘 수정 필요.
class BuyThread(QThread):
    def __init__(self, pj: Project):
        super().__init__()
        self.project = pj
        # print(len(list(self.project.algorithms.values())))

    def run(self):
        while True:
            for ticker in self.project.tickers:
                print(Project.runner_amount)

                data: DataFrame
                signal = True
                for al in self.project.algorithms:
                    try:
                        data = pu.get_ohlcv(ticker=ticker, interval=al.datatype, count=30)  # data의 규격은 일단 ohclv로 함, 30개만 가져옴.
                    except:
                        print("요청 초과!")
                        data = None
                        signal = False
                    if data is None:
                        break

                    signal = signal and bool(al.buy_algorithm(data))

                if signal:
                    print('hi')
                    if self.project.status == 'Release':
                        self.order_release(ticker, data)
                    elif self.project.status == 'Testing':
                        self.order_testing(ticker, data)
                    # print('here')
                self.msleep(250 * Project.runner_amount)

    # 프로젝트가 Release 상태 시 실제 주문, 일단 1/10주문으로 설정
    def order_release(self, ticker, data):
        print('orororo')
        order_balance = self.project.balance / 1.0005  # 최대 주문 가능 금액, 업비트 일반 주문 수수료 0.05%
        if order_balance < 5000:
            print("balance not enough!")
            return

        price = float(data['close'][-1])
        amount = order_balance / price
        order = Account.my_account.buy_limit_order(ticker, price, amount)

        self.project.real_holdings.append(order)
        self.project.tickers.remove(ticker)

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), order))

    # 1/3 주문으로 설정
    def order_testing(self, ticker, data):
        order_balance = self.project.test_account.balance / 3 / 1.0005 # 최대 주문 가능 금액, 업비트 일반 주문 수수료 0.05%
        if order_balance < 5000:
            print("balance not enough!")
            return

        price = float(data['close'][-1])
        amount = order_balance / price
        test_order = {
            'currency': ticker, 'balance': amount, 'avg_buy_price': price, 'created_at': datetime.now()
            , 'status': "Testing", 'side': 'bid'
        }
        self.project.test_holdings.append(test_order)
        self.project.tickers.remove(ticker)

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), test_order))
        self.project.test_account.buy_order(test_order)
        print(ticker)


# 티커 관련 알고리즘 수정 필요, 매도량 및 매도가 관련 알고리즘 수정 필요.
class SellThread(QThread):
    def __init__(self, pj: Project):
        super().__init__()
        self.project = pj

    # 주문단위로 판단하게 수정.
    def run(self):
        while True:
            # 일단 테스트 주문을 기준으로 만들었다. 나중에 실제와도 호환되게 수정할것. 174line
            for order in self.project.test_holdings:
                ticker = order['currency']

                data: DataFrame
                signal = True
                for al in self.project.algorithms:
                    try:
                        data = pu.get_ohlcv(ticker=ticker, interval=al.datatype, count=30)  # data의 규격은 일단 ohclv로 함, 30개만 가져옴.
                    except:
                        print("요청 초과!")
                        data = None
                        signal = False
                    if data is None:
                        break

                    signal = signal and bool(al.sell_algorithm(data, order, self.project.status))

                if signal:
                    if self.project.status == 'Release':
                        self.order_release(order, data)
                    elif self.project.status == 'Testing':
                        print('here?')
                        self.order_testing(order, data)
                    # print('there')
                self.msleep(1000 * Project.runner_amount)

    # 프로젝트가 Release 상태 시 실제 주문, 일단 풀주문으로 설정
    def order_release(self, order, data):
        ticker = order['currency']
        price = float(data['close'][-1])
        amount = Account.my_account.get_balance(ticker)
        order = Account.my_account.sell_limit_order(ticker, price, amount)

        self.project.real_holdings.remove(order)
        self.project.tickers.append(ticker)

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), order))

    # order 기반 주문
    def order_testing(self, order, data):
        ticker = order['currency']
        price = float(data['close'][-1])
        amount = float(self.project.test_account.wallet[ticker]['balance'])
        test_order = {
            'currency': ticker, 'balance': amount, 'avg_sell_price': price, 'created_at': datetime.now()
            , 'status': 'Testing', 'side': 'ask'
        }

        self.project.test_holdings.remove(order)
        self.project.tickers.append(ticker)

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), test_order))
        self.project.test_account.sell_order(test_order)
        print(ticker)
