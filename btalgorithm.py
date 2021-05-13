from datetime import datetime
from datetime import timedelta
from pandas import DataFrame
import random

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
            Algorithm.algs.extend([BreakVolatilityAlg, LowValueAlg, StopLossAlg, TestChimpanzeeAlg])
            Algorithm.activated = True

        self.datatype = 'day'

    # buy, sell은 하위 알고리즘 클래스들에서 재정의 할 것. 만약 정의 되어있지 않다면 True 반환해서 코드 진행에 피해 안가게 함.
    def buy_algorithm(self, data):
        return True

    def sell_algorithm(self, data, order, status):
        return False

    # 각자 다른 시간 포맷을 datetime형으로 반환
    @staticmethod
    def to_datetime(time: str, status: str):
        temp: datetime
        if status == 'Release':
            get_time = time.split('T')
            temp = datetime(int(get_time[0][:4]), int(get_time[0][5:7]), int(get_time[0][-2:])
                            , int(get_time[1][:2]), int(get_time[1][3:5]), int(get_time[1][6:8]))
        elif status == 'Testing':
            temp = time

        return temp


# 테스트용 침팬지 매수 매도 알고리즘
class TestChimpanzeeAlg(Algorithm):
    title = '테스트용 침팬지'
    description = '랜덤으로 매수와 매도를 결정한다'

    def __init__(self):
        super().__init__()
        self.datatype = 'day'

    # 1% 확률로 매수
    def buy_algorithm(self, data):
        if random.random() * 100 < 1:
            return True
        else:
            return False

    # 0.05% 확률로 매도
    def sell_algorithm(self, data, order, status):
        if random.random() * 100 < 0.05:
            return True
        else:
            return False


# 래리 윌리엄스 변동성 돌파전략
class BreakVolatilityAlg(Algorithm):
    title = '래리 윌리엄스의 변동성 돌파전략'
    description = '변동성 돌파 전략 사용, 전일고점과 전일저점의 차이 만큼 당일 상승하면 매수 후 당일 12시 매도'

    def __init__(self):
        super().__init__()
        self.datatype = "day"

    # 변동성 돌파 전략, k = 1
    def buy_algorithm(self, data):
        now_hour = datetime.now().hour
        if 0 <= now_hour < 10:
            return False

        df = data
        yd = df.iloc[-2]  # yesterday project_data

        today_open = df.iloc[-1]['open']
        yd_var = yd['high'] - yd['low']
        target = today_open + yd_var * 1

        if df.iloc[-1]['close'] >= target:
            return True
        else:
            return False

    # 당일 12시 매도
    def sell_algorithm(self, data, order, status):
        buy_order_time = self.to_datetime(order['created_at'], status)

        sell_time = datetime(buy_order_time.year, buy_order_time.month, buy_order_time.day
                             , hour=0, minute=0, second=0) + timedelta(days=1)
        if datetime.now() > sell_time:
            return True
        else:
            return False


# 두 번째 알고리즘! / 임시 폐지
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


# 눌림목 매매 알고리즘 / 임시 폐지
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
        is_up.pop(0)
        false_stack = 0
        true_stack = 0

        # 그래프 형태 수집
        signal = is_up[0]
        while signal:
            if false_stack == 0 and true_stack == 0:
                if not is_up[0]:
                    false_stack += 1
                else:
                    signal = False
            elif false_stack > 0 and true_stack == 0:
                if not is_up[0]:
                    false_stack += 1
                else:
                    true_stack += 1
            elif false_stack > 0 and true_stack > 0:
                if is_up[0]:
                    true_stack += 1
                else:
                    signal = False

            if len(is_up) == 1:
                signal = False
            else:
                is_up.pop(0)

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
        buy_order_time = self.to_datetime(order['created_at'], status)

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


# 기존 내가 매매하던 방법대로 가자. 저평가 매수 전략
class LowValueAlg(Algorithm):
    title = '저평가 매수 전략'
    description = '작전이 들어올 만한 종목을 미리 선정해서 매수함.'

    def __init__(self):
        super().__init__()
        self.datatype = 'day'

        # 변동성이 낮은 3개 종목 선정, [변동폭, 카운트]
        self.low_volatility = []
        self.max_size = 3

    # 내림차순으로 정렬
    def sort_lower(self):
        lt = self.low_volatility
        for i in range(len(lt)):
            for j in range(i+1, len(lt)):
                if lt[i][0] < lt[j][0]:
                    temp = lt[i]
                    lt[i] = lt[j]
                    lt[j] = temp

        self.low_volatility = lt

    # 작업마다 수명 1씩 올리기, ticker 개수 초과 이면 리스트에서 제거
    def aging(self):
        pop_list = []
        for i in range(len(self.low_volatility)):
            self.low_volatility[i][1] += 1
            if self.low_volatility[i][1] > 118:
                pop_list.append(i)

        pop_list.reverse()
        for i in pop_list:
            self.low_volatility.pop(i)

        self.sort_lower()

    # 지금이 매매시간인지 판단
    def is_right_time(self):
        # 지정된 시간에만 매매
        now = datetime.now()
        buy_start_time = datetime(now.year, now.month, now.day, 8, 50, 0)
        buy_end_time = datetime(now.year, now.month, now.day, 8, 59, 30)
        if buy_start_time < now < buy_end_time:
            return True
        else:
            return False

    def buy_algorithm(self, data):
        self.aging()

        # 과거 10일간 종가 대비 변동폭의 평균
        day10_ohclv = data.iloc[range(-11, -1)]
        day10_vol_avg = 0
        for i in range(len(day10_ohclv)):
            this_ohclv = day10_ohclv.iloc[-(i+1)]
            day10_vol_avg = (day10_vol_avg * i + (this_ohclv['high'] - this_ohclv['low']) / this_ohclv['close'] * 100) / (i+1)

        # 아예 값이 같으면 대체
        for i in range(len(self.low_volatility)):
            if self.low_volatility[i][0] == day10_vol_avg:
                self.low_volatility[i] = [day10_vol_avg, 1]
                return self.is_right_time()

        # 리스트가 비었으면 추가
        if len(self.low_volatility) < self.max_size:
            self.low_volatility.append([day10_vol_avg, 1])
            self.sort_lower()
            return False

        # 리스트가 꽉 차있으면 비교하여 밀어내기
        if self.low_volatility[0][0] >= day10_vol_avg:
            self.low_volatility[0] = [day10_vol_avg, 1]
            self.sort_lower()
            return self.is_right_time()

        return False

    # 이익 실현: +15%, 손절매: -10%
    def sell_algorithm(self, data, order, status):
        now_price = data['close'][-1]
        avg_buy_price = order['avg_buy_price']
        if avg_buy_price * 0.9 < now_price < avg_buy_price * 1.15:
            return False
        else:
            return True


# 스캘핑 매매
class ScalpingAlg(Algorithm):
    pass
