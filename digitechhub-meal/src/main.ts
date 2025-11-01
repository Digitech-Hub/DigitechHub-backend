import { NestFactory } from '@nestjs/core';
import { AppModule } from './app.module';
import { DocumentBuilder, SwaggerModule } from '@nestjs/swagger';

async function bootstrap() {
  const app = await NestFactory.create(AppModule);

  // Swagger 설정
  const config = new DocumentBuilder()
    .setTitle('Digitech Hub Meal API')
    .setDescription('급식 정보 제공을 위한 마이크로서비스 API')
    .setVersion('1.0.0')
    .build();
  const document = SwaggerModule.createDocument(app, config);
  SwaggerModule.setup('docs', app, document);
  SwaggerModule.setup('api/meal/docs', app, document); // Kong Gateway 경로

  await app.listen(process.env.PORT ?? 3000);
}
void bootstrap();
