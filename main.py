import sys
import time
from pandas import DataFrame
from PyQt5 import uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from btproject import *
from btalgorithm import *

main_ui = uic.loadUiType("main.ui")[0]


class AddAlgInProject(QDialog):
    class AlgInProject(QWidget):
        def __init__(self, alg: Algorithm):
            super(AddAlgInProject.AlgInProject, self).__init__()
            ui = 'algorithms_in_project.ui'
            uic.loadUi(ui, self)

            self.alg = alg

            self.algorithm_title_label.setText(self.alg.title)

    def __init__(self, parent):
        super(AddAlgInProject, self).__init__(parent)
        ui = 'add_algorithms_in_project.ui'
        uic.loadUi(ui, self)
        self.algorithm_comboBox.addItems(MainWindow.algs.keys())

        self.algorithms = []

        self.add_alg_pushButton.clicked.connect(self.add_algorithm)
        self.del_alg_pushButton.clicked.connect(self.del_algorithm)
        self.accept_pushButton.clicked.connect(self.accept)
        self.reject_pushButton.clicked.connect(self.reject)

        self.show()

    @pyqtSlot()
    def add_algorithm(self):
        item = QListWidgetItem(self.algorithm_listWidget)
        self.algorithms.append(MainWindow.algs[self.algorithm_comboBox.currentText()])
        widget = AddAlgInProject.AlgInProject(self.algorithms[-1])
        item.setSizeHint(QSize(0, 50))
        self.algorithm_listWidget.setItemWidget(item, widget)
        self.algorithm_listWidget.addItem(item)

    @pyqtSlot()
    def del_algorithm(self):
        item = self.algorithm_listWidget.currentItem()
        self.algorithms.pop(self.algorithm_listWidget.currentRow())
        self.algorithm_listWidget.takeItem(self.algorithm_listWidget.row(item))

    @pyqtSlot()
    def accept(self):
        self.accepted = True
        super(AddAlgInProject, self).accept()

    @pyqtSlot()
    def reject(self):
        self.accepted = False
        super(AddAlgInProject, self).reject()


class TradeLog(QDialog):
    def __init__(self, parent):
        super(TradeLog, self).__init__(parent)
        ui = 'trade_log.ui'
        uic.loadUi(ui, self)
        self.project_comboBox.addItems(MainWindow.pjs.keys())

        self.apply_pushButton.clicked.connect(self.sort_log)

        self.show()

    @pyqtSlot()
    def sort_log(self):
        # 로그 구분 범위에 따라 나누어서 해당 로그만 표시
        sort = self.project_comboBox.currentText()
        print(sort)
        if sort == 'All':
            print(len(Project.order_log))
            # QTableWidget.setItem()
            self.log_tableWidget.setRowCount(len(Project.order_log))
            for i, log in enumerate(Project.order_log):
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

        self.show()

    # 보유코인-보유수량-매수평균가-매수금액-평가금액-평가손익
    def initialize_balance(self):
        test_acc = self.project.test_account

        data = [['KRW', '-', '-', '-', str(test_acc.balance), '-']]
        for currency in test_acc.wallet.keys():
            amount = test_acc.wallet[currency]['balance']
            buy_price = test_acc.wallet[currency]['avg_buy_price']
            now_price = pu.get_current_price(currency)
            data.append([
                currency
                , str(round(amount, 8))
                , str(buy_price)
                , str(int(amount*buy_price))
                , str(int(amount*now_price))
                , str(round((amount*now_price-amount*buy_price)/(amount*buy_price)*100, 2))
            ])

        print(data)
        self.balance_tableWidget.setRowCount(len(data))
        for i, d in enumerate(data):
            for j, d2 in enumerate(d):
                item = QTableWidgetItem(d2)
                self.balance_tableWidget.setItem(i, j, item)


class MainWindow(QMainWindow, main_ui):
    algs = {}
    pjs = {}

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

    class ProjectInMain(QWidget):
        def __init__(self, pj: Project):
            super(MainWindow.ProjectInMain, self).__init__()
            ui = 'projects_in_main.ui'
            uic.loadUi(ui, self)

            self.project = pj
            self.title = pj.title

            self.project_title_label.setText(self.title)
            t = ''
            for i in pj.algorithms:
                t = t + i.title + ', '
            t = t.rstrip(', ')
            self.components_label.setText(t)

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
            print(self.project.status)

        @pyqtSlot()
        def run_backtest(self):
            # 추후 백테스팅 하는 알고리즘 만들어 추가하기
            pass

        @pyqtSlot()
        def show_detail(self):
            # 추후 세부사항 표시해주는 위젯 띄우기
            window = ProjectDetail(self, self.project)
            window.exec_()

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowIcon(QIcon("stock_icon.png"))

        self.log_pushButton.clicked.connect(self.trade_log)
        self.add_project_pushButton.clicked.connect(self.add_project)
        self.delete_project_pushButton.clicked.connect(self.delete_project)

        # QListWidget에 Item 추가하는 법
        item = QListWidgetItem(self.algorithm_listWidget)
        widget = MainWindow.AlgInMain(ObserveSoaringCoinAlg)
        item.setSizeHint(QSize(0, 60))
        self.algorithm_listWidget.setItemWidget(item, widget)
        self.algorithm_listWidget.addItem(item)

        MainWindow.algs[widget.title] = ObserveSoaringCoinAlg()

    @pyqtSlot()
    def add_project(self):
        window = AddAlgInProject(self)
        window.exec_()
        if window.accepted:
            # 프로젝트 생성해야 함
            item = QListWidgetItem(self.projects_listWidget)
            # items = MainWindow.ProjectLWI(item)
            pj = Project('first_pj', 'First_Project', window.algorithms)
            widget = MainWindow.ProjectInMain(pj)
            item.setSizeHint(QSize(0, 70))

            self.projects_listWidget.setItemWidget(item, widget)
            self.projects_listWidget.addItem(item)

            # 같은 title의 프로젝트 두개 이상 생성하면 에러뜬다
            MainWindow.pjs[widget.title] = pj

    @pyqtSlot()
    def trade_log(self):
        window = TradeLog(self)
        # 로그 창 관련 슬롯 만들어야 함

    @pyqtSlot()
    def delete_project(self):
        item = self.projects_listWidget.currentItem()
        del MainWindow.pjs[self.projects_listWidget.itemWidget(item).title]
        self.projects_listWidget.takeItem(self.projects_listWidget.row(item))


if __name__ == "__main__":
    key = Account()  # 암호 키값 초기화
    project = Project('test', 'test', {'oad': ObserveSoaringCoinAlg()})


#    project.project_release()
#    time.sleep(5)
#    project.project_off()

    app = QApplication(sys.argv)
    myWindow = MainWindow()
    myWindow.show()
    app.exec_()