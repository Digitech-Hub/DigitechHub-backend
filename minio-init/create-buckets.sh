#!/bin/bash

# MinIO 버킷 생성 스크립트
# 이 스크립트는 MinIO 컨테이너가 완전히 시작된 후 실행됩니다.

echo "MinIO 버킷 생성을 시작합니다..."

# MinIO 클라이언트 설치 (mc)
if ! command -v mc &> /dev/null; then
    echo "MinIO 클라이언트를 설치합니다..."
    wget https://dl.min.io/client/mc/release/linux-amd64/mc
    chmod +x mc
    sudo mv mc /usr/local/bin/
fi

# MinIO 서버 연결 설정
echo "MinIO 서버에 연결합니다..."
mc alias set myminio http://localhost:9000 minioadmin minioadmin123

# 버킷 생성
echo "Equipment 버킷을 생성합니다..."
mc mb myminio/equipment --ignore-existing

# 버킷 정책 설정 (공개 읽기)
echo "버킷 정책을 설정합니다..."
mc anonymous set download myminio/equipment

# 버킷 목록 확인
echo "생성된 버킷 목록:"
mc ls myminio

echo "MinIO 버킷 생성이 완료되었습니다!"
