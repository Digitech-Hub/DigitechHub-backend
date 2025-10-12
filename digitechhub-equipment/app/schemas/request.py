from datetime import datetime
from pydantic import BaseModel, Field

class RentEquipmentRequest(BaseModel):
    """
    기자재 대여 요청 스키마
    """
    due_date: datetime = Field(
        ...,
        description="대여 만료일 (현재 시간보다 이후여야 함)",
        example="2024-01-15T18:00:00",
        json_schema_extra={
            "example": {
                "due_date": "2024-01-15T18:00:00"
            }
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "due_date": "2024-01-15T18:00:00"
            }
        }


class ExtendRentalRequest(BaseModel):
    """
    대여 기간 연장 요청 스키마
    """
    new_due_date: datetime = Field(
        ...,
        description="새로운 대여 만료일 (현재 만료일보다 이후여야 함)",
        example="2024-01-20T18:00:00",
        json_schema_extra={
            "example": {
                "new_due_date": "2024-01-20T18:00:00"
            }
        }
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "new_due_date": "2024-01-20T18:00:00"
            }
        }