import sys
import cv2
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QTimer, Qt

class CameraViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("USB Camera Toggle Viewer")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # 버튼 먼저 추가
        self.toggle_button = QPushButton("Toggle Camera")
        self.layout.addWidget(self.toggle_button)
        self.toggle_button.clicked.connect(self.toggle_camera)

        # QLabel 생성, 크기 제한
        self.label = QLabel("Camera Output")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setFixedSize(640, 480)  # 화면 크기 제한
        self.layout.addWidget(self.label)

        # 카메라 초기화
        self.cam_indices = [0, 2]  # C270 = 0, ABKO = 2
        self.current_index = 0
        self.cap = cv2.VideoCapture(self.cam_indices[self.current_index])
        if not self.cap.isOpened():
            print(f"Camera {self.cam_indices[self.current_index]} 열 수 없음")

        # 타이머
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    def update_frame(self):
        ret, frame = self.cap.read()
        if ret:
            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            h, w, ch = rgb_image.shape
            bytes_per_line = ch * w
            qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
            pixmap = QPixmap.fromImage(qt_image).scaled(
                self.label.width(), self.label.height(), Qt.KeepAspectRatio
            )
            self.label.setPixmap(pixmap)

    def toggle_camera(self):
        self.cap.release()
        self.current_index = 1 - self.current_index
        self.cap = cv2.VideoCapture(self.cam_indices[self.current_index])
        if not self.cap.isOpened():
            print(f"Camera {self.cam_indices[self.current_index]} 열 수 없음")

    def closeEvent(self, event):
        self.cap.release()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = CameraViewer()
    viewer.show()
    sys.exit(app.exec_())
