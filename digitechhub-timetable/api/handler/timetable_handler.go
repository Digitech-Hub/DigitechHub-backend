package handler

import (
	"context"
	"net/http"
	"time"

	"digitechhub-timetable/api/presenter"
	"digitechhub-timetable/pkg/entities"
	"digitechhub-timetable/pkg/timetable"

	"github.com/gofiber/fiber/v2"
	"github.com/rs/zerolog"
)

type TimetableHandler struct {
	service timetable.Service
	logger  zerolog.Logger
}

func NewTimetableHandler(service timetable.Service, logger zerolog.Logger) *TimetableHandler {
	return &TimetableHandler{
		service: service,
		logger:  logger,
	}
}

func (h *TimetableHandler) GetStatus(c *fiber.Ctx) error {
	return c.JSON(presenter.APIResponse{
		Success: true,
		Message: "OK",
	})
}

func (h *TimetableHandler) GetThisWeekTimetables(c *fiber.Ctx) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 쿼리 파라미터 파싱
	grade := c.QueryInt("grade", 0)       // 학년
	classNumber := c.QueryInt("class", 0) // 반

	timetables, err := h.service.GetThisWeekTimetables(ctx, grade, classNumber)

	if err != nil {
		h.logger.Error().Err(err).Msg("failed to get timetables")
		return c.Status(http.StatusInternalServerError).JSON(presenter.APIResponse{
			Success: false,
			Message: "Failed to retrieve timetables",
			Error:   err.Error(),
		})
	}

	return c.JSON(presenter.APIResponse{
		Success: true,
		Message: "Timetables retrieved successfully",
		Data:    timetables,
	})
}

// GetTimetableBySpecificDay - 특정 일의 시간표를 가져오는 핸들러
func (h *TimetableHandler) GetTimetableBySpecificDay(c *fiber.Ctx) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 쿼리 파라미터 파싱
	grade := c.QueryInt("grade", 0)
	classNumber := c.QueryInt("class", 0)
	dayOfWeekStr := c.Query("day", "")
	semester := c.Query("semester", "FIRST")
	year := c.QueryInt("year", time.Now().Year())

	// DayOfWeek 문자열을 enum으로 변환
	var dayOfWeek entities.DayOfWeek
	switch dayOfWeekStr {
	case "MONDAY":
		dayOfWeek = entities.Monday
	case "TUESDAY":
		dayOfWeek = entities.Tuesday
	case "WEDNESDAY":
		dayOfWeek = entities.Wednesday
	case "THURSDAY":
		dayOfWeek = entities.Thursday
	case "FRIDAY":
		dayOfWeek = entities.Friday
	case "SATURDAY":
		dayOfWeek = entities.Saturday
	case "SUNDAY":
		dayOfWeek = entities.Sunday
	default:
		return c.Status(http.StatusBadRequest).JSON(presenter.APIResponse{
			Success: false,
			Message: "Invalid day of week. Must be one of: MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY",
		})
	}

	timetables, err := h.service.GetTimetableBySpecificDay(ctx, grade, classNumber, dayOfWeek, semester, year)
	if err != nil {
		h.logger.Error().Err(err).Msg("failed to get timetable for specific day")
		return c.Status(http.StatusInternalServerError).JSON(presenter.APIResponse{
			Success: false,
			Message: "Failed to retrieve timetable for specific day",
			Error:   err.Error(),
		})
	}

	return c.JSON(presenter.APIResponse{
		Success: true,
		Message: "Timetable for specific day retrieved successfully",
		Data:    timetables,
	})
}

// GetTodayTimetable - 오늘의 시간표를 가져오는 핸들러
func (h *TimetableHandler) GetTodayTimetable(c *fiber.Ctx) error {
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	// 쿼리 파라미터 파싱
	grade := c.QueryInt("grade", 0)
	classNumber := c.QueryInt("class", 0)
	semester := c.Query("semester", "FIRST")
	year := c.QueryInt("year", time.Now().Year())

	timetables, err := h.service.GetTodayTimetable(ctx, grade, classNumber, semester, year)
	if err != nil {
		h.logger.Error().Err(err).Msg("failed to get today's timetable")
		return c.Status(http.StatusInternalServerError).JSON(presenter.APIResponse{
			Success: false,
			Message: "Failed to retrieve today's timetable",
			Error:   err.Error(),
		})
	}

	return c.JSON(presenter.APIResponse{
		Success: true,
		Message: "Today's timetable retrieved successfully",
		Data:    timetables,
	})
}
