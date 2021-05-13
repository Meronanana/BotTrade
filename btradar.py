"""
기존 Algorithm - Project 관계의 주문 처리가 광범위한 티커를 점검하여 반응속도가 늦을 수 밖에 없다는 문제점이 있다.
암호화폐 자동매매는 코인 보유에 대한 리스크가 크므로 장기 - 스윙 보다는 단타 스캘핑 위주의 투자를 해야한다.
신설되는 Radar 클래스는 Project 에서 점검해야 하는 티커를 알려줌 으로써 더욱 유용한 티커만을 점검하게 한다.
"""

import pyupbit as pu
from PyQt5.QtCore import *


class Radar:
    def __init__(self, title: str = None, comp: list = None):
        self.title = title
        self.components = [] if comp is None else comp

    def get_radar_data(self):
        return [self.title, self.components]

    # RadarComponent 들이 반환하는 티커 중 중복하는 것만 반환
    def get_tickers(self):
        result = pu.get_tickers(fiat="KRW")
        for comp in self.components:
            result = list(set(result).intersection(comp.tickers))

        return result

    def radar_on(self):
        for comp in self.components:
            comp.start()

    def radar_off(self):
        for comp in self.components:
            comp.terminate()


# 티커를 KRW 시장 전체로 가지는 기본적인 레이더
class RadarComponent(QThread):
    description: str
    comps: list
    activated = False

    krw_tickers = pu.get_tickers("KRW")
    runner_amount = 0

    def __init__(self):
        # 컴포넌트 리스트 초기화
        if not RadarComponent.activated:
            RadarComponent.comps = []
            RadarComponent.comps.extend([FindRapidStarComp])
            RadarComponent.activated = True

        self.tickers = RadarComponent.krw_tickers

    def is_remarkable(self, ticker):
        return True

    def start(self, priority=None):
        RadarComponent.runner_amount += 1
        super().start()

    def terminate(self):
        RadarComponent.runner_amount -= 1
        super().terminate()

    def run(self):
        while True:
            for ticker in RadarComponent.krw_tickers:
                if self.is_remarkable(ticker):
                    self.tickers.append(ticker)
                else:
                    for out in self.tickers:
                        if out == ticker:
                            self.tickers.remove(out)

                # 초당 4개의 정보 이용
                self.msleep(250 * RadarComponent.runner_amount)


# 급등주 포착 레이더
class FindRapidStarComp(RadarComponent):
    description = "급등주 포착"

    def __init__(self):
        super().__init__()

    # 최근 20분간 5% 이상 상승한 분봉이 있다면 True
    def is_remarkable(self, ticker):
        data = pu.get_ohlcv(ticker=ticker, interval="minute1", count=20)
        for date, ohclv in data.iterrows():
            # 분봉 한개 추출
            diff = (ohclv['close'] - ohclv['open']) / ohclv['open'] * 100
            if diff > 5:
                return True

        return False
