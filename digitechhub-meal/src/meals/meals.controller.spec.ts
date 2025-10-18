/* eslint-disable @typescript-eslint/unbound-method */
import { Test, TestingModule } from '@nestjs/testing';
import { MealsController } from './meals.controller';
import { MealsService } from './meals.service';
import { MealResponse } from './types/neis-api.types';

describe('MealsController', () => {
  let controller: MealsController;
  let service: MealsService;

  const mockSuccessResponse: MealResponse = {
    success: true,
    message: '식단 정보를 가져왔습니다.',
    data: {
      mealInfo: {
        mealServiceDietInfo: [
          {
            head: [
              {
                list_total_count: 1,
                RESULT: { CODE: 'INFO-000', MESSAGE: '정상 처리되었습니다.' },
              },
            ],
            row: [
              {
                ATPT_OFCDC_SC_CODE: 'B10',
                ATPT_OFCDC_SC_NM: '서울특별시교육청',
                SD_SCHUL_CODE: '7010572',
                SCHUL_NM: '서울디지텍고등학교',
                MMEAL_SC_CODE: '2',
                MMEAL_SC_NM: '중식',
                MLSV_YMD: '20251016',
                MLSV_FGR: '240',
                DDISH_NM:
                  '·혼합잡곡밥 (5)<br/>·사골소고기국 (5.6.13.16)<br/>·브로콜리&초장 (5.6.13)<br/>·베이컨스크램블에그 (1.5.10.13)<br/>·언양식불고기(완제)&파채 (2.5.16.6.10)<br/>·배추김치 (9)<br/>·미니약과 1개 (5.6)',
                ORPLC_INFO:
                  '쇠고기(종류) : 호주산<br/>돼지고기 식육가공품 : 언양식(국내산),베이컨(수입)<br/>닭고기 식육가공품 : 국내산<br/>쌀 : 국내산<br/>배추 : 국내산<br/>고춧가루 : 국내산<br/>비고 : ',
                CAL_INFO: '777.4 Kcal',
                NTR_INFO:
                  '탄수화물(g) : 98.2<br/>단백질(g) : 38.4<br/>지방(g) : 23.8<br/>비타민A(R.E) : 168.5<br/>티아민(mg) : 0.4<br/>리보플라빈(mg) : 0.6<br/>비타민C(mg) : 25.7<br/>칼슘(mg) : 164.9<br/>철분(mg) : 5.4',
                MLSV_FROM_YMD: '20251016',
                MLSV_TO_YMD: '20251016',
              },
            ],
          },
        ],
      },
      dishNames: [
        '혼합잡곡밥',
        '사골소고기국',
        '브로콜리&초장',
        '베이컨스크램블에그',
        '언양식불고기&파채',
        '배추김치',
        '미니약과 1개',
      ],
      date: '20251016',
      hasData: true,
      cached: false,
      responseTime: 56,
    },
  };

  const mockEmptyResponse: MealResponse = {
    success: true,
    message: '해당 날짜의 식단 정보가 없습니다.',
    data: {
      mealInfo: {
        RESULT: { CODE: 'INFO-200', MESSAGE: '해당하는 데이터가 없습니다.' },
      },
      dishNames: [],
      date: '20251017',
      hasData: false,
      cached: false,
      responseTime: 12,
    },
  };

  beforeEach(async () => {
    const mockMealService = {
      getTodayLunch: jest.fn(),
      getMealByDate: jest.fn(),
    };

    const module: TestingModule = await Test.createTestingModule({
      controllers: [MealsController],
      providers: [{ provide: MealsService, useValue: mockMealService }],
    }).compile();

    controller = module.get<MealsController>(MealsController);
    service = module.get<MealsService>(MealsService);
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  it('should be defined', () => {
    expect(controller).toBeDefined();
  });

  describe('getTodayLunch', () => {
    it('should return today lunch data when successful', async () => {
      // Given
      (service.getTodayLunch as jest.Mock).mockResolvedValue(
        mockSuccessResponse,
      );

      // When
      const result = await controller.getTodayLunch();

      // Then
      expect(service.getTodayLunch).toHaveBeenCalledTimes(1);
      expect(service.getTodayLunch).toHaveBeenCalledWith();
      expect(result).toEqual(mockSuccessResponse);
      expect(result.success).toBe(true);
      expect(result.data?.hasData).toBe(true);
      expect(result.data?.dishNames).toHaveLength(7);
      expect(result.data?.dishNames).toContain('혼합잡곡밥');
    });

    it('should return empty response when no data available', async () => {
      // Given
      (service.getTodayLunch as jest.Mock).mockResolvedValue(mockEmptyResponse);

      // When
      const result = await controller.getTodayLunch();

      // Then
      expect(service.getTodayLunch).toHaveBeenCalledTimes(1);
      expect(result).toEqual(mockEmptyResponse);
      expect(result.success).toBe(true);
      expect(result.data?.hasData).toBe(false);
      expect(result.data?.dishNames).toHaveLength(0);
    });

    it('should handle service errors', async () => {
      // Given
      const errorMessage = 'API 호출 중 오류가 발생했습니다.';
      (service.getTodayLunch as jest.Mock).mockRejectedValue(
        new Error(errorMessage),
      );

      // When & Then
      await expect(controller.getTodayLunch()).rejects.toThrow(errorMessage);
      expect(service.getTodayLunch).toHaveBeenCalledTimes(1);
    });
  });

  describe('getMealByDate', () => {
    it('should return meal data for valid date', async () => {
      // Given
      const testDate = '20251016';
      (service.getMealByDate as jest.Mock).mockResolvedValue(
        mockSuccessResponse,
      );

      // When
      const result = await controller.getMealByDate(testDate);

      // Then
      expect(service.getMealByDate).toHaveBeenCalledTimes(1);
      expect(service.getMealByDate).toHaveBeenCalledWith(testDate);
      expect(result).toEqual(mockSuccessResponse);
      expect(result.success).toBe(true);
      expect(result.data?.date).toBe(testDate);
    });

    it('should return empty response for date with no meal data', async () => {
      // Given
      const testDate = '20251017';
      const emptyResponseForDate = {
        ...mockEmptyResponse,
        data: { ...mockEmptyResponse.data, date: testDate },
      };
      (service.getMealByDate as jest.Mock).mockResolvedValue(
        emptyResponseForDate,
      );

      // When
      const result = await controller.getMealByDate(testDate);

      // Then
      expect(service.getMealByDate).toHaveBeenCalledTimes(1);
      expect(service.getMealByDate).toHaveBeenCalledWith(testDate);
      expect(result).toEqual(emptyResponseForDate);
      expect(result.data?.hasData).toBe(false);
      expect(result.data?.date).toBe(testDate);
    });

    it('should handle invalid date format', async () => {
      // Given
      const invalidDate = 'invalid-date';
      const errorResponse: MealResponse = {
        success: false,
        message: '잘못된 날짜 형식입니다. YYYY-MM-DD 형식으로 입력해주세요.',
        data: {
          mealInfo: {
            RESULT: { CODE: 'ERROR-400', MESSAGE: 'Invalid date format' },
          },
          dishNames: [],
          date: invalidDate,
          hasData: false,
          cached: false,
          responseTime: 0,
        },
      };
      (service.getMealByDate as jest.Mock).mockResolvedValue(errorResponse);

      // When
      const result = await controller.getMealByDate(invalidDate);

      // Then
      expect(service.getMealByDate).toHaveBeenCalledTimes(1);
      expect(service.getMealByDate).toHaveBeenCalledWith(invalidDate);
      expect(result.success).toBe(false);
      expect(result.message).toContain('잘못된 날짜 형식');
    });

    it('should handle service errors', async () => {
      // Given
      const testDate = '20251016';
      const errorMessage = '데이터베이스 연결 오류가 발생했습니다.';
      (service.getMealByDate as jest.Mock).mockRejectedValue(
        new Error(errorMessage),
      );

      // When & Then
      await expect(controller.getMealByDate(testDate)).rejects.toThrow(
        errorMessage,
      );
      expect(service.getMealByDate).toHaveBeenCalledTimes(1);
      expect(service.getMealByDate).toHaveBeenCalledWith(testDate);
    });

    it('should handle empty date parameter', async () => {
      // Given
      const emptyDate = '';
      const errorResponse: MealResponse = {
        success: false,
        message: '날짜를 입력해주세요.',
        data: {
          mealInfo: {
            RESULT: {
              CODE: 'ERROR-400',
              MESSAGE: 'Date parameter is required',
            },
          },
          dishNames: [],
          date: emptyDate,
          hasData: false,
          cached: false,
          responseTime: 0,
        },
      };
      (service.getMealByDate as jest.Mock).mockResolvedValue(errorResponse);

      // When
      const result = await controller.getMealByDate(emptyDate);

      // Then
      expect(service.getMealByDate).toHaveBeenCalledTimes(1);
      expect(service.getMealByDate).toHaveBeenCalledWith(emptyDate);
      expect(result.success).toBe(false);
      expect(result.message).toContain('날짜를 입력해주세요');
    });
  });
});
