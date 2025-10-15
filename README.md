# 💡 비전을 이용한 물류 보조 로봇 YOUME

## 1. 프로젝트 개요

### 1-1. 프로젝트 소개
**프로젝트 명** : 비전을 이용한 물류 보조 로봇 YOUME  
**프로젝트 정의** : 작업자의 움직임을 추적하고, 물류 적재·운반·안전 관리를 수행하는 AI 기반 스마트 물류 보조 로봇 시스템

### 1-2. 개발 배경 및 필요성
물류센터 및 작업 현장에서는 반복적인 운반 작업, 인력 부족, 작업자 안전 문제가 지속적으로 발생하고 있습니다. 기존의 수동 장비(지게차·자키 등)는 작업자 개입이 필요하며 사고 위험이 존재합니다.  
따라서 **작업자의 움직임을 추적하여 자율적으로 운반을 지원하고, 헬멧 착용 감지 및 응급 상황 대응이 가능한 AI 기반 물류 보조 로봇의 필요성**이 대두되었습니다.

### 1-3. 프로젝트 특장점
- OpenCV 기반 실시간 객체 인식 및 추적
- YOLOv8 활용 헬멧 착용 여부 감지
- RFID 카드 인증으로 사용자 권한 제어
- MySQL 기반 물류 정보 저장 및 LCD 조회
- Flutter + Flask 기반 관리자 앱 제공
- 리니어 액추에이터를 이용한 물류 적재 기능
- Bluetooth/USART 기반 라즈베리파이-아두이노 통신

### 1-4. 주요 기능
- ✅ 객체 인식 및 추적 (OpenCV, Tracker)
- ✅ 사용자 인증 (RFID)
- ✅ 헬멧 착용 여부 판단 (YOLOv8)
- ✅ 응급 상황 알림
- ✅ 물품 위치 조회/수정/저장 (MySQL + LCD)
- ✅ 앱 기반 물류 관리 (Flutter + Flask)
- ✅ 리니어 액추에이터 적재 기능
- ✅ Bluetooth / USART 통신

### 1-5. 기대 효과 및 활용 분야
**기대 효과**
- 작업자 안전 확보 및 산업재해 감소
- 물류 효율 증대 및 자동화 수준 향상
- 작업자의 피로도 및 인력 부담 감소
- 스마트 물류·스마트팩토리 연계 가능성

**활용 분야**
- 물류센터 및 창고
- 대형 마트 및 유통매장
- 공장 내 부품 이송
- 건설 현장
- 자동화 물류 설비 산업

### 1-6. 기술 스택
**프론트엔드 / 앱**  
- Flutter

**백엔드**  
- Flask (Python)

**AI / Vision**  
- OpenCV  
- YOLOv8  
- HaarCascade  
- Tracker (KCF 등)

**데이터베이스**  
- MySQL

**임베디드 & 통신**  
- Raspberry Pi  
- Arduino  
- Bluetooth / USART  
- PID제어

**언어**  
- Python, Java, SQL, C

---

## 2. 팀원 소개
| 이름 | 역할 | 담당 |
|------|------|------|
| 김건희 | 팀장 | Tracking · Flutter · Flask · MySQL |
| 이유나 | SW |  헬멧 감지 |
| 정석호 | SW / HW | 응급상황 감지 · HW 설계 |
| 윤준서 | 모터제어 / HW | 센서 · 회로 · 모터 제어 |
| 하경욱 | 멘토 | 기술 자문 및 피드백 |

---

## 3. 시스템 구성도
### ✅ 서비스 구성도
<img width="643" height="350" alt="Image" src="https://github.com/user-attachments/assets/653d9efc-6243-427b-80ba-805a93d21362" />

### ✅ 하드웨어 구성도
<img width="643" height="363" alt="Image" src="https://github.com/user-attachments/assets/6d769523-056e-43de-8b32-1358f9a1e5de" />

## 4. 작품 소개영상
[![YOUME 시연 영상](https://github.com/user-attachments/assets/d0cba4cf-4ef0-44c3-83c9-4def7aaa6331)](https://www.youtube.com/watch?v=2qM_VF10ME4)

---

## 5. 핵심 소스코드
· 소스코드 설명 : HaarCascade와 Tracker API를 이용하여 Tracking 기능을 구현

```python
class Tracking(QThread):
    result_signal = pyqtSignal(QPixmap)  # QPixmap 전송 (기존 API 유지)

    def __init__(self):
        super().__init__()
        # 외부 스레드
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

        # Haarcascade
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
                self.camera_thread.switch_camera(1)
                self.fall_detect_thread.update_frame(frame)
                cv2.putText(frame, "emergency situation!", (10, 90),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            else:
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
