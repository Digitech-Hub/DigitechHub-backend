import { NeisResponse, NeisEmptyResponse } from '../types/neis-api.types';

/**
 * 안전한 JSON 직렬화/역직렬화를 위한 헬퍼 함수
 */
export function safeJsonStringify<T>(value: T): string {
  try {
    return JSON.stringify(value);
  } catch (error) {
    console.error('JSON stringify error:', error);
    return '{}';
  }
}

export function safeJsonParse<T>(value: string): T | null {
  try {
    return JSON.parse(value) as T;
  } catch (error) {
    console.error('JSON parse error:', error);
    return null;
  }
}

/**
 * 안전한 JSON 파싱과 타입 검증을 동시에 수행
 */
export function safeParseMealData(
  data: string,
): NeisResponse | NeisEmptyResponse | null {
  try {
    let parsed: unknown;

    if (typeof data === 'string') {
      try {
        parsed = JSON.parse(data);
      } catch (parseError) {
        console.error('JSON parse error:', parseError);
        return null;
      }
    } else {
      parsed = data;
    }

    // 타입 가드 함수들을 사용하여 안전하게 타입 검증
    if (isEmptyDataResponse(parsed)) {
      return parsed;
    }

    if (isValidMealResponse(parsed)) {
      return parsed;
    }

    return null;
  } catch (error) {
    console.error('Failed to parse meal data:', error);
    return null;
  }
}

/**
 * 타입 가드: 빈 데이터 응답인지 확인
 */
export function isEmptyDataResponse(data: unknown): data is NeisEmptyResponse {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const obj = data as Record<string, unknown>;

  if (
    !('RESULT' in obj) ||
    typeof obj.RESULT !== 'object' ||
    obj.RESULT === null
  ) {
    return false;
  }

  const result = obj.RESULT as Record<string, unknown>;

  return (
    'CODE' in result &&
    'MESSAGE' in result &&
    typeof result.CODE === 'string' &&
    typeof result.MESSAGE === 'string' &&
    result.CODE === 'INFO-200' &&
    result.MESSAGE === '해당하는 데이터가 없습니다.'
  );
}

/**
 * 타입 가드: 유효한 급식 데이터 응답인지 확인
 */
export function isValidMealResponse(data: unknown): data is NeisResponse {
  if (typeof data !== 'object' || data === null) {
    return false;
  }

  const obj = data as Record<string, unknown>;

  return (
    'mealServiceDietInfo' in obj &&
    Array.isArray(obj.mealServiceDietInfo) &&
    obj.mealServiceDietInfo.length > 0 &&
    typeof obj.mealServiceDietInfo === 'object'
  );
}

/**
 * DDISH_NM에서 요리명을 추출하고 <br/> 태그를 제거
 */
export function extractDishNames(mealInfo: NeisResponse): string[] {
  const dishNames: string[] = [];

  try {
    for (const dietInfo of mealInfo.mealServiceDietInfo) {
      if (dietInfo.row && Array.isArray(dietInfo.row)) {
        for (const row of dietInfo.row) {
          if (row.DDISH_NM && typeof row.DDISH_NM === 'string') {
            // <br/> 태그를 제거하고 줄바꿈으로 분리
            const cleanedDishes = row.DDISH_NM.replace(/<br\s*\/?>/gi, '\n') // <br/> 또는 <br> 태그를 줄바꿈으로 변경
              .split('\n') // 줄바꿈으로 분리
              .map((dish) => dish.trim()) // 앞뒤 공백 제거
              .filter((dish) => dish.length > 0) // 빈 문자열만 제거
              .map((dish) => dish.replace(/^·/, '')) // · 기호 제거
              .map((dish) => dish.replace(/\s*\([^)]*\)/g, '')); // 괄호와 그 앞의 공백 제거

            dishNames.push(...cleanedDishes);
          }
        }
      }
    }
  } catch (error) {
    console.error('Failed to extract dish names:', error);
  }

  return dishNames;
}
