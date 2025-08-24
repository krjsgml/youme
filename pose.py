import cv2
import mediapipe as mp

cap = cv2.VideoCapture(0)
pose = mp.solutions.pose.Pose()

while True:
    ret, frame = cap.read()
    if not ret:
        break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = pose.process(rgb)
    print(results.pose_landmarks is not None)
    if results.pose_landmarks:
        for lm in results.pose_landmarks.landmark:
            h, w, c = frame.shape
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(frame, (cx, cy), 3, (0, 255, 0), -1)
    cv2.imshow("pose", frame)
    if cv2.waitKey(1) & 0xFF == 27:
        break
