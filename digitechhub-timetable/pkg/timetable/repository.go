package timetable

import (
	"context"
	"database/sql"
	"fmt"
	"time"

	"digitechhub-timetable/pkg/entities"
	"github.com/jmoiron/sqlx"
	"github.com/rs/zerolog"
)

type Repository interface {
	CreateTimetable(ctx context.Context, timetable *entities.Timetable) (*entities.Timetable, error)
	GetTimetable(ctx context.Context, id int) (*entities.Timetable, error)
	GetTimetables(ctx context.Context, grade, classNumber int, dayOfWeek string, semester string, academicYear int) ([]entities.Timetable, error)
	UpdateTimetable(ctx context.Context, id int, timetable *entities.Timetable) error
	DeleteTimetable(ctx context.Context, id int) error
	GetTimetablesByGradeAndClass(ctx context.Context, grade, classNumber int) ([]entities.Timetable, error)
	GetTimetablesByDay(ctx context.Context, dayOfWeek entities.DayOfWeek) ([]entities.Timetable, error)
	GetTimetablesBySemester(ctx context.Context, semester entities.Semester, academicYear int) ([]entities.Timetable, error)
}

type repository struct {
	db     *sqlx.DB
	logger zerolog.Logger
}

func NewRepository(db *sqlx.DB, logger zerolog.Logger) Repository {
	return &repository{
		db:     db,
		logger: logger,
	}
}

func (r *repository) CreateTimetable(ctx context.Context, timetable *entities.Timetable) (*entities.Timetable, error) {
	query := `INSERT INTO timetables (grade, class_number, subject, day_of_week, semester, academic_year) 
			  VALUES (?, ?, ?, ?, ?, ?)`
	
	result, err := r.db.ExecContext(ctx, query, 
		timetable.Grade, timetable.ClassNumber, timetable.Subject, 
		timetable.DayOfWeek, timetable.Semester, timetable.AcademicYear)
	
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to create timetable")
		return nil, fmt.Errorf("failed to create timetable: %w", err)
	}

	id, _ := result.LastInsertId()
	timetable.ID = int(id)
	timetable.CreatedAt = time.Now()
	timetable.UpdatedAt = time.Now()

	return timetable, nil
}

func (r *repository) GetTimetable(ctx context.Context, id int) (*entities.Timetable, error) {
	var timetable entities.Timetable
	err := r.db.GetContext(ctx, &timetable, "SELECT * FROM timetables WHERE id = ?", id)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, fmt.Errorf("timetable not found")
		}
		r.logger.Error().Err(err).Msg("failed to get timetable")
		return nil, fmt.Errorf("failed to retrieve timetable: %w", err)
	}

	return &timetable, nil
}

func (r *repository) GetTimetables(ctx context.Context, grade, classNumber int, dayOfWeek string, semester string, academicYear int) ([]entities.Timetable, error) {
	query := "SELECT * FROM timetables WHERE 1=1"
	args := []interface{}{}

	if grade > 0 {
		query += " AND grade = ?"
		args = append(args, grade)
	}
	if classNumber > 0 {
		query += " AND class_number = ?"
		args = append(args, classNumber)
	}
	if dayOfWeek != "" {
		query += " AND day_of_week = ?"
		args = append(args, dayOfWeek)
	}
	if semester != "" {
		query += " AND semester = ?"
		args = append(args, semester)
	}
	if academicYear > 0 {
		query += " AND academic_year = ?"
		args = append(args, academicYear)
	}

	query += " ORDER BY grade, class_number, day_of_week"

	var timetables []entities.Timetable
	err := r.db.SelectContext(ctx, &timetables, query, args...)
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to get timetables")
		return nil, fmt.Errorf("failed to retrieve timetables: %w", err)
	}

	return timetables, nil
}

func (r *repository) UpdateTimetable(ctx context.Context, id int, timetable *entities.Timetable) error {
	query := `UPDATE timetables SET grade=?, class_number=?, subject=?, day_of_week=?, semester=?, academic_year=?, updated_at=CURRENT_TIMESTAMP WHERE id=?`
	
	result, err := r.db.ExecContext(ctx, query, 
		timetable.Grade, timetable.ClassNumber, timetable.Subject, 
		timetable.DayOfWeek, timetable.Semester, timetable.AcademicYear, id)
	
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to update timetable")
		return fmt.Errorf("failed to update timetable: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("timetable not found")
	}

	return nil
}

func (r *repository) DeleteTimetable(ctx context.Context, id int) error {
	result, err := r.db.ExecContext(ctx, "DELETE FROM timetables WHERE id = ?", id)
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to delete timetable")
		return fmt.Errorf("failed to delete timetable: %w", err)
	}

	rowsAffected, _ := result.RowsAffected()
	if rowsAffected == 0 {
		return fmt.Errorf("timetable not found")
	}

	return nil
}

func (r *repository) GetTimetablesByGradeAndClass(ctx context.Context, grade, classNumber int) ([]entities.Timetable, error) {
	query := "SELECT * FROM timetables WHERE grade = ? AND class_number = ? ORDER BY day_of_week"
	
	var timetables []entities.Timetable
	err := r.db.SelectContext(ctx, &timetables, query, grade, classNumber)
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to get timetables by grade and class")
		return nil, fmt.Errorf("failed to retrieve timetables by grade and class: %w", err)
	}

	return timetables, nil
}

func (r *repository) GetTimetablesByDay(ctx context.Context, dayOfWeek entities.DayOfWeek) ([]entities.Timetable, error) {
	query := "SELECT * FROM timetables WHERE day_of_week = ? ORDER BY grade, class_number"
	
	var timetables []entities.Timetable
	err := r.db.SelectContext(ctx, &timetables, query, dayOfWeek)
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to get timetables by day")
		return nil, fmt.Errorf("failed to retrieve timetables by day: %w", err)
	}

	return timetables, nil
}

func (r *repository) GetTimetablesBySemester(ctx context.Context, semester entities.Semester, academicYear int) ([]entities.Timetable, error) {
	query := "SELECT * FROM timetables WHERE semester = ? AND academic_year = ? ORDER BY grade, class_number, day_of_week"
	
	var timetables []entities.Timetable
	err := r.db.SelectContext(ctx, &timetables, query, semester, academicYear)
	if err != nil {
		r.logger.Error().Err(err).Msg("failed to get timetables by semester")
		return nil, fmt.Errorf("failed to retrieve timetables by semester: %w", err)
	}

	return timetables, nil
}
