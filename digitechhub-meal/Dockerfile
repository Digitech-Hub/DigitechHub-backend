# 멀티 스테이지 빌드로 보안 강화 및 이미지 크기 최적화
FROM node:22-alpine AS build

# 작업 디렉토리 설정
WORKDIR /app

# pnpm 설치 (더 빠른 패키지 관리자)
RUN npm install -g pnpm

# package.json과 pnpm-lock.yaml 복사 (레이어 캐싱 최적화)
COPY package.json pnpm-lock.yaml ./

# 의존성 설치
RUN pnpm install --frozen-lockfile

# 소스 코드 복사
COPY . .

# Prisma 클라이언트 생성
RUN pnpm prisma generate

# 애플리케이션 빌드
RUN pnpm run build

# 런타임 스테이지
FROM node:22-alpine AS runtime

# 보안을 위한 비루트 사용자 생성
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nestjs -u 1001

# 작업 디렉토리 설정
WORKDIR /app

# 키 디렉토리 생성
RUN mkdir -p /app/keys && chown nestjs:nodejs /app/keys

# pnpm 설치
RUN npm install -g pnpm

# 빌드 스테이지에서 필요한 파일들만 복사
COPY --from=build /app/dist ./dist
COPY --from=build /app/node_modules ./node_modules
COPY --from=build /app/package.json ./package.json
COPY --from=build /app/prisma ./prisma

# Prisma 클라이언트 생성 (런타임에서도 필요)
RUN pnpm prisma generate

# 비루트 사용자로 소유권 변경
RUN chown -R nestjs:nodejs /app
USER nestjs

# 포트 노출
EXPOSE 3000

# 환경 변수 설정
ENV NODE_ENV=production
ENV PORT=3000

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=3s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:3000/api/meals/health || exit 1

# 애플리케이션 실행
CMD ["pnpm", "run", "start:prod"]
