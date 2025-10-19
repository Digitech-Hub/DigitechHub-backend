package routes

import (
	"digitechhub-timetable/api/handler"

	"github.com/gofiber/fiber/v2"
)

func SetupTimetableRoutes(app *fiber.App, timetableHandler *handler.TimetableHandler) {
	api := app.Group("/api")
	v1 := api.Group("/v1")

	timetables := v1.Group("/timetables")
	timetables.Get("/health", timetableHandler.GetStatus)
	timetables.Get("/week", timetableHandler.GetThisWeekTimetables)
	timetables.Get("/day", timetableHandler.GetTimetableBySpecificDay)
	timetables.Get("/today", timetableHandler.GetTodayTimetable)
}
