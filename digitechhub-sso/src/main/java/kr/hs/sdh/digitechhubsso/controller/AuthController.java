package kr.hs.sdh.digitechhubsso.controller;

import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
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
@Tag(name = "인증 API", description = "사용자 인증 관련 API 엔드포인트")
public class AuthController {
    
    private final AuthService authService;
    
    @Value("${app.frontend.url:http://localhost:5173}")
    private String frontendUrl;

    /**
     * 회원가입
     */
    @Operation(summary = "회원가입", description = "새로운 사용자를 등록합니다. 이메일 인증이 필요한 경우 인증 링크가 발송됩니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "201", description = "회원가입 성공",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "400", description = "잘못된 요청 데이터",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "409", description = "이미 존재하는 이메일")
    })
    @PostMapping("/register")
    public ResponseEntity<ApiResponseDTO<Map<String, Object>>> register(
            @Valid @RequestBody @Schema(description = "회원가입 요청 정보") RegisterUserRequestDTO dto) {
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
    @Operation(summary = "로그인", description = "이메일과 비밀번호로 로그인합니다. 성공 시 Access Token과 Refresh Token을 반환합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "로그인 성공",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "401", description = "인증 실패 (잘못된 이메일/비밀번호)",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "403", description = "인증 실패 (이메일 미인증 등)",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class)))
    })
    @PostMapping("/login")
    public ResponseEntity<ApiResponseDTO<AuthResponseDTO>> login(
            @Valid @RequestBody @Schema(description = "로그인 요청 정보") LoginRequestDTO dto,
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
    @Operation(summary = "이메일 인증", description = "이메일로 받은 인증 토큰으로 이메일을 인증합니다. 성공/실패 시 프론트엔드로 리다이렉트됩니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "302", description = "리다이렉트 (성공 또는 실패 페이지로 이동)"),
        @ApiResponse(responseCode = "400", description = "잘못된 토큰")
    })
    @GetMapping("/verify-email")
    public void verifyEmail(
            @Parameter(description = "이메일 인증 토큰", required = true, example = "eyJhbGc...")
            @RequestParam("token") String token, 
            HttpServletResponse response) throws IOException {
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
    @Operation(summary = "토큰 갱신", description = "Refresh Token을 사용하여 새로운 Access Token과 Refresh Token을 발급받습니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "토큰 갱신 성공",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "401", description = "토큰 만료 또는 무효한 토큰",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class)))
    })
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
    @Operation(summary = "토큰 검증", description = "Access Token의 유효성을 검증합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "토큰 검증 성공",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "401", description = "토큰 만료 또는 무효한 토큰",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class)))
    })
    @PostMapping("/validate")
    public ResponseEntity<ApiResponseDTO<Map<String, Object>>> validate(
            @Parameter(description = "Authorization 헤더 (Bearer token)", required = true, 
                       example = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            @RequestHeader("Authorization") String authHeader) {
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
    @Operation(summary = "로그아웃", description = "사용자 로그아웃을 처리합니다. Refresh Token을 무효화합니다.")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "로그아웃 성공",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class))),
        @ApiResponse(responseCode = "401", description = "인증 실패",
                content = @Content(mediaType = "application/json",
                        schema = @Schema(implementation = ApiResponseDTO.class)))
    })
    @PostMapping("/logout")
    public ResponseEntity<ApiResponseDTO<Map<String, Object>>> logout(
            @Parameter(description = "Authorization 헤더 (Bearer token)", required = true,
                       example = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
            @RequestHeader("Authorization") String authHeader,
            HttpServletResponse httpResponse) {
        ApiResponseDTO<Map<String, Object>> response = authService.logout(authHeader, httpResponse);
        return ResponseEntity.ok(response);
    }

    @Operation(summary = "Health Check", description = "서비스 상태를 확인합니다.")
    @ApiResponse(responseCode = "200", description = "서비스 정상")
    @GetMapping("/health")
    public ResponseEntity<String> health() {
        return ResponseEntity.ok("OK");
    }
}
