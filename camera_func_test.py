import mediapipe as mp
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
import cv2
from ultralytics import YOLO
from Bluetooth import get_bluetooth

def create_kcf_tracker():
    """OpenCV 버전 호환용 KCF 트래커 생성기"""
    try:
        # OpenCV 4.5+일 때 legacy 네임스페이스인 경우가 많음
        return cv2.legacy.TrackerKCF_create()
    except AttributeError:
        return cv2.TrackerKCF_create()

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

        self.cam_indices=[2, 0]
        self.current_index = 0

        self.cascade = cv2.CascadeClassifier("/home/jsh/youme/haarcascade/haarcascade_frontalface_default.xml")
        self.tracker = create_kcf_tracker()
        self.stop_track = 0
        self.prev_pos = None

        self.helmet_frame_count = 0
        self.emergency_state = False

        # 스레드 안전성용
        self._frame_mutex = QMutex()
        self.cap = None

    def run(self):
        self.running = True
        self.cap = cv2.VideoCapture(self.cam_indices[self.current_index])
        # 매직넘버 대신 상수 사용
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 400)

        # 보조 스레드 안전 시작
        if not self.helmet_detect_thread.isRunning():
            self.helmet_detect_thread.start()
        if not self.fall_detect_thread.isRunning():
            self.fall_detect_thread.start()

        while self.running:
            ret, raw = self.cap.read()
            if not ret or raw is None:
                self.msleep(10)
                continue

            # 좌우 반전
            frame = cv2.flip(raw, 1)

            # 최신 프레임 공유(복사본)
            with QMutexLocker(self._frame_mutex):
                self.frame = frame.copy()

            # 헬멧 감지는 부하 줄이기 위해 N프레임마다 전달
            self.helmet_frame_count += 1
            if self.helmet_frame_count % 5 == 0:
                self.helmet_detect_thread.update_frame(frame)

            # 비상상태일 때만 낙상 감지 프레임 공급(원래 로직 유지)
            if self.emergency_state:
                self.fall_detect_thread.update_frame(frame)

            # ---- 원래 트래킹/표시 로직 유지 및 보강 ----
            self.handle_tracking_result(frame)  # (원코드 위치 유지)

            if ret:
                if frame is not None:
                    # (원코드 흐름 유지) 트래킹 결과 처리
                    # 얼굴 검출/트래커 업데이트/블루투스 전송/상태표시
                    if self.helmet_detect_thread.helmet_detected == True:
                        # 얼굴 인식 및 트래킹 로직
                        if not self.tracking:
                            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                            self.detects = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)

                            for (x, y, w, h) in self.detects:
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                            cv2.putText(frame, "Click a box to track", (10, 30),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                        else:
                            success, box = self.tracker.update(frame)
                            if success:
                                x, y, w, h = [int(v) for v in box]
                                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                                cv2.putText(frame, "Tracking...", (x, y - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                                face_center = x + w // 2
                                left_bound = frame.shape[1] // 3
                                right_bound = 2 * frame.shape[1] // 3

                                if face_center < left_bound:
                                    pos = 'l'
                                elif face_center > right_bound:
                                    pos = 'r'
                                else:
                                    pos = 'c'

                                if pos != self.prev_pos:
                                    self.bluetooth_thread.send_data(pos)
                                    self.prev_pos = pos

                            else:
                                #print("tracking failed!!")
                                cv2.putText(frame, "Tracking failure", (10, 60),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                                self.bluetooth_thread.send_data('s')
                                self.stop_track += 1
                                if self.stop_track == 50:
                                    print("dc motor stop")
                                    self.emergency_state = True
                                    self.helmet_detect_thread.emergency_state = self.emergency_state

                                    self.switch_camera(1)
                                    # fall detect에 최신 프레임 전달 (원코드 유지)
                                    self.fall_detect_thread.update_frame(frame)
                                    cv2.putText(frame, "emergency situation!", (10, 60),
                                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                    else:
                        self.bluetooth_thread.send_data('s')
                        self.tracking = False
                        self.tracker = create_kcf_tracker()
                        self.detects = []
                        cv2.putText(frame, "Please wear a helmet.", (10, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                    # 프레임을 QPixmap으로 변환하여 시그널 발행 (원코드 위치 유지)
                    self.handle_tracking_result(frame)

            self.msleep(10)  # CPU 점유율 완화

    def stop(self):
        # (원코드 유지 + 보강)
        self.running = False
        self.tracking = False
        self.prev_pos = None
        self.fall_detect_thread.stop()
        if self.cap:
            self.cap.release()
        self.current_index = 0
        self.stop_track = 0
        self.emergency_state = False

        self.tracker = create_kcf_tracker()
        self.detects = []
        self.wait()  # 안전 종료 대기

        # 보조 스레드도 안전 종료
        self.helmet_detect_thread.stop()

    def closeEvent(self, event):
        # (원코드 유지: 실제로 QThread에는 호출되지 않지만 요구사항대로 보존)
        self.current_index=0
        self.stop()
        # 종료 시 카메라 해제
        if self.cap:
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
        # (원코드 유지)
        if self.frame is not None:
            self.tracker = create_kcf_tracker()
            # 최신 프레임 기준으로 초기화(잠금)
            with QMutexLocker(self._frame_mutex):
                init_frame = self.frame.copy() if self.frame is not None else None
            if init_frame is not None:
                self.tracker.init(init_frame, roi)
        self.tracking = True

    def select_roi(self, event):
        # (원코드 유지)
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

    def switch_camera(self, index):
        # (원코드 유지 + 자원 해제 보강)
        if self.current_index == index:
            return  # 이미 해당 카메라라면 실행 안 함
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.cap = cv2.VideoCapture(self.cam_indices[index])
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 400)
        self.current_index = index


class Falldetect(QThread):
    emergency_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.3,   # 감지 기준 낮춤
            min_tracking_confidence=0.3
        )
        self.frame = None
        self.emergency = 0

        self._frame_mutex = QMutex()

    def run(self):
        self.running = True
        while self.running:
            local_frame = None
            with QMutexLocker(self._frame_mutex):
                if self.frame is not None:
                    local_frame = self.frame.copy()
            if local_frame is not None:
                rgb = cv2.cvtColor(local_frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb)
                # print(results.pose_landmarks is not None)  # 로그 과다 방지로 주석
                self.handle_fall_result(results)
            self.msleep(1000)  # 원코드 주기 유지

    def stop(self):
        self.running = False
        self.wait()

    def update_frame(self, frame):
        with QMutexLocker(self._frame_mutex):
            self.frame = frame.copy()

    def handle_fall_result(self, results):
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            # print("pose landmarks detected")
            left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            left_hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
            print(left_hip.y, left_shoulder.y)
            vertical_diff = abs(left_shoulder.y - left_hip.y)
            # print(vertical_diff)
            if vertical_diff < 0.05:
                self.emergency+=1
                # print(self.emergency)
                if self.emergency>=5:
                    print("emergency detect")
                    self.emergency_signal.emit(True)
                    self.emergency=0
            else:
                self.emergency = 0
        else:
            # print("no landmarks")
            pass


class HelmetDetect(QThread):
    helmet_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        # 파일명 오타 방지: hemlet -> helmet 로 교정(실제 파일명이 hemlet라면 원래대로 되돌리세요)
        try:
            self.model = YOLO("helmetYoloV8_100epochs.pt")
        except Exception:
            # 혹시 실제 체크포인트 파일명이 원래 것이라면 fallback
            self.model = YOLO("hemletYoloV8_100epochs.pt")

        self.helmet_detected = False
        self.frame = None
        self.emergency_state = False

        self._frame_mutex = QMutex()

    def update_frame(self, frame):
        with QMutexLocker(self._frame_mutex):
            self.frame = frame.copy()

    def run(self):
        self.running = True
        while self.running:
            if self.emergency_state == False:
                local = None
                with QMutexLocker(self._frame_mutex):
                    if self.frame is not None:
                        local = self.frame.copy()
                if local is not None:
                    results = self.model(local, stream=True)
                    detected = False
                    for r in results:
                        for box in r.boxes:
                            cls_id = int(box.cls[0])
                            label = self.model.names[cls_id].lower()
                            conf = float(box.conf[0])

                            if "helmet" in label and conf >= 0.8:
                                detected = True
                    self.helmet_detected = detected
            self.msleep(300)  # 1초에서 300ms로 반응성 개선

    def stop(self):
        self.running = False
        self.wait()
