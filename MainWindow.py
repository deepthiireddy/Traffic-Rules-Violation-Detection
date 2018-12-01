import cv2
import qdarkstyle
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QMainWindow, QStatusBar, QListWidget, QAction, qApp, QMenu
from PyQt5.uic import loadUi

from Database import Database
from TrafficProcessor import TrafficProcessor
from ViolationItem import ViolationItem
from add_windows.AddCamera import AddCamera
from add_windows.AddCar import AddCar
from add_windows.AddRule import AddRule
from add_windows.AddViolation import AddViolation


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("./UI/MainWindow.ui", self)

        self.live_preview.setScaledContents(True)
        from PyQt5.QtWidgets import QSizePolicy
        self.live_preview.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)

        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Welcome")

        self.search_button.clicked.connect(self.search)
        self.clear_button.clicked.connect(self.clear)
        self.refresh_button.clicked.connect(self.refresh)

        self.database = Database.getInstance()

        cam_groups = self.database.getCamGroupList()
        self.camera_group.clear()
        self.camera_group.addItems(name for name in cam_groups)
        self.camera_group.setCurrentIndex(0)
        self.camera_group.currentIndexChanged.connect(self.camGroupChanged)

        cams = self.database.getCamList(self.camera_group.currentText())
        self.cam_selector.clear()
        self.cam_selector.addItems(name for name, location, feed in cams)
        self.cam_selector.setCurrentIndex(0)
        self.cam_selector.currentIndexChanged.connect(self.camChanged)

        self.processor = TrafficProcessor(self.cam_selector.currentText())

        self.log_tabwidget.clear()
        self.violation_list = QListWidget(self)
        self.search_result = QListWidget(self)
        self.log_tabwidget.addTab(self.violation_list, "Violations")
        self.log_tabwidget.addTab(self.search_result, "Search Result")


        self.feed = None
        self.vs = None
        self.updateCamInfo()

        self.updateLog()

        self.initMenu()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_image)
        self.timer.start(50)

    def initMenu(self):
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&File')

        # File menu

        ## add record manually
        addRec = QMenu("Add Record", self)

        act = QAction('Add Car', self)
        act.setStatusTip('Add Car Manually')
        act.triggered.connect(self.addCar)
        addRec.addAction(act)

        act = QAction('Add Rule', self)
        act.setStatusTip('Add Rule Manually')
        act.triggered.connect(self.addRule)
        addRec.addAction(act)

        act = QAction('Add Violation', self)
        act.setStatusTip('Add Violation Manually')
        act.triggered.connect(self.addViolation)
        addRec.addAction(act)

        act = QAction('Add Camera', self)
        act.setStatusTip('Add Camera Manually')
        act.triggered.connect(self.addCamera)
        addRec.addAction(act)

        fileMenu.addMenu(addRec)

        # check archive record ( Create window and add button to restore them)
        act = QAction('&Archives', self)
        act.setStatusTip('Show Archived Records')
        act.triggered.connect(self.showArch)
        fileMenu.addAction(act)


        settingsMenu = menubar.addMenu('&Settings')
        themeMenu = QMenu("Themes", self)
        settingsMenu.addMenu(themeMenu)

        act = QAction('Dark', self)
        act.setStatusTip('Dark Theme')
        act.triggered.connect(lambda: qApp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()))
        themeMenu.addAction(act)

        act = QAction('White', self)
        act.setStatusTip('White Theme')
        act.triggered.connect(lambda: qApp.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()))
        themeMenu.addAction(act)

        ## Add Exit
        fileMenu.addSeparator()
        act = QAction('&Exit', self)
        act.setShortcut('Ctrl+Q')
        act.setStatusTip('Exit application')
        act.triggered.connect(qApp.quit)
        fileMenu.addAction(act)


    def addCamera(self):
        addWin = AddCamera(parent=self)
        addWin.show()

    def addCar(self):
        addWin = AddCar(parent=self)
        addWin.show()

    def addViolation(self):
        pass
        addWin = AddViolation(parent=self)
        addWin.show()

    def addRule(self):
        addWin = AddRule(parent=self)
        addWin.show()

    def showArch(self):
        print("Showing archinve")

    def updateSearch(self):
        pass


    def update_image(self):
        _, frame = self.vs.read()


        packet = self.processor.cross_violation(frame)
        cropped_car_images = packet['list_of_cars']  # list of cropped images of violated cars
        print(cropped_car_images)



        qimg = self.toQImage(packet['frame'])
        self.live_preview.setPixmap(QPixmap.fromImage(qimg))

    def updateCamInfo(self):
        count, location, self.feed = self.database.getCamDetails(self.cam_selector.currentText())
        self.feed = 'videos/' + self.feed
        self.processor = TrafficProcessor(self.cam_selector.currentText())
        self.vs = cv2.VideoCapture(self.feed)
        # print(count, location, self.feed)
        self.cam_id.setText(self.cam_selector.currentText())
        self.address.setText(location)
        self.total_records.setText(str(count))

    def updateLog(self):
        self.violation_list.clear()
        rows = self.database.getUnclearedViolationsFromCam(str(self.cam_selector.currentText()))
        for row in rows:
            # print(row)
            listWidget = ViolationItem()
            listWidget.setData(row)
            listWidgetItem = QtWidgets.QListWidgetItem(self.violation_list)
            listWidgetItem.setSizeHint(listWidget.sizeHint())
            self.violation_list.addItem(listWidgetItem)
            self.violation_list.setItemWidget(listWidgetItem, listWidget)

    @QtCore.pyqtSlot()
    def refresh(self):
        self.updateCamInfo()
        self.updateLog()


    @QtCore.pyqtSlot()
    def search(self):
        from SearchWindow import SearchWindow
        searchWindow = SearchWindow(self.search_result, parent=self)
        searchWindow.show()

    @QtCore.pyqtSlot()
    def clear(self):
        qm = QtWidgets.QMessageBox
        prompt = qm.question(self, '', "Are you sure to reset all the values?", qm.Yes | qm.No)
        if prompt == qm.Yes:
            self.database.clearCamLog()
            self.updateLog()
        else:
            pass

    def toQImage(self, raw_img):
        from numpy import copy
        img = copy(raw_img)
        qformat = QImage.Format_Indexed8
        if len(img.shape) == 3:
            if img.shape[2] == 4:
                qformat = QImage.Format_RGBA8888
            else:
                qformat = QImage.Format_RGB888

        outImg = QImage(img.tobytes(), img.shape[1], img.shape[0], img.strides[0], qformat)
        outImg = outImg.rgbSwapped()
        return outImg

    @QtCore.pyqtSlot()
    def camChanged(self):
        self.updateCamInfo()
        self.updateLog()

    @QtCore.pyqtSlot()
    def camGroupChanged(self):
        cams = self.database.getCamList(self.camera_group.currentText())
        self.cam_selector.clear()
        self.cam_selector.addItems(name for name, location in cams)
        self.cam_selector.setCurrentIndex(0)
        # self.cam_selector.currentIndexChanged.connect(self.camChanged)
