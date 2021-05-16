import pyupbit as pu
from pandas import DataFrame
from PyQt5.QtCore import *
from bttestaccount import *
from btradar import *
from datetime import datetime
import asyncio


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

    # 시간 - 로그내용([프로젝트], 티커, 매수/매도, 수량, 평균단가, 거래총액)
    def order_to_log(self):
        log_time: str
        log_content: str
        if self.status == 'Release':
            # log_time = self.order_time.
            pass
        elif self.status == 'Testing':
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

    # 프로젝트 불러오기로 생성: [title, algs, r_hold, t_hold, div, test_acc]
    def __init__(self, title: str = "Untitled", algs: list = [], tickers: dict = None,
                 r_hold: list = None, t_hold: list = None, div: int = 1, test_acc: TestAccount = None,
                 radar: Radar = None):
        self.title = title  # 프로젝트 제목
        self.algorithms = algs  # 알고리즘 객체로 이루어진 리스트
        self.tickers = pu.get_tickers(fiat="KRW") if tickers is None else tickers
        self.buy_thread = BuyThread(self)
        self.sell_thread = SellThread(self)
        self.status = 'Off'  # 현재 프로젝트 상태 Off로 초기화
        self.balance = 10000  # 프로젝트에서 사용 가능한 현금량
        self.real_holdings = [] if r_hold is None else r_hold  # 실제 계좌에서 매수한 종목 리스트
        self.test_holdings = [] if t_hold is None else t_hold  # 테스트 계좌에서 매수한 종목 리스트
        self.divide_for = div  # 자금 분할 개수

        self.test_account = TestAccount() if test_acc is None else test_acc

        self.radar = Radar(comps=[RadarComponent()]) if radar is None else radar

    def __del__(self):
        self.project_off()

    def get_project_data(self):
        # [title, algs, tickers, r_hold, t_hold, div, test_acc, radar.title]
        return [self.title, self.algorithms, self.tickers, self.real_holdings,
                self.test_holdings, self.divide_for, self.test_account.get_acc_data(), self.radar.title]

    # 프로젝트가 실제 매매에 사용 중, 현재 테스트중이므로 비활성화
    def project_release(self):
        if self.status != 'Release':
            self.status = 'Release'
            # self.buy_thread.start()
            # self.sell_thread.start()
            # print('started?')

    # 프로젝트가 실제 데이터를 활용한 테스트 중
    def project_testing(self):
        if self.status != 'Testing':
            self.status = 'Testing'
            self.buy_thread.start()
            self.sell_thread.start()
            self.radar.radar_on()

            print(self.status)

    # 프로젝트에서 레이더만 활성화
    def project_radar_only(self):
        if self.status != 'Radar Only':
            self.status = 'Radar Only'
            self.buy_thread.terminate()
            self.sell_thread.terminate()
            self.radar.radar_on()

            print(self.status)

    # 프로젝트가 현재 비활성화
    def project_off(self):
        if self.status != 'Off':
            self.status = 'Off'
            self.buy_thread.terminate()
            self.sell_thread.terminate()
            self.radar.radar_off()

            print(self.status)


# 티커 관련 알고리즘 수정 필요, 매수량 및 매수가 관련 알고리즘 수정 필요.
class BuyThread(QThread):
    runner_amount = 0

    def __init__(self, pj: Project):
        super().__init__()
        self.project = pj

    def start(self, priority=None):
        BuyThread.runner_amount += 1
        super().start()

    def terminate(self):
        BuyThread.runner_amount -= 1
        super().terminate()

    def run(self):
        while True:
            self.project.tickers = self.project.radar.get_tickers()
            if self.project.tickers is None:
                print('sleep 10 sec')
                self.sleep(10)
                print('Wake Up!')
                continue

            for ticker in self.project.tickers:
                data: tuple

                signal = True   # 모두 통과해야 매수
                for al in self.project.algorithms:
                    try:
                        data = pu.get_ohlcv(ticker=ticker, interval=al.datatype, count=30)  # data의 규격은 일단 ohclv로 함, 30개만 가져옴.
                    except:
                        print("요청 초과!")
                        signal = False
                        break

                    signal = signal and bool(al.buy_algorithm(data))

                if signal:
                    if self.project.status == 'Release':
                        self.order_release(ticker, data)
                    elif self.project.status == 'Testing':
                        self.order_testing(ticker, data)

                # 초당 10/3*alg 개의 정보 이용
                self.msleep(300 * BuyThread.runner_amount)

    # 프로젝트가 Release 상태 시 실제 주문
    def order_release(self, ticker, data):
        order_balance = self.project.balance / 1.0005  # 최대 주문 가능 금액, 업비트 일반 주문 수수료 0.05%
        if order_balance < 5000:
            print("balance not enough!")
            return

        price = float(data['close'][-1])
        amount = order_balance / price
        order = Account.my_account.buy_limit_order(ticker, price, amount)

        self.project.real_holdings.append(order)

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), order))

    def order_testing(self, ticker, data):
        # 최대 주문 가능 금액, 업비트 일반 주문 수수료 0.05%
        try:
            order_balance = self.project.test_account.balance / (self.project.divide_for - len(self.project.test_account.wallet)) / 1.0005
        except:
            order_balance = 0

        if order_balance < 5000:
            print("balance not enough!")
            return

        price = float(data['close'][-1])
        amount = order_balance / price
        test_order = {
            'currency': ticker, 'balance': amount, 'avg_buy_price': price, 'created_at': datetime.now()
            , 'status': "Testing", 'side': 'bid'
        }

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), test_order))
        self.project.test_account.buy_order(test_order)


# 티커 관련 알고리즘 수정 필요, 매도량 및 매도가 관련 알고리즘 수정 필요.
class SellThread(QThread):
    runner_amount = 0

    def __init__(self, pj: Project):
        super().__init__()
        self.project = pj

    def start(self, priority=None):
        SellThread.runner_amount += 1
        super().start()

    def terminate(self):
        SellThread.runner_amount -= 1
        super().terminate()

    # 주문단위로 판단하게 수정.
    def run(self):
        while True:
            # 일단 테스트 주문을 기준으로 만들었다. 나중에 실제와도 호환되게 수정할것. 174line
            check = list(self.project.test_account.wallet.values())
            if len(check) == 0:
                self.sleep(30)
                continue
            for order in check:
                ticker = order['currency']

                data: tuple
                signal = False  # 하나라도 통과하면 매도
                for al in self.project.algorithms:
                    try:
                        data = pu.get_ohlcv(ticker=ticker, interval=al.datatype, count=30)  # data의 규격은 일단 ohclv로 함, 30개만 가져옴.
                    except Exception:
                        print("요청 초과!")
                        signal = False
                        break

                    signal = signal or bool(al.sell_algorithm(data, order, self.project.status))

                if signal:
                    if self.project.status == 'Release':
                        self.order_release(order, data)
                    elif self.project.status == 'Testing':
                        self.order_testing(order, data)

                # 초당 2*alg 개의 정보 이용
                self.msleep(500 * SellThread.runner_amount)

    # 프로젝트가 Release 상태 시 실제 주문, 일단 풀주문으로 설정
    def order_release(self, order, data):
        ticker = order['currency']
        price = float(data['close'][-1])
        amount = Account.my_account.get_balance(ticker)
        order = Account.my_account.sell_limit_order(ticker, price, amount)

        self.project.real_holdings.remove(order)

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

        Project.order_log.append(Order(datetime.now(), self.project, str(ticker), str(self.project.status), test_order))
        self.project.test_account.sell_order(test_order)
