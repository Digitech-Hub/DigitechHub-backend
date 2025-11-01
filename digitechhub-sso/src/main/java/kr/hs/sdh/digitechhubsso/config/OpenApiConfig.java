package kr.hs.sdh.digitechhubsso.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class OpenApiConfig {

    @Value("${app.domain:http://localhost:8080}")
    private String domain;

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("Digitech Hub SSO API")
                        .version("1.0.0")
                        .description("Digitech Hub Single Sign-On 서비스 API 문서"))
                .servers(List.of(
                        new Server().url("http://localhost:8080").description("로컬 개발 서버"),
                        new Server().url("http://localhost:8000").description("Kong Gateway"),
                        new Server().url(domain).description("프로덕션 서버")
                ));
    }
}

