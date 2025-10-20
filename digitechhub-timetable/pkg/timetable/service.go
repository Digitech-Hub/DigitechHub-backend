package timetable

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"strings"
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

// NEIS API 응답용 시간표 구조체 (필드 타입이 다를 수 있음)
type neisTimetable struct {
	Grade        string `json:"GRADE"`
	ClassNumber  string `json:"CLASS_NM"`
	Subject      string `json:"ITRT_CNTNT"`
	Date         string `json:"ALL_TI_YMD"`
	Semester     string `json:"SEM"`
	AcademicYear string `json:"AY"`
}

// 과목 정보만 담는 간단한 구조체
// @Description 과목 정보
type SubjectInfo struct {
	Subject string `json:"subject" example:"공업 일반" description:"과목명"`
}

// 서비스 인터페이스
type Service interface {
	GetThisWeekTimetables(ctx context.Context, grade, classNumber int) ([]SubjectInfo, error)
	GetTimetableBySpecificDay(ctx context.Context, grade, classNumber int, dayOfWeek entities.DayOfWeek, semester string, academicYear int) ([]SubjectInfo, error)
	GetTodayTimetable(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]SubjectInfo, error)
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
func (s *service) GetThisWeekTimetables(ctx context.Context, grade, classNumber int) ([]SubjectInfo, error) {
	now := time.Now()
	currentYear := now.Year()
	semester := getCurrentSemester(now)

	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("semester", semester).
		Int("academicYear", currentYear).
		Msg("Getting this week's timetables")

	// 1. Redis 캐시 확인 (주간 시간표는 모든 요일 포함)
	cacheKey := buildCacheKey(grade, classNumber, "WEEK", semester, currentYear)
	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Msg("Checking Redis cache for week timetables")
	
	cachedTimetable, err := s.getTimetableFromCache(ctx, cacheKey)
	if err == nil && cachedTimetable != nil {
		s.logger.Info().
			Str("cacheKey", cacheKey).
			Int("cachedCount", len(cachedTimetable)).
			Msg("Cache hit for week timetables")
		return s.convertTimetablesToSubjects(cachedTimetable), nil
	}

	if err == redis.Nil {
		s.logger.Debug().
			Str("cacheKey", cacheKey).
			Msg("Cache miss for week timetables")
	} else if err != nil {
		s.logger.Warn().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to get week timetables from cache, continuing with DB query")
	}

	// 2. 데이터베이스 확인
	s.logger.Debug().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("semester", semester).
		Int("academicYear", currentYear).
		Msg("Querying database for week timetables")
	
	timetable, err := s.repository.GetTimetables(ctx, grade, classNumber, "", semester, currentYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Int("grade", grade).
			Int("classNumber", classNumber).
			Msg("Failed to get week timetables from database")
		return nil, fmt.Errorf("failed to get week timetables from database: %w", err)
	}

	s.logger.Debug().
		Int("dbResultCount", len(timetable)).
		Msg("Database query completed for week timetables")

	// 데이터베이스에서 찾은 경우 캐시에 저장하고 반환
	if len(timetable) > 0 {
		s.logger.Info().
			Int("foundCount", len(timetable)).
			Msg("Found week timetables in database, caching results")
		
		// entities.Timetable을 SubjectInfo로 변환
		subjects := s.convertTimetablesToSubjects(timetable)
		
		if cacheErr := s.cacheTimetable(ctx, cacheKey, timetable); cacheErr != nil {
			s.logger.Warn().
				Err(cacheErr).
				Str("cacheKey", cacheKey).
				Msg("Failed to cache week timetables, but continuing")
		} else {
			s.logger.Debug().
				Str("cacheKey", cacheKey).
				Msg("Successfully cached week timetables")
		}
		return subjects, nil
	}

	// 3. NEIS API에서 조회
	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("semester", semester).
		Int("academicYear", currentYear).
		Msg("Week timetables not found in DB, fetching from NEIS API")
	
	newTimetable, err := s.fetchFromNeisAPI(ctx, grade, classNumber, semester, currentYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Msg("Failed to fetch week timetables from NEIS API")
		return nil, fmt.Errorf("failed to fetch week timetables from NEIS API: %w", err)
	}

	s.logger.Info().
		Int("apiResultCount", len(newTimetable)).
		Msg("Successfully fetched week timetables from NEIS API")

	// 4. 데이터베이스에 저장하고 캐시에 저장
	if len(newTimetable) > 0 {
		s.logger.Debug().
			Int("saveCount", len(newTimetable)).
			Msg("Saving week timetables to database")
		
		if err := s.saveTimetables(ctx, newTimetable); err != nil {
			s.logger.Error().
				Err(err).
				Msg("Failed to save week timetables to database")
			// Don't return error, we still have the data
		} else {
			s.logger.Info().
				Int("savedCount", len(newTimetable)).
				Msg("Successfully saved week timetables to database")
		}

		s.logger.Debug().
			Str("cacheKey", cacheKey).
			Msg("Caching week timetables from NEIS API")
		
		if err := s.cacheTimetable(ctx, cacheKey, newTimetable); err != nil {
			s.logger.Warn().
				Err(err).
				Str("cacheKey", cacheKey).
				Msg("Failed to cache week timetables from NEIS API")
		} else {
			s.logger.Debug().
				Str("cacheKey", cacheKey).
				Msg("Successfully cached week timetables from NEIS API")
		}
		
		// SubjectInfo로 변환하여 반환
		return s.convertTimetablesToSubjects(newTimetable), nil
	} else {
		s.logger.Warn().Msg("No week timetables returned from NEIS API")
		return []SubjectInfo{}, nil
	}
}

// GetTimetableBySpecificDay 특정 요일의 시간표를 조회합니다
func (s *service) GetTimetableBySpecificDay(ctx context.Context, grade, classNumber int, dayOfWeek entities.DayOfWeek, semester string, academicYear int) ([]SubjectInfo, error) {
	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Getting timetable for specific day")

	// 1. Redis 캐시 확인
	cacheKey := buildCacheKey(grade, classNumber, string(dayOfWeek), semester, academicYear)
	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Str("dayOfWeek", string(dayOfWeek)).
		Msg("Checking Redis cache for specific day timetable")
	
	cachedTimetable, err := s.getTimetableFromCache(ctx, cacheKey)
	if err == nil && cachedTimetable != nil {
		s.logger.Info().
			Str("cacheKey", cacheKey).
			Int("cachedCount", len(cachedTimetable)).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Cache hit for specific day timetable")
		return s.convertTimetablesToSubjects(cachedTimetable), nil
	}

	if err == redis.Nil {
		s.logger.Debug().
			Str("cacheKey", cacheKey).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Cache miss for specific day timetable")
	} else if err != nil {
		s.logger.Warn().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to get specific day timetable from cache, continuing with DB query")
	}

	// 2. 데이터베이스 확인
	s.logger.Debug().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Querying database for specific day timetable")
	
	timetable, err := s.repository.GetTimetables(ctx, grade, classNumber, string(dayOfWeek), semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Int("grade", grade).
			Int("classNumber", classNumber).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Failed to get specific day timetable from database")
		return nil, fmt.Errorf("failed to get timetables from database: %w", err)
	}

	s.logger.Debug().
		Int("dbResultCount", len(timetable)).
		Str("dayOfWeek", string(dayOfWeek)).
		Msg("Database query completed for specific day timetable")

	// 데이터베이스에서 찾은 경우 캐시에 저장하고 반환
	if len(timetable) > 0 {
		s.logger.Info().
			Int("foundCount", len(timetable)).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Found specific day timetable in database, caching results")
		
		if cacheErr := s.cacheTimetable(ctx, cacheKey, timetable); cacheErr != nil {
			s.logger.Warn().
				Err(cacheErr).
				Str("cacheKey", cacheKey).
				Msg("Failed to cache specific day timetable, but continuing")
		} else {
			s.logger.Debug().
				Str("cacheKey", cacheKey).
				Msg("Successfully cached specific day timetable")
		}
		return s.convertTimetablesToSubjects(timetable), nil
	}

	// 3. NEIS API에서 조회
	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Specific day timetable not found in DB, fetching from NEIS API")
	
	newTimetable, err := s.fetchFromNeisAPI(ctx, grade, classNumber, semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Failed to fetch specific day timetable from NEIS API")
		return nil, fmt.Errorf("failed to fetch from NEIS API: %w", err)
	}

	s.logger.Info().
		Int("apiResultCount", len(newTimetable)).
		Str("dayOfWeek", string(dayOfWeek)).
		Msg("Successfully fetched specific day timetable from NEIS API")

	// 4. 데이터베이스에 저장하고 캐시에 저장
	if len(newTimetable) > 0 {
		s.logger.Debug().
			Int("saveCount", len(newTimetable)).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Saving specific day timetable to database")
		
		if err := s.saveTimetables(ctx, newTimetable); err != nil {
			s.logger.Error().
				Err(err).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Failed to save specific day timetable to database")
			// Don't return error, we still have the data
		} else {
			s.logger.Info().
				Int("savedCount", len(newTimetable)).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Successfully saved specific day timetable to database")
		}

		s.logger.Debug().
			Str("cacheKey", cacheKey).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Caching specific day timetable from NEIS API")
		
		if err := s.cacheTimetable(ctx, cacheKey, newTimetable); err != nil {
			s.logger.Warn().
				Err(err).
				Str("cacheKey", cacheKey).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Failed to cache specific day timetable from NEIS API")
		} else {
			s.logger.Debug().
				Str("cacheKey", cacheKey).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Successfully cached specific day timetable from NEIS API")
		}
	} else {
		s.logger.Warn().
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("No specific day timetable returned from NEIS API")
	}

	return s.convertTimetablesToSubjects(newTimetable), nil
}

// GetTodayTimetable 오늘의 시간표를 조회합니다
func (s *service) GetTodayTimetable(ctx context.Context, grade, classNumber int, semester string, academicYear int) ([]SubjectInfo, error) {
	dayOfWeek := getDayOfWeek(time.Now())

	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Getting today's timetable")

	// 1. Redis 캐시 확인
	cacheKey := buildCacheKey(grade, classNumber, string(dayOfWeek), semester, academicYear)
	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Str("dayOfWeek", string(dayOfWeek)).
		Msg("Checking Redis cache for today's timetable")
	
	cachedTimetable, err := s.getTimetableFromCache(ctx, cacheKey)
	if err == nil && cachedTimetable != nil {
		s.logger.Info().
			Str("cacheKey", cacheKey).
			Int("cachedCount", len(cachedTimetable)).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Cache hit for today's timetable")
		return s.convertTimetablesToSubjects(cachedTimetable), nil
	}

	if err == redis.Nil {
		s.logger.Debug().
			Str("cacheKey", cacheKey).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Cache miss for today's timetable")
	} else if err != nil {
		s.logger.Warn().
			Err(err).
			Str("cacheKey", cacheKey).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Failed to get today's timetable from cache, continuing with DB query")
	}

	// 2. 데이터베이스 확인
	s.logger.Debug().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Querying database for today's timetable")
	
	timetable, err := s.repository.GetTimetables(ctx, grade, classNumber, string(dayOfWeek), semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Int("grade", grade).
			Int("classNumber", classNumber).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Failed to get today's timetable from database")
		return nil, fmt.Errorf("failed to get today's timetable from database: %w", err)
	}

	s.logger.Debug().
		Int("dbResultCount", len(timetable)).
		Str("dayOfWeek", string(dayOfWeek)).
		Msg("Database query completed for today's timetable")

	// 데이터베이스에서 찾은 경우 캐시에 저장하고 반환
	if len(timetable) > 0 {
		s.logger.Info().
			Int("foundCount", len(timetable)).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Found today's timetable in database, caching results")
		
		if cacheErr := s.cacheTimetable(ctx, cacheKey, timetable); cacheErr != nil {
			s.logger.Warn().
				Err(cacheErr).
				Str("cacheKey", cacheKey).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Failed to cache today's timetable, but continuing")
		} else {
			s.logger.Debug().
				Str("cacheKey", cacheKey).
				Msg("Successfully cached today's timetable")
		}
		return s.convertTimetablesToSubjects(timetable), nil
	}

	// 3. NEIS API에서 조회
	s.logger.Info().
		Int("grade", grade).
		Int("classNumber", classNumber).
		Str("dayOfWeek", string(dayOfWeek)).
		Str("semester", semester).
		Int("academicYear", academicYear).
		Msg("Today's timetable not found in DB, fetching from NEIS API")
	
	newTimetable, err := s.fetchFromNeisAPI(ctx, grade, classNumber, semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Failed to fetch today's timetable from NEIS API")
		return nil, fmt.Errorf("failed to fetch today's timetable from NEIS API: %w", err)
	}

	s.logger.Info().
		Int("apiResultCount", len(newTimetable)).
		Str("dayOfWeek", string(dayOfWeek)).
		Msg("Successfully fetched today's timetable from NEIS API")

	// 4. 데이터베이스에 저장하고 캐시에 저장
	if len(newTimetable) > 0 {
		if err := s.saveTimetables(ctx, newTimetable); err != nil {
			s.logger.Error().
				Err(err).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Failed to save today's timetable to database")
			// Don't return error, we still have the data
		} else {
			s.logger.Info().
				Int("savedCount", len(newTimetable)).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Successfully saved today's timetable to database")
		}

		s.logger.Debug().
			Str("cacheKey", cacheKey).
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("Caching today's timetable from NEIS API")
		
		if err := s.cacheTimetable(ctx, cacheKey, newTimetable); err != nil {
			s.logger.Warn().
				Err(err).
				Str("cacheKey", cacheKey).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Failed to cache today's timetable from NEIS API")
		} else {
			s.logger.Debug().
				Str("cacheKey", cacheKey).
				Str("dayOfWeek", string(dayOfWeek)).
				Msg("Successfully cached today's timetable from NEIS API")
		}
	} else {
		s.logger.Warn().
			Str("dayOfWeek", string(dayOfWeek)).
			Msg("No today's timetable returned from NEIS API")
		return []SubjectInfo{}, nil
	}

	return s.convertTimetablesToSubjects(newTimetable), nil
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

	// 디버깅을 위해 원시 응답 로그 출력 (RESULT만 있는 경우를 위해)
	s.logger.Debug().
		Str("rawResponse", string(body)).
		Msg("Raw NEIS API response")

	// 먼저 원시 JSON으로 파싱하여 구조 확인
	s.logger.Debug().
		Str("responseLength", fmt.Sprintf("%d", len(body))).
		Msg("Attempting to parse NEIS response as raw JSON")
	
	var rawResponse map[string]interface{}
	if err := json.Unmarshal(body, &rawResponse); err != nil {
		s.logger.Error().
			Err(err).
			Str("rawResponse", string(body)).
			Msg("Failed to unmarshal raw NEIS response")
		return nil, fmt.Errorf("failed to unmarshal raw NEIS response: %w", err)
	}
	
	s.logger.Debug().
		Int("responseKeys", len(rawResponse)).
		Msg("Successfully parsed raw NEIS response")

	// 응답 구조 분석을 위한 로깅
	s.logger.Info().
		Interface("responseKeys", getMapKeys(rawResponse)).
		Msg("NEIS response structure analysis")

	// RESULT 키가 있는 경우 오류 응답일 가능성이 있음
	if resultData, hasResult := rawResponse["RESULT"]; hasResult {
		s.logger.Warn().
			Interface("resultData", resultData).
			Msg("NEIS API returned RESULT field, checking for errors")
		
		// RESULT 데이터가 맵인 경우 오류 메시지 확인
		if resultMap, ok := resultData.(map[string]interface{}); ok {
			if code, hasCode := resultMap["CODE"]; hasCode {
				if message, hasMessage := resultMap["MESSAGE"]; hasMessage {
					s.logger.Error().
						Str("code", fmt.Sprintf("%v", code)).
						Str("message", fmt.Sprintf("%v", message)).
						Msg("NEIS API returned error")
					return []entities.Timetable{}, fmt.Errorf("NEIS API error: %s - %s", code, message)
				}
			}
		}
	}

	// hisTimetable 배열 처리
	hisTimetableData, ok := rawResponse["hisTimetable"]
	if !ok {
		s.logger.Warn().
			Interface("availableKeys", getMapKeys(rawResponse)).
			Msg("No hisTimetable field found in NEIS response")
		return []entities.Timetable{}, nil
	}

	hisTimetableArray, ok := hisTimetableData.([]interface{})
	if !ok || len(hisTimetableArray) == 0 {
		s.logger.Warn().
			Interface("hisTimetableData", hisTimetableData).
			Msg("Empty hisTimetable array in NEIS response")
		return []entities.Timetable{}, nil
	}

	// hisTimetable 배열에서 row 데이터를 찾기
	var rowData interface{}
	var foundRowData bool

	for i, hisTimetableItem := range hisTimetableArray {
		hisTimetableObj, ok := hisTimetableItem.(map[string]interface{})
		if !ok {
			s.logger.Warn().
				Int("index", i).
				Interface("item", hisTimetableItem).
				Msg("Invalid hisTimetable object structure, skipping")
			continue
		}

		s.logger.Debug().
			Int("index", i).
			Interface("hisTimetableKeys", getMapKeys(hisTimetableObj)).
			Msg("hisTimetable object structure")

		// row 데이터 찾기
		if row, exists := hisTimetableObj["row"]; exists {
			rowData = row
			foundRowData = true
			s.logger.Info().
				Int("foundAtIndex", i).
				Msg("Found row data in hisTimetable array")
			break
		}
	}

	if !foundRowData {
		s.logger.Warn().
			Int("totalItems", len(hisTimetableArray)).
			Msg("No row data found in any hisTimetable item")
		return []entities.Timetable{}, nil
	}

	rowArray, ok := rowData.([]interface{})
	if !ok {
		s.logger.Warn().Msg("Row data is not an array")
		return []entities.Timetable{}, nil
	}

	s.logger.Info().
		Int("totalRowCount", len(rowArray)).
		Msg("Found row array from NEIS API")

	// row 배열을 neisTimetable 구조체로 변환
	var neisTimetables []neisTimetable
	today := time.Now().Format("20060102") // YYYYMMDD 형식
	
	s.logger.Info().
		Str("today", today).
		Msg("Filtering for today's date")

	// 날짜 범위 분석을 위한 변수
	dateSet := make(map[string]bool)

	for i, rowItem := range rowArray {
		rowObj, ok := rowItem.(map[string]interface{})
		if !ok {
			s.logger.Warn().
				Int("index", i).
				Msg("Skipping invalid row item")
			continue
		}

		neis := neisTimetable{}
		
		// 각 필드를 안전하게 추출
		if grade, ok := rowObj["GRADE"].(string); ok {
			neis.Grade = grade
		}
		if classNm, ok := rowObj["CLASS_NM"].(string); ok {
			neis.ClassNumber = classNm
		}
		if itrtCntnt, ok := rowObj["ITRT_CNTNT"].(string); ok {
			neis.Subject = itrtCntnt
		}
		if allTiYmd, ok := rowObj["ALL_TI_YMD"].(string); ok {
			neis.Date = allTiYmd
			// 날짜 수집
			dateSet[allTiYmd] = true
		}
		if sem, ok := rowObj["SEM"].(string); ok {
			neis.Semester = sem
		}
		if ay, ok := rowObj["AY"].(string); ok {
			neis.AcademicYear = ay
		}

		// 처음 몇 개 항목의 날짜 정보를 로그로 출력
		if i < 5 {
			s.logger.Debug().
				Int("index", i).
				Str("date", neis.Date).
				Str("subject", neis.Subject).
				Msg("Sample timetable item")
		}

		// 오늘 날짜에 해당하는 시간표만 필터링
		if neis.Date == today {
			s.logger.Info().
				Str("date", neis.Date).
				Str("today", today).
				Str("subject", neis.Subject).
				Msg("Found today's timetable item")
			neisTimetables = append(neisTimetables, neis)
		}
	}

	// 날짜 분석 결과 출력
	var dates []string
	for date := range dateSet {
		dates = append(dates, date)
	}
	
	s.logger.Info().
		Interface("availableDates", dates).
		Int("uniqueDateCount", len(dates)).
		Msg("Available dates in NEIS API response")

	// 오늘 날짜에 데이터가 없으면 가장 최근의 같은 요일 데이터 찾기
	if len(neisTimetables) == 0 {
		s.logger.Info().Msg("No timetable found for today, looking for most recent same weekday")
		
		// 오늘의 요일 계산
		todayTime, _ := time.Parse("20060102", today)
		todayWeekday := todayTime.Weekday()
		
		var recentTimetables []neisTimetable
		var mostRecentDate string
		
		// 모든 데이터를 다시 순회하여 같은 요일 찾기
		for _, rowItem := range rowArray {
			rowObj, ok := rowItem.(map[string]interface{})
			if !ok {
				continue
			}
			
			dateStr, ok := rowObj["ALL_TI_YMD"].(string)
			if !ok {
				continue
			}
			
			// 날짜 파싱하여 요일 확인
			date, err := time.Parse("20060102", dateStr)
			if err != nil {
				continue
			}
			
			// 같은 요일이고 오늘보다 이전 날짜인 경우
			if date.Weekday() == todayWeekday && dateStr < today {
				// 가장 최근 날짜 업데이트
				if mostRecentDate == "" || dateStr > mostRecentDate {
					mostRecentDate = dateStr
					recentTimetables = nil // 새로운 최근 날짜이므로 기존 데이터 초기화
				}
				
				// 가장 최근 날짜와 같으면 추가
				if dateStr == mostRecentDate {
					neis := neisTimetable{}
					if grade, ok := rowObj["GRADE"].(string); ok {
						neis.Grade = grade
					}
					if classNm, ok := rowObj["CLASS_NM"].(string); ok {
						neis.ClassNumber = classNm
					}
					if itrtCntnt, ok := rowObj["ITRT_CNTNT"].(string); ok {
						neis.Subject = itrtCntnt
					}
					if allTiYmd, ok := rowObj["ALL_TI_YMD"].(string); ok {
						neis.Date = allTiYmd
					}
					if sem, ok := rowObj["SEM"].(string); ok {
						neis.Semester = sem
					}
					if ay, ok := rowObj["AY"].(string); ok {
						neis.AcademicYear = ay
					}
					recentTimetables = append(recentTimetables, neis)
				}
			}
		}
		
		if len(recentTimetables) > 0 {
			s.logger.Info().
				Str("mostRecentDate", mostRecentDate).
				Int("foundCount", len(recentTimetables)).
				Msg("Found most recent same weekday timetable")
			neisTimetables = recentTimetables
		} else {
			s.logger.Warn().Msg("No timetable found for today or recent same weekday")
		}
	}

	s.logger.Info().
		Int("rawCount", len(neisTimetables)).
		Msg("Successfully parsed raw timetables from NEIS API")

	// NEIS 응답을 entities.Timetable로 변환
	timetables, err := s.convertNeisToEntities(neisTimetables, grade, classNumber, semester, academicYear)
	if err != nil {
		s.logger.Error().
			Err(err).
			Msg("Failed to convert NEIS timetables to entities")
		return nil, fmt.Errorf("failed to convert NEIS timetables to entities: %w", err)
	}

	s.logger.Info().
		Int("convertedCount", len(timetables)).
		Msg("Successfully converted NEIS timetables to entities")

	return timetables, nil
}

// saveTimetables 여러 시간표를 데이터베이스에 저장합니다
func (s *service) saveTimetables(ctx context.Context, timetables []entities.Timetable) error {
	s.logger.Debug().
		Int("totalCount", len(timetables)).
		Msg("Starting to save timetables to database")
	
	for i := range timetables {
		if _, err := s.repository.CreateTimetable(ctx, &timetables[i]); err != nil {
			s.logger.Error().
				Err(err).
				Int("index", i).
				Int("totalCount", len(timetables)).
				Msg("Failed to save timetable")
			return fmt.Errorf("failed to save timetable at index %d: %w", i, err)
		}
	}
	
	s.logger.Debug().
		Int("savedCount", len(timetables)).
		Msg("Successfully saved all timetables to database")
	
	return nil
}

// getMapKeys 맵의 키들을 슬라이스로 반환합니다
func getMapKeys(m map[string]interface{}) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	return keys
}

// convertNeisToSubjects NEIS API 응답을 SubjectInfo로 변환합니다
func (s *service) convertNeisToSubjects(neisTimetables []neisTimetable) ([]SubjectInfo, error) {
	s.logger.Debug().
		Int("inputCount", len(neisTimetables)).
		Msg("Converting NEIS timetables to subjects")
	
	var subjects []SubjectInfo
	
	for _, neis := range neisTimetables {
		// 과목명에서 * 글자 제거
		cleanedSubject := strings.ReplaceAll(neis.Subject, "*", "")
		cleanedSubject = strings.TrimSpace(cleanedSubject)
		
		subject := SubjectInfo{
			Subject: cleanedSubject,
		}

		subjects = append(subjects, subject)
	}

	s.logger.Debug().
		Int("outputCount", len(subjects)).
		Msg("Successfully converted NEIS timetables to subjects")

	return subjects, nil
}

// convertNeisToEntities NEIS API 응답을 entities.Timetable로 변환합니다
func (s *service) convertNeisToEntities(neisTimetables []neisTimetable, grade, classNumber int, semester string, academicYear int) ([]entities.Timetable, error) {
	s.logger.Debug().
		Int("inputCount", len(neisTimetables)).
		Msg("Converting NEIS timetables to entities")
	
	var timetables []entities.Timetable
	
	for _, neis := range neisTimetables {
		// 요일 파싱 (NEIS API의 ALL_TI_YMD에서 요일 추출)
		dayOfWeek, err := s.parseDayOfWeekFromDate(neis.Date)
		if err != nil {
			s.logger.Warn().
				Err(err).	
				Str("date", neis.Date).
				Msg("Failed to parse day of week, skipping")
			continue
		}

		timetable := entities.Timetable{
			Grade:        grade, // 요청 파라미터에서 가져옴
			ClassNumber:  classNumber, // 요청 파라미터에서 가져옴
			Subject:      neis.Subject,
			DayOfWeek:    dayOfWeek,
			Semester:     entities.Semester(semester),
			AcademicYear: academicYear, // 요청 파라미터에서 가져옴
		}

		timetables = append(timetables, timetable)
	}

	s.logger.Debug().
		Int("outputCount", len(timetables)).
		Msg("Successfully converted NEIS timetables to entities")

	return timetables, nil
}

// convertTimetablesToSubjects entities.Timetable을 SubjectInfo로 변환합니다
func (s *service) convertTimetablesToSubjects(timetables []entities.Timetable) []SubjectInfo {
	var subjects []SubjectInfo
	
	for _, timetable := range timetables {
		// 과목명에서 * 글자 제거
		cleanedSubject := strings.ReplaceAll(timetable.Subject, "*", "")
		cleanedSubject = strings.TrimSpace(cleanedSubject)
		
		subject := SubjectInfo{
			Subject: cleanedSubject,
		}
		subjects = append(subjects, subject)
	}
	
	return subjects
}

// parseDayOfWeekFromDate 날짜 문자열에서 요일을 추출합니다
func (s *service) parseDayOfWeekFromDate(dateStr string) (entities.DayOfWeek, error) {
	// NEIS API의 ALL_TI_YMD 형식에 따라 날짜 파싱
	// 예: "20240304" 형태의 문자열
	if len(dateStr) != 8 {
		return entities.Monday, fmt.Errorf("invalid date format: %s", dateStr)
	}

	date, err := time.Parse("20060102", dateStr)
	if err != nil {
		return entities.Monday, fmt.Errorf("failed to parse date %s: %w", dateStr, err)
	}

	return getDayOfWeek(date), nil
}

// getTimetableFromCache Redis 캐시에서 시간표를 조회합니다
func (s *service) getTimetableFromCache(ctx context.Context, cacheKey string) ([]entities.Timetable, error) {
	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Msg("Retrieving timetable from Redis cache")
	
	cachedData, err := s.redis.Get(ctx, cacheKey).Result()
	if err != nil {
		s.logger.Debug().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to retrieve from Redis cache")
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

	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Int("unmarshaledCount", len(timetable)).
		Msg("Successfully retrieved and unmarshaled timetable from cache")

	return timetable, nil
}

// cacheTimetable 시간표를 Redis 캐시에 저장합니다
func (s *service) cacheTimetable(ctx context.Context, cacheKey string, timetable []entities.Timetable) error {
	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Int("timetableCount", len(timetable)).
		Dur("ttl", cacheTTL).
		Msg("Caching timetable to Redis")
	
	encodedData, err := json.Marshal(timetable)
	if err != nil {
		s.logger.Error().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to marshal timetable for caching")
		return fmt.Errorf("failed to marshal timetable: %w", err)
	}

	if err := s.redis.Set(ctx, cacheKey, encodedData, cacheTTL).Err(); err != nil {
		s.logger.Error().
			Err(err).
			Str("cacheKey", cacheKey).
			Msg("Failed to set cache in Redis")
		return fmt.Errorf("failed to set cache: %w", err)
	}

	s.logger.Debug().
		Str("cacheKey", cacheKey).
		Int("cachedCount", len(timetable)).
		Msg("Successfully cached timetable to Redis")

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
