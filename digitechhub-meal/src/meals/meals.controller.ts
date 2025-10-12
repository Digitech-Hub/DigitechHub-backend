import { Controller, Get, Query } from '@nestjs/common';
import { MealsService } from './meals.service';
import { MealResponse } from './types/neis-api.types';

@Controller('api/meals')
export class MealsController {
  constructor(private readonly mealsService: MealsService) {}

  @Get('today')
  getTodayLunch(): Promise<MealResponse> {
    return this.mealsService.getTodayLunch();
  }

  @Get('date')
  getMealByDate(@Query('date') date: string): Promise<MealResponse> {
    return this.mealsService.getMealByDate(date);
  }
}
