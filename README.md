# K-Meal Scraping

> 코리아텍(한국기술교육대학교) 식단 정보 크롤링 프로젝트

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 📋 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#-기술-스택)
- [설치 방법](#-설치-방법)
- [사용 방법](#-사용-방법)
- [프로젝트 구조](#-프로젝트-구조)
- [데이터베이스 스키마](#-데이터베이스-스키마)
- [환경 변수](#-환경-변수)
- [API 문서](#-api-문서)
- [개발 가이드](#-개발-가이드)
- [문제 해결](#-문제-해결)
- [라이선스](#-라이선스)

## 🎯 프로젝트 소개

K-Meal Scraping은 코리아텍 포털에서 식단 정보를 자동으로 크롤링하여 데이터베이스에 저장하는 Python 기반 애플리케이션입니다. 수집된 데이터는 PostgreSQL 데이터베이스, CSV, JSON 형식으로 저장되어 다양한 용도로 활용할 수 있습니다.

### 왜 이 프로젝트가 필요한가요?

- 📊 **데이터 수집 자동화**: 매일 수동으로 식단을 확인할 필요 없이 자동으로 수집
- 🔍 **식단 검색 및 분석**: 저장된 데이터를 활용한 식단 검색, 통계, 분석 가능
- 🔗 **API 개발 기반**: 수집된 데이터를 기반으로 식단 알림 서비스, 모바일 앱 등 개발 가능
- 📱 **다양한 형식 지원**: DB, CSV, JSON 등 다양한 형식으로 저장하여 활용도 극대화

## ✨ 주요 기능

### 🔐 인증
- 코리아텍 포털 4단계 SSO 인증 자동화
- JSESSIONID 쿠키 기반 세션 관리
- IP 주소 헤더 설정 (X-Forwarded-For, X-Real-IP)

### 🕷️ 크롤링
- **전체 식당 지원**
  - 1캠퍼스: 한식, 일품, Special Food, 능수관
  - 2캠퍼스: 코너1
- **전체 식사 시간 지원**: 아침, 점심, 저녁
- **날짜 범위 크롤링**: 원하는 기간의 식단 데이터 일괄 수집
- **서버 부하 방지**: 요청 간 자동 지연 처리
- **에러 복구**: 개별 요청 실패 시에도 전체 프로세스 계속 진행

### 💾 데이터 저장
- **PostgreSQL 데이터베이스**
  - 정규화된 스키마 (meals, meal_menu_items)
  - 중복 데이터 자동 방지 (ID 해시 기반)
  - 트랜잭션 관리 및 롤백
- **CSV 파일**
  - Excel 호환 (UTF-8 with BOM)
  - 구분자: 세미콜론(;)
- **JSON 파일**
  - UTF-8 인코딩
  - 들여쓰기 적용 (읽기 쉬운 형식)

### 🎮 실행 모드
- **일반 모드**: 2주 전 ~ 2주 후 (총 29일)
- **초기화 모드** (`--init`): 올해 1월 1일 ~ 한 달 후
- **테스트 모드** (`--test`): 오늘 하루만

### 📊 로깅 및 모니터링
- 파일 로깅 (타임스탬프 포함)
- 콘솔 실시간 출력
- 진행 상황 추적
- 상세한 에러 로그

## 🛠️ 기술 스택

| 카테고리 | 기술 |
|---------|------|
| 언어 | Python 3.8+ |
| 웹 크롤링 | requests, BeautifulSoup4, lxml |
| 데이터베이스 | PostgreSQL, SQLAlchemy, psycopg2-binary |
| 환경 관리 | python-dotenv |
| 데이터 처리 | csv, json |

## 📦 설치 방법

### 1. 저장소 클론

```bash
git clone https://github.com/Choi-JJunho/kapp-scraping.git
cd kapp-scraping
```

### 2. 가상환경 생성 및 활성화

```bash
# 가상환경 생성
python -m venv .venv

# 활성화 (Linux/Mac)
source .venv/bin/activate

# 활성화 (Windows)
.venv\Scripts\activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

```bash
# 환경 변수 예시 파일 복사
cp .env.example kapp-config/kapp-scraping/.env

# .env 파일 편집
nano kapp-config/kapp-scraping/.env
```

**.env 파일 내용:**
```env
# 코리아텍 포털 로그인 정보
PORTAL_ID=your_portal_id
PORTAL_PW=your_password
YOUR_IP_ADDRESS=your_ip_address

# 데이터베이스 설정
DB_HOST=localhost
DB_PORT=5432
DB_NAME=kapp
DB_USERNAME=postgres
DB_PASSWORD=your_db_password
DB_SSLMODE=prefer
```

### 5. PostgreSQL 데이터베이스 준비

```bash
# PostgreSQL 설치 (Ubuntu/Debian)
sudo apt-get install postgresql postgresql-contrib

# PostgreSQL 서비스 시작
sudo service postgresql start

# 데이터베이스 생성
sudo -u postgres createdb kapp

# (선택) 비밀번호 설정
sudo -u postgres psql
postgres=# ALTER USER postgres PASSWORD 'your_password';
postgres=# \q
```

## 🚀 사용 방법

### 기본 실행

```bash
# 일반 모드 (2주 전 ~ 2주 후)
python src/main.py

# 초기 데이터 수집 (올해 1월 1일 ~ 한 달 후)
python src/main.py --init

# 테스트 모드 (오늘 하루만)
python src/main.py --test
```

### 실행 예시

```bash
$ python src/main.py --test

🚀 포털에 로그인 중...
✅ 로그인 성공. 인증된 세션이 준비되었습니다.

📅 테스트 모드 (오늘 하루치만)
📅 2025-01-15부터 2025-01-15까지 식단 데이터를 수집합니다
📊 처리할 총 일수: 1일

🧪 테스트 모드: 자동으로 진행합니다.

🍽️ 식단 데이터 수집을 시작합니다...
[1/1] Processing 2025-01-15...
2025-01-15의 식단 데이터를 가져오는 중...
  ✅ Found 18 meals

✅ 총 18개의 식단 정보를 성공적으로 수집했습니다!

💾 Saving 18 menu entries to all formats...
💾 Saved 18 menu entries to koreatech_meals_2025.csv
💾 Saved 18 menu entries to koreatech_meals_2025.json
💾 Database: Saved 18 new entries (0 duplicates skipped)

📋 샘플 결과 (처음 5개 항목):
  [breakfast/Korean Food (한식)] 김치찌개, 계란말이, 밥, 김치 (650 kcal, 5000 won)
  [lunch/Korean Food (한식)] 돈까스, 스파게티, 샐러드 (820 kcal, 6000 won)
  ...
```

### 출력 파일

실행 후 다음 파일들이 생성됩니다:

```
kapp-scraping/
├── koreatech_meals_2025.csv          # CSV 형식
├── koreatech_meals_2025.json         # JSON 형식
└── logs/
    └── kmeal_scraping_20250115_103000.log  # 로그 파일
```

## 📁 프로젝트 구조

```
kapp-scraping/
├── src/
│   ├── main.py                    # 메인 실행 스크립트
│   └── kmeal/                     # 메인 패키지
│       ├── __init__.py           # 패키지 초기화
│       ├── config.py             # 데이터베이스 설정
│       ├── crawler.py            # 크롤링 로직 (420줄)
│       ├── models.py             # 데이터 모델 (273줄)
│       ├── storage.py            # 데이터 저장 (304줄)
│       └── utils.py              # 유틸리티 함수
├── kapp-config/                   # 환경 변수 저장소 (Git 서브모듈)
│   └── kapp-scraping/
│       └── .env                  # 환경 변수 파일
├── logs/                         # 로그 파일 저장 디렉토리
├── requirements.txt              # Python 의존성
├── .env.example                  # 환경 변수 예시
├── .gitignore                   # Git 제외 파일
├── .gitmodules                  # Git 서브모듈 설정
└── README.md                    # 프로젝트 문서 (이 파일)
```

### 주요 모듈 설명

#### `src/main.py`
- 애플리케이션 엔트리포인트
- 명령행 인자 파싱
- 전체 실행 프로세스 오케스트레이션

#### `src/kmeal/crawler.py`
- **KoreatechMealCrawler**: 크롤링 클래스
  - `portal_login()`: 4단계 SSO 인증
  - `send_meal_request()`: Nexacro API 요청
  - `parse_meal_response()`: XML 응답 파싱
  - `get_all_menus_for_day()`: 특정 날짜 전체 식단 수집
  - `get_meals_for_date_range()`: 날짜 범위 크롤링

#### `src/kmeal/models.py`
- **User**: 사용자 테이블 모델
- **MealDB**: 식단 기본 정보 테이블
- **MealMenuItem**: 메뉴 아이템 테이블
- **MenuEntity**: 크롤링 데이터 엔티티

#### `src/kmeal/storage.py`
- **MealStorage**: 데이터 저장 클래스
  - `save_to_database()`: PostgreSQL 저장
  - `save_to_csv()`: CSV 파일 저장
  - `save_to_json()`: JSON 파일 저장
  - `save_all_formats()`: 모든 형식 동시 저장

#### `src/kmeal/config.py`
- `get_database_url()`: 데이터베이스 연결 URL 생성

#### `src/kmeal/utils.py`
- `setup_logging()`: 로깅 시스템 초기화

## 🗄️ 데이터베이스 스키마

### ERD (Entity Relationship Diagram)

```
┌─────────────────────┐
│      users          │
├─────────────────────┤
│ id (PK)             │
│ email (UNIQUE)      │
│ password            │
│ name                │
│ student_employee_id │
│ created_at          │
│ updated_at          │
└─────────────────────┘

┌─────────────────────┐
│      meals          │
├─────────────────────┤
│ id (PK)             │◄─┐
│ date                │  │
│ dining_time         │  │ One-to-Many
│ place               │  │
│ price               │  │
│ kcal                │  │
│ created_at          │  │
│ updated_at          │  │
└─────────────────────┘  │
                         │
┌─────────────────────┐  │
│  meal_menu_items    │  │
├─────────────────────┤  │
│ meal_id (PK, FK)    │──┘
│ menu_item (PK)      │
└─────────────────────┘
```

### 테이블 상세

#### `users` 테이블
향후 사용자별 식단 관리 기능을 위한 테이블 (현재 미사용)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BigInteger | 기본키 |
| email | String(255) | 이메일 (UNIQUE) |
| password | String(255) | 비밀번호 |
| name | String(100) | 이름 |
| student_employee_id | String(50) | 학번/교직원번호 |
| created_at | DateTime | 생성일시 |
| updated_at | DateTime | 수정일시 |

#### `meals` 테이블
식단 기본 정보

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BigInteger | 기본키 (MD5 해시) |
| date | Date | 식단 날짜 |
| dining_time | String(20) | 식사 시간 |
| place | String(100) | 식당 이름 |
| price | Integer | 가격 (원) |
| kcal | Integer | 열량 (kcal) |
| created_at | DateTime | 생성일시 |
| updated_at | DateTime | 수정일시 |

**ID 생성 방식**: `MD5(date + dining_time + place)`의 첫 15자리

#### `meal_menu_items` 테이블
식단의 개별 메뉴 아이템 (정규화)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| meal_id | BigInteger | 외래키 (meals.id) |
| menu_item | String(200) | 메뉴 이름 |

**복합 기본키**: (meal_id, menu_item)

### SQL 예시

```sql
-- 특정 날짜의 모든 식단 조회
SELECT m.date, m.dining_time, m.place, m.price, m.kcal,
       STRING_AGG(mi.menu_item, ', ') as menu_items
FROM meals m
LEFT JOIN meal_menu_items mi ON m.id = mi.meal_id
WHERE m.date = '2025-01-15'
GROUP BY m.id, m.date, m.dining_time, m.place, m.price, m.kcal
ORDER BY m.dining_time, m.place;

-- 가장 많이 제공된 메뉴 TOP 10
SELECT menu_item, COUNT(*) as count
FROM meal_menu_items
GROUP BY menu_item
ORDER BY count DESC
LIMIT 10;

-- 식당별 평균 칼로리
SELECT place, AVG(kcal) as avg_kcal, AVG(price) as avg_price
FROM meals
GROUP BY place
ORDER BY avg_kcal DESC;
```

## 🔧 환경 변수

### 필수 환경 변수

| 변수명 | 설명 | 예시 | 필수 |
|--------|------|------|------|
| `PORTAL_ID` | 코리아텍 포털 로그인 ID | `2019136000` | ✅ |
| `PORTAL_PW` | 코리아텍 포털 비밀번호 | `mypassword` | ✅ |
| `YOUR_IP_ADDRESS` | 요청 헤더에 사용할 IP | `127.0.0.1` | ✅ |

### 데이터베이스 환경 변수

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `DB_HOST` | 데이터베이스 호스트 | `localhost` | ❌ |
| `DB_PORT` | 데이터베이스 포트 | `5432` | ❌ |
| `DB_NAME` | 데이터베이스 이름 | `kapp` | ❌ |
| `DB_USERNAME` | 데이터베이스 사용자명 | `postgres` | ❌ |
| `DB_PASSWORD` | 데이터베이스 비밀번호 | (없음) | ❌ |
| `DB_SSLMODE` | SSL 연결 모드 | `prefer` | ❌ |

### 환경 변수 파일 위치

```
kapp-config/kapp-scraping/.env
```

이 디렉토리는 Git 서브모듈로 관리되며, 민감한 정보를 안전하게 보관합니다.

## 📚 API 문서

### 인증 엔드포인트

#### 1단계: 로그인 자격증명 확인
```http
POST https://portal.koreatech.ac.kr/ktp/login/checkLoginId.do
Content-Type: application/x-www-form-urlencoded

login_id={PORTAL_ID}&login_pwd={PORTAL_PW}
```

#### 2단계: 2차 로그인 인증
```http
POST https://portal.koreatech.ac.kr/ktp/login/checkSecondLoginCert.do
Content-Type: application/x-www-form-urlencoded

login_id={PORTAL_ID}
```

#### 3단계: SSO 어서션
```http
POST https://portal.koreatech.ac.kr/exsignon/sso/sso_assert.jsp
```

#### 4단계: 최종 SSO 로그인
```http
GET https://kut90.koreatech.ac.kr/ssoLogin_ext.jsp?PGM_ID=CO::CO0998W&locale=ko
```

### 식단 조회 엔드포인트

```http
POST https://kut90.koreatech.ac.kr/nexacroController.do
Content-Type: text/xml; charset=utf-8

<?xml version="1.0" encoding="UTF-8"?>
<Root xmlns="http://www.nexacroplatform.com/platform/dataset">
    <Parameters>
        {쿠키 정보}
        <Parameter id="method">getList_sp</Parameter>
        <Parameter id="sqlid">NK_COT_MEAL_PLAN.NP_SELECT_11</Parameter>
    </Parameters>
    <Dataset id="input1">
        <Row>
            <Col id="EAT_DATE">2025-01-15</Col>
            <Col id="EAT_TYPE">lunch</Col>
            <Col id="RESTURANT">Korean Food (한식)</Col>
            <Col id="CAMPUS">Campus1</Col>
        </Row>
    </Dataset>
</Root>
```

**응답 예시:**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<Root>
    <Parameters>
        <Parameter id="ErrorCode">0</Parameter>
        <Parameter id="ErrorMsg"></Parameter>
    </Parameters>
    <Dataset id="output">
        <Row>
            <Col id="EAT_DATE">2025-01-15</Col>
            <Col id="EAT_TYPE">lunch</Col>
            <Col id="RESTURANT">Korean Food (한식)</Col>
            <Col id="PRICE">5000</Col>
            <Col id="KCAL">650</Col>
            <Col id="DISH">김치찌개
계란말이
밥
김치
650 kcal
5,000 원</Col>
        </Row>
    </Dataset>
</Root>
```

## 🔨 개발 가이드

### 코드 스타일

이 프로젝트는 다음 스타일 가이드를 따릅니다:
- PEP 8 (Python 코드 스타일)
- Google Python Docstring 스타일
- 타입 힌트 사용 (Python 3.8+)

### 새로운 식당 추가하기

`src/kmeal/crawler.py`의 `__init__` 메서드에서 식당 목록을 수정:

```python
def __init__(self, portal_id: str, portal_pw: str, ip_address: str) -> None:
    # ...
    self.campus1_restaurants: List[str] = [
        "Korean Food (한식)",
        "Onedish Food (일품)",
        "Special Food ",
        "Faculty (능수관)",
        "새로운 식당 이름"  # 추가
    ]
```

### 테스트

```bash
# 테스트 모드로 동작 확인
python src/main.py --test

# 로그 파일 확인
tail -f logs/kmeal_scraping_*.log
```

### 디버깅

로그 레벨을 DEBUG로 변경하려면 `src/kmeal/utils.py`에서:

```python
logging.basicConfig(
    level=logging.DEBUG,  # INFO에서 DEBUG로 변경
    # ...
)
```

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. 로그인 실패

**증상:**
```
❌ 포털 로그인 실패 - 쿠키에서 JSESSIONID를 찾을 수 없음
```

**해결 방법:**
- `.env` 파일의 `PORTAL_ID`와 `PORTAL_PW`가 정확한지 확인
- 코리아텍 포털 웹사이트에서 직접 로그인 테스트
- IP 주소가 올바른지 확인

#### 2. 데이터베이스 연결 실패

**증상:**
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**해결 방법:**
```bash
# PostgreSQL 서비스 상태 확인
sudo service postgresql status

# 서비스 시작
sudo service postgresql start

# 연결 테스트
psql -h localhost -U postgres -d kapp
```

#### 3. 모듈을 찾을 수 없음

**증상:**
```
ModuleNotFoundError: No module named 'requests'
```

**해결 방법:**
```bash
# 가상환경이 활성화되어 있는지 확인
which python  # .venv/bin/python 이어야 함

# 의존성 재설치
pip install -r requirements.txt
```

#### 4. 일부 식단 데이터 누락

**증상:**
```
⚠️ Korean Food (한식)의 breakfast 식단 데이터 없음
```

**원인 및 대응:**
- 해당 날짜/시간에 실제로 식단이 없을 수 있음 (정상)
- 네트워크 일시적 오류 (재실행 시도)
- 포털 점검 중 (나중에 재시도)

### 로그 확인

로그 파일에서 상세한 에러 정보 확인:

```bash
# 최신 로그 파일 보기
ls -lt logs/

# 로그 내용 확인
cat logs/kmeal_scraping_20250115_103000.log

# 에러만 필터링
grep "ERROR" logs/kmeal_scraping_*.log
```

## 🤝 기여하기

기여는 언제나 환영합니다! 다음 절차를 따라주세요:

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 기여 가이드라인

- 코드 스타일: PEP 8 준수
- 커밋 메시지: 명확하고 간결하게
- 테스트: 변경사항에 대한 테스트 추가
- 문서화: Docstring 작성 필수

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

```
MIT License

Copyright (c) 2025 Choi-JJunho

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

## 👤 작성자

**Choi-JJunho**

- GitHub: [@Choi-JJunho](https://github.com/Choi-JJunho)

## 📧 문의

프로젝트에 대한 질문이나 제안이 있으시면:

- GitHub Issues: [이슈 생성하기](https://github.com/Choi-JJunho/kapp-scraping/issues)

## 🙏 감사의 말

- 코리아텍 포털 팀에게 API 접근을 허용해주신 점 감사드립니다
- 이 프로젝트를 사용하는 모든 개발자분들께 감사드립니다

## 📝 변경 이력

### v1.0.0 (2025-01-15)
- 🎉 초기 릴리스
- ✨ 코리아텍 식단 크롤링 기능
- 💾 PostgreSQL, CSV, JSON 저장 기능
- 📚 타입 힌트 및 docstring 추가
- 📖 상세한 README.md 작성

---

⭐ 이 프로젝트가 도움이 되었다면 Star를 눌러주세요!
