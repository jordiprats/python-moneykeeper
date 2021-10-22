from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5 import QtCore

from PyQt5 import QtWidgets
from PyQt5.QtCore import QSize
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QGridLayout, QWidget, QCheckBox, QSystemTrayIcon, \
    QSpacerItem, QSizePolicy, QMenu, QAction, QStyle, qApp

from datetime import datetime, timedelta

import requests
import time
import json
import os

app = None
jira_url = ""
jira_username = ""
jira_password = ""
jira_project = ""
debug = True
window_mode = False
main_window = None
quit_refresh = False

check_unattended_incidents = True
check_assigned_incidents = True

class jiraWorker(QRunnable):

    def setMainWindow(self, MainWindow):
        self.MainWindow = MainWindow
        self.refresh=False

    def setRefresh(self, refresh):
        self.refresh=refresh

    @pyqtSlot()
    def run(self):
        global debug, quit_refresh
        self.refresh=False

        refresh_interval = 60

        previous_status = ""

        if debug:
            print("running fetch_incident_count")

        previous_unattended_incident_count=0
        previous_user_assigned_incident_count=0
        while True:
            if quit_refresh:
                return
            try:
                settings = QtCore.QSettings("__settings.ini", QSettings.IniFormat)

                settings.sync()
                if debug:
                    print("checking incidents...")

                try:
                    refresh_interval = int(settings.value("refresh_interval"))
                except Exception as e:
                    if debug:
                        print("jiraWorker::run - refresh_internal: "+str(e))
                    refresh_interval = 60

                try:
                    rest_endpoint = settings.value("rest_endpoint")
                    if not rest_endpoint:
                        rest_endpoint = '127.0.0.1:5002'
                except:
                    rest_endpoint = '127.0.0.1:5002'


                #
                # get data
                #

                response = requests.get('http://'+rest_endpoint+'/calefaccio')

                print(str(response.text))

                calefaccio_data = json.loads(response.text)

                print(str(calefaccio_data['is_active']))

                if calefaccio_data['is_active'] == "True":
                    print('activa')

                #
                # analyze data
                #

                scriptDir = os.path.dirname(os.path.realpath(__file__))
                # self.setWindowIcon(QIcon(scriptDir + os.path.sep + 'moneybag.png'))


                print(scriptDir + os.path.sep + 'moneyface.png')

                if calefaccio_data['is_active'] != "True":
                    self.MainWindow.tray_icon.setIcon(self.MainWindow.style().standardIcon(QStyle.SP_DialogApplyButton))
                    # self.MainWindow.tray_icon.setIcon(self.MainWindow.setWindowIcon(QIcon(scriptDir + os.path.sep + 'moneyface.png')))
                else:
                    self.MainWindow.tray_icon.setIcon(self.MainWindow.style().standardIcon(QStyle.SP_MessageBoxWarning))
                    # self.MainWindow.tray_icon.setIcon(self.MainWindow.setWindowIcon(QIcon(scriptDir + os.path.sep + 'moneybag.png')))

                if previous_status != calefaccio_data['is_active']:
                    if not QSystemTrayIcon.isSystemTrayAvailable():
                        import notify2

                        notify2.init("moneykeeper Desktop")
                        n = notify2.Notification("Canvi d'estat de la calefacció")
                        n.set_urgency(notify2.URGENCY_NORMAL)
                        n.show()
                    else:
                        print('no isSystemTrayAvailable')
                        if calefaccio_data['is_active'] == "True":
                            self.MainWindow.tray_icon.showMessage(
                                "Canvi d'estat de la calefacció",
                                "Encesa",
                                QSystemTrayIcon.Warning,
                                msecs=10000
                            )
                    previous_status = calefaccio_data['is_active']

                self.MainWindow.tray_icon.show()
                if debug:
                    print("Sleeping "+str(refresh_interval)+" seconds")
                for i in range(refresh_interval):
                    if self.refresh:
                        if debug:
                            print("aborting sleep at "+str(i)+" seconds")
                        self.refresh=False
                        break
                    else:
                        time.sleep(1)
            except Exception as e:
                print("Exception jiraWorker::run: "+str(e)+" ==> Sleeping "+str(refresh_interval)+" seconds")
                for i in range(refresh_interval):
                    if self.refresh:
                        if debug:
                            print("aborting sleep at "+str(i)+" seconds")
                        self.refresh=False
                        break
                    else:
                        time.sleep(1)

class MainWindow(QMainWindow):
    check_box = None
    tray_icon = None

    def tear_down(self):
        global app, quit_refresh
        self.close()
        quit_refresh = True
        sys.exit(app.quit())

    def force_refresh(self):
        self.jira_worker.setRefresh(True)

    # Override the class constructor
    def __init__(self):
        global debug

        self.settings = QtCore.QSettings("__settings.ini", QSettings.IniFormat)


        try:
            rest_endpoint_value = self.settings.value("rest_endpoint")
            if not rest_endpoint_value:
                rest_endpoint_value = '127.0.0.1:5002'
                self.settings.setValue("rest_endpoint", '127.0.0.1:5002')
        except:
            rest_endpoint_value = '127.0.0.1:5002'

        try:
            refresh_interval_str = str(int(self.settings.value("refresh_interval")))
            if not refresh_interval_str:
                refresh_interval_str = '60'
                self.settings.setValue("refresh_interval", '60')
        except:
            refresh_interval_str = '60'

        # Be sure to call the super class method
        QMainWindow.__init__(self)
        self.setWindowIcon(self.style().standardIcon(QStyle.SP_DialogSaveButton))
        self.threadpool = QThreadPool()
        self.jira_worker = jiraWorker()
        self.jira_worker.setMainWindow(self)

        self.setMinimumSize(QSize(480, 80))             # Set sizes
        self.setWindowTitle("moneykeeper Desktop")  # Set a title
        central_widget = QWidget(self)                  # Create a central widget
        self.setCentralWidget(central_widget)           # Set the central widget

        layout = QtWidgets.QVBoxLayout(self)
        central_widget.setLayout(layout)   # Set the layout into the central widget

        window_title = QLabel("moneykeeper Desktop settings", self)
        window_title.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        window_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(window_title)

        self.rest_endpoint = QtWidgets.QLineEdit(self)
        self.rest_endpoint.setText(rest_endpoint_value)
        layout.addWidget(QLabel("rest endpoint (including port):", self))
        layout.addWidget(self.rest_endpoint)

        self.check_interval = QtWidgets.QLineEdit(self)
        self.check_interval.setText(refresh_interval_str)
        layout.addWidget(QLabel("refresh interval (in seconds):", self))
        layout.addWidget(self.check_interval)

        #
        # Init QSystemTrayIcon
        #
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
        self.tray_icon.setVisible(True)

        refresh_action = QAction("Refresh", self)
        settings_action = QAction("Settings", self)
        quit_action = QAction("Exit", self)

        refresh_action.triggered.connect(self.force_refresh)
        settings_action.triggered.connect(self.show)
        quit_action.triggered.connect(self.tear_down)

        tray_menu = QMenu(parent=None)
        tray_menu.aboutToShow.connect(self.force_refresh)
        tray_menu.addAction(refresh_action)
        tray_menu.addAction(settings_action)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

        # run bg job
        self.threadpool.start(self.jira_worker)


    # Override closeEvent, to intercept the window closing event
    # The window will be closed only if there is no check mark in the check box
    def closeEvent(self, event):
        global quit_refresh

        if quit_refresh:
            return

        try:
            self.settings.setValue("rest_endpoint", self.rest_endpoint.text())
        except:
            self.settings.setValue("rest_endpoint", '127.0.0.1:5002')

        try:
            self.settings.setValue("refresh_interval", str(int(self.check_interval.text())))
        except:
            self.settings.setValue("refresh_interval", '60')

        self.settings.sync()
        event.ignore()
        self.hide()
        self.force_refresh()

if __name__ == "__main__":
    import sys

    app = QApplication(sys.argv)

    main_window = MainWindow()
    sys.exit(app.exec())
