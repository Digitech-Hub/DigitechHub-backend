"""
JWT 토큰 검증 유틸리티

SSO 서버에서 발급한 JWT 토큰을 Public Key를 사용하여 검증합니다.
"""

import jwt
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


class JWTAuth:
    """
    JWT 토큰 검증 클래스
    """
    
    def __init__(self, public_key_path: str = "keys/public_key.pem"):
        """
        JWT 검증기 초기화
        
        Args:
            public_key_path: Public Key 파일 경로
        """
        self.public_key_path = public_key_path
        self._public_key = None
    
    def _load_public_key(self) -> bytes:
        """
        Public Key 파일을 로드합니다.
        
        Returns:
            bytes: Public Key 데이터
        """
        if self._public_key is None:
            try:
                # 프로젝트 루트에서 키 파일 찾기
                key_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), self.public_key_path)
                
                with open(key_file, 'rb') as key_file:
                    self._public_key = key_file.read()
            except FileNotFoundError:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Public key file not found"
                )
            except Exception as e:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to load public key: {str(e)}"
                )
        
        return self._public_key
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        JWT 토큰을 검증하고 페이로드를 반환합니다.
        
        Args:
            token: JWT 토큰 문자열
            
        Returns:
            Dict[str, Any]: 토큰 페이로드
            
        Raises:
            HTTPException: 토큰이 유효하지 않은 경우
        """
        try:
            public_key_data = self._load_public_key()
            
            # Public Key 객체 생성
            public_key = serialization.load_pem_public_key(public_key_data)
            
            # 토큰 검증 및 디코딩
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],
                options={"verify_exp": True, "verify_signature": True}
            )
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.InvalidTokenError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token verification failed: {str(e)}"
            )
    
    def get_user_info(self, token: str) -> Dict[str, Any]:
        """
        토큰에서 사용자 정보를 추출합니다.
        
        Args:
            token: JWT 토큰 문자열
            
        Returns:
            Dict[str, Any]: 사용자 정보 (username, userId, role 등)
        """
        payload = self.verify_token(token)
        
        return {
            "username": payload.get("sub"),
            "userId": payload.get("userId"),
            "role": payload.get("role"),
            "issued_at": payload.get("iat"),
            "expires_at": payload.get("exp")
        }


# 전역 JWT 검증기 인스턴스
jwt_auth = JWTAuth()
