package presenter

import (
	"digitechhub-timetable/pkg/entities"
	"time"
)

type TimetableRequest struct {
	Grade        int                `json:"grade" validate:"required,min=1,max=3"`
	ClassNumber  int                `json:"class_number" validate:"required,min=1,max=20"`
	Subject      string             `json:"subject" validate:"required,min=1,max=50"`
	DayOfWeek    entities.DayOfWeek `json:"day_of_week" validate:"required"`
	Semester     entities.Semester  `json:"semester" validate:"required"`
	AcademicYear int                `json:"academic_year" validate:"required"`
}

type TimetableResponse struct {
	ID           int                `json:"id"`
	Grade        int                `json:"grade"`
	ClassNumber  int                `json:"class_number"`
	Subject      string             `json:"subject"`
	DayOfWeek    entities.DayOfWeek `json:"day_of_week"`
	Semester     entities.Semester  `json:"semester"`
	AcademicYear int                `json:"academic_year"`
	CreatedAt    time.Time          `json:"created_at"`
	UpdatedAt    time.Time          `json:"updated_at"`
}

// @Description API 응답 공통 구조체
type APIResponse struct {
	Success bool   `json:"success" example:"true" description:"성공 여부"`
	Message string `json:"message" example:"OK" description:"응답 메시지"`
	Data    any    `json:"data,omitempty" description:"응답 데이터"`
	Error   string `json:"error,omitempty" description:"오류 메시지 (실패 시에만 포함)"`
}
