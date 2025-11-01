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

	timetables.Get("/health", timetableHandler.GetStatus)
	timetables.Get("/week", timetableHandler.GetThisWeekTimetables)
	timetables.Get("/day", timetableHandler.GetTimetableBySpecificDay)
	timetables.Get("/today", timetableHandler.GetTodayTimetable)
}
