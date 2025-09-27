package kr.hs.sdh.digitechhubsso.controller;

import jakarta.servlet.http.HttpServletResponse;
import jakarta.validation.Valid;
import kr.hs.sdh.digitechhubsso.dto.*;
import kr.hs.sdh.digitechhubsso.service.AuthService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;
import java.util.Map;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
@Slf4j
public class AuthController {
    
    private final AuthService authService;
    
    @Value("${app.frontend.url:http://localhost:5173}")
    private String frontendUrl;

    /**
     * 회원가입
     */
    @PostMapping("/register")
    public ResponseEntity<ApiResponseDTO<Map<String, Object>>> register(@Valid @RequestBody RegisterUserRequestDTO dto) {
        ApiResponseDTO<Map<String, Object>> response = authService.register(dto);
        
        if (response.isSuccess()) {
            return ResponseEntity.status(HttpStatus.CREATED).body(response);
        } else {
            return ResponseEntity.badRequest().body(response);
        }
    }

    /**
     * 로그인
     */
    @PostMapping("/login")
    public ResponseEntity<ApiResponseDTO<AuthResponseDTO>> login(
            @Valid @RequestBody LoginRequestDTO dto,
            HttpServletResponse httpResponse) {
        ApiResponseDTO<AuthResponseDTO> response = authService.login(dto, httpResponse);
        
        if (response.isSuccess()) {
            return ResponseEntity.ok(response);
        } else {
            HttpStatus status = response.getMessage().contains("인증") ? 
                    HttpStatus.FORBIDDEN : HttpStatus.UNAUTHORIZED;
            return ResponseEntity.status(status).body(response);
        }
    }

    /**
     * 이메일 인증 (프론트엔드로 리다이렉트)
     */
    @GetMapping("/verify-email")
    public void verifyEmail(@RequestParam("token") String token, HttpServletResponse response) throws IOException {
        EmailVerificationRequestDTO dto = new EmailVerificationRequestDTO();
        dto.setToken(token);
        
        ApiResponseDTO<Map<String, Object>> result = authService.verifyEmail(dto);
        
        if (result.isSuccess()) {
            // 성공 시 프론트엔드 성공 페이지로 리다이렉트
            String successUrl = frontendUrl + "/auth/verify-success?message=" + 
                java.net.URLEncoder.encode("이메일 인증이 완료되었습니다.", "UTF-8");
            response.sendRedirect(successUrl);
        } else {
            // 실패 시 프론트엔드 실패 페이지로 리다이렉트
            String errorUrl = frontendUrl + "/auth/verify-error?message=" + 
                java.net.URLEncoder.encode(result.getMessage(), "UTF-8");
            response.sendRedirect(errorUrl);
        }
    }

    /**
     * 토큰 갱신
     */
    @PostMapping("/refresh")
    public ResponseEntity<ApiResponseDTO<AuthResponseDTO>> refresh(
            jakarta.servlet.http.HttpServletRequest request,
            HttpServletResponse httpResponse) {
        ApiResponseDTO<AuthResponseDTO> response = authService.refresh(request, httpResponse);
        
        if (response.isSuccess()) {
            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
        }
    }

    /**
     * 토큰 검증
     */
    @PostMapping("/validate")
    public ResponseEntity<ApiResponseDTO<Map<String, Object>>> validate(@RequestHeader("Authorization") String authHeader) {
        ApiResponseDTO<Map<String, Object>> response = authService.validate(authHeader);
        
        if (response.isSuccess()) {
            return ResponseEntity.ok(response);
        } else {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(response);
        }
    }

    /**
     * 로그아웃
     */
    @PostMapping("/logout")
    public ResponseEntity<ApiResponseDTO<Map<String, Object>>> logout(
            @RequestHeader("Authorization") String authHeader,
            HttpServletResponse httpResponse) {
        ApiResponseDTO<Map<String, Object>> response = authService.logout(authHeader, httpResponse);
        return ResponseEntity.ok(response);
    }

    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }
}
