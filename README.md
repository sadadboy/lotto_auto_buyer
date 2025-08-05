# 로또 자동구매 시스템 (통합 버전)

## 🎲 개요
동행복권 사이트에서 로또를 자동으로 구매하는 시스템입니다.
자동충전, GUI 대시보드, 도커 지원 등 다양한 기능을 제공합니다.

## ✨ 주요 기능
- **자동 로또 구매**: 다양한 구매 방식 지원 (자동/반자동/수동)
- **자동충전**: 잔액 부족 시 자동으로 충전 (5000원 이하)
- **GUI 대시보드**: 웹 기반 관리 인터페이스
- **스케줄링**: 정해진 시간에 자동 구매
- **도커 지원**: 오라클 클라우드 등 클라우드 환경 배포 가능
- **통계 분석**: AI 추천, 통계 기반 번호 생성

## 📋 요구사항
- Python 3.10 이상
- Chrome 브라우저
- ChromeDriver (자동 설치됨)

## 🚀 빠른 시작

### 1. 의존성 설치
```bash
pip install -r requirements.txt
```

### 2. 설정 파일 수정
`lotto_config.json` 파일에서 로그인 정보와 설정을 수정하세요:
```json
{
  "login": {
    "user_id": "your_id",
    "password": "your_password"
  },
  "payment": {
    "auto_recharge": true,
    "recharge_amount": 50000,
    "min_balance": 5000
  }
}
```

### 3. 로또 구매 실행
```bash
# 즉시 구매
python lotto_auto_buyer.py --now

# GUI 대시보드 실행
python dashboard.py

# 스케줄러 실행
python scheduler.py
```

## 🐳 도커로 실행

### 1. 도커 이미지 빌드
```bash
docker-compose build
```

### 2. 도커 컨테이너 실행
```bash
docker-compose up -d
```

### 3. 대시보드 접속
브라우저에서 http://localhost:5000 접속

## 📁 프로젝트 구조
```
lotto_auto_complete/
├── lotto_auto_buyer.py      # 메인 구매 로직
├── dashboard.py             # GUI 대시보드
├── scheduler.py             # 스케줄 실행
├── lotto_config.json        # 설정 파일
├── requirements.txt         # 의존성 목록
├── Dockerfile              # 도커 이미지 설정
├── docker-compose.yml      # 도커 컴포즈 설정
├── templates/              # HTML 템플릿
│   └── index.html
├── screenshots/            # 구매 스크린샷
├── logs/                   # 로그 파일
└── data/                   # 데이터 파일
```

## 🔧 주요 기능 설명

### 1. 구매 방식
- **자동**: 시스템이 자동으로 번호 선택
- **반자동**: 3개 번호 지정, 나머지 자동
- **수동(랜덤)**: 완전 랜덤 번호
- **수동(AI추천)**: AI가 분석한 추천 번호
- **수동(통계분석)**: 역대 당첨 통계 기반 번호

### 2. 자동충전 기능
- 잔액이 5000원 이하일 때 자동으로 충전
- 설정에서 충전 금액 조정 가능
- 현재는 충전 페이지 접근만 구현 (실제 충전은 수동)

### 3. GUI 대시보드
- 실시간 상태 모니터링
- 설정 관리
- 구매 내역 조회
- 로그 확인
- 스크린샷 갤러리

### 4. 스케줄링
- 매주 특정 요일/시간에 자동 실행
- 설정 파일에서 스케줄 변경 가능

## ⚠️ 주의사항
1. 로그인 정보는 안전하게 관리하세요
2. 자동충전 기능 사용 시 충전 한도를 확인하세요
3. 과도한 구매는 자제하세요
4. 테스트 후 실제 사용하세요

## 🔍 문제 해결

### Chrome 드라이버 오류
```bash
# webdriver-manager가 자동으로 처리하지만, 수동 설치가 필요한 경우:
# https://chromedriver.chromium.org/ 에서 다운로드
```

### 도커 실행 오류
```bash
# 도커 서비스 재시작
docker-compose down
docker-compose up -d --build
```

### 로그 확인
```bash
# 실시간 로그 확인
tail -f lotto_auto_buyer.log

# 도커 로그 확인
docker-compose logs -f
```

## 📝 라이센스
이 프로젝트는 개인 사용 목적으로 만들어졌습니다.
상업적 사용은 금지됩니다.

## 🤝 기여
버그 리포트나 기능 제안은 이슈를 생성해주세요.
