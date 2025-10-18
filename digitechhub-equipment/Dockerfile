# Python FastAPI 서비스를 위한 멀티 스테이지 빌드
FROM python:3.12-slim AS build
WORKDIR /app

# 시스템 패키지 업데이트 및 빌드 도구 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    pkg-config \
    default-libmysqlclient-dev \
    && rm -rf /var/lib/apt/lists/*

# pyproject.toml 복사 및 의존성 설치
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
# 소스 코드 복사
COPY . .

# 런타임 스테이지
FROM python:3.12-slim AS runtime

# 보안을 위한 비루트 사용자 생성
RUN groupadd -r appuser --gid=1000 && \
    useradd -r -g appuser --uid=1000 --home-dir=/app --shell=/bin/bash appuser

# 작업 디렉토리 설정
WORKDIR /app

# 키 디렉토리 생성
RUN mkdir -p /app/keys && chown appuser:appuser /app/keys

# 시스템 패키지 업데이트 및 필수 도구 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    libmariadb3 \
    && rm -rf /var/lib/apt/lists/*

# 빌드 스테이지에서 Python 패키지 복사
COPY --from=build --chown=appuser:appuser /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=build --chown=appuser:appuser /usr/local/bin /usr/local/bin

# 소스 코드 복사
COPY --chown=appuser:appuser . .

# 환경 변수 설정
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 비루트 사용자로 전환
USER appuser

# 포트 노출
EXPOSE 3001

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:3001/api/equipments/health || exit 1

# 애플리케이션 실행 (직접 실행, bash 불필요)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3001"]