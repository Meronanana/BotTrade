import sys
import time
import pickle
from pandas import DataFrame
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from btproject import *
from btalgorithm import *
import devtools

main_ui = uic.loadUiType("main.ui")[0]


def load_data():
    radar_data = {}
    project_data = {}

    # Radar 정보 Loading
    try:
        with open('radarFiles.pickle', 'rb') as file:
            serialized = pickle.load(file)
            for line in serialized:
                # [title, comp_data[get_comp_data[class_name, tickers]]]
                comps = []
                for i in range(len(line[1])):
                    comp_class = RadarComponent.comps[line[1][i][0]]
                    comp = comp_class()
                    comp.set_tickers(line[1][i][1])
                    comps.append(comp)

                radar_data[line[0]] = Radar(title=line[0], comps=comps)
    except(FileNotFoundError, EOFError):
        pass

    # Project 정보 Loading
    try:
        with open('projectFiles.pickle', 'rb') as file:
            serialized = pickle.load(file)
            for line in serialized:
                if len(line) == 7:
                    # [title, algs, tickers, r_hold, t_hold, div, test_acc]
                    project_data[line[0]] = \
                        Project(title=line[0], algs=line[1], tickers=line[2], r_hold=line[3],
                                t_hold=line[4], div=line[5], test_acc=TestAccount(line[6][0], line[6][1]))
                elif len(line) == 8:
                    # [title, algs, tickers, r_hold, t_hold, div, test_acc, radar]
                    project_data[line[0]] = \
                        Project(title=line[0], algs=line[1], tickers=line[2], r_hold=line[3],
                                t_hold=line[4], div=line[5], test_acc=TestAccount(line[6][0], line[6][1]),
                                radar=radar_data[line[7]])
    except(FileNotFoundError, EOFError):
        pass

    return [radar_data, project_data]


# 레이더 data는 프로젝트 data처럼 받아올 것이다
def write_data(radar_data: dict, project_data: dict):
    # 정보들 파이썬 기본 클래스로 직렬화
    # Radar writing
    serialized = []
    for title in radar_data.keys():
        # [title, comp_data[get_comp_data[class_name, tickers]]]
        add = radar_data[title].get_radar_data()
        serialized.append(add)

    with open('radarFiles.pickle', 'wb') as file:
        pickle.dump(serialized, file)

    # Project writing
    serialized = []
    for title in project_data.keys():
        # [title, algs, r_hold, t_hold, div, test_acc.get_acc_data, radar.title]
        add = project_data[title].get_project_data()
        serialized.append(add)

    with open('projectFiles.pickle', 'wb') as file:
        pickle.dump(serialized, file)


class AddRadar(QDialog):
    class CompInRadar(QWidget):
        def __init__(self, comp: RadarComponent):
            super().__init__()
            ui = 'comp_in_radar.ui'
            uic.loadUi(ui, self)

            self.comp = comp

            self.component_title_label.setText(self.comp.description)

    class SetRadarDetail(QDialog):
        def __init__(self, parent, detail: tuple):
            super().__init__(parent)
            ui = 'set_radar_detail.ui'
            uic.loadUi(ui, self)

            self.title = detail[0]
            self.description = detail[1]

            self.initialize_detail()

            self.accept_pushButton.clicked.connect(self.accept)
            self.reject_pushButton.clicked.connect(self.reject)

            self.show()

        def initialize_detail(self):
            self.title_lineEdit.setText(self.title)
            self.description_lineEdit.setText(self.description)

        @pyqtSlot()
        def accept(self):
            self.accepted = True
            self.title = str(self.title_lineEdit.text())
            self.description = str(self.description_lineEdit.text())
            super().accept()

        @pyqtSlot()
        def reject(self):
            self.accepted = False
            super().reject()

    def __init__(self, parent):
        super().__init__(parent)
        ui = 'add_radar_in_main.ui'
        uic.loadUi(ui, self)
        self.component_comboBox.addItems(RadarComponent.descriptions())

        self.title = 'New_Radar'
        self.description = 'No description'
        self.comps = []

        self.detail_pushButton.clicked.connect(self.set_detail)
        self.add_comp_pushButton.clicked.connect(self.add_component)
        self.del_comp_pushButton.clicked.connect(self.del_component)
        self.accept_pushButton.clicked.connect(self.accept)
        self.reject_pushButton.clicked.connect(self.reject)

    @pyqtSlot()
    def set_detail(self):
        window = AddRadar.SetRadarDetail(self, (self.title, self.description))
        window.exec_()
        if window.accepted:
            self.title = str(window.title)
            self.description = str(window.description)

    @pyqtSlot()
    def add_component(self):
        item = QListWidgetItem(self.component_listWidget)
        comp = RadarComponent.find_radar_component(self.component_comboBox.currentText())
        comp_instance = comp()
        self.comps.append(comp_instance)
        widget = AddRadar.CompInRadar(self.comps[-1])
        item.setSizeHint(QSize(0, 50))
        self.component_listWidget.setItemWidget(item, widget)
        self.component_listWidget.addItem(item)

    @pyqtSlot()
    def del_component(self):
        item = self.component_listWidget.currentItem()
        self.comps.pop(self.component_listWidget.currentRow())
        self.component_listWidget.takeItem(self.component_listWidget.row(item))

    @pyqtSlot()
    def accept(self):
        self.accepted = True
        super(AddRadar, self).accept()

    @pyqtSlot()
    def reject(self):
        self.accepted = False
        super(AddRadar, self).reject()


class AddProject(QDialog):
    class AlgInProject(QWidget):
        def __init__(self, alg: Algorithm):
            super().__init__()
            ui = 'algorithms_in_project.ui'
            uic.loadUi(ui, self)

            self.alg = alg

            self.algorithm_title_label.setText(self.alg.title)

    class RadarInProject(QWidget):
        def __init__(self, radar: Radar):
            super().__init__()
            ui = 'radar_in_project.ui'
            uic.loadUi(ui, self)

            self.radar = radar

            self.radar_title_label.setText(self.radar.title)
            print(radar.title)

    class SetProjectDetail(QDialog):
        def __init__(self, parent, detail: tuple):
            super(AddProject.SetProjectDetail, self).__init__(parent)
            ui = 'set_project_detail.ui'
            uic.loadUi(ui, self)

            self.title = detail[0]
            self.description = detail[1]
            self.divide_for = detail[2]

            self.initialize_detail()

            self.accept_pushButton.clicked.connect(self.accept)
            self.reject_pushButton.clicked.connect(self.reject)

            self.show()

        def initialize_detail(self):
            self.title_lineEdit.setText(self.title)
            self.description_lineEdit.setText(self.description)
            self.divide_for_spinBox.setValue(int(self.divide_for))

        @pyqtSlot()
        def accept(self):
            self.accepted = True
            self.title = str(self.title_lineEdit.text())
            self.description = str(self.description_lineEdit.text())
            self.divide_for = int(self.divide_for_spinBox.value())
            super(AddProject.SetProjectDetail, self).accept()

        @pyqtSlot()
        def reject(self):
            self.accepted = False
            super(AddProject.SetProjectDetail, self).reject()

    def __init__(self, parent):
        super(AddProject, self).__init__(parent)
        ui = 'add_algorithms_in_project.ui'
        uic.loadUi(ui, self)
        self.algorithm_comboBox.addItems(MainWindow.algs.keys())
        self.radar_comboBox.addItems(MainWindow.rds.keys())

        self.title = 'New_Project'
        self.description = 'No description'
        self.algorithms = []
        self.radar = MainWindow.rds[self.radar_comboBox.currentText()]
        self.divide_for = '1'

        self.algorithm_comboBox.activated.connect(self.add_algorithm)
        self.radar_comboBox.activated.connect(self.change_radar)
        self.detail_pushButton.clicked.connect(self.set_detail)
        self.del_alg_pushButton.clicked.connect(self.del_algorithm)
        self.accept_pushButton.clicked.connect(self.accept)
        self.reject_pushButton.clicked.connect(self.reject)

        self.show()

    @pyqtSlot()
    def set_detail(self):
        window = AddProject.SetProjectDetail(self, (self.title, self.description, self.divide_for))
        window.exec_()
        if window.accepted:
            self.title = str(window.title)
            self.description = str(window.description)
            self.divide_for = int(window.divide_for)

    @pyqtSlot()
    def add_algorithm(self):
        item = QListWidgetItem(self.algorithm_listWidget)
        self.algorithms.append(MainWindow.algs[self.algorithm_comboBox.currentText()])
        widget = AddProject.AlgInProject(self.algorithms[-1])
        item.setSizeHint(QSize(0, 50))
        self.algorithm_listWidget.setItemWidget(item, widget)
        self.algorithm_listWidget.addItem(item)

    @pyqtSlot()
    def change_radar(self):
        self.radar = MainWindow.rds[self.radar_comboBox.currentText()]

    @pyqtSlot()
    def del_algorithm(self):
        item = self.algorithm_listWidget.currentItem()
        self.algorithms.pop(self.algorithm_listWidget.currentRow())
        self.algorithm_listWidget.takeItem(self.algorithm_listWidget.row(item))

    @pyqtSlot()
    def accept(self):
        self.accepted = True
        super(AddProject, self).accept()

    @pyqtSlot()
    def reject(self):
        self.accepted = False
        super(AddProject, self).reject()


class TradeLog(QDialog):
    def __init__(self, parent):
        super(TradeLog, self).__init__(parent)
        ui = 'trade_log.ui'
        uic.loadUi(ui, self)
        self.project_comboBox.addItems(MainWindow.pjs.keys())
        self.sort_log()

        self.apply_pushButton.clicked.connect(self.sort_log)

        self.show()

    @pyqtSlot()
    def sort_log(self):
        # 로그 구분 범위에 따라 나누어서 해당 로그만 표시
        sort = self.project_comboBox.currentText()
        if sort == 'All':
            # QTableWidget.setItem()
            self.log_tableWidget.setRowCount(len(Project.order_log))
            for i, log in enumerate(reversed(Project.order_log)):
                order_log = log.order_to_log()
                item_time = QTableWidgetItem(order_log[0])
                item_content = QTableWidgetItem(order_log[1])
                # item_time.setSizeHint(QSize(100, 0))
                # item_content.setSizeHint(QSize(200, 0))
                self.log_tableWidget.setItem(i, 0, item_time)
                self.log_tableWidget.setItem(i, 1, item_content)


class ProjectDetail(QDialog):
    def __init__(self, parent, pj: Project):
        super(ProjectDetail, self).__init__(parent)
        ui = 'project_detail.ui'
        uic.loadUi(ui, self)
        self.project = pj

        self.title_lineEdit.setText(self.project.title)
        self.initialize_balance()

        self.reset_pushButton.clicked.connect(self.initialize_balance)

        self.show()

    def initialize_balance(self):
        test_acc = self.project.test_account

        # 총보유자산-총매수금액-총평가금액-총평가손익-총평가수익률
        acc_balance = test_acc.get_test_account()
        self.total_balance_lineEdit.setText(str(acc_balance[0]))
        self.total_bought_lineEdit.setText(str(acc_balance[1]))
        self.total_evaluate_lineEdit.setText(str(acc_balance[2]))
        self.diff_lineEdit.setText(str(acc_balance[3]))
        self.diff_rate_lineEdit.setText(str(acc_balance[4])+'%')

        # 보유코인-보유수량-매수평균가-매수금액-평가금액-평가손익
        data = [['KRW', '-', '-', '-', str(test_acc.balance), '-']]
        for currency in test_acc.wallet:
            amount = test_acc.wallet[currency]['balance']
            buy_price = test_acc.wallet[currency]['avg_buy_price']
            now_price = pu.get_current_price(currency)
            data.append([
                currency
                , str(round(amount, 8))
                , str(round(buy_price, 2))
                , str(int(amount*buy_price))
                , str(int(amount*now_price))
                , str(round((amount*now_price-amount*buy_price)/(amount*buy_price)*100, 2))+'%'
            ])

        self.balance_tableWidget.setRowCount(len(data))
        for i, d in enumerate(data):
            for j, d2 in enumerate(d):
                item = QTableWidgetItem(d2)
                self.balance_tableWidget.setItem(i, j, item)


class MainWindow(QMainWindow, main_ui):
    algs = {}
    pjs = {}
    rds = {}

    class AlgInMain(QWidget):
        def __init__(self, alg: Algorithm):
            super(MainWindow.AlgInMain, self).__init__()
            ui = 'algorithms_in_main.ui'
            uic.loadUi(ui, self)

            self.title = alg.title
            self.description = alg.description

            self.algorithm_title_label.setText(self.title)
            self.algorithm_dp_label.setText(self.description)

            # 시그널-슬롯 연결
            self.detail_pushButton.clicked.connect(self.show_detail)

        @pyqtSlot()
        def show_detail(self):
            # 추후 세부사항 표시 위젯 띄우기
            pass

    class RadarInMain(QWidget):
        def __init__(self, rd: Radar):
            super().__init__()
            ui = 'radar_in_main.ui'
            uic.loadUi(ui, self)

            self.radar = rd
            self.title = rd.title

            self.radar_title_label.setText(self.title)
            t = ''
            for i in rd.components:
                print(i)
                t = t + i.__class__.description + ', '
            t = t.rstrip(', ')
            self.components_label.setText(t)

            # 버튼 시그널-슬롯 연결
            self.detail_pushButton.clicked.connect(self.show_detail)

        @pyqtSlot()
        def show_detail(self):
            # 속성 표시하는 Dialog 하나 만들기
            pass

    class ProjectInMain(QWidget):
        def __init__(self, pj: Project):
            super(MainWindow.ProjectInMain, self).__init__()
            ui = 'projects_in_main.ui'
            uic.loadUi(ui, self)

            self.project = pj
            self.title = pj.title

            self.project_title_label.setText(self.title)
            t = ''      # algorithms_label text 설정
            for i in pj.algorithms:
                t = t + i.title + ', '
            t = t.rstrip(', ')
            self.algorithms_label.setText(t)
            self.radar_label.setText(pj.radar.title)

            # 버튼 시그널-슬롯 연결
            self.apply_pushButton.clicked.connect(self.set_project_status)
            self.backtest_pushButton.clicked.connect(self.run_backtest)
            self.detail_pushButton.clicked.connect(self.show_detail)

        @pyqtSlot()
        def set_project_status(self):
            t = self.status_choose_comboBox.currentText()
            if t == 'Release':
                self.status_label.setText('R')
                self.project.project_release()
            elif t == 'Testing':
                self.status_label.setText('T')
                self.project.project_testing()
            elif t == 'Off':
                self.status_label.setText('-')
                self.project.project_off()

        @pyqtSlot()
        def run_backtest(self):
            # 추후 백테스팅 하는 알고리즘 만들어 추가하기
            pass

        @pyqtSlot()
        def show_detail(self):
            window = ProjectDetail(self, self.project)
            window.exec_()

    def __init__(self, radars: dict, projects: dict):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("stock_icon.png"))

        # 알고리즘, 레이더, 프로젝트들 초기화
        self.add_algorithms()

        if radars is None:
            pass
        else:
            for title in radars.keys():
                radar = radars[title]
                self.create_radar_in_main(radar)

        if projects is None:
            pass
        else:
            for title in projects.keys():
                project = projects[title]
                self.create_project_in_main(project)

        # 버튼들 시그널-슬롯 연결
        self.log_pushButton.clicked.connect(self.trade_log)
        self.add_radar_pushButton.clicked.connect(self.add_radar)
        self.delete_radar_pushButton.clicked.connect(self.delete_radar)
        self.add_project_pushButton.clicked.connect(self.add_project)
        self.delete_project_pushButton.clicked.connect(self.delete_project)
        self.ram_usage_pushButton.clicked.connect(devtools.memory_usage)

    # 알고리즘들을 Dialog에 표시
    def add_algorithms(self):
        for alg in Algorithm.algs:
            # QListWidget에 Item 추가하는 법
            item = QListWidgetItem(self.algorithm_listWidget)
            widget = MainWindow.AlgInMain(alg)
            item.setSizeHint(QSize(0, 60))
            self.algorithm_listWidget.setItemWidget(item, widget)
            self.algorithm_listWidget.addItem(item)
            MainWindow.algs[widget.title] = alg()

    def create_radar_in_main(self, radar):
        item = QListWidgetItem(self.radars_listWidget)
        widget = MainWindow.RadarInMain(radar)
        item.setSizeHint(QSize(0, 70))

        self.radars_listWidget.setItemWidget(item, widget)
        self.radars_listWidget.addItem(item)

        # 같은 title의 레이더 두개 이상 생성하면 에러뜬다
        MainWindow.rds[widget.title] = radar

    # Dialog에 project 나타내는 Widget을 생성
    def create_project_in_main(self, project):
        item = QListWidgetItem(self.projects_listWidget)
        widget = MainWindow.ProjectInMain(project)
        item.setSizeHint(QSize(0, 90))

        self.projects_listWidget.setItemWidget(item, widget)
        self.projects_listWidget.addItem(item)

        # 같은 title의 프로젝트 두개 이상 생성하면 에러뜬다
        MainWindow.pjs[widget.title] = project

    # Slots for Radar
    @pyqtSlot()
    def add_radar(self):
        window = AddRadar(self)
        window.exec_()
        if window.accepted:
            rd = Radar(title=str(window.title), comps=window.comps)
            self.create_radar_in_main(rd)

    @pyqtSlot()
    def delete_radar(self):
        item = self.radars_listWidget.currentItem()
        radar = MainWindow.rds[self.radars_listWidget.itemWidget(item).title]
        radar.radar_off()
        del MainWindow.rds[self.radars_listWidget.itemWidget(item).title]
        self.radars_listWidget.takeItem(self.radars_listWidget.row(item))

    # Slots for Project
    @pyqtSlot()
    def trade_log(self):
        window = TradeLog(self)

    @pyqtSlot()
    def add_project(self):
        window = AddProject(self)
        window.exec_()
        if window.accepted:
            pj = Project(title=str(window.title), algs=window.algorithms, div=window.divide_for, radar=window.radar)
            self.create_project_in_main(pj)

    @pyqtSlot()
    def delete_project(self):
        item = self.projects_listWidget.currentItem()
        project = MainWindow.pjs[self.projects_listWidget.itemWidget(item).title]
        project.project_off()
        del MainWindow.pjs[self.projects_listWidget.itemWidget(item).title]
        self.projects_listWidget.takeItem(self.projects_listWidget.row(item))


if __name__ == "__main__":
    key = Account()  # 암호 키값 초기화
    Algorithm()      # 알고리즘 리스트 초기화
    RadarComponent()  # 레이더 컴포넌트 딕셔너리 초기화
    data = load_data()
    radars = data[0]        # 저장된 레이더들 불러오기
    projects = data[1]      # 저장된 프로젝트들 불러오기

    app = QApplication(sys.argv)
    myWindow = MainWindow(radars, projects)
    myWindow.show()
    app.exec_()

    write_data(myWindow.rds, myWindow.pjs)
