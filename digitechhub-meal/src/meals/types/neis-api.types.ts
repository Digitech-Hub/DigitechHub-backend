export interface NeisMealInfo {
  ATPT_OFCDC_SC_CODE: string;
  ATPT_OFCDC_SC_NM: string;
  SD_SCHUL_CODE: string;
  SCHUL_NM: string;
  MMEAL_SC_CODE: string;
  MMEAL_SC_NM: string;
  MLSV_YMD: string;
  MLSV_FGR: string;
  DDISH_NM: string;
  ORPLC_INFO: string;
  CAL_INFO: string;
  NTR_INFO: string;
  MLSV_FROM_YMD: string;
  MLSV_TO_YMD: string;
}

export interface NeisResult {
  CODE: string;
  MESSAGE: string;
}

export interface NeisResponse {
  mealServiceDietInfo: Array<{
    head: Array<{
      list_total_count: number;
      RESULT: NeisResult;
    }>;
    row?: NeisMealInfo[];
  }>;
}

// 빈 데이터 응답 타입
export interface NeisEmptyResponse {
  RESULT: NeisResult;
}

export interface MealResponse {
  success: boolean;
  message: string;
  data: {
    mealInfo?: NeisResponse | NeisEmptyResponse;
    dishNames?: string[];
    date: string;
    hasData: boolean;
    cached: boolean;
    responseTime?: number;
  } | null;
}
