# Digitech Hub SSO

Digitech Hub의 Single Sign-On (SSO) 서버로, 중앙화된 인증 및 인가를 담당하는 Spring Boot 기반 마이크로서비스입니다.

## 📋 프로젝트 개요

- **목적**: Digitech Hub 생태계의 통합 인증 서비스 제공
- **역할**: 사용자 인증, 토큰 발급/검증, 세션 관리
- **아키텍처**: 마이크로서비스 기반 SSO 서버

## 🛠 기술 스택

- **Java**: 17
- **Framework**: Spring Boot 3.5.6
- **Build Tool**: Maven
- **Database**: MySQL 8.0
- **Cache**: Redis 7.2
- **Security**: Spring Security + JWT
- **ORM**: Spring Data JPA
- **기타**: Lombok, DevTools

## 📦 주요 의존성

```xml
- Spring Boot Starter Web
- Spring Boot Starter Security
- Spring Boot Starter Data JPA
- Spring Boot Starter Data Redis
- MySQL Connector
- JJWT (JSON Web Token)
- Lombok
- Spring Boot DevTools
```

## 🏗 프로젝트 구조

```
src/main/java/kr/hs/sdh/digitechhubsso/
├── config/          # 설정 클래스 (Security, Redis, JPA 등)
├── controller/      # REST API 컨트롤러
├── model/          # 엔티티 및 DTO
├── service/        # 비즈니스 로직
└── DigitechhubSsoApplication.java
```

## 🚀 실행 방법

### 1. 사전 요구사항

- Java 17 이상
- Maven 3.6 이상
- Docker & Docker Compose

### 2. 로컬 개발 환경 실행

```bash
# 1. 의존성 설치
mvn clean install

# 2. 애플리케이션 실행
mvn spring-boot:run
```

### 3. Docker 환경 실행

```bash
# 전체 스택 실행 (MySQL + Redis + SSO Server)
docker-compose up -d

# 로그 확인
docker-compose logs -f sso-server
```

## 🗄 데이터베이스

### MySQL 데이터베이스

- **SSO 전용 DB**: `digitechhub_sso`
- **공용 서비스 DB**: `digitechhub_service`

### Redis

- 세션 관리 및 토큰 캐싱
- 포트: 6379

## ⚙️ 설정

### application.properties

```properties
spring.application.name=digitechhub-sso
```

### Docker 환경 변수

```yaml
SPRING_DATASOURCE_URL: jdbc:mysql://mysql:3306/digitechhub_sso
SPRING_DATASOURCE_USERNAME: digitechhub_user
SPRING_DATASOURCE_PASSWORD: user_pass1234!@
SPRING_REDIS_HOST: redis
```

## 🔧 개발 환경

### 포트 설정

- **SSO Server**: 8080
- **MySQL**: 3306
- **Redis**: 6379

### 데이터베이스 접속 정보

- **Host**: localhost (Docker) / localhost:3306 (로컬)
- **Username**: digitechhub_user
- **Password**: user_pass1234!@

## 📝 API 문서

> API 문서는 개발 진행에 따라 업데이트됩니다.

### 주요 엔드포인트

- `POST /api/auth/login` - 사용자 로그인
- `POST /api/auth/logout` - 사용자 로그아웃
- `POST /api/auth/refresh` - 토큰 갱신
- `GET /api/auth/validate` - 토큰 검증
- `POST /api/auth/register` - 사용자 등록

## 🔐 보안 기능

- JWT 기반 토큰 인증
- Spring Security 통합
- Redis를 활용한 세션 관리
- 토큰 만료 및 갱신 메커니즘

## 🧪 테스트

```bash
# 단위 테스트 실행
mvn test

# 통합 테스트 실행
mvn verify
```

## 📈 모니터링

- Spring Boot Actuator (추가 예정)
- 애플리케이션 메트릭 수집
- 헬스 체크 엔드포인트

## 🤝 기여 가이드

1. 이슈 생성 또는 기존 이슈 확인
2. Feature 브랜치 생성
3. 코드 작성 및 테스트
4. Pull Request 생성

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 통해 연락해주세요.

