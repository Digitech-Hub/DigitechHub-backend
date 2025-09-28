# DigiTech Hub Equipment API

> 장비 관리 시스템을 위한 마이크로서비스 API

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.117+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0+-red.svg)](https://www.sqlalchemy.org/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## 📋 목차

- [개요](#개요)
- [주요 기능](#주요-기능)
- [기술 스택](#기술-스택)
- [설치 및 실행](#설치-및-실행)
- [프로젝트 구조](#프로젝트-구조)
- [API 문서](#api-문서)
- [데이터베이스](#데이터베이스)
- [개발 가이드](#개발-가이드)
- [기여하기](#기여하기)

## 🎯 개요

DigiTech Hub Equipment API는 교육 기관의 장비 및 기자재를 효율적으로 관리하기 위한 마이크로서비스입니다. 학생과 교직원이 장비를 대여하고 반납할 수 있는 시스템을 제공합니다.

### 주요 특징

- 🚀 **FastAPI 기반**: 높은 성능과 자동 API 문서 생성
- 🔒 **타입 안전성**: SQLAlchemy 2.0과 Pydantic을 통한 타입 힌트 지원
- 📊 **UUID 기반**: 분산 시스템에 적합한 고유 식별자
- 🔄 **자동 타임스탬프**: 생성/수정 시간 자동 관리
- 📝 **구조화된 로깅**: 체계적인 로그 관리 시스템

## ✨ 주요 기능

### 장비 관리
- 장비 등록, 수정, 삭제
- 장비 상태 관리 (사용 가능, 대여 중, 고장, 수리 중)
- 장비 유형별 분류 및 관리

### 대여 시스템
- 장비 대여 및 반납 처리
- 대여 이력 추적 및 관리
- 사용자별 대여 기록 조회

### 관리 기능
- 실시간 장비 현황 모니터링
- 대여 통계 및 분석
- 관리자 전용 기능

## 🛠 기술 스택

### Backend
- **FastAPI**: 현대적이고 빠른 웹 프레임워크
- **SQLAlchemy 2.0**: ORM 및 데이터베이스 추상화
- **Pydantic**: 데이터 검증 및 직렬화
- **Uvicorn**: ASGI 서버

### Database
- **MySQL 8.0**: 메인 데이터베이스
- **PyMySQL**: MySQL 연결 드라이버

### Development Tools
- **uv**: 빠른 Python 패키지 관리자
- **Python 3.12+**: 최신 Python 기능 활용

## 🚀 설치 및 실행

### 사전 요구사항

- Python 3.12 이상
- MySQL 8.0 이상
- uv 패키지 관리자

### 1. 저장소 클론

```bash
git clone <repository-url>
cd digitech-hub/backend/digitechhub-equipment
```

### 2. 가상환경 설정 및 의존성 설치

```bash
# uv를 사용한 의존성 설치
uv sync

# 또는 pip 사용 시
pip install -e .
```

### 3. 환경 변수 설정

```bash
# .env 파일 생성 (선택사항)
export DATABASE_URL="mysql+pymysql://digitechhub_equipment_user:digitechhub_equipment!!1234@localhost:3307/digitechhub_equipment"
export HOST="0.0.0.0"
export PORT="8000"
export ENVIRONMENT="development"
```

### 4. 데이터베이스 설정

MySQL 데이터베이스가 실행 중인지 확인하고, 필요한 테이블들이 자동으로 생성됩니다.

### 5. 서버 실행

#### 개발 모드 (권장)

```bash
# uv 사용
uv run fastapi dev app/main.py --host 0.0.0.0 --port 8000

# 또는 직접 실행
uv run python -m app.main
```

#### 프로덕션 모드

```bash
# uv 사용
uv run fastapi run app/main.py --host 0.0.0.0 --port 8000

# 또는 uvicorn 직접 사용
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 6. 서버 확인

서버가 성공적으로 실행되면 다음 URL에서 확인할 수 있습니다:

- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **ReDoc 문서**: http://localhost:8000/redoc
- **헬스체크**: http://localhost:8000/health

## 📁 프로젝트 구조

```
digitechhub-equipment/
├── app/                          # 애플리케이션 코드
│   ├── __init__.py
│   ├── main.py                   # FastAPI 애플리케이션 진입점
│   ├── models/                   # 데이터베이스 모델
│   │   ├── __init__.py
│   │   ├── abstract_base.py      # 기본 모델 클래스
│   │   ├── equipment.py          # 장비 모델
│   │   ├── equipemnt_type.py     # 장비 유형 모델
│   │   └── rental_history.py     # 대여 이력 모델
│   ├── routers/                  # API 라우터 (향후 확장)
│   ├── schemas/                  # Pydantic 스키마 (향후 확장)
│   ├── services/                 # 비즈니스 로직 (향후 확장)
│   ├── crud/                     # CRUD 작업 (향후 확장)
│   ├── utils/                    # 유틸리티 함수
│   │   ├── __init__.py
│   │   ├── database.py           # 데이터베이스 설정
│   │   ├── dependencies.py       # 의존성 주입
│   │   └── logger.py             # 로깅 설정
│   ├── configs/                  # 설정 파일 (향후 확장)
│   ├── constants/                # 상수 정의 (향후 확장)
│   └── exceptions/               # 예외 처리 (향후 확장)
├── pyproject.toml                # 프로젝트 설정 및 의존성
├── uv.lock                       # 의존성 잠금 파일
├── .python-version               # Python 버전 지정
└── README.md                     # 프로젝트 문서
```

## 📚 API 문서

### 기본 엔드포인트

| 메서드 | 엔드포인트 | 설명 |
|--------|------------|------|
| GET | `/` | API 정보 |
| GET | `/health` | 헬스체크 |
| GET | `/docs` | Swagger UI 문서 |
| GET | `/redoc` | ReDoc 문서 |

### 예시 응답

#### 헬스체크
```json
{
  "status": "healthy",
  "message": "DigiTech Hub Equipment API is running",
  "version": "0.1.0"
}
```

## 🗄 데이터베이스

### 테이블 구조

#### Equipment (장비)
- `id`: UUID 기본 키
- `alias`: 장비 별칭
- `status`: 장비 상태 (available, checked_out, broken, fixing)
- `equipment_type_id`: 장비 유형 ID (외래 키)
- `is_public`: 공개 여부
- `admin_comment`: 관리자 전용 코멘트
- `created_at`: 생성 시간
- `updated_at`: 수정 시간

#### EquipmentType (장비 유형)
- `id`: UUID 기본 키
- `name`: 장비 유형 이름
- `description`: 장비 유형 설명
- `is_public`: 공개 여부
- `comment`: 추가 설명
- `equipment_image`: 장비 이미지 URL
- `created_at`: 생성 시간
- `updated_at`: 수정 시간

#### RentalHistory (대여 이력)
- `id`: UUID 기본 키
- `equipment_id`: 장비 ID (외래 키)
- `user_id`: 사용자 ID
- `rental_date`: 대여 날짜
- `return_date`: 반납 날짜
- `is_returned`: 반납 여부
- `created_at`: 생성 시간
- `updated_at`: 수정 시간

### 관계

- Equipment ↔ EquipmentType: 다대일 관계
- Equipment ↔ RentalHistory: 일대다 관계

## 🔧 개발 가이드

### 코드 스타일

- **타입 힌트**: 모든 함수와 변수에 타입 힌트 사용
- **독스트링**: 한국어 독스트링으로 가독성 향상
- **로깅**: 구조화된 로깅 시스템 사용
- **에러 처리**: 적절한 예외 처리 및 로깅

### 새로운 기능 추가

1. **모델 추가**: `app/models/` 디렉토리에 새 모델 파일 생성
2. **스키마 추가**: `app/schemas/` 디렉토리에 Pydantic 스키마 정의
3. **라우터 추가**: `app/routers/` 디렉토리에 API 엔드포인트 정의
4. **서비스 추가**: `app/services/` 디렉토리에 비즈니스 로직 구현

### 테스트

```bash
# 테스트 실행 (향후 구현 예정)
uv run pytest

# 테스트 커버리지 (향후 구현 예정)
uv run pytest --cov=app
```

### 로깅

애플리케이션은 구조화된 로깅 시스템을 사용합니다:

```python
from app.utils.logger import logger

logger.info("정보 메시지")
logger.warning("경고 메시지")
logger.error("에러 메시지")
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### 기여 가이드라인

- 코드 스타일을 일관되게 유지해주세요
- 새로운 기능 추가 시 테스트를 포함해주세요
- 독스트링과 타입 힌트를 적절히 사용해주세요
- 커밋 메시지는 명확하고 간결하게 작성해주세요


## 🚀 향후 계획

- [ ] 인증 및 권한 관리 시스템
- [ ] 실시간 알림 시스템
- [ ] 장비 예약 시스템
- [ ] 대시보드 및 분석 기능
- [ ] 모바일 앱 지원
- [ ] 다국어 지원


