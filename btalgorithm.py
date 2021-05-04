import pyupbit as pu
from datetime import datetime
from datetime import timedelta

# 각각의 프로젝트에 쓰일 알고리즘들을 모두 관리하는 모듈이다.


# 모든 알고리즘 클래스들의 최상위 클래스
class Algorithm:
    title: str
    description: str

    def __init__(self):
        pass

    # buy, sell은 하위 알고리즘 클래스들에서 재정의 할 것. 만약 정의 되어있지 않다면 True 반환해서 코드 진행에 피해 안가게 함.
    def buy_algorithm(self, data):
        return True

    def sell_algorithm(self, data):
        return True


# 급등주 포착으로 매매
class ObserveSoaringCoinAlg(Algorithm):
    title = '급등주 포착으로 빠르고 강력한 단타매매'
    description = '변동성 돌파 전략 사용, 전일고점과 전일저점의 차이 만큼 당일 상승하면 매수 후 20분 후 매도'

    def __init__(self):
        super().__init__()

    # 변동성 돌파 전략, k = 1
    def buy_algorithm(self, data):
        df = data
        yd = df.iloc[-2]  # yesterday data

        today_open = df.iloc[-1]['open']
        yd_var = yd['high'] - yd['low']
        target = today_open + yd_var * 1

        if df.iloc[-1]['close'] >= target:
            print('buy_alg_im buy')
            return True
        else:
            print('buy_alg_not buy')
            return False

    # 매수 20분 후 매도
    def sell_algorithm(self, data, order, status):
        get_time: str
        buy_order_time: datetime

        if status == 'Release':
            print('pass release')
            get_time = str(order['created_at']).split('T')
            buy_order_time = datetime(int(get_time[0][:4]), int(get_time[0][5:7]), int(get_time[0][-2:]),
                                          int(get_time[1][:2]), int(get_time[1][3:5]), int(get_time[1][6:8]))
        elif status == 'Testing':
            print('sell_alg_pass test')
            get_time = order['created_at']
            buy_order_time = get_time

        if (datetime.now() - buy_order_time + timedelta(seconds=1)).seconds > 1200:
            print('im sell')
            return True
        else:
            print('not sell')
            return False


