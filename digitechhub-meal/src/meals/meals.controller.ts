import { Controller, Get, Query } from '@nestjs/common';
import { ApiOperation, ApiQuery, ApiResponse, ApiTags } from '@nestjs/swagger';
import { MealResponseDto } from './dto/meal-response.dto';
import { MealsService } from './meals.service';

@ApiTags('Meals')
@Controller('api/meals')
export class MealsController {
  constructor(private readonly mealsService: MealsService) {}

  @Get('today')
  @ApiOperation({
    summary: '오늘의 급식 조회',
    description: '오늘 날짜의 급식 정보를 조회합니다.',
  })
  @ApiResponse({
    status: 200,
    description: '성공적으로 급식 정보를 반환합니다.',
    type: MealResponseDto,
  })
  async getTodayLunch(): Promise<MealResponseDto> {
    return await this.mealsService.getTodayLunch();
  }

  @Get('date')
  @ApiOperation({
    summary: '특정 날짜의 급식 조회',
    description: '지정한 날짜의 급식 정보를 조회합니다.',
  })
  @ApiQuery({
    name: 'date',
    description: '조회할 날짜 (YYYYMMDD 형식, 예: 20250101)',
    required: true,
    example: '20250101',
  })
  @ApiResponse({
    status: 200,
    description: '성공적으로 급식 정보를 반환합니다.',
    type: MealResponseDto,
  })
  async getMealByDate(@Query('date') date: string): Promise<MealResponseDto> {
    return await this.mealsService.getMealByDate(date);
  }
}
