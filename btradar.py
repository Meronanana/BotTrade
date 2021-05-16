"""
기존 Algorithm - Project 관계의 주문 처리가 광범위한 티커를 점검하여 반응속도가 늦을 수 밖에 없다는 문제점이 있다.
암호화폐 자동매매는 코인 보유에 대한 리스크가 크므로 장기 - 스윙 보다는 단타 스캘핑 위주의 투자를 해야한다.
신설되는 Radar 클래스는 Project 에서 점검해야 하는 티커를 알려줌 으로써 더욱 유용한 티커만을 점검하게 한다.
"""

import pyupbit as pu
from PyQt5.QtCore import *


class Radar:
    def __init__(self, title: str = None, comps: list = None):
        self.title = title
        self.components = [] if comps is None else comps

    # [title, comp_data[get_comp_data[class_name, tickers]]]
    def get_radar_data(self):
        comp_data = []
        for comp in self.components:
            comp_data.append(comp.get_comp_data())
        return [self.title, comp_data]

    # RadarComponent 들이 반환하는 티커 중 중복하는 것만 반환
    def get_tickers(self):
        result = pu.get_tickers(fiat="KRW")
        for comp in self.components:
            if len(comp.tickers) == 0:
                return None

            result = list(set(result).intersection(comp.tickers))

        print(result)
        return result

    def radar_on(self):
        print("Radar ON")
        for comp in self.components:
            comp.start()

    def radar_off(self):
        print("Radar OFF")
        for comp in self.components:
            comp.terminate()


# 티커를 KRW 시장 전체로 가지는 기본적인 레이더
class RadarComponent(QThread):
    description = "Default"
    comps: dict
    activated = False

    krw_tickers = pu.get_tickers("KRW")
    runner_amount = 0

    def __init__(self, tickers: list = None):
        super().__init__()
        # 컴포넌트 리스트 초기화
        if not RadarComponent.activated:
            RadarComponent.comps = {'Default': RadarComponent, 'FindRapidStarComp': FindRapidStarComp}
            RadarComponent.activated = True

        self.tickers = RadarComponent.krw_tickers if tickers is None else tickers

    # [class_name, tickers]
    def get_comp_data(self):
        return [self.__class__.__name__, self.tickers]

    def set_tickers(self, tickers: list):
        self.tickers = tickers

    def is_remarkable(self, ticker):
        return True

    @staticmethod
    def descriptions():
        result = []
        for comp in RadarComponent.comps.values():
            result.append(comp.description)

        return result

    @staticmethod
    def find_radar_component(description: str):
        for comp in RadarComponent.comps.values():
            if comp.description == description:
                return comp

        return None

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
                    try:
                        self.tickers.remove(ticker)
                    except ValueError:
                        pass
                    self.tickers.append(ticker)
                else:
                    try:
                        self.tickers.remove(ticker)
                    except ValueError:
                        pass

                # 초당 4개의 정보 이용
                self.msleep(250 * RadarComponent.runner_amount)


# 급등주 포착 레이더
class FindRapidStarComp(RadarComponent):
    description = "급등주 포착"

    def __init__(self):
        super().__init__()

    # 최근 20분간 2% 이상 상승한 1분봉이 있다면 True
    def is_remarkable(self, ticker):
        try:
            data = pu.get_ohlcv(ticker=ticker, interval="minute1", count=20)
        except Exception:
            return False

        for date, ohclv in data.iterrows():
            # 분봉 한개 추출
            diff = (ohclv['close'] - ohclv['open']) / ohclv['open'] * 100
            if diff > 2:
                return True

        return False
