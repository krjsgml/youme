import mediapipe as mp
import time
import cv2
import numpy as np
from ultralytics import YOLO
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from Bluetooth import get_bluetooth  # 기존 모듈

# -------------------------
# 헬퍼: 트래커 생성기 (KCF 우선, MOSSE 폴백)
# -------------------------
def create_kcf_tracker():
    try:
        return cv2.legacy.TrackerKCF_create()
    except Exception:
        try:
            return cv2.TrackerKCF_create()
        except Exception:
            # KCF 실패 시 MOSSE 폴백 (가벼움, 빠름)
            try:
                return cv2.legacy.TrackerMOSSE_create()
            except Exception:
                return cv2.TrackerMOSSE_create()

def create_mosse_tracker():
    try:
        return cv2.legacy.TrackerMOSSE_create()
    except Exception:
        return cv2.TrackerMOSSE_create()

# -------------------------
# CameraThread: 카메라 캡처 전담 (Tracking에서 capture를 직접 하지 않음)
# emits frames as numpy arrays (object)
# -------------------------
class CameraThread(QThread):
    frame_signal = pyqtSignal(object)  # numpy.ndarray

    def __init__(self, cam_indices=[2, 0], width=640, height=400, parent=None):
        super().__init__(parent)
        self.cam_indices = cam_indices
        self.width = width
        self.height = height
        self.current_index = 0
        self._running = False
        self.cap = None

    def run(self):
        self._running = True
        self._open_camera(self.current_index)
        while self._running:
            if not self.cap or not self.cap.isOpened():
                # 재시도
                time.sleep(0.1)
                self._open_camera(self.current_index)
                continue
            ret, frame = self.cap.read()
            if not ret or frame is None:
                time.sleep(0.01)
                continue
            # 좌우 반전은 여기서 해도 괜찮음 (UI 일관성)
            frame = cv2.flip(frame, 1)
            # emit (object) 프레임. 수신측에서 복사 결정
            self.frame_signal.emit(frame)
            # 아주 짧게 sleep 하여 CPU 과다점유 방지
            time.sleep(0.01)

    def _open_camera(self, index):
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
            self.cap = cv2.VideoCapture(self.cam_indices[index])
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
            self.current_index = index
        except Exception as e:
            print("카메라 오픈 실패:", e)
            self.cap = None

    def switch_camera(self, index):
        if index == self.current_index:
            return
        self._open_camera(index)

    def stop(self):
        self._running = False
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.wait()


# -------------------------
# Falldetect (원본 로직 유지 + 안전성 보강)
# -------------------------
class Falldetect(QThread):
    emergency_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        print("\n\n\nfall init\n\n\n")
        self.running = False
        self.pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.3,
            min_tracking_confidence=0.3
        )
        self.frame = None
        self.emergency = 0
        self._frame_mutex = QMutex()
        self.left_hip = None
        self.left_shoulder = None

    def run(self):
        self.running = True
        self.left_hip = None
        self.left_shoulder = None
        while self.running:
            local_frame = None
            with QMutexLocker(self._frame_mutex):
                if self.frame is not None:
                    # copy 한 번만
                    local_frame = self.frame.copy()
                    self.frame = None  # 사용 후 해제하여 메모리 누적 방지
            if local_frame is not None:
                rgb = cv2.cvtColor(local_frame, cv2.COLOR_BGR2RGB)
                results = self.pose.process(rgb)
                self.handle_fall_result(results, self.frame)
            # 300ms 주기로 반응성/부하 균형 (원래 1000ms였으나 응답성 개선)
            self.msleep(300)

    def stop(self):
        self.running = False
        self.wait()

    def update_frame(self, frame):
        with QMutexLocker(self._frame_mutex):
            self.frame = frame.copy()

    def handle_fall_result(self, results, frame):
        if results.pose_landmarks:
            landmarks = results.pose_landmarks.landmark
            self.left_shoulder = landmarks[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER]
            self.left_hip = landmarks[mp.solutions.pose.PoseLandmark.LEFT_HIP]
            vertical_diff = abs(self.left_shoulder.y - self.left_hip.y)
            if vertical_diff < 0.2:
                self.emergency += 1
                if self.emergency >= 10:
                    print("emergency detect")
                    cv2.putText(frame, "emergency situation!", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    self.emergency_signal.emit(True)
                    self.emergency = 0
            else:
                self.emergency = 0
        else:
            pass


# -------------------------
# HelmetDetect (개선: stream=True 제거, 추론 주기 제어)
# -------------------------
class HelmetDetect(QThread):
    helmet_signal = pyqtSignal(object)

    def __init__(self):
        super().__init__()
        self.running = False
        # 모델 로드: 파일명 오타에 대한 폴백 유지
        try:
            self.model = YOLO("helmetYoloV8_100epochs.pt")
        except Exception:
            self.model = YOLO("hemletYoloV8_100epochs.pt")
        self.helmet_detected = False
        self.frame = None
        self.emergency_state = False
        self._frame_mutex = QMutex()
        # 추론 주기 제어 (ms)
        self.infer_interval_ms = 300

    def update_frame(self, frame):
        with QMutexLocker(self._frame_mutex):
            # 가능한 적게 복사
            self.frame = frame.copy()

    def run(self):
        self.running = True
        last_time = 0.0
        while self.running:
            if self.emergency_state:
                # 비상 상태면 헬멧 판단 정지(원래 로직)
                self.msleep(100)
                continue
            now = time.time() * 1000.0
            if now - last_time < self.infer_interval_ms:
                self.msleep(10)
                continue
            local = None
            with QMutexLocker(self._frame_mutex):
                if self.frame is not None:
                    local = self.frame.copy()
                    self.frame = None
            last_time = now
            if local is None:
                continue
            try:
                # stream=False로 단일 추론 (generator 오버헤드 제거)
                results = self.model(local)
            except Exception as e:
                print("HelmetDetect model inference error:", e)
                self.msleep(50)
                continue

            detected = False
            # results는 리스트로 반환됨
            for r in results:
                # r.boxes 가능. ultralytics 버전에 따라 객체 구조가 다를 수 있음.
                if hasattr(r, 'boxes'):
                    for box in r.boxes:
                        cls_id = int(box.cls[0])
                        label = self.model.names[cls_id].lower()
                        conf = float(box.conf[0])
                        if "helmet" in label and conf >= 0.8:
                            detected = True
            self.helmet_detected = detected
            # 시그널로 외부에 상태 알리기(필요시 사용)
            self.helmet_signal.emit(self.helmet_detected)
            self.msleep(10)

    def stop(self):
        self.running = False
        self.wait()


# -------------------------
# Tracking: 메인 로직(트래킹/블루투스/상태관리)
# - CameraThread에서 frame_signal을 받아 내부 상태로 저장
# - UI 업데이트 빈도 제한 (max_update_fps)
# -------------------------
class Tracking(QThread):
    result_signal = pyqtSignal(QPixmap)  # QPixmap 전송 (기존 API 유지)

    def __init__(self):
        super().__init__()
        # 하드웨어/외부 스레드들
        self.bluetooth_thread = get_bluetooth()
        self.fall_detect_thread = Falldetect()
        self.helmet_detect_thread = HelmetDetect()

        # 카메라는 별도 스레드로 분리
        self.camera_thread = CameraThread(cam_indices=[2, 0], width=640, height=400)
        self.camera_thread.frame_signal.connect(self.on_camera_frame)

        # 상태 플래그
        self.running = False
        self.tracking = False
        self.detects = []
        self.prev_pos = None
        self.stop_track = 0
        self.stop_dc_motor_flag = False
        self.stop_dc_no_helmet_Flag = False
        self.helmet_frame_count = 0
        self.emergency_state = False

        # ROI/트래커
        self.tracker = create_kcf_tracker()
        self._frame_mutex = QMutex()
        self.frame = None  # 최신 프레임(원본 numpy 배열)
        self.cam_indices = [2, 0]
        self.current_index = 0

        # Haar cascade
        self.cascade = cv2.CascadeClassifier("/home/jsh/youme/haarcascade/haarcascade_frontalface_default.xml")

        # UI update rate limiting
        self.max_update_fps = 10.0
        self._last_update_time = 0.0

    # ---------- Camera -> Tracking frame 수신 슬롯 ----------
    def on_camera_frame(self, frame):
        # camera thread에서 전달되는 원본 프레임을 안전하게 저장
        with QMutexLocker(self._frame_mutex):
            # shallow copy -> 이후 필요 시 .copy() 수행
            self.frame = frame.copy()

    # ---------- run: 메인 루프 ----------
    def run(self):
        # 시작
        self.running = True

        # 카메라 스레드 시작
        if not self.camera_thread.isRunning():
            self.camera_thread.start()

        # 보조 감지 스레드 시작(헬멧)
        if not self.helmet_detect_thread.isRunning():
            self.helmet_detect_thread.start()

        while self.running:
            local = None
            with QMutexLocker(self._frame_mutex):
                if self.frame is not None:
                    local = self.frame.copy()

            if local is None:
                self.msleep(5)
                continue
            
            frame = local
            self.helmet_frame_count += 1
            if self.helmet_frame_count % 5 == 0:
                self.helmet_detect_thread.update_frame(frame)

            if self.emergency_state:
                # ✅ 응급상황일 때는 오직 이 텍스트만 출력
                self.camera_thread.switch_camera(1)
                self.fall_detect_thread.update_frame(frame)

            else:
                # ✅ 응급상황이 아닐 때만 나머지 텍스트 출력 허용
                if self.helmet_detect_thread.helmet_detected:
                    self.stop_dc_motor_flag = False
                    self.stop_dc_no_helmet_Flag = False

                    if not self.tracking:
                        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                        self.detects = self.cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
                        for (x, y, w, h) in self.detects:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

                        cv2.putText(frame, "Click a box to track", (10, 30),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                    else:
                        try:
                            success, box = self.tracker.update(frame)
                        except Exception:
                            self.tracker = create_mosse_tracker()
                            success = False
                            box = None

                        if success and box is not None:
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

                            self.stop_track = 0
                        else:
                            cv2.putText(frame, "Tracking failure", (10, 60),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

                            if not self.stop_dc_motor_flag:
                                self.bluetooth_thread.send_data('s')
                                self.stop_dc_motor_flag = True

                            self.stop_track += 1
                            if self.stop_track >= 50:
                                if not self.fall_detect_thread.isRunning():
                                    self.fall_detect_thread.start()
                                print("dc motor stop")
                                self.emergency_state = True
                                self.helmet_detect_thread.emergency_state = True

                else:
                    if not self.stop_dc_no_helmet_Flag:
                        self.bluetooth_thread.send_data('s')
                        self.stop_dc_no_helmet_Flag = True

                    self.tracking = False
                    self.tracker = create_kcf_tracker()
                    self.detects = []
                    cv2.putText(frame, "Please wear a helmet.", (10, 60),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            now = time.time()
            if now - self._last_update_time >= (1.0 / self.max_update_fps):
                self._last_update_time = now
                self.handle_tracking_result(frame)

            self.msleep(5)

        # 루프 종료 시 정리
        self.camera_thread.stop()
        # 보조 스레드 중지
        try:
            self.helmet_detect_thread.stop()
        except Exception:
            pass
        try:
            self.fall_detect_thread.stop()
        except Exception:
            pass

    # ---------- 안전 중지 ----------
    def stop(self):
        self.running = False
        self.tracking = False
        self.prev_pos = None
        self.stop_dc_motor_flag = False
        self.stop_dc_no_helmet_Flag = False
        self.stop_track = 0
        self.emergency_state = False

        try:
            self.camera_thread.switch_camera(0)
            self.camera_thread.current_index = 0
        except Exception:
            pass

        # stop fall detect if running
        try:
            if self.fall_detect_thread.isRunning():
                self.fall_detect_thread.stop()
        except Exception:
            pass

        # camera thread stop handled in run or explicitly
        try:
            self.camera_thread.stop()
        except Exception:
            pass

        # retry helmet stop
        try:
            if self.helmet_detect_thread.isRunning():
                self.helmet_detect_thread.stop()
        except Exception:
            pass

        # wait for this thread to finish
        self.wait()

    # ---------- QPixmap 변환 (원본 함수 유지하되 호출 빈도 제한) ----------
    def handle_tracking_result(self, frame):
        # rgb 변환 및 QPixmap 생성
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qt_image)
        self.result_signal.emit(pixmap)

    # ---------- ROI 설정 ----------
    def set_roi(self, roi):
        # self.frame은 항상 mutex로 보호
        with QMutexLocker(self._frame_mutex):
            init_frame = self.frame.copy() if self.frame is not None else None
        if init_frame is not None:
            # 트래커 재생성 후 초기화 (KCF 우선)
            try:
                self.tracker = create_kcf_tracker()
                self.tracker.init(init_frame, roi)
            except Exception:
                # MOSSE 폴백
                self.tracker = create_mosse_tracker()
                self.tracker.init(init_frame, roi)
            self.tracking = True

    # ---------- ROI 선택 (마우스 이벤트 처리) ----------
    def select_roi(self, event):
        if not self.running:
            print('작동 x')
            return
        x, y = event.x(), event.y()
        if self.tracking:
            print("현재 추적 중")
            return

        # 현재 검출된 얼굴 리스트 사용
        detects = self.detects
        for (x1, y1, w, h) in detects:
            if x1 < x < x1 + w and y1 < y < y1 + h:
                roi = (x1, y1, w, h)
                self.set_roi(roi)
                if not self.fall_detect_thread.isRunning():
                    self.fall_detect_thread.start()
                print("Tracking 시작:", roi)
                break

    # ---------- 카메라 직접 전환(외부 호출용) ----------
    def switch_camera(self, index):
        self.camera_thread.switch_camera(index)
