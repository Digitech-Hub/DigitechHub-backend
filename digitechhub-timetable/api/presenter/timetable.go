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

type APIResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
	Data    any    `json:"data,omitempty"`
	Error   string `json:"error,omitempty"`
}
