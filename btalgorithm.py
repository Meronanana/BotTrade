from datetime import datetime
from datetime import timedelta
from pandas import DataFrame

# 각각의 프로젝트에 쓰일 알고리즘들을 모두 관리하는 모듈이다.


# 모든 알고리즘 클래스들의 최상위 클래스
class Algorithm:
    title: str
    description: str
    algs: list
    activated = False

    def __init__(self):
        # 알고리즘 리스트 초기화
        if not Algorithm.activated:
            Algorithm.algs = []
            Algorithm.algs.extend([BreakVolatilityAlg, CatchRapidStarAlg, StopLossAlg, ValuefeTradeAlg])
            Algorithm.activated = True

        self.datatype: str

    # buy, sell은 하위 알고리즘 클래스들에서 재정의 할 것. 만약 정의 되어있지 않다면 True 반환해서 코드 진행에 피해 안가게 함.
    def buy_algorithm(self, data):
        return True

    def sell_algorithm(self, data, order, status):
        return False


# 래리 윌리엄스 변동성 돌파전략
class BreakVolatilityAlg(Algorithm):
    title = '래리 윌리엄스의 변동성 돌파전략'
    description = '변동성 돌파 전략 사용, 전일고점과 전일저점의 차이 만큼 당일 상승하면 매수 후 당일 종가 매도'

    def __init__(self):
        super().__init__()
        self.datatype = "day"

    # 변동성 돌파 전략, k = 1
    def buy_algorithm(self, data):
        df = data
        yd = df.iloc[-2]  # yesterday data

        today_open = df.iloc[-1]['open']
        yd_var = yd['high'] - yd['low']
        target = today_open + yd_var * 1

        if df.iloc[-1]['close'] >= target:
            return True
        else:
            return False

    # 당일 종가 매도
    def sell_algorithm(self, data, order, status):
        buy_order_time: datetime

        if status == 'Release':
            get_time = str(order['created_at']).split('T')
            buy_order_time = datetime(int(get_time[0][:4]), int(get_time[0][5:7]), int(get_time[0][-2:])
                                      , int(get_time[1][:2]), int(get_time[1][3:5]), int(get_time[1][6:8]))
        elif status == 'Testing':
            buy_order_time = order['created_at']

        sell_time = datetime(buy_order_time.year, buy_order_time.month, buy_order_time.day
                             , hour=0, minute=0, second=0) + timedelta(days=1)
        if datetime.now() > sell_time:
            return True
        else:
            return False


# 두 번째 알고리즘!
class CatchRapidStarAlg(Algorithm):
    title = '급등주 포착으로 빠르고 강력한 단타매매'
    description = '변동성 돌파 전략 사용, 1분봉*5개 기준 전 기간 (최고-최저)*2 만큼 오르면 매수'

    def __init__(self):
        super().__init__()
        self.datatype = "minute1"

    # 변동성 돌파 전략, k = 2, 최근 5분간 변동성 추적
    def buy_algorithm(self, data):
        df = data

        df_highs = list(df['high'])
        df_lows = list(df['low'])
        high = df_highs[-6]
        low = df_lows[-6]
        for i in range(-5, -1):
            if high < df_highs[i]:
                high = df_highs[i]
            if low > df_lows[i]:
                low = df_lows[i]

        bf5_var = high - low

        # 변동성이 전봉종가의 1% 미만이면 건드리지 않음.
        if bf5_var < data.iloc[-2]['close'] * 0.01:
            return False

        target = df.iloc[-1]['open'] + bf5_var * 2

        if df.iloc[-1]['close'] >= target:
            return True
        else:
            return False

    def sell_algorithm(self, data, order, status):
        """
        최소 매수 20분 후 매도
        buy_order_time: datetime

        if status == 'Release':
            get_time = str(order['created_at']).split('T')
            buy_order_time = datetime(int(get_time[0][:4]), int(get_time[0][5:7]), int(get_time[0][-2:]),
                                          int(get_time[1][:2]), int(get_time[1][3:5]), int(get_time[1][6:8]))
        elif status == 'Testing':
            buy_order_time = order['created_at']

        if (datetime.now() - buy_order_time + timedelta(seconds=1)).seconds > 1200:
            return True
        else:
            return False
        """
        # 거래량이 이전보다 적으면 매도
        buy_order_time: datetime

        if status == 'Release':
            get_time = str(order['created_at']).split('T')
            buy_order_time = datetime(int(get_time[0][:4]), int(get_time[0][5:7]), int(get_time[0][-2:]),
                                      int(get_time[1][:2]), int(get_time[1][3:5]), int(get_time[1][6:8]))
        elif status == 'Testing':
            buy_order_time = order['created_at']

        if (datetime.now() - buy_order_time + timedelta(seconds=1)).seconds > 120:
            vol = list(data['volume'])
            if vol[-2] < vol[-3]:
                return True
            else:
                return False
        else:
            return False


# 손절 알고리즘!
class StopLossAlg(Algorithm):
    title = '손절 알고리즘 : -3%'
    description = '수익률이 -3%시, 추가 손해를 막기 위해 손절.'

    def __init__(self):
        super().__init__()
        self.datatype = "day"

    # -3%시, 손절
    def sell_algorithm(self, data, order, status):
        stop_loss = float(order['avg_buy_price']) * 0.97

        if stop_loss > float(data.iloc[-1]['close']):
            return True
        else:
            return False


# 눌림목 매매 알고리즘, 생각보다 쉽지않다...
class ValuefeTradeAlg(Algorithm):
    title = '눌림목 매매 알고리즘'
    description = '1차 상승 이후 눌림목에서 매수, 2차 상승 이후 매도'

    def __init__(self):
        super().__init__()
        self.datatype = "minute1"

    def buy_algorithm(self, data: DataFrame):
        is_up = []
        length = len(data['open'])
        for i in range(length):
            if (data.iloc[i]['close'] - data.iloc[i]['open']) > 0:
                is_up.append(True)
            else:
                is_up.append(False)

        is_up.reverse()
        false_stack = 0
        true_stack = 0

        # 그래프 형태 수집
        signal = is_up[0]
        while signal and false_stack < 5 and true_stack < 10:
            if false_stack == 0 and true_stack == 0:
                if not is_up[0]:
                    false_stack += 1
                    continue
                else:
                    signal = False
                    break
            elif false_stack > 0 and true_stack == 0:
                if not is_up[0]:
                    false_stack += 1
                    continue
                else:
                    true_stack += 1
                    continue
            elif false_stack > 0 and true_stack > 0:
                if is_up[0]:
                    true_stack += 1
                    continue
                else:
                    signal = False
                    break

        # 양봉 3회 이상 음봉 2회 이하일 때 눌림목으로 판단
        if true_stack < 3 or false_stack > 2:
            return False

        # 최근 상승 3개봉동안 거래량이 증가추세임
        increase = True
        for i in range(3):
            increase = increase and (data['volume'][-3-false_stack-i] > data['volume'][-3-false_stack-i-1])
        if not increase:
            return False

        # 하락분이 상승분의 60퍼센트를 넘지않을 때 눌림목으로 판단
        descend = data['open'][-3-false_stack+1] - data['close'][-3]
        ascend = data['close'][-3-false_stack] - data['open'][-3-false_stack-true_stack+1]
        if ascend * 0.1 < descend < ascend * 0.6:
            return True
        else:
            return False

    # 거래량이 이전보다 꽤 낮아지거나 거대 음봉에 접어들면 매도
    def sell_algorithm(self, data, order, status):
        if status == 'Release':
            get_time = str(order['created_at']).split('T')
            buy_order_time = datetime(int(get_time[0][:4]), int(get_time[0][5:7]), int(get_time[0][-2:]),
                                      int(get_time[1][:2]), int(get_time[1][3:5]), int(get_time[1][6:8]))
        elif status == 'Testing':
            buy_order_time = order['created_at']

        if (datetime.now() - buy_order_time + timedelta(seconds=1)).seconds > 120:
            # 거래량이 이전 분봉의 반토막이 나면 매도
            vol = list(data['volume'])
            vol_bool = vol[-2] < vol[-3] * 0.5

            # 가격이 이전 분봉 상승분의 50% 이상 하락하면 매도
            first_ascend = data.iloc[-2]['close'] - data.iloc[-2]['open']
            after_descend = data.iloc[-1]['open'] - data.iloc[-1]['close']
            var_bool = after_descend > first_ascend * 0.5

            if vol_bool or var_bool:
                return True
            else:
                return False
        else:
            return False
