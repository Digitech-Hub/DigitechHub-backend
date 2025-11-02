package routes

import (
	"digitechhub-timetable/api/handler"
	"digitechhub-timetable/docs"

	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/swagger"
	"github.com/swaggo/swag"
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
	// 더 구체적인 경로(/docs-json)를 먼저 등록
	timetables.Get("/docs-json", func(c *fiber.Ctx) error {
		c.Set("Content-Type", "application/json")
		swaggerJSON, err := swag.ReadDoc(docs.SwaggerInfo.InstanceName())
		if err != nil {
			return c.Status(500).JSON(fiber.Map{
				"error": "Failed to read swagger docs",
			})
		}
		return c.SendString(swaggerJSON)
	})
	// Swagger UI 정적 리소스를 제공하기 위해 와일드카드 경로 사용
	timetables.Get("/docs/*", swagger.New(swagger.Config{
		URL:         "/api/timetables/docs-json",
		DeepLinking: true,
	}))
	timetables.Get("/docs", swagger.New(swagger.Config{
		URL:         "/api/timetables/docs-json",
		DeepLinking: true,
	}))

	timetables.Get("/health", timetableHandler.GetStatus)
	timetables.Get("/week", timetableHandler.GetThisWeekTimetables)
	timetables.Get("/day", timetableHandler.GetTimetableBySpecificDay)
	timetables.Get("/today", timetableHandler.GetTodayTimetable)
}
