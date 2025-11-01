package kr.hs.sdh.digitechhubsso.config;

import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/docs").setViewName("forward:/swagger-ui/index.html");
        registry.addViewController("/api/auth/docs").setViewName("forward:/swagger-ui/index.html");
    }
}

