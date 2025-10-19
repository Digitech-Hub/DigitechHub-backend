package timetable

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"time"

	"digitechhub-timetable/pkg/entities"

	"github.com/go-playground/validator/v10"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog"
)

// 상수 정의
const (
	baseURL            = "https://open.neis.go.kr/hub/hisTimetable"
	atptOfcdcScCode    = "B10"     // 서울특별시교육청
	sdSchulCode        = "7010572" // 서울디지텍고등학교
	apiTimeout         = 10 * time.Second
	cacheTTL           = 24 * time.Hour
	firstSemesterStart = 3
	firstSemesterEnd   = 8
)

// NEIS API 응답 구조체
type neisResponse struct {
	HisTimetable []neisTimetableWrapper `json:"hisTimetable"`
}

type neisTimetableWrapper struct {
	Head []neisHead           `json:"head"`
	Row  []entities.Timetable `json:"row"`
}

type neisHead struct {
	ListTotalCount int `json:"list_total_count"`
	Result         struct {
		Code    string `json:"CODE"`
		Message string `json:"MESSAGE"`
	} `json:"RESULT"`
}

// 서비스 인터페이스
type Service interface {
	GetThisWeekTimetables(ctx context.Context, grade, classNumber int) ([]entities.Timetable, error)
	GetThisWeekAllTimetables(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]entities.Timetable, error)
	GetTimetableBySpecificDay(ctx context.Context, grade, classNumber int, dayOfWeek entities.DayOfWeek, semester string, academicYear int) ([]entities.Timetable, error)
	GetTodayTimetable(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]entities.Timetable, error)
}

type service struct {
	repository Repository
	validate   *validator.Validate
	logger     zerolog.Logger
	redis      *redis.Client
	neisAPIKey string
	httpClient *http.Client
}

// NewService 새로운 시간표 서비스를 생성합니다
func NewService(repository Repository, logger zerolog.Logger, redis *redis.Client, neisAPIKey string) Service {
	return &service{
		repository: repository,
		validate:   validator.New(),
		logger:     logger,
		redis:      redis,
		neisAPIKey: neisAPIKey,
		httpClient: &http.Client{
			Timeout: apiTimeout,
		},
	}
}

// GetThisWeekTimetables 현재 주의 시간표를 조회합니다
func (s *service) GetThisWeekTimetables(ctx context.Context, grade, classNumber int) ([]entities.Timetable, error) {
	now := time.Now()
	currentYear := now.Year()
	semester := getCurrentSemester(now)

	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("semester", semester).
		Int("academicYear", currentYear).
		Msg("Getting this week's timetables")

	return s.repository.GetTimetables(ctx, grade, classNumber, "", semester, currentYear)
}

// GetThisWeekAllTimetables 현재 주의 모든 시간표를 조회합니다
func (s *service) GetThisWeekAllTimetables(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]entities.Timetable, error) {
	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Getting all timetables for this week")

	return s.repository.GetTimetables(ctx, grade, classNumber, "", semester, academicYear)
}

// GetTimetableBySpecificDay 특정 요일의 시간표를 조회합니다
func (s *service) GetTimetableBySpecificDay(ctx context.Context, grade, classNumber int, dayOfWeek entities.DayOfWeek, semester string, academicYear int) ([]entities.Timetable, error) {
	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Getting timetable for specific day")

	// 1. Redis 캐시 확인
	cacheKey := buildCacheKey(grade, classNumber, string(dayOfWeek), semester, academicYear)
	cachedTimetable, err := s.getTimetableFromCache(ctx, cacheKey)
	if err == nil && cachedTimetable != nil {
		s.logger.Debug().Str("cacheKey", cacheKey).Msg("Cache hit")
		return cachedTimetable, nil
	}

	if err != nil && err != redis.Nil {
		s.logger.Warn().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to get timetable from cache, continuing with DB query")
	}

	// 2. 데이터베이스 확인
	timetable, err := s.repository.GetTimetables(ctx, grade, classNumber, string(dayOfWeek), semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Int("grade", grade).
			Int("classNumber", classNumber).
			Msg("Failed to get timetables from database")
		return nil, fmt.Errorf("failed to get timetables from database: %w", err)
	}

	// 데이터베이스에서 찾은 경우 캐시에 저장하고 반환
	if len(timetable) > 0 {
		if cacheErr := s.cacheTimetable(ctx, cacheKey, timetable); cacheErr != nil {
			s.logger.Warn().
				Err(cacheErr).
				Str("cacheKey", cacheKey).
				Msg("Failed to cache timetable, but continuing")
		}
		return timetable, nil
	}

	// 3. NEIS API에서 조회
	s.logger.Info().Msg("Timetable not found in DB, fetching from NEIS API")
	newTimetable, err := s.fetchFromNeisAPI(ctx, grade, classNumber, semester, academicYear)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch from NEIS API: %w", err)
	}

	// 4. 데이터베이스에 저장하고 캐시에 저장
	if len(newTimetable) > 0 {
		if err := s.saveTimetables(ctx, newTimetable); err != nil {
			s.logger.Error().
				Err(err).
				Msg("Failed to save timetables to database")
			// Don't return error, we still have the data
		}

		if err := s.cacheTimetable(ctx, cacheKey, newTimetable); err != nil {
			s.logger.Warn().
				Err(err).
				Msg("Failed to cache timetable")
		}
	}

	return newTimetable, nil
}

// GetTodayTimetable 오늘의 시간표를 조회합니다
func (s *service) GetTodayTimetable(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]entities.Timetable, error) {
	dayOfWeek := getDayOfWeek(time.Now())

	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Getting today's timetable")

	timetable, err := s.repository.GetTimetables(ctx, grade, classNumber, string(dayOfWeek), semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Msg("Failed to get today's timetable")
		return nil, fmt.Errorf("failed to get today's timetable: %w", err)
	}

	if timetable == nil {
		return []entities.Timetable{}, nil
	}

	return timetable, nil
}

// fetchFromNeisAPI NEIS Open API에서 시간표 데이터를 가져옵니다
func (s *service) fetchFromNeisAPI(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]entities.Timetable, error) {
	requestURL := s.buildNeisAPIURL(academicYear, semester, grade, classNumber)

	s.logger.Debug().
		Str("url", requestURL).
		Msg("Fetching from NEIS API")

	req, err := http.NewRequestWithContext(ctx, http.MethodGet, requestURL, nil)
	if err != nil {
		return nil, fmt.Errorf("failed to create request: %w", err)
	}

	resp, err := s.httpClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("failed to fetch from NEIS API: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil, fmt.Errorf("NEIS API returned status %d", resp.StatusCode)
	}

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, fmt.Errorf("failed to read response body: %w", err)
	}

	var neisResp neisResponse
	if err := json.Unmarshal(body, &neisResp); err != nil {
		return nil, fmt.Errorf("failed to unmarshal NEIS response: %w", err)
	}

	// 응답에 데이터가 있는지 확인
	if len(neisResp.HisTimetable) == 0 {
		s.logger.Warn().Msg("NEIS API returned empty response")
		return []entities.Timetable{}, nil
	}

	// API 오류 확인
	if len(neisResp.HisTimetable[0].Head) > 0 {
		result := neisResp.HisTimetable[0].Head[0].Result
		if result.Code != "INFO-000" {
			s.logger.Error().
				Str("code", result.Code).
				Str("message", result.Message).
				Msg("NEIS API returned error")
			return nil, fmt.Errorf("NEIS API error: %s - %s", result.Code, result.Message)
		}
	}

	timetables := neisResp.HisTimetable[0].Row
	s.logger.Info().
		Int("count", len(timetables)).
		Msg("Successfully fetched timetables from NEIS API")

	return timetables, nil
}

// saveTimetables 여러 시간표를 데이터베이스에 저장합니다
func (s *service) saveTimetables(ctx context.Context, timetables []entities.Timetable) error {
	for i := range timetables {
		if _, err := s.repository.CreateTimetable(ctx, &timetables[i]); err != nil {
			s.logger.Error().
				Err(err).
				Int("index", i).
				Msg("Failed to save timetable")
			return fmt.Errorf("failed to save timetable at index %d: %w", i, err)
		}
	}
	return nil
}

// getTimetableFromCache Redis 캐시에서 시간표를 조회합니다
func (s *service) getTimetableFromCache(ctx context.Context, cacheKey string) ([]entities.Timetable, error) {
	cachedData, err := s.redis.Get(ctx, cacheKey).Result()
	if err != nil {
		return nil, err
	}

	var timetable []entities.Timetable
	if err := json.Unmarshal([]byte(cachedData), &timetable); err != nil {
		s.logger.Error().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to unmarshal cached timetable")
		return nil, err
	}

	return timetable, nil
}

// cacheTimetable 시간표를 Redis 캐시에 저장합니다
func (s *service) cacheTimetable(ctx context.Context, cacheKey string, timetable []entities.Timetable) error {
	encodedData, err := json.Marshal(timetable)
	if err != nil {
		return fmt.Errorf("failed to marshal timetable: %w", err)
	}

	if err := s.redis.Set(ctx, cacheKey, encodedData, cacheTTL).Err(); err != nil {
		return fmt.Errorf("failed to set cache: %w", err)
	}

	return nil
}

// buildNeisAPIURL NEIS API 요청 URL을 구성합니다
func (s *service) buildNeisAPIURL(year int, semester string, grade, class int) string {
	u, err := url.Parse(baseURL)
	if err != nil {
		s.logger.Fatal().Err(err).Msg("Failed to parse base URL")
		return ""
	}

	semesterCode := semesterToCode(semester)

	q := u.Query()
	q.Set("KEY", s.neisAPIKey)
	q.Set("Type", "json")
	q.Set("pIndex", "1")
	q.Set("pSize", "100")
	q.Set("ATPT_OFCDC_SC_CODE", atptOfcdcScCode)
	q.Set("SD_SCHUL_CODE", sdSchulCode)
	q.Set("AY", fmt.Sprintf("%d", year))
	q.Set("SEM", semesterCode)
	q.Set("GRADE", fmt.Sprintf("%d", grade))
	q.Set("CLASS_NM", fmt.Sprintf("%d", class))

	u.RawQuery = q.Encode()
	return u.String()
}

// 헬퍼 함수들

// buildCacheKey 시간표용 캐시 키를 생성합니다
func buildCacheKey(grade, classNumber int, dayOfWeek, semester string, academicYear int) string {
	return fmt.Sprintf("timetable:%d:%d:%s:%s:%d", grade, classNumber, dayOfWeek, semester, academicYear)
}

// getCurrentSemester 날짜를 기준으로 현재 학기를 결정합니다
func getCurrentSemester(date time.Time) string {
	month := date.Month()
	if month >= firstSemesterStart && month <= firstSemesterEnd {
		return "FIRST"
	}
	return "SECOND"
}

// semesterToCode 학기 문자열을 NEIS API 코드로 변환합니다
func semesterToCode(semester string) string {
	if semester == "FIRST" {
		return "1"
	}
	return "2"
}

// getDayOfWeek time.Weekday를 entities.DayOfWeek로 변환합니다
func getDayOfWeek(date time.Time) entities.DayOfWeek {
	switch date.Weekday() {
	case time.Monday:
		return entities.Monday
	case time.Tuesday:
		return entities.Tuesday
	case time.Wednesday:
		return entities.Wednesday
	case time.Thursday:
		return entities.Thursday
	case time.Friday:
		return entities.Friday
	case time.Saturday:
		return entities.Saturday
	case time.Sunday:
		return entities.Sunday
	default:
		return entities.Monday // fallback
	}
}
