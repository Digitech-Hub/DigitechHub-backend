// main.go
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
package main

import (
	"context"
	"errors"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"digitechhub-timetable/api/handler"
	"digitechhub-timetable/api/routes"
	"digitechhub-timetable/pkg/timetable"
	
	_ "digitechhub-timetable/docs"

	_ "github.com/go-sql-driver/mysql"
	"github.com/gofiber/fiber/v2"
	"github.com/gofiber/fiber/v2/middleware/cors"
	"github.com/gofiber/fiber/v2/middleware/limiter"
	fiberlogger "github.com/gofiber/fiber/v2/middleware/logger"
	"github.com/gofiber/fiber/v2/middleware/recover"
	"github.com/gofiber/fiber/v2/middleware/requestid"
	"github.com/jmoiron/sqlx"
	"github.com/joho/godotenv"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
)

const (
	defaultPort           = "3002"
	defaultEnv            = "development"
	dbConnectTimeout      = 5 * time.Second
	serverShutdownTimeout = 15 * time.Second
)

type Config struct {
	Port         string
	Env          string
	DatabaseDSN  string
	AllowOrigins string
	RedisURL     string
	NeisAPIKey   string
}

type Server struct {
	app    *fiber.App
	db     *sqlx.DB
	redis  *redis.Client
	config Config
	logger zerolog.Logger
}

func init() {
	// .env 파일 로드, .env가 존재하지 않는다면 환경변수 로딩
	if err := godotenv.Load(); err != nil {
		fmt.Fprintln(os.Stderr, "⚠️  .env not found — using environment variables")
	}
}

func loadConfig() (Config, error) {
	cfg := Config{
		Port:         getEnv("PORT", defaultPort),
		Env:          getEnv("ENVIRONMENT", defaultEnv),
		DatabaseDSN:  getEnv("DATABASE_DSN", "digitechhub_timetable_user:digitechhubtimetable1234@digitechhub-mysql:3306/digitechhub_timetable?parseTime=true&loc=Local"),
		AllowOrigins: getEnv("ALLOW_ORIGINS", "http://localhost:5173"),
		RedisURL:     getEnv("REDIS_URL", "redis://digitechhub-redis:6379"),
		NeisAPIKey:   getEnv("NEIS_API_KEY", ""),
	}

	if cfg.Env == "production" && cfg.DatabaseDSN == "" {
		return cfg, errors.New("DATABASE_DSN is required in production")
	}

	if cfg.Env == "production" && cfg.NeisAPIKey == "" {
		return cfg, errors.New("NEIS_API_KEY is required in production")
	}

	return cfg, nil
}

func getEnv(key, fallback string) string {
	if v := strings.TrimSpace(os.Getenv(key)); v != "" {
		return v
	}
	return fallback
}

func newLogger(env string) zerolog.Logger {
	if env == "production" {
		zerolog.SetGlobalLevel(zerolog.InfoLevel)
		return log.Output(zerolog.ConsoleWriter{Out: os.Stdout}).With().Timestamp().Logger()
	}
	zerolog.SetGlobalLevel(zerolog.DebugLevel)
	console := zerolog.ConsoleWriter{Out: os.Stderr, TimeFormat: time.RFC3339}
	return zerolog.New(console).With().Timestamp().Logger()
}

func connectDB(dsn string, logger zerolog.Logger) (*sqlx.DB, error) {
	if dsn == "" {
		return nil, errors.New("empty DSN")
	}

	db, err := sqlx.Open("mysql", dsn)
	if err != nil {
		return nil, fmt.Errorf("open db: %w", err)
	}

	db.SetMaxOpenConns(25)
	db.SetMaxIdleConns(10)
	db.SetConnMaxLifetime(30 * time.Minute)

	ctx, cancel := context.WithTimeout(context.Background(), dbConnectTimeout)
	defer cancel()
	if err := db.PingContext(ctx); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("ping db: %w", err)
	}

	logger.Info().Msg("Connected to database")
	return db, nil
}

func connectRedis(redisURL string, logger zerolog.Logger) (*redis.Client, error) {
	if redisURL == "" {
		return nil, errors.New("empty Redis URL")
	}

	opt, err := redis.ParseURL(redisURL)
	if err != nil {
		return nil, fmt.Errorf("parse redis url: %w", err)
	}

	client := redis.NewClient(opt)

	ctx, cancel := context.WithTimeout(context.Background(), dbConnectTimeout)
	defer cancel()

	if err := client.Ping(ctx).Err(); err != nil {
		_ = client.Close()
		return nil, fmt.Errorf("ping redis: %w", err)
	}

	logger.Info().Msg("Connected to Redis")
	return client, nil
}

func NewServer(cfg Config) (*Server, error) {
	logger := newLogger(cfg.Env)

	db, err := connectDB(cfg.DatabaseDSN, logger)
	if err != nil {
		logger.Error().Err(err).Msg("database connection failed")
		return nil, err
	}

	redisClient, err := connectRedis(cfg.RedisURL, logger)
	if err != nil {
		logger.Error().Err(err).Msg("redis connection failed")
		_ = db.Close()
		return nil, err
	}

	app := fiber.New(fiber.Config{
		CaseSensitive:         true,
		AppName:               "Digitechhub Timetable MicroService",
		DisableStartupMessage: cfg.Env == "production",
	})

	s := &Server{
		app:    app,
		db:     db,
		redis:  redisClient,
		config: cfg,
		logger: logger,
	}

	s.setupMiddleware()
	s.setupRoutes()

	logger.Info().Str("port", cfg.Port).Str("env", cfg.Env).Msg("server instance created")
	return s, nil
}

func (s *Server) setupMiddleware() {
	s.app.Use(recover.New())

	s.app.Use(requestid.New())

	s.app.Use(cors.New(cors.Config{
		AllowOrigins:     s.config.AllowOrigins,
		AllowCredentials: true,
		AllowMethods:     "GET,POST,PUT,DELETE,OPTIONS",
		AllowHeaders:     "Origin, Content-Type, Accept, Authorization",
		MaxAge:           3600,
	}))

	s.app.Use(limiter.New(limiter.Config{
		Max:        100,
		Expiration: 1 * time.Minute,
		KeyGenerator: func(c *fiber.Ctx) string {
			return c.IP()
		},
		LimitReached: func(c *fiber.Ctx) error {
			return c.Status(http.StatusTooManyRequests).JSON(fiber.Map{
				"error": "rate limit exceeded",
			})
		},
	}))

	s.app.Use(fiberlogger.New(fiberlogger.Config{
		Format:     `{"time":"${time}","id":"${locals:requestid}","ip":"${ip}","method":"${method}","path":"${path}","status":${status},"latency":"${latency}","bytes":"${bytes}"}%n`,
		TimeFormat: time.RFC3339,
		TimeZone:   "Asia/Seoul",
	}))
}

func (s *Server) setupRoutes() {
	// 레포지토리 초기화
	timetableRepository := timetable.NewRepository(s.db, s.logger)
	// 서비스 초기화
	timetableService := timetable.NewService(timetableRepository, s.logger, s.redis, s.config.NeisAPIKey)
	// 핸들러 초기화
	timetableHandler := handler.NewTimetableHandler(timetableService, s.logger)
	// 라우팅
	routes.SetupTimetableRoutes(s.app, timetableHandler)
}

func (s *Server) Start() error {
	addr := fmt.Sprintf(":%s", s.config.Port)
	s.logger.Info().Str("addr", addr).Msg("starting server")
	return s.app.Listen(addr)
}

func (s *Server) Shutdown(ctx context.Context) error {
	s.logger.Info().Msg("shutting down server")
	shutdownErr := make(chan error, 1)

	go func() {
		if err := s.app.ShutdownWithContext(ctx); err != nil {
			shutdownErr <- err
			return
		}
		if s.db != nil {
			if err := s.db.Close(); err != nil {
				shutdownErr <- fmt.Errorf("db close: %w", err)
				return
			}
		}
		if s.redis != nil {
			if err := s.redis.Close(); err != nil {
				shutdownErr <- fmt.Errorf("redis close: %w", err)
				return
			}
		}
		shutdownErr <- nil
	}()

	select {
	case <-ctx.Done():
		return ctx.Err()
	case err := <-shutdownErr:
		return err
	}
}

func main() {
	cfg, err := loadConfig()
	if err != nil {
		fmt.Fprintf(os.Stderr, "config error: %v\n", err)
		os.Exit(1)
	}

	server, err := NewServer(cfg)
	if err != nil {
		fmt.Fprintf(os.Stderr, "server init error: %v\n", err)
		os.Exit(1)
	}

	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGINT, syscall.SIGTERM)

	go func() {
		<-stop
		ctx, cancel := context.WithTimeout(context.Background(), serverShutdownTimeout)
		defer cancel()
		if err := server.Shutdown(ctx); err != nil {
			server.logger.Error().Err(err).Msg("error during shutdown")
		} else {
			server.logger.Info().Msg("shutdown complete")
		}
	}()

	if err := server.Start(); err != nil && !errors.Is(err, http.ErrServerClosed) {
		server.logger.Fatal().Err(err).Msg("server error")
	}
}
