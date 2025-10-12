# YOUME – 비전을 이용한 물류 보조 로봇

## ✅ 프로젝트 소개
YOUME는 **작업자의 움직임을 인식하고 추적하며 물류 작업을 보조하는 스마트 로봇**입니다.  
자키(핸드카트)의 기동성과 지게차의 적재 기능을 결합해, **작업자의 안전 확보와 물류 효율 향상**을 목표로 개발되었습니다.

## ✅ 주요 기능
- 객체 인식 및 추적 (OpenCV, Tracker)
- 응급상황 감지
- 헬멧 착용 여부 판별 (YOLOv8)
- RFID 기반 사용자 인증
- DB 저장 및 물품 위치 조회 (MySQL, LCD)
- 앱 기반 물류 관리 (Flutter + Flask)
- 리니어 액추에이터 물품 적재 기능
- Bluetooth / USART 통신

## ✅ 시스템 구조
```
Flutter App ↔ Flask API ↔ MySQL DB
          ↕
      Raspberry Pi
          ↕
   Arduino · Sensors · Motors
```

## ✅ 기술 스택
**Frontend:** Flutter  
**Backend:** Flask (Python)  
**Database:** MySQL  
**임베디드:** Raspberry Pi, Arduino  
**Vision:** OpenCV, YOLOv8  
**통신:** Bluetooth, USART  
**제어:** PID, 모터드라이버  
**언어:** Python, Java, SQL, C

## ✅ 개발 환경
- Raspberry Pi OS, Windows
- Thonny, Arduino IDE, VS Code, Android Studio
- Python, C, Java, SQL
- GitHub, Google Sheets, KakaoTalk

## ✅ 팀원
| 이름 | 역할 | 담당 |
|------|------|------|
| 홍길동 | 팀장 | 프로젝트 총괄 |
| 김철수 | 개발 | OpenCV/객체추적 |
| 이영희 | 앱/DB | Flutter/Flask/MySQL |
| 박민수 | H/W | 회로·모터 제어 |

## ✅ 시연 자료 (추가 예정)
- 로봇 전체 모습
- 헬멧 감지 화면
- 물품 적재 장면
- 앱 UI 스크린샷

## ✅ 기대효과
- 작업자 안전 확보 및 산업재해 감소
- 물류 자동화 및 인력 부담 완화
- 자율주행·스마트팩토리 확장 가능성
