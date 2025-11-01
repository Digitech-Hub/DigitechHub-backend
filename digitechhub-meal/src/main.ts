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
  
  // Kong Gateway를 위한 Swagger UI 경로 추가
  app.use('/api/meal/docs', (req, res, next) => {
    if (req.url === '/api/meal/docs' || req.url === '/api/meal/docs/') {
      res.redirect('/docs');
    } else {
      next();
    }
  });

  await app.listen(process.env.PORT ?? 3000);
}
void bootstrap();
