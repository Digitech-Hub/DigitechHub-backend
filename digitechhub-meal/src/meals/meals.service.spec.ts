/* eslint-disable @typescript-eslint/unbound-method */
import { Test, TestingModule } from '@nestjs/testing';
import { MealsService } from './meals.service';
import { ConfigModule, ConfigService } from '@nestjs/config';
import { HttpModule, HttpService } from '@nestjs/axios';
import { PrismaService } from '../prisma/prisma.service';
import { CacheModule, CACHE_MANAGER } from '@nestjs/cache-manager';
import { of, throwError } from 'rxjs';
import type { CacheStore } from '../types/cache.types';
import type { AxiosRequestConfig, AxiosResponse } from 'axios';

describe('MealsService', () => {
  let service: MealsService;
  let httpService: HttpService;
  let prismaService: PrismaService;
  let cacheManager: CacheStore;

  const mockNeisResponse = {
    mealServiceDietInfo: [
      { head: [{ list_total_count: 1 }] },
      {
        row: [
          {
            ATPT_OFCDC_SC_CODE: 'B10',
            SD_SCHUL_CODE: '7010572',
            MLSV_YMD: '20241018',
            DDISH_NM: '밥<br/>김치찌개(1.2.3)<br/>제육볶음(5.6)<br/>샐러드',
            CAL_INFO: '800 Kcal',
          },
        ],
      },
    ],
  };

  const mockEmptyResponse = {
    RESULT: {
      CODE: 'INFO-200',
      MESSAGE: '해당하는 데이터가 없습니다.',
    },
  };

  const mockMealResponse = {
    success: true,
    message: '식단 정보를 가져왔습니다.',
    data: {
      mealInfo: mockNeisResponse,
      dishNames: ['밥', '김치찌개', '제육볶음', '샐러드'],
      date: '20241018',
      hasData: true,
      cached: false,
      responseTime: 100,
    },
  };

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      imports: [
        ConfigModule.forRoot({
          isGlobal: true,
          envFilePath: '.env.test',
        }),
        HttpModule,
        CacheModule.register({
          isGlobal: true,
        }),
      ],
      providers: [
        PrismaService,
        MealsService,
        {
          provide: ConfigService,
          useValue: {
            get: jest.fn((key: string) => {
              const config: Record<string, string> = {
                NEIS_API_KEY: 'test-api-key',
                REDIS_HOST: 'localhost',
                REDIS_PORT: '6379',
              };
              return config[key];
            }),
          },
        },
      ],
    }).compile();

    service = module.get<MealsService>(MealsService);
    httpService = module.get<HttpService>(HttpService);
    prismaService = module.get<PrismaService>(PrismaService);
    cacheManager = module.get<CacheStore>(CACHE_MANAGER);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(service).toBeDefined();
  });

  describe('getTodayLunch', () => {
    it('should return cached data when available', async () => {
      const today = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      const cacheKey = `meal:${today}`;

      jest.spyOn(cacheManager, 'get').mockResolvedValue(mockMealResponse);

      const result = await service.getTodayLunch();

      expect(result.success).toBe(true);
      expect(result.data?.cached).toBe(true);
      expect(cacheManager.get).toHaveBeenCalledWith(cacheKey);
    });

    it('should fetch from API when cache misses', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest.spyOn(cacheManager, 'set').mockResolvedValue(undefined);
      jest.spyOn(httpService, 'get').mockReturnValue(
        of({
          data: mockNeisResponse,
          status: 200,
          statusText: 'OK',
          headers: {},
          config: {} as AxiosRequestConfig,
        } as AxiosResponse),
      );
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue(null);
      jest.spyOn(prismaService.mealInfo, 'create').mockResolvedValue({
        id: 1,
        meal_date: new Date(),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥', '김치찌개', '제육볶음', '샐러드'],
      });

      const result = await service.getTodayLunch();

      expect(result.success).toBe(true);
      expect(result.data?.hasData).toBe(true);
      expect(result.data?.cached).toBe(false);
      expect(jest.mocked(httpService).get).toHaveBeenCalled();
    });

    it('should handle API error gracefully', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest
        .spyOn(httpService, 'get')
        .mockReturnValue(throwError(() => new Error('API Error')));

      const result = await service.getTodayLunch();

      expect(result.success).toBe(false);
      expect(result.message).toBe('식단 정보를 가져올 수 없습니다.');
      expect(result.data?.hasData).toBe(false);
    });

    it('should handle missing API key', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      (service as unknown as { KEY: string | undefined }).KEY = undefined;

      const result = await service.getTodayLunch();

      expect(result.success).toBe(false);
      expect(result.message).toBe('식단 정보를 가져올 수 없습니다.');
    });

    it('should handle empty data response from API', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest.spyOn(cacheManager, 'set').mockResolvedValue(undefined);
      jest.spyOn(httpService, 'get').mockReturnValue(
        of({
          data: mockEmptyResponse,
          status: 200,
          statusText: 'OK',
          headers: {},
          config: {} as AxiosRequestConfig,
        } as AxiosResponse),
      );

      const result = await service.getTodayLunch();

      expect(result.success).toBe(true);
      expect(result.data?.hasData).toBe(false);
    });
  });

  describe('getMealByDate', () => {
    const testDate = '2024-10-18';
    const formattedDate = '20241018';

    it('should return cached data when available', async () => {
      const cacheKey = `meal:${formattedDate}`;
      jest.spyOn(cacheManager, 'get').mockResolvedValue(mockMealResponse);

      const result = await service.getMealByDate(testDate);

      expect(result.success).toBe(true);
      expect(result.data?.cached).toBe(true);
      expect(jest.mocked(cacheManager).get).toHaveBeenCalledWith(cacheKey);
    });

    it('should return database data when cache misses', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest.spyOn(cacheManager, 'set').mockResolvedValue(undefined);
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue({
        id: 1,
        meal_date: new Date(2024, 9, 18),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥', '김치찌개', '제육볶음', '샐러드'],
      });

      const result = await service.getMealByDate(testDate);

      expect(result.success).toBe(true);
      expect(result.data?.hasData).toBe(true);
      expect(result.message).toContain('데이터베이스');
    });

    it('should fetch from API when cache and DB miss', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest.spyOn(cacheManager, 'set').mockResolvedValue(undefined);
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue(null);
      jest.spyOn(prismaService.mealInfo, 'create').mockResolvedValue({
        id: 1,
        meal_date: new Date(2024, 9, 18),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥', '김치찌개', '제육볶음', '샐러드'],
      });
      jest.spyOn(httpService, 'get').mockReturnValue(
        of({
          data: mockNeisResponse,
          status: 200,
          statusText: 'OK',
          headers: {},
          config: {} as AxiosRequestConfig,
        } as AxiosResponse),
      );

      const result = await service.getMealByDate(testDate);

      expect(result.success).toBe(true);
      expect(result.data?.hasData).toBe(true);
      expect(jest.mocked(httpService).get).toHaveBeenCalled();
    });

    it('should validate date format correctly', async () => {
      const result = await service.getMealByDate('invalid-date');

      expect(result.success).toBe(false);
      expect(result.message).toBe('식단 정보를 가져올 수 없습니다.');
      expect(result.data?.hasData).toBe(false);
    });

    it('should handle YYYYMMDD format', async () => {
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue({
        id: 1,
        meal_date: new Date(2024, 9, 18),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥', '김치찌개'],
      });
      jest.spyOn(cacheManager, 'set').mockResolvedValue(undefined);

      const result = await service.getMealByDate('20241018');

      expect(result.success).toBe(true);
      expect(result.data?.date).toBe('20241018');
    });

    it('should reject invalid year range', async () => {
      const result = await service.getMealByDate('2019-01-01');

      expect(result.success).toBe(false);
      expect(result.message).toBe('식단 정보를 가져올 수 없습니다.');
      expect(result.data?.hasData).toBe(false);
    });

    it('should reject invalid month', async () => {
      const result = await service.getMealByDate('2024-13-01');

      expect(result.success).toBe(false);
      expect(result.message).toBe('식단 정보를 가져올 수 없습니다.');
      expect(result.data?.hasData).toBe(false);
    });

    it('should reject invalid day', async () => {
      const result = await service.getMealByDate('2024-02-30');

      expect(result.success).toBe(false);
      expect(result.message).toBe('식단 정보를 가져올 수 없습니다.');
      expect(result.data?.hasData).toBe(false);
    });
  });

  describe('Database operations', () => {
    it('should save meal data to database successfully', async () => {
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue(null);
      jest.spyOn(prismaService.mealInfo, 'create').mockResolvedValue({
        id: 1,
        meal_date: new Date(2024, 9, 18),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥', '김치찌개'],
      });

      await (
        service as unknown as {
          saveMealDataToDatabase: (date: string, data: any) => Promise<void>;
        }
      ).saveMealDataToDatabase('20241018', mockNeisResponse);

      expect(jest.mocked(prismaService.mealInfo).create).toHaveBeenCalled();
    });

    it('should not save duplicate meal data', async () => {
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue({
        id: 1,
        meal_date: new Date(2024, 9, 18),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥'],
      });
      const createSpy = jest.spyOn(prismaService.mealInfo, 'create');

      await (
        service as unknown as {
          saveMealDataToDatabase: (date: string, data: any) => Promise<void>;
        }
      ).saveMealDataToDatabase('20241018', mockNeisResponse);

      expect(createSpy).not.toHaveBeenCalled();
    });

    it('should handle database save errors gracefully', async () => {
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue(null);
      jest
        .spyOn(prismaService.mealInfo, 'create')
        .mockRejectedValue(new Error('Database error'));

      await expect(
        (
          service as unknown as {
            saveMealDataToDatabase: (date: string, data: any) => Promise<void>;
          }
        ).saveMealDataToDatabase('20241018', mockNeisResponse),
      ).resolves.not.toThrow();
    });
  });

  describe('Helper methods', () => {
    it('should parse date string correctly', () => {
      const result = (
        service as unknown as { parseDateFromString: (date: string) => Date }
      ).parseDateFromString('20241018');

      expect(result).toBeInstanceOf(Date);
      expect(result.getFullYear()).toBe(2024);
      expect(result.getMonth()).toBe(9); // October (0-indexed)
      expect(result.getDate()).toBe(18);
    });

    it('should throw error for invalid date string', () => {
      expect(() => {
        (
          service as unknown as { parseDateFromString: (date: string) => Date }
        ).parseDateFromString('invalid');
      }).toThrow();
    });

    it('should validate and format date correctly', () => {
      expect(
        (
          service as unknown as {
            validateAndFormatDate: (date: string) => string;
          }
        ).validateAndFormatDate('2024-10-18'),
      ).toBe('20241018');
      expect(
        (
          service as unknown as {
            validateAndFormatDate: (date: string) => string;
          }
        ).validateAndFormatDate('20241018'),
      ).toBe('20241018');
    });

    it('should extract error messages correctly', () => {
      expect(
        (
          service as unknown as { getErrorMessage: (error: any) => string }
        ).getErrorMessage(new Error('Test error')),
      ).toBe('Test error');
      expect(
        (
          service as unknown as { getErrorMessage: (error: any) => string }
        ).getErrorMessage('String error'),
      ).toBe('String error');
      expect(
        (
          service as unknown as { getErrorMessage: (error: any) => string }
        ).getErrorMessage({ message: 'Object error' }),
      ).toBe('Object error');
      expect(
        (
          service as unknown as { getErrorMessage: (error: any) => string }
        ).getErrorMessage(null),
      ).toBe('Unknown error occurred');
    });
  });

  describe('Cache operations', () => {
    it('should set cache with correct TTL', async () => {
      const setSpy = jest
        .spyOn(cacheManager, 'set')
        .mockResolvedValue(undefined);
      jest.spyOn(cacheManager, 'get').mockResolvedValue(null);
      jest.spyOn(prismaService.mealInfo, 'findFirst').mockResolvedValue(null);
      jest.spyOn(prismaService.mealInfo, 'create').mockResolvedValue({
        id: 1,
        meal_date: new Date(),
        meal_info: JSON.stringify(mockNeisResponse),
        dish_names: ['밥'],
      });
      jest.spyOn(httpService, 'get').mockReturnValue(
        of({
          data: mockNeisResponse,
          status: 200,
          statusText: 'OK',
          headers: {},
          config: {} as AxiosRequestConfig,
        } as AxiosResponse),
      );

      await service.getTodayLunch();

      expect(setSpy).toHaveBeenCalledWith(
        expect.any(String),
        expect.any(Object),
        3600,
      );
    });
  });
});
