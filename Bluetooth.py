import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import QThread, pyqtSignal
from bluetooth import *  # PyBluez

class Bluetooth(QThread):
    result_signal = pyqtSignal(object)
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(Bluetooth, cls).__new__(cls)
        return cls._instance

    def __init__(self, mac_address="98:DA:60:0A:F8:2B", port=1):
        # 부모 클래스 먼저 초기화
        super().__init__()
        
        # 이미 초기화되었으면 return
        if getattr(self, "_initialized", False):
            return

        self.mac_address = mac_address
        self.port = port
        self._running = True
        self.sock = None
        self.send_queue = []
        self._connected = False
        self._initialized = True
        
    def run(self):
        while self._running:
            try:
                print("\n\n\n")
                print("bluetooth init")
                print("\n\n\n")
                self.sock = BluetoothSocket(RFCOMM)
                self.sock.connect((self.mac_address, self.port))
                print("블루투스 연결 성공")
                self._connected = True
                time.sleep(1)
                break
            except BluetoothError as e:
                print(f"블루투스 연결 대기 중... {e}")
                time.sleep(1)

        try:
            while self._running:
                self.receive_message()
                self.send_message()
                time.sleep(0.01)
        except Exception as e:
            print(f'에러 발생: {e}')
        finally:
            if self.sock:
                self.sock.close()
            print('블루투스 연결 종료')

    def receive_message(self):
        try:
            self.sock.settimeout(0.1)
            data = self.sock.recv(1024)
            if data:
                message = data.decode().strip()
                print(message)
                self.result_signal.emit(message)
                self.handle_received_message(message)
        except (BluetoothError, OSError):
            pass

    def send_message(self):
        if self.send_queue:
            message = self.send_queue.pop(0)
            try:
                self.sock.send((message + '\n').encode('utf-8'))
            except BluetoothError as e:
                print(f"전송 오류: {e}")

    def send_data(self, message):
        self.send_queue.append(message)

    def stop(self):
        self._running = False
        self.wait()

    def handle_received_message(self, message):
        pass

# ✅ 모듈 전역에서 하나만 생성
_bluetooth_instance = Bluetooth()

# ✅ getter 함수로 안전하게 가져다 씀
def get_bluetooth():
    return _bluetooth_instance
