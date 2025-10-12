import { Injectable, Logger, Inject } from '@nestjs/common';
import { HttpService } from '@nestjs/axios';
import { ConfigService } from '@nestjs/config';
import { CACHE_MANAGER } from '@nestjs/cache-manager';
import { firstValueFrom } from 'rxjs';
import {
  NeisResponse,
  MealResponse,
  NeisEmptyResponse,
} from './types/neis-api.types';
import { PrismaService } from '../prisma/prisma.service';
import type { CacheStore } from '../types/cache.types';
import {
  extractDishNames,
  isEmptyDataResponse,
  isValidMealResponse,
  safeJsonStringify,
} from './utils/type-guards';

@Injectable()
export class MealsService {
  private readonly logger = new Logger(MealsService.name);

  ATPT_OFCDC_SC_CODE = 'B10'; // 시도교육청 코드
  SD_SCHUL_CODE = '7010572'; // 서울디지텍고등학교 행정표준코드
  TYPE = 'json';
  KEY: string | undefined;

  constructor(
    private httpService: HttpService,
    private configService: ConfigService,
    private prismaService: PrismaService,
    @Inject(CACHE_MANAGER) private cacheManager: CacheStore,
  ) {
    this.KEY = configService.get<string>('NEIS_API_KEY');
  }

  async getTodayLunch(): Promise<MealResponse> {
    const startTime = Date.now();
    const today = new Date();
    const formattedDate = today.toISOString().slice(0, 10).replace(/-/g, '');
    const cacheKey = `meal:${formattedDate}`;

    try {
      // API 키 검증
      if (!this.KEY) {
        this.logger.error('NEIS API KEY is not configured');
        throw new Error('NEIS API KEY is not set.');
      }

      this.logger.log(`Starting meal data fetch for date: ${formattedDate}`);

      // Redis에서 캐시된 데이터 확인
      const cachedData = await this.cacheManager.get<MealResponse>(cacheKey);
      if (cachedData) {
        const duration = Date.now() - startTime;
        this.logger.log(`Cache hit for date: ${formattedDate} (${duration}ms)`);

        // 캐시된 데이터에 응답 시간 업데이트
        return {
          success: cachedData.success,
          message: cachedData.data?.hasData
            ? '식단 정보를 캐시에서 가져왔습니다.'
            : '식단 정보를 캐시에서 가져올 수 없습니다.',
          data: cachedData.data
            ? {
                ...cachedData.data,
                responseTime: duration,
                cached: true,
              }
            : null,
        };
      }

      this.logger.log(
        `Cache miss for date: ${formattedDate}, fetching from API`,
      );

      // API에서 데이터 가져오기
      const apiResponse = await this.fetchMealDataFromAPI(formattedDate);

      if (apiResponse.success) {
        // 데이터베이스에 저장 (실제 급식 데이터가 있는 경우만)
        if (apiResponse.data?.hasData) {
          await this.saveMealDataToDatabase(
            formattedDate,
            apiResponse.data.mealInfo as NeisResponse,
          );
        }

        // Redis에 캐시 저장 (1시간)
        await this.cacheManager.set<MealResponse>(cacheKey, apiResponse, 3600);

        const duration = Date.now() - startTime;
        this.logger.log(
          `Data cached for date: ${formattedDate} (${duration}ms)`,
        );

        // 응답 시간 추가
        return {
          success: apiResponse.success,
          message: apiResponse.data?.hasData
            ? '식단 정보를 가져왔습니다.'
            : '식단 정보를 가져올 수 없습니다.',
          data: apiResponse.data
            ? {
                ...apiResponse.data,
                responseTime: duration,
                cached: false,
              }
            : null,
        };
      }

      return apiResponse;
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMessage = this.getErrorMessage(error);

      this.logger.error(
        `Failed to fetch meal data for date: ${formattedDate} (${duration}ms)`,
        {
          error: errorMessage,
          cacheKey,
        },
      );

      return {
        success: false,
        message: '식단 정보를 가져올 수 없습니다.',
        data: {
          date: formattedDate,
          hasData: false,
          cached: false,
          responseTime: duration,
        },
      };
    }
  }

  async getMealByDate(date: string): Promise<MealResponse> {
    const startTime = Date.now();

    try {
      // 날짜 형식 검증 및 포맷팅
      const formattedDate = this.validateAndFormatDate(date);
      const cacheKey = `meal:${formattedDate}`;

      this.logger.log(`Starting meal data fetch for date: ${formattedDate}`);

      // 1. Redis 캐시에서 확인
      const cachedData = await this.cacheManager.get<MealResponse>(cacheKey);
      if (cachedData) {
        const duration = Date.now() - startTime;
        this.logger.log(`Cache hit for date: ${formattedDate} (${duration}ms)`);

        return {
          success: cachedData.success,
          message: cachedData.data?.hasData
            ? '식단 정보를 캐시에서 가져왔습니다.'
            : '식단 정보를 캐시에서 가져올 수 없습니다.',
          data: cachedData.data
            ? {
                ...cachedData.data,
                responseTime: duration,
                cached: true,
              }
            : null,
        };
      }

      // 2. 데이터베이스에서 확인
      const dbData = await this.getMealDataFromDatabase(formattedDate);
      if (dbData) {
        const duration = Date.now() - startTime;
        this.logger.log(
          `Database hit for date: ${formattedDate} (${duration}ms)`,
        );

        // dishNames가 없으면 mealInfo에서 직접 추출
        let dishNames = dbData.dishNames;
        if (
          !dishNames &&
          dbData.hasData &&
          isValidMealResponse(dbData.mealInfo)
        ) {
          try {
            dishNames = extractDishNames(dbData.mealInfo);
          } catch (error) {
            this.logger.warn(
              `Failed to extract dish names from database mealInfo for date: ${formattedDate}`,
              {
                error: this.getErrorMessage(error),
              },
            );
          }
        }

        const response = {
          success: true,
          message: dbData.hasData
            ? '식단 정보를 데이터베이스에서 가져왔습니다.'
            : '식단 정보를 데이터베이스에서 가져올 수 없습니다.',
          data: {
            mealInfo: dbData.mealInfo,
            dishNames,
            date: formattedDate,
            hasData: dbData.hasData,
            cached: false,
            responseTime: duration,
          },
        };

        // Redis에 캐시 저장 (1시간)
        await this.cacheManager.set<MealResponse>(cacheKey, response, 3600);

        return response;
      }

      // 3. API에서 가져오기 (DB에 없는 경우)
      this.logger.log(
        `Cache and DB miss for date: ${formattedDate}, fetching from API`,
      );

      if (!this.KEY) {
        throw new Error('NEIS API KEY is not configured');
      }

      const apiResponse = await this.fetchMealDataFromAPI(formattedDate);

      if (apiResponse.success) {
        // 데이터베이스에 저장 (실제 급식 데이터가 있는 경우만)
        if (apiResponse.data?.hasData) {
          await this.saveMealDataToDatabase(
            formattedDate,
            apiResponse.data.mealInfo as NeisResponse,
          );
        }

        // Redis에 캐시 저장 (1시간)
        await this.cacheManager.set<MealResponse>(cacheKey, apiResponse, 3600);

        const duration = Date.now() - startTime;
        this.logger.log(
          `Data fetched from API and cached for date: ${formattedDate} (${duration}ms)`,
        );

        return {
          success: apiResponse.success,
          message: apiResponse.data?.hasData
            ? '식단 정보를 API에서 가져왔습니다.'
            : '식단 정보를 API에서 가져올 수 없습니다.',
          data: apiResponse.data
            ? {
                ...apiResponse.data,
                responseTime: duration,
                cached: false,
              }
            : null,
        };
      }

      return apiResponse;
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMessage = this.getErrorMessage(error);

      this.logger.error(
        `Failed to fetch meal data for date: ${date} (${duration}ms)`,
        {
          error: errorMessage,
          date,
        },
      );

      return {
        success: false,
        message: '식단 정보를 가져올 수 없습니다.',
        data: {
          date: this.validateAndFormatDate(date),
          hasData: false,
          cached: false,
          responseTime: duration,
        },
      };
    }
  }

  /**
   * 안전한 에러 메시지 추출
   */
  private getErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }

    if (typeof error === 'string') {
      return error;
    }

    if (error && typeof error === 'object' && 'message' in error) {
      return String((error as { message: unknown }).message);
    }

    return 'Unknown error occurred';
  }

  /**
   * NEIS API에서 급식 데이터를 가져오는 메서드
   */
  private async fetchMealDataFromAPI(
    formattedDate: string,
  ): Promise<MealResponse> {
    const startTime = Date.now();

    try {
      if (!this.KEY) {
        throw new Error('NEIS API KEY is not configured');
      }

      // URL 구성
      const baseUrl = 'https://open.neis.go.kr/hub/mealServiceDietInfo';
      const params = new URLSearchParams({
        KEY: this.KEY,
        Type: this.TYPE,
        ATPT_OFCDC_SC_CODE: this.ATPT_OFCDC_SC_CODE,
        SD_SCHUL_CODE: this.SD_SCHUL_CODE,
        MLSV_YMD: formattedDate,
      });

      const url = `${baseUrl}?${params.toString()}`;
      this.logger.log(
        `Fetching meal data from NEIS API for date: ${formattedDate}`,
      );

      const response = await firstValueFrom(this.httpService.get<unknown>(url));
      const responseData = response.data;

      const duration = Date.now() - startTime;
      this.logger.log(
        `NEIS API response received for date: ${formattedDate} (${duration}ms)`,
      );

      // 빈 데이터 응답 처리 (INFO-200: 해당하는 데이터가 없습니다)
      if (isEmptyDataResponse(responseData)) {
        this.logger.log(`No meal data available for date: ${formattedDate}`);
        return {
          success: true,
          message: '식단 정보를 가져올 수 없습니다.',
          data: {
            mealInfo: responseData,
            date: formattedDate,
            hasData: false,
            cached: false,
          },
        };
      }

      // 정상적인 급식 데이터 응답 처리
      if (isValidMealResponse(responseData)) {
        this.logger.log(`Valid meal data found for date: ${formattedDate}`);

        // DDISH_NM에서 요리명 추출
        let dishNames: string[] = [];
        try {
          dishNames = extractDishNames(responseData);
        } catch (error) {
          this.logger.warn(
            `Failed to extract dish names from API response for date: ${formattedDate}`,
            {
              error: this.getErrorMessage(error),
            },
          );
        }

        return {
          success: true,
          message: '식단 정보를 가져왔습니다.',
          data: {
            mealInfo: responseData,
            dishNames,
            date: formattedDate,
            hasData: true,
            cached: false,
          },
        };
      }

      // 예상하지 못한 응답 형식
      this.logger.warn(
        `Unexpected API response format for date: ${formattedDate}`,
        {
          responseType: typeof responseData,
          hasResult: 'RESULT' in (responseData as Record<string, unknown>),
          hasMealInfo:
            'mealServiceDietInfo' in (responseData as Record<string, unknown>),
        },
      );

      throw new Error('NEIS API response data is not valid.');
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMessage = this.getErrorMessage(error);

      this.logger.error(
        `Failed to fetch meal data from NEIS API for date: ${formattedDate} (${duration}ms)`,
        {
          error: errorMessage,
          formattedDate,
        },
      );

      return {
        success: false,
        message: '식단 정보를 가져올 수 없습니다.',
        data: {
          date: formattedDate,
          hasData: false,
          cached: false,
          responseTime: duration,
        },
      };
    }
  }

  /**
   * 데이터베이스에 급식 데이터를 저장하는 메서드
   */
  private async saveMealDataToDatabase(
    formattedDate: string,
    mealData: NeisResponse,
  ): Promise<void> {
    const startTime = Date.now();

    try {
      const mealDate = this.parseDateFromString(formattedDate);

      // 이미 해당 날짜의 데이터가 있는지 확인
      const existingMeal = await this.prismaService.mealInfo.findFirst({
        where: {
          meal_date: {
            gte: new Date(
              mealDate.getFullYear(),
              mealDate.getMonth(),
              mealDate.getDate(),
            ),
            lt: new Date(
              mealDate.getFullYear(),
              mealDate.getMonth(),
              mealDate.getDate() + 1,
            ),
          },
        },
      });

      if (existingMeal) {
        this.logger.log(`Meal data already exists for date: ${formattedDate}`);
        return;
      }

      // 새 데이터 저장 - 안전한 JSON 직렬화 사용
      const serializedData = safeJsonStringify(mealData);

      // DDISH_NM에서 요리명 추출
      let dishNames: string[] = [];
      try {
        dishNames = extractDishNames(mealData);
      } catch (error) {
        this.logger.warn(
          `Failed to extract dish names for date: ${formattedDate}`,
          {
            error: this.getErrorMessage(error),
          },
        );
      }

      await this.prismaService.mealInfo.create({
        data: {
          meal_date: mealDate,
          meal_info: serializedData,
          dish_names: dishNames.length > 0 ? dishNames : undefined,
        },
      });

      const duration = Date.now() - startTime;
      this.logger.log(
        `Meal data saved to database for date: ${formattedDate} (${duration}ms)`,
      );
    } catch (error) {
      const duration = Date.now() - startTime;
      const errorMessage = this.getErrorMessage(error);

      this.logger.error(
        `Failed to save meal data to database for date: ${formattedDate} (${duration}ms)`,
        {
          error: errorMessage,
          formattedDate,
        },
      );

      // 데이터베이스 저장 실패는 전체 프로세스를 중단시키지 않음
    }
  }

  /**
   * 날짜 문자열을 Date 객체로 안전하게 변환
   */
  private parseDateFromString(dateString: string): Date {
    try {
      const year = parseInt(dateString.slice(0, 4), 10);
      const month = parseInt(dateString.slice(4, 6), 10) - 1; // JavaScript 월은 0부터 시작
      const day = parseInt(dateString.slice(6, 8), 10);

      const date = new Date(year, month, day);

      // 날짜 유효성 검증
      if (isNaN(date.getTime())) {
        throw new Error(`Invalid date: ${dateString}`);
      }

      return date;
    } catch (error) {
      const errorMessage = this.getErrorMessage(error);
      this.logger.error(`Failed to parse date string: ${dateString}`, {
        error: errorMessage,
      });
      throw new Error(`Invalid date format: ${dateString}`);
    }
  }

  /**
   * 날짜 형식 검증 및 포맷팅
   */
  private validateAndFormatDate(date: string): string {
    // YYYY-MM-DD 또는 YYYYMMDD 형식 지원
    let formattedDate: string;

    if (date.includes('-')) {
      // YYYY-MM-DD 형식인 경우
      formattedDate = date.replace(/-/g, '');
    } else if (/^\d{8}$/.test(date)) {
      // YYYYMMDD 형식인 경우
      formattedDate = date;
    } else {
      throw new Error(
        `Invalid date format: ${date}. Expected YYYY-MM-DD or YYYYMMDD`,
      );
    }

    // 날짜 유효성 검증
    const year = parseInt(formattedDate.slice(0, 4), 10);
    const month = parseInt(formattedDate.slice(4, 6), 10);
    const day = parseInt(formattedDate.slice(6, 8), 10);

    if (year < 2020 || year > 2030) {
      throw new Error(
        `Invalid year: ${year}. Year must be between 2020 and 2030`,
      );
    }

    if (month < 1 || month > 12) {
      throw new Error(
        `Invalid month: ${month}. Month must be between 1 and 12`,
      );
    }

    if (day < 1 || day > 31) {
      throw new Error(`Invalid day: ${day}. Day must be between 1 and 31`);
    }

    // 실제 날짜 유효성 검증
    const testDate = new Date(year, month - 1, day);
    if (
      testDate.getFullYear() !== year ||
      testDate.getMonth() !== month - 1 ||
      testDate.getDate() !== day
    ) {
      throw new Error(`Invalid date: ${formattedDate}`);
    }

    return formattedDate;
  }

  /**
   * 데이터베이스에서 급식 데이터 조회
   */
  private async getMealDataFromDatabase(formattedDate: string): Promise<{
    mealInfo: NeisResponse | NeisEmptyResponse;
    dishNames?: string[];
    hasData: boolean;
  } | null> {
    try {
      const mealDate = this.parseDateFromString(formattedDate);

      const mealRecord = await this.prismaService.mealInfo.findFirst({
        where: {
          meal_date: {
            gte: new Date(
              mealDate.getFullYear(),
              mealDate.getMonth(),
              mealDate.getDate(),
            ),
            lt: new Date(
              mealDate.getFullYear(),
              mealDate.getMonth(),
              mealDate.getDate() + 1,
            ),
          },
        },
        orderBy: {
          meal_date: 'desc',
        },
      });

      if (!mealRecord) {
        this.logger.log(
          `No meal data found in database for date: ${formattedDate}`,
        );
        return null;
      }

      // JSON 데이터 파싱 - 안전한 타입 처리
      let mealInfo: NeisResponse | NeisEmptyResponse;

      if (typeof mealRecord.meal_info === 'string') {
        try {
          const parsed = JSON.parse(mealRecord.meal_info) as unknown;
          if (isEmptyDataResponse(parsed)) {
            mealInfo = parsed;
          } else if (isValidMealResponse(parsed)) {
            mealInfo = parsed;
          } else {
            this.logger.warn(
              `Invalid meal data format in database for date: ${formattedDate}`,
            );
            return null;
          }
        } catch (parseError) {
          this.logger.error(
            `Failed to parse meal data from database for date: ${formattedDate}`,
            {
              error: this.getErrorMessage(parseError),
            },
          );
          return null;
        }
      } else {
        // Prisma가 이미 객체로 파싱한 경우
        const parsed = mealRecord.meal_info as unknown;
        if (isEmptyDataResponse(parsed)) {
          mealInfo = parsed;
        } else if (isValidMealResponse(parsed)) {
          mealInfo = parsed;
        } else {
          this.logger.warn(
            `Invalid meal data format in database for date: ${formattedDate}`,
          );
          return null;
        }
      }

      const hasData = isValidMealResponse(mealInfo);

      // dish_names 파싱
      let dishNames: string[] | undefined;
      if (mealRecord.dish_names && Array.isArray(mealRecord.dish_names)) {
        dishNames = mealRecord.dish_names as string[];
      }

      this.logger.log(
        `Found meal data in database for date: ${formattedDate}, hasData: ${hasData}, dishCount: ${dishNames?.length || 0}`,
      );

      return {
        mealInfo,
        dishNames,
        hasData,
      };
    } catch (error) {
      const errorMessage = this.getErrorMessage(error);
      this.logger.error(
        `Failed to query meal data from database for date: ${formattedDate}`,
        {
          error: errorMessage,
        },
      );
      return null;
    }
  }
}
