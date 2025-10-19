package entities

import "time"

type Timetable struct {
	ID           int       `json:"id" db:"id"`
	Grade        int       `json:"grade" db:"grade" validate:"required,min=1,max=3"`
	ClassNumber  int       `json:"class_number" db:"class_number" validate:"required,min=1,max=20"`
	Subject      string    `json:"subject" db:"subject" validate:"required,min=1,max=50"`
	DayOfWeek    DayOfWeek `json:"day_of_week" db:"day_of_week" validate:"required"`
	Semester     Semester  `json:"semester" db:"semester" validate:"required"`
	AcademicYear int       `json:"academic_year" db:"academic_year" validate:"required"`
	CreatedAt    time.Time `json:"created_at" db:"created_at"`
	UpdatedAt    time.Time `json:"updated_at" db:"updated_at"`
}
