import { Controller, Get, Query } from '@nestjs/common';
import { MealsService } from './meals.service';
import { MealResponse } from './types/neis-api.types';

@Controller('api/meals')
export class MealsController {
  constructor(private readonly mealsService: MealsService) {}

  @Get('today')
  async getTodayLunch(): Promise<MealResponse> {
    return await this.mealsService.getTodayLunch();
  }

  @Get('date')
  async getMealByDate(@Query('date') date: string): Promise<MealResponse> {
    return await this.mealsService.getMealByDate(date);
  }
}
