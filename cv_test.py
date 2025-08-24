import cv2
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'  # 또는 'offscreen', 'minimal' 등 시도


cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()

    cv2.imshow("cam", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
