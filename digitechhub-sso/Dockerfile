# 멀티 스테이지 빌드 - 멀티 플랫폼 지원
# ARM64, AMD64 모두 지원
FROM --platform=$BUILDPLATFORM maven:3.9-eclipse-temurin-17 AS build

# 빌드 인자 선언
ARG TARGETPLATFORM
ARG BUILDPLATFORM

# 작업 디렉토리 설정
WORKDIR /app

# pom.xml 복사 및 의존성 다운로드 (레이어 캐싱 최적화)
COPY pom.xml .
RUN mvn dependency:go-offline -B

# 소스 코드 복사 및 빌드
COPY src ./src
RUN mvn clean package -DskipTests

# 런타임 스테이지 - ARM64/AMD64 모두 네이티브 지원
FROM eclipse-temurin:17-jre-jammy

# 메타데이터
LABEL maintainer="digitechhub"
LABEL description="DigiTechHub SSO Service - Multi-platform support"

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && \
  apt-get install -y --no-install-recommends \
  curl \
  ca-certificates \
  tzdata && \
  # 타임존 설정 (서울)
  ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
  echo "Asia/Seoul" > /etc/timezone && \
  # 캐시 정리
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# 보안을 위한 비루트 사용자 생성
RUN groupadd -r appuser --gid=1000 && \
  useradd -r -g appuser --uid=1000 --home-dir=/app --shell=/bin/bash appuser

# 작업 디렉토리 설정
WORKDIR /app

# 키 디렉토리 생성
RUN mkdir -p /app/keys && chown appuser:appuser /app/keys

# 빌드 스테이지에서 생성된 JAR 파일 복사
COPY --from=build --chown=appuser:appuser /app/target/*.jar /app/digitechhub-sso.jar

# 비루트 사용자로 전환
USER appuser

# 포트 노출
EXPOSE 8080

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8080/api/auth/health || exit 1

# 컨테이너 환경을 위한 JVM 최적화 설정
ENV JAVA_OPTS="-Xmx512m -Xms256m \
  -XX:+UseContainerSupport \
  -XX:MaxRAMPercentage=75.0 \
  -XX:+ExitOnOutOfMemoryError \
  -XX:+HeapDumpOnOutOfMemoryError \
  -XX:HeapDumpPath=/app/heapdump.hprof \
  -Djava.security.egd=file:/dev/./urandom"

# 애플리케이션 실행
ENTRYPOINT ["sh", "-c", "java $JAVA_OPTS -jar digitechhub-sso.jar"]