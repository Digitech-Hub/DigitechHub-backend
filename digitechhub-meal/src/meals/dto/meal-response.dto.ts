import { ApiProperty } from '@nestjs/swagger';

class MealDataDto {
  @ApiProperty({ required: false })
  mealInfo?: any;

  @ApiProperty({ required: false, type: [String], description: '요리 이름 목록' })
  dishNames?: string[];

  @ApiProperty({ description: '조회 날짜 (YYYYMMDD)' })
  date: string;

  @ApiProperty({ description: '데이터 존재 여부' })
  hasData: boolean;

  @ApiProperty({ description: '캐시 여부' })
  cached: boolean;

  @ApiProperty({ required: false, description: '응답 시간(ms)' })
  responseTime?: number;
}

export class MealResponseDto {
  @ApiProperty({ description: '성공 여부' })
  success: boolean;

  @ApiProperty({ description: '응답 메시지' })
  message: string;

  @ApiProperty({ type: MealDataDto, nullable: true })
  data: MealDataDto | null;
}
