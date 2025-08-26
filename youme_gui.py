import mediapipe as mp
import sys
import time
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt, QEvent, QTimer, QSize
import json, os
from Bluetooth import get_bluetooth
from camera_func_test import Tracking
from Keyboard import SoftKeyboardDialog
from database import DB
from bluetooth import *
import threading
from flask_server.app import app
import os
os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = "/usr/lib/qt5/plugins/platforms"


class Youme(QMainWindow):
    def __init__(self):
        super().__init__()
        # bluetooth 쓰레드
        self.bluetooth_thread = get_bluetooth()
        self.bluetooth_thread.result_signal.connect(self.handle_bluetooth_message)  # 시그널 연결
        if not self.bluetooth_thread.isRunning():
            self.bluetooth_thread.start()
        self.bluetooth_thread.send_data("0")
        # Tracking 쓰레드
        self.tracking_thread = Tracking()
        self.tracking_thread.result_signal.connect(self.update_cam_label)  # 시그널 연결
        self.tracking_thread.fall_detect_thread.emergency_signal.connect(self.handle_emergency)

        self.wait_dialog = None
        self.is_waiting = True
        self.current_user = None
        self.emergency = False

        # DB 클래스
        self.db = DB()
        self.area = None
        self.line_edits = []
        self.InitUI()
        self.user = None

        flask_thread = threading.Thread(target= lambda: app.run(host='0.0.0.0', port=5000, debug=True, use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()

    def InitUI(self):
        self.setWindowTitle("Youme Camera")

        self.setFixedSize(800, 480)  # 예: 800x480 해상도

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.main_layout = QHBoxLayout()
        self.central_widget.setLayout(self.main_layout)

        self.cam_layout = QHBoxLayout()
        self.func_layout = QVBoxLayout()

        self.main_layout.addLayout(self.cam_layout, 7)
        self.main_layout.addLayout(self.func_layout, 3)

        # 카메라 영상 표시용 QLabel
        self.cam_label = QLabel(self)
        self.cam_label.setAlignment(Qt.AlignCenter)
        self.cam_label.setFixedSize(640, 400)

        self.cam_layout.addWidget(self.cam_label)

        self.start_btn = QPushButton("START")
        self.stop_btn = QPushButton("STOP")
        self.transfer_btn = QPushButton("Transfer")
        self.map_btn = QPushButton("MAP")
        self.edit_item = QPushButton("Edit")
        self.close_btn = QPushButton("Close")
        self.close_btn.setVisible(False)

        self.func_layout.addWidget(self.start_btn)
        self.func_layout.addWidget(self.stop_btn)
        self.func_layout.addWidget(self.transfer_btn)
        self.func_layout.addWidget(self.map_btn)
        self.func_layout.addWidget(self.edit_item)
        self.func_layout.addWidget(self.close_btn)

        self.start_btn.clicked.connect(self.start_cam)
        self.stop_btn.clicked.connect(self.stop_cam)
        self.transfer_btn.clicked.connect(self.transfer)
        self.map_btn.clicked.connect(self.map)
        self.edit_item.clicked.connect(self.edit)
        self.close_btn.clicked.connect(self.close_event)

        self.stop_btn.setEnabled(False)

        self.cam_label.mousePressEvent = self.tracking_thread.select_roi

    
    def update_cam_label(self, pixmap):
        # 카메라 영상 업데이트 (UI에서 QImage를 QLabel로 표시)
        self.cam_label.setPixmap(pixmap)
        if not self.tracking_thread.running:
            self.stop_cam()


    def start_cam(self):
        # 카메라 시작
        self.bluetooth_thread.send_data('1')
        self.tracking_thread.start()
        self.tracking_thread.result_signal.connect(self.update_cam_label)  # 시그널 연결
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
 

    def stop_cam(self):
        # 카메라 종료
        self.tracking_thread.stop()

        QTimer.singleShot(0, self.cam_label.clear)
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        time.sleep(1)
        if self.tracking_thread.emergency_state == False:
            self.bluetooth_thread.send_data('0')


    def handle_emergency(self, signal):
        self.bluetooth_thread.send_data('e')
        print("emergency!")

        self.db.record_emergency(self.user)

        self.tracking_thread.stop()
        QTimer.singleShot(0, self.cam_label.clear)
        print("e s")
        time.sleep(1)
        print("e f")
        self.start_btn.setVisible(False)
        self.stop_btn.setVisible(False)
        self.transfer_btn.setVisible(False)
        self.map_btn.setVisible(False)
        self.edit_item.setVisible(False)
        self.close_btn.setVisible(True)

        self.cam_label.setText("EMERENCY!")


    def transfer(self):
        self.bluetooth_thread.send_data('2')
        self.transfer_dialog = QDialog(self)
        self.transfer_dialog.setWindowTitle("Transfer Dialog")
        self.transfer_dialog.setFixedSize(800,480)

        transfer_layout = QHBoxLayout()

        # step
        step_layout = QVBoxLayout()
        step_label = QLabel("STEP MOTOR")
        step_label.setAlignment(Qt.AlignCenter)
        step_label.setMaximumHeight(30)
        step_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_step_up = QPushButton("▲")
        btn_step_up.setFixedSize(QSize(80, 80))  # ���簢��
        btn_step_stop = QPushButton("▆")
        btn_step_stop.setFixedSize(QSize(80, 80))
        btn_step_down = QPushButton("▼")
        btn_step_down.setFixedSize(QSize(80, 80))
        step_layout.addWidget(step_label)
        step_layout.addWidget(btn_step_up)
        step_layout.addWidget(btn_step_stop)
        step_layout.addWidget(btn_step_down)

        btn_step_up.clicked.connect(lambda: self.bluetooth_thread.send_data('f'))
        btn_step_stop.clicked.connect(lambda: self.bluetooth_thread.send_data('s'))
        btn_step_down.clicked.connect(lambda: self.bluetooth_thread.send_data('b'))

        # step
        linear_layout = QVBoxLayout()
        linear_label = QLabel("LINEAR ACTUATOR")
        linear_label.setAlignment(Qt.AlignCenter)
        linear_label.setMaximumHeight(30)
        linear_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_linear_up = QPushButton("▲")
        btn_linear_up.setFixedSize(QSize(80, 80))
        btn_linear_stop = QPushButton("▆")
        btn_linear_stop.setFixedSize(QSize(80, 80))
        btn_linear_down = QPushButton("▼")
        btn_linear_down.setFixedSize(QSize(80, 80))
        linear_layout.addWidget(linear_label)
        linear_layout.addWidget(btn_linear_up)
        linear_layout.addWidget(btn_linear_stop)
        linear_layout.addWidget(btn_linear_down)

        btn_linear_up.clicked.connect(lambda: self.bluetooth_thread.send_data('u'))
        btn_linear_stop.clicked.connect(lambda: self.bluetooth_thread.send_data('s'))
        btn_linear_down.clicked.connect(lambda: self.bluetooth_thread.send_data('d'))

        # dc
        dc_layout = QVBoxLayout()
        dc_label = QLabel("DC MOTOR")
        dc_label.setAlignment(Qt.AlignCenter)
        dc_label.setMaximumHeight(30)
        dc_label.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        btn_dc_up = QPushButton("▲")
        btn_dc_up.setFixedSize(QSize(80, 80))
        btn_dc_stop = QPushButton("▆")
        btn_dc_stop.setFixedSize(QSize(80, 80))
        btn_dc_down = QPushButton("▼")
        btn_dc_down.setFixedSize(QSize(80, 80))
        dc_layout.addWidget(dc_label)
        dc_layout.addWidget(btn_dc_up)
        dc_layout.addWidget(btn_dc_stop)
        dc_layout.addWidget(btn_dc_down)

        btn_dc_up.clicked.connect(lambda: self.bluetooth_thread.send_data('g'))
        btn_dc_stop.clicked.connect(lambda: self.bluetooth_thread.send_data('s'))
        btn_dc_down.clicked.connect(lambda: self.bluetooth_thread.send_data('r'))


        # ���̾ƿ� ��ġ��
        transfer_layout.addLayout(step_layout)
        transfer_layout.addLayout(linear_layout)
        transfer_layout.addLayout(dc_layout)

        close_btn = QPushButton("close")
        close_btn.setFixedSize(50,30)
        transfer_layout.addWidget(close_btn)
        close_btn.clicked.connect(self.transfer_dialog.close)
        close_btn.clicked.connect(lambda: self.bluetooth_thread.send_data("0"))

        self.transfer_dialog.setLayout(transfer_layout)
        self.transfer_dialog.show()


    def map(self):
        self.map_dialog = QDialog(self)
        self.map_dialog.setWindowTitle("Map Dialog")
        self.map_dialog.setFixedSize(800,480)

        map_layout = QVBoxLayout()
        self.line_edits = []

        # 검색창
        search_input = QLineEdit()
        search_input.installEventFilter(self)
        self.search_input = search_input  # 참조 저장
        search_input.setPlaceholderText("품목을 입력하세요...")
        self.line_edits.append(search_input)

        # 검색 버튼
        search_button = QPushButton("검색")
        search_button.clicked.connect(self.select_item)
        # 닫기 버튼
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.map_dialog.close)

        # 레이아웃 구성
        youme_map = QLabel()
        youme_map.mousePressEvent = self.select_location
        youme_map.setFixedSize(778, 360)

        pixmap = QPixmap('/home/jsh/youme/imgs/map.png')
        #pixmap = QPixmap('C:\youme\youme\src\kimgunhee\imgs\map.png')
        youme_map.setPixmap(pixmap)

        map_layout.addWidget(youme_map)

        map_layout.addWidget(search_input)
        map_layout.addWidget(search_button)
        map_layout.addWidget(close_btn)

        self.map_dialog.setLayout(map_layout)
        self.map_dialog.exec_()
        

    def select_item(self):
        name = self.search_input.text().strip()
        print(name)
        locations = self.db.search_item(name)
        locations_text = ', '.join(locations)+'에 있습니다.' if locations else "등록된 구역이 없습니다."

        QMessageBox.information(self.map_dialog, f"{name}", f"{locations_text}")
        

    def select_location(self, event):
        x, y = event.x(), event.y()

        if x < 389 and y < 180:
            self.area = "A"
        elif x < 389 and y >= 180:
            self.area = "B"
        elif x >= 389 and y < 180:
            self.area = "C"
        else:
            self.area = "D"

        items = self.db.search_location(self.area)
        print(items)
        item_text = ', '.join(items) if items else "등록된 항목이 없습니다."

        QMessageBox.information(self, f"{self.area} 구역", f"{self.area} 구역에 있는 항목:\n{item_text}")


    def eventFilter(self, obj, event):
        if isinstance(obj, QLineEdit) and event.type() == QEvent.MouseButtonPress:
            if obj in getattr(self, "line_edits", []):
                keyboard = SoftKeyboardDialog(obj)
                keyboard.exec_()
                return True
        return super().eventFilter(obj, event)
    

    def edit(self):
        self.edit_dialog = QDialog()
        self.edit_dialog.setWindowTitle("Edit Dialog")
        self.edit_dialog.setFixedSize(800, 480)

        # 전체 레이아웃
        main_layout = QVBoxLayout()
        self.edit_dialog.setLayout(main_layout)

        # === 1. 버튼을 포함한 상단 고정 레이아웃 ===
        button_layout = QHBoxLayout()
        add_item_btn = QPushButton("ADD Item")
        remove_item_btn = QPushButton("REMOVE Item")
        button_layout.addWidget(add_item_btn)
        button_layout.addWidget(remove_item_btn)

        # 버튼을 감싼 위젯 (고정)
        button_widget = QWidget()
        button_widget.setLayout(button_layout)
        main_layout.addWidget(button_widget)

        # === 2. 아래에 동적으로 바뀌는 레이아웃을 위한 공간 ===
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)

        dynamic_widget = QWidget()
        self.dynamic_layout = QVBoxLayout(dynamic_widget)
        dynamic_widget.setLayout(self.dynamic_layout)

        scroll_area.setWidget(dynamic_widget)
        main_layout.addWidget(scroll_area)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.edit_dialog.close)
        main_layout.addWidget(close_btn)

        # === 동적 위젯 클리어 함수 ===
        def clear_dynamic_layout():
            while self.dynamic_layout.count():
                child = self.dynamic_layout.takeAt(0)
                if child.widget():
                    child.widget().deleteLater()


        # === ADD ITEM ===
        def show_add_fields():
            clear_dynamic_layout()
            self.line_edits = []

            area_select = QComboBox()
            # DB에서 location 값을 가져옴
            locations = self.db.search_location('*')  # search_location 메서드에서 모든 location을 가져옴
            area_select.addItems(['select location'] + locations)  # 기본값 'select location' 추가 후 locations 리스트 결합
            self.dynamic_layout.addWidget(area_select)

            # 검색창
            item_input = QLineEdit()
            item_input.installEventFilter(self)
            self.item_input = item_input  # 참조 저장
            item_input.setPlaceholderText("추가할 품목명을 입력하세요")
            self.line_edits.append(item_input)
            self.dynamic_layout.addWidget(item_input)

            confirm_btn = QPushButton("추가하기")
            self.dynamic_layout.addWidget(confirm_btn)

            def on_confirm():
                name = item_input.text().strip()
                area = area_select.currentText()
                if name and area!='select location':
                    self.add_item(name, area)

            confirm_btn.clicked.connect(on_confirm)

        # === REMOVE ITEM ===
        def show_remove_message():
            clear_dynamic_layout()
            self.line_edits = []

            # 검색창
            item_remove = QLineEdit()
            item_remove.installEventFilter(self)
            self.item_remove = item_remove  # 참조 저장
            item_remove.setPlaceholderText("삭제할 품목명을 입력하세요")
            self.line_edits.append(item_remove)
            self.dynamic_layout.addWidget(item_remove)

            confirm_btn = QPushButton("삭제하기")
            self.dynamic_layout.addWidget(confirm_btn)

            def on_remove():
                name = item_remove.text().strip()
                if name:
                    self.remove_item(name)

            confirm_btn.clicked.connect(on_remove)

        # === 버튼 연결 ===
        add_item_btn.clicked.connect(show_add_fields)
        remove_item_btn.clicked.connect(show_remove_message)

        self.edit_dialog.exec_()


    def add_item(self, name, area):
        try:
            self.db.add_item(area, name)
            QMessageBox.information(self.edit_dialog, "아이템 추가 결과", f"{area}에 {name}이 추가되었습니다.")
        except:
            QMessageBox.warning(self.edit_dialog, "아이템 추가 결과", "실패하였습니다.")


    def remove_item(self, name):
        try:
            flg = self.db.remove_item(name)
            if flg==2:
                QMessageBox.information(self.edit_dialog, "아이템 삭제 결과", f"{name}이 한 개 삭제되었습니다.")
            elif flg==1:
                QMessageBox.information(self.edit_dialog, "아이템 삭제 결과", f"{name}이 삭제되었습니다.")
            else:
                QMessageBox.information(self.edit_dialog, "아이템 삭제 결과", f"{name}이 없습니다.")
        except:
            QMessageBox.information(self.edit_dialog, "아이템 삭제 결과", "실패하였습니다.")


    def handle_bluetooth_message(self, data):
        self.user = self.db.search_by_id(data)
        if not self.user:
            if self.wait_dialog.isVisible():
                QMessageBox.warning(self.wait_dialog, "경고","등록되지않은 카드입니다.")
            return

        if self.is_waiting:
            self.current_user = self.user
            self.db.log_usage(self.user)
            if self.wait_dialog.isVisible():
                self.wait_dialog.accept()  
            self.show()                 
            self.is_waiting = False

        else:
            if self.user == self.current_user:
                self.db.log_usage(self.user)
                self.hide()
                self.wait_dialog = WaitForCardDialog()
                self.wait_dialog.show()
                self.is_waiting = True


    def show_wait_dialog(self):
        if self.wait_dialog and self.wait_dialog.isVisible():
            return
        self.wait_dialog = WaitForCardDialog()
        self.wait_dialog.exec_()

    def close_event(self):
        self.bluetooth_thread.send_data("a")
        time.sleep(1)
        self.close()
        

class WaitForCardDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("카드 인식 대기")
        self.setFixedSize(800, 480)
        layout = QVBoxLayout()
        label = QLabel("카드를 인식시켜주세요.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)


 
if __name__ == '__main__':
    gui = QApplication(sys.argv)
    youme = Youme()   
    youme.show()  
    youme.show_wait_dialog()  
    sys.exit(gui.exec_())  
