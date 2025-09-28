"""
응답 변환 데코레이터

API 엔드포인트의 응답을 자동으로 표준화된 형태로 변환하는 데코레이터들입니다.
"""

import functools
import inspect
from typing import Any, Callable, Optional, Type, Union

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.utils.response_factory import ResponseFactory


def standardize_response(
    success_message: Optional[str] = None,
    status_code: int = 200,
    include_request: bool = True
):
    """
    API 응답을 표준화된 형태로 변환하는 데코레이터
    
    Args:
        success_message: 성공 시 메시지 (None이면 함수명 기반으로 자동 생성)
        status_code: HTTP 상태 코드
        include_request: Request 객체를 응답 생성에 포함할지 여부
    
    Usage:
        @standardize_response("사용자 정보를 성공적으로 조회했습니다.")
        async def get_user(user_id: int) -> dict:
            return {"id": user_id, "name": "John"}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> JSONResponse:
            try:
                # 함수 실행
                result = await func(*args, **kwargs)
                
                # Request 객체 추출
                request = None
                if include_request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get('request')
                
                # 메시지 생성
                message = success_message
                if not message:
                    message = f"{func.__name__.replace('_', ' ').title()}가 성공적으로 처리되었습니다."
                
                # 응답 생성
                return ResponseFactory.success(
                    data=result,
                    message=message,
                    request=request,
                    status_code=status_code
                )
                
            except Exception as e:
                # 에러 처리
                request = None
                if include_request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get('request')
                
                return ResponseFactory.error(
                    message=f"{func.__name__.replace('_', ' ')} 처리 중 오류가 발생했습니다: {str(e)}",
                    error_code="INTERNAL_ERROR",
                    error_details={"exception": str(e)},
                    request=request,
                    status_code=500
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> JSONResponse:
            try:
                # 함수 실행
                result = func(*args, **kwargs)
                
                # Request 객체 추출
                request = None
                if include_request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get('request')
                
                # 메시지 생성
                message = success_message
                if not message:
                    message = f"{func.__name__.replace('_', ' ').title()}가 성공적으로 처리되었습니다."
                
                # 응답 생성
                return ResponseFactory.success(
                    data=result,
                    message=message,
                    request=request,
                    status_code=status_code
                )
                
            except Exception as e:
                # 에러 처리
                request = None
                if include_request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get('request')
                
                return ResponseFactory.error(
                    message=f"{func.__name__.replace('_', ' ')} 처리 중 오류가 발생했습니다: {str(e)}",
                    error_code="INTERNAL_ERROR",
                    error_details={"exception": str(e)},
                    request=request,
                    status_code=500
                )
        
        # 비동기 함수인지 확인
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def handle_errors(
    error_mappings: Optional[dict] = None,
    default_message: str = "요청 처리 중 오류가 발생했습니다.",
    include_request: bool = True
):
    """
    에러 처리를 위한 데코레이터
    
    Args:
        error_mappings: 에러 타입별 메시지 매핑
        default_message: 기본 에러 메시지
        include_request: Request 객체를 응답 생성에 포함할지 여부
    
    Usage:
        @handle_errors({
            ValueError: "잘못된 값이 입력되었습니다.",
            FileNotFoundError: "파일을 찾을 수 없습니다."
        })
        async def process_file(filename: str):
            # 함수 구현
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Request 객체 추출
                request = None
                if include_request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get('request')
                
                # 에러 메시지 결정
                message = default_message
                if error_mappings:
                    for error_type, error_message in error_mappings.items():
                        if isinstance(e, error_type):
                            message = error_message
                            break
                
                return ResponseFactory.error(
                    message=message,
                    error_code="INTERNAL_ERROR",
                    error_details={"exception": str(e), "type": type(e).__name__},
                    request=request,
                    status_code=500
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Request 객체 추출
                request = None
                if include_request:
                    for arg in args:
                        if isinstance(arg, Request):
                            request = arg
                            break
                    if not request:
                        request = kwargs.get('request')
                
                # 에러 메시지 결정
                message = default_message
                if error_mappings:
                    for error_type, error_message in error_mappings.items():
                        if isinstance(e, error_type):
                            message = error_message
                            break
                
                return ResponseFactory.error(
                    message=message,
                    error_code="INTERNAL_ERROR",
                    error_details={"exception": str(e), "type": type(e).__name__},
                    request=request,
                    status_code=500
                )
        
        # 비동기 함수인지 확인
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def paginate(
    page_param: str = "page",
    per_page_param: str = "per_page",
    default_per_page: int = 10,
    max_per_page: int = 100
):
    """
    페이지네이션을 위한 데코레이터
    
    Args:
        page_param: 페이지 번호 파라미터명
        per_page_param: 페이지당 항목 수 파라미터명
        default_per_page: 기본 페이지당 항목 수
        max_per_page: 최대 페이지당 항목 수
    
    Usage:
        @paginate()
        async def get_items(request: Request, page: int = 1, per_page: int = 10) -> list:
            # 함수 구현
            return items, total_count
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # 페이지네이션 파라미터 추출
            request = None
            page = 1
            per_page = default_per_page
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    # Query 파라미터에서 페이지네이션 정보 추출
                    if hasattr(arg, 'query_params'):
                        page = int(arg.query_params.get(page_param, 1))
                        per_page = min(int(arg.query_params.get(per_page_param, default_per_page)), max_per_page)
                    break
            
            # 함수 실행
            result = await func(*args, **kwargs)
            
            # 결과가 튜플인지 확인 (데이터, 총 개수)
            if isinstance(result, tuple) and len(result) == 2:
                data, total = result
            else:
                # 단일 결과인 경우
                data = result
                total = len(data) if isinstance(data, list) else 1
            
            # 페이지네이션 응답 생성
            return ResponseFactory.paginated(
                data=data,
                page=page,
                per_page=per_page,
                total=total,
                request=request
            )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            # 페이지네이션 파라미터 추출
            request = None
            page = 1
            per_page = default_per_page
            
            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    # Query 파라미터에서 페이지네이션 정보 추출
                    if hasattr(arg, 'query_params'):
                        page = int(arg.query_params.get(page_param, 1))
                        per_page = min(int(arg.query_params.get(per_page_param, default_per_page)), max_per_page)
                    break
            
            # 함수 실행
            result = func(*args, **kwargs)
            
            # 결과가 튜플인지 확인 (데이터, 총 개수)
            if isinstance(result, tuple) and len(result) == 2:
                data, total = result
            else:
                # 단일 결과인 경우
                data = result
                total = len(data) if isinstance(data, list) else 1
            
            # 페이지네이션 응답 생성
            return ResponseFactory.paginated(
                data=data,
                page=page,
                per_page=per_page,
                total=total,
                request=request
            )
        
        # 비동기 함수인지 확인
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


def validate_request(schema: Type):
    """
    요청 검증을 위한 데코레이터
    
    Args:
        schema: Pydantic 스키마 클래스
    
    Usage:
        @validate_request(UserCreateSchema)
        async def create_user(request: Request, user_data: UserCreateSchema):
            # 함수 구현
            pass
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                # Request 객체에서 데이터 추출 및 검증
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request and hasattr(request, 'json'):
                    # JSON 데이터 검증
                    data = await request.json()
                    validated_data = schema(**data)
                    
                    # 검증된 데이터를 kwargs에 추가
                    kwargs['validated_data'] = validated_data
                
                return await func(*args, **kwargs)
                
            except Exception as e:
                return ResponseFactory.error(
                    message=f"요청 데이터 검증에 실패했습니다: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    error_details={"exception": str(e)},
                    request=request,
                    status_code=422
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                # Request 객체에서 데이터 추출 및 검증
                request = None
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
                
                if request and hasattr(request, 'json'):
                    # JSON 데이터 검증 (동기)
                    import asyncio
                    data = asyncio.run(request.json())
                    validated_data = schema(**data)
                    
                    # 검증된 데이터를 kwargs에 추가
                    kwargs['validated_data'] = validated_data
                
                return func(*args, **kwargs)
                
            except Exception as e:
                return ResponseFactory.error(
                    message=f"요청 데이터 검증에 실패했습니다: {str(e)}",
                    error_code="VALIDATION_ERROR",
                    error_details={"exception": str(e)},
                    request=request,
                    status_code=422
                )
        
        # 비동기 함수인지 확인
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
