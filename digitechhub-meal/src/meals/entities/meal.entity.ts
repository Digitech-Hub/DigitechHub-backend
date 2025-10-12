import { Prisma } from '@prisma/client';

export class MealInfo {
  id: number;
  meal_date: Date;
  meal_info: Prisma.JsonValue;
}
