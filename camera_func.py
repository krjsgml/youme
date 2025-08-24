import mediapipe as mp
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal
import cv2
from ultralytics import YOLO
from Bluetooth import get_bluetooth

class Tracking(QThread):
    result_signal = pyqtSignal(QPixmap)  # QPixmap을 시그널로 전송

    def __init__(self):
        super().__init__()
        self.bluetooth_thread = get_bluetooth()
        self.fall_detect_thread = Falldetect()
        self.helmet_detect_thread = HelmetDetect()

        self.cam_flg = 0
        self.running = False
        self.frame = None
        self.tracking = False
        self.detects = []

        self.cam_indices=[0, 2]
        self.current_index = 0

        self.cascade = cv2.CascadeClassifier("/home/jsh/youme/haarcascade/haarcascade_frontalface_default.xml")
        self.tracker = cv2.TrackerKCF_create()
        self.stop_track = 0
        self.prev_pos = None

        self.helmet_frame_count = 0

 
    def run(self):
        self.running = True
        self.cap = cv2.VideoCapture(self.cam_indices[self.current_index])
        self.cap.set(3, 640)  # 카메라 영상의 가로 길이를 640으로 설정
        self.cap.set(4, 400)  # 카메라 영상의 세로 길이를 400으로 설정
        while self.running:
            ret, self.frame = self.cap.read()
            if not ret or self.frame is None:
                continue  # 프레임 못받았으면 다음 루프

            fall_detect_frame = self.frame.copy()
            helmet_detect_frame = self.frame.copy()
            self.frame = cv2.flip(self.frame, 1)

            if ret:
                if self.frame is not None:
                    self.handle_tracking_result(self.frame)
                    
                    if not self.helmet_detect_thread.isRunning():
                        self.helmet_detect_thread.start()
                    self.helmet_frame_count += 1
                    if self.helmet_frame_count % 5 == 0:
                        self.helmet_detect_thread.update_frame(helmet_detect_frame)

                    # 헬멧인식
                    if self.helmet_detect_thread.helmet_detected == True:
                        # 얼굴 인식 및 트래킹 로직
                        if not self.tracking:
                            gray = cv2.cvtColor(self.frame, cv2.COLOR_BGR2GRAY)
                            self.detects = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
    
                            for (x, y, w, h) in self.detects:
                                cv2.rectangle(self.frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            cv2.putText(self.frame, "Click a box to track", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            
                        else:
                            success, box = self.tracker.update(self.frame)

                            
                                
                            if success:   
                                x, y, w, h = [int(v) for v in box]
                                cv2.rectangle(self.frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                cv2.putText(self.frame, "Tracking...", (x, y - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                                face_center = x+w//2
                                frame_center = self.frame.shape[1]//2

                                left_bound = self.frame.shape[1] // 3
                                right_bound = 2*self.frame.shape[1] // 3

                                if face_center < left_bound:
                                    pos = 'l'
                                elif face_center > right_bound:
                                    pos = 'r'
                                else:
                                    pos = 'c'

                                if pos!=self.prev_pos:
                                    self.bluetooth_thread.send_data(pos)
                                    self.prev_pos = pos
                                
                            else:
                                cv2.putText(self.frame, "Tracking failure", (10, 60),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                self.bluetooth_thread.send_data('s')
                                self.stop_track += 1
                                if self.stop_track ==50:
                                    print("dc motor stop")
                                    self.cap.release()
                                    self.current_index = 1
                                    self.cap = cv2.VideoCapture(self.cam_indices[self.current_index])
                                    if not self.fall_detect_thread.isRunning():
                                        self.fall_detect_thread.start()
                                    self.fall_detect_thread.update_frame(fall_detect_frame)

                    else:
                        self.bluetooth_thread.send_data('s')
                        self.tracking = False
                        self.tracker = cv2.TrackerKCF_create()
                        self.detects = [] 
                    # 프레임을 QPixmap으로 변환하여 시그널 발행
                    self.handle_tracking_result(self.frame)

            #self.msleep(10)


    def stop(self):
        self.running = False
        self.tracking = False
        self.prev_pos = None
        self.fall_detect_thread.stop()
        self.cap.release()
        self.current_index=0
        self.stop_track = 0

        self.tracker = cv2.TrackerKCF_create()
        self.detects = []
        self.wait()


    def closeEvent(self, event):
        self.current_index=0
        self.stop()
        # 종료 시 카메라 해제
        self.cap.release()
        event.accept()


    def handle_tracking_result(self, frame):
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.result_signal.emit(pixmap)  # 여기서 시그널로 메인 UI에 전달


    def set_roi(self, roi):
        if self.frame is not None:
            self.tracker = cv2.TrackerKCF_create()
            self.tracker.init(self.frame, roi)

        self.tracking = True


    def select_roi(self, event):
        if not self.running:
            print('작동 x')

        else:
            x, y = event.x(), event.y()
            # 이미 트래킹 중이면 무시
            if self.tracking:
                print("현재 추적 중")
                return
    
            # 트래킹 가능한 얼굴 영역 리스트 가져오기
            detects = self.detects
    
            for (x1, y1, w, h) in detects:
                if x1 < x < x1 + w and y1 < y < y1 + h:
                    roi = (x1, y1, w, h)
                    self.set_roi(roi)
                    if not self.fall_detect_thread.isRunning():
                        self.fall_detect_thread.start()
                    print("Tracking 시작:", roi)
                    break


class Falldetect(QThread):
    emergency_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.pose = mp.solutions.pose.Pose()
        self.frame = None
        self.emergency = 0


    def run(self):
        self.running = True
        while self.running:
            if self.frame is not None:
                rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb)
                self.handle_fall_result(results)
            self.msleep(1000)


    def stop(self):
        self.running = False
        self.wait()


    def update_frame(self, frame):
        self.frame = frame


    def handle_fall_result(self, results):
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark

            #left_wrist = landmarks[mp.solutions.pose.PoseLandmark.LEFT_WRIST]
            #right_wrist = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_WRIST]
            left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            #right_shoulder = landmarks[mp.solutions.pose.PoseLandmark.RIGHT_SHOULDER]
            left_hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]

            vertical_diff = abs(left_shoulder.y - left_hip.y)

            if vertical_diff < 0.05:
                self.emergency+=1
                if self.emergency>=5:
                    print("emergency detect")
                    self.emergency_signal.emit(True)
                    self.emergency=0
            
            else:
                self.emergency = 0


class HelmetDetect(QThread):
    helmet_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.model = YOLO("hemletYoloV8_100epochs.pt")
        self.helmet_detected = False
        self.frame = None

    def update_frame(self, frame):
        self.frame = frame

    def run(self):
        self.running = True
        while self.running:
            if self.frame is not None:
                results = self.model(self.frame, stream=True)
                for r in results:
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id].lower()
                        conf = float(box.conf[0])

                        if "helmet" in label and conf >= 0.8:
                            self.helmet_detected = True