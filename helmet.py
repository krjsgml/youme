from ultralytics import YOLO
import cv2

# YOLO 모델 로드
model = YOLO("C:/Users/82109/Desktop/helmet/helmet-detection-yolov8/models/hemletYoloV8_100epochs.pt")

# 웹캠 열기
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("웹캠을 열 수 없습니다.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        break

    # YOLOv8 추론
    results = model(frame, stream=True)

    helmet_detected = False

    for r in results:
        for box in r.boxes:
            cls_id = int(box.cls[0])
            label = model.names[cls_id].lower()

            # 박스 좌표
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = float(box.conf[0])

            # 조건: 클래스가 helmet이고, 신뢰도 >= 0.8
            if "helmet" in label and conf >= 0.8:
                helmet_detected = True
                color = (0, 255, 0)  # 초록 (헬멧)

                # 헬멧 테두리 (바운딩 박스)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 3)
                cv2.putText(frame, f"Helmet {conf:.2f}", (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

    # 중앙 상단에 O/X 표시
    if helmet_detected:
        text, color = "O", (0, 255, 0)
    else:
        text, color = "X", (0, 0, 255)

    cv2.putText(frame, text, (frame.shape[1] // 2 - 20, 100),
                cv2.FONT_HERSHEY_SIMPLEX, 4, color, 10)

    cv2.imshow("Helmet Detection - Bounding Box", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
