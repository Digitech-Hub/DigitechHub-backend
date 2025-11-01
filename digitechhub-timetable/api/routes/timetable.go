package routes

import (
	"digitechhub-timetable/api/handler"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/swagger"
)

// @title Digitech Hub Timetable API
// @version 1.0
// @description 서울디지텍고등학교 시간표 조회 API
// @termsOfService http://swagger.io/terms/

// @contact.name API Support
// @contact.url http://www.swagger.io/support
// @contact.email support@swagger.io

// @license.name Apache 2.0
// @license.url http://www.apache.org/licenses/LICENSE-2.0.html

// @host localhost:3002
// @BasePath /api
// @schemes http https

func SetupTimetableRoutes(app *fiber.App, timetableHandler *handler.TimetableHandler) {
	api := app.Group("/api")

	timetables := api.Group("/timetables")
	
	// Swagger 문서 엔드포인트
	app.Get("/docs/*", swagger.HandlerDefault)
	timetables.Get("/docs/*", swagger.HandlerDefault)

	// @Summary Health Check
	// @Description 서비스 상태 확인
	// @Tags Health
	// @Accept json
	// @Produce json
	// @Success 200 {object} presenter.APIResponse
	// @Router /timetables/health [get]
	timetables.Get("/health", timetableHandler.GetStatus)

	// @Summary 주간 시간표 조회
	// @Description 현재 주의 시간표를 조회합니다
	// @Tags Timetable
	// @Accept json
	// @Produce json
	// @Param grade query int true "학년 (1-3)"
	// @Param class query int true "반 (1-20)"
	// @Success 200 {object} presenter.APIResponse{data=[]timetable.SubjectInfo}
	// @Failure 400 {object} presenter.APIResponse
	// @Failure 500 {object} presenter.APIResponse
	// @Router /timetables/week [get]
	timetables.Get("/week", timetableHandler.GetThisWeekTimetables)

	// @Summary 특정 요일 시간표 조회
	// @Description 특정 요일의 시간표를 조회합니다
	// @Tags Timetable
	// @Accept json
	// @Produce json
	// @Param grade query int true "학년 (1-3)"
	// @Param class query int true "반 (1-20)"
	// @Param day query string true "요일" Enums(MONDAY, TUESDAY, WEDNESDAY, THURSDAY, FRIDAY, SATURDAY, SUNDAY)
	// @Param semester query string false "학기" Enums(FIRST, SECOND)
	// @Param year query int false "학년도" default(2025)
	// @Success 200 {object} presenter.APIResponse{data=[]timetable.SubjectInfo}
	// @Failure 400 {object} presenter.APIResponse
	// @Failure 500 {object} presenter.APIResponse
	// @Router /timetables/day [get]
	timetables.Get("/day", timetableHandler.GetTimetableBySpecificDay)

	// @Summary 오늘 시간표 조회
	// @Description 오늘의 시간표를 조회합니다
	// @Tags Timetable
	// @Accept json
	// @Produce json
	// @Param grade query int true "학년 (1-3)"
	// @Param class query int true "반 (1-20)"
	// @Param semester query string false "학기" Enums(FIRST, SECOND)
	// @Param year query int false "학년도" default(2025)
	// @Success 200 {object} presenter.APIResponse{data=[]timetable.SubjectInfo}
	// @Failure 400 {object} presenter.APIResponse
	// @Failure 500 {object} presenter.APIResponse
	// @Router /timetables/today [get]
	timetables.Get("/today", timetableHandler.GetTodayTimetable)
}
