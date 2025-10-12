package kr.hs.sdh.digitechhubsso.service;

import jakarta.servlet.http.Cookie;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import kr.hs.sdh.digitechhubsso.dto.*;
import kr.hs.sdh.digitechhubsso.model.EmailToken;
import kr.hs.sdh.digitechhubsso.model.Role;
import kr.hs.sdh.digitechhubsso.model.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.Arrays;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

@Service
@Slf4j
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class AuthService {
    
    private final UserService userService;
    private final JWTService jwtService;
    private final EmailService emailService;
    private final PasswordEncoder passwordEncoder;
    private final CacheService cacheService;
    
    // 쿠키 설정 상수
    private static final String REFRESH_TOKEN_COOKIE_NAME = "digitechhub_refreshToken";
    @Value("${jwt.refresh-expiration}")
    private int REFRESH_TOKEN_COOKIE_MAX_AGE;
    
    /**
     * 회원가입 처리
     */
    @Transactional
    public ApiResponseDTO<Map<String, Object>> register(RegisterUserRequestDTO dto) {
        try {
            // 이메일 중복 확인
            if (userService.findByEmailWithTokens(dto.getEmail()).isPresent()) {
                return ApiResponseDTO.error("이미 사용 중인 이메일입니다");
            }
            
            // 전화번호 중복 확인
            if (userService.findByEmailWithTokens(dto.getPhone()).isPresent()) {
                return ApiResponseDTO.error("이미 사용 중인 전화번호입니다");
            }
            
            // 사용자 생성
            User user = User.builder()
                    .email(dto.getEmail())
                    .name(dto.getName())
                    .password(passwordEncoder.encode(dto.getPassword()))
                    .phone(dto.getPhone())
                    .role(Role.valueOf(dto.getRole()))
                    .build();
            
            // 사용자 저장
            User savedUser = userService.save(user);
            
            // 이메일 인증 토큰 생성
            EmailToken emailToken = userService.createEmailVerificationToken(savedUser);
            
            // 인증 이메일 전송
            emailService.sendVerificationEmail(
                    savedUser.getEmail(),
                    "DigitechHub 이메일 인증",
                    emailToken.getToken()
            );
            
            log.info("User registered successfully: {}", savedUser.getEmail());
            
            return ApiResponseDTO.success(
                    "회원가입이 완료되었습니다. 이메일을 확인하여 인증을 완료해주세요.",
                    Map.of("userId", savedUser.getId(), "email", savedUser.getEmail())
            );
                    
        } catch (Exception e) {
            log.error("Registration failed: {}", e.getMessage(), e);
            return ApiResponseDTO.error("회원가입 중 오류가 발생했습니다");
        }
    }
    
    /**
     * 로그인 처리 (Redis 캐싱 적용)
     */
    @Transactional
    public ApiResponseDTO<AuthResponseDTO> login(LoginRequestDTO dto, HttpServletResponse response) {
        try {
            // 로그인 시도 횟수 확인
            Long loginAttempts = cacheService.getLoginAttempts(dto.getEmail());
            if (loginAttempts >= 5) {
                return ApiResponseDTO.error("너무 많은 로그인 시도가 있었습니다. 15분 후 다시 시도해주세요.");
            }
            
            // 캐시에서 사용자 프로필 조회 시도
            User user = cacheService.getUserProfileByEmail(dto.getEmail());
            if (user == null) {
                // 캐시에 없으면 DB에서 조회
                user = userService.findByEmailWithTokens(dto.getEmail()).orElse(null);
                if (user != null) {
                    // 사용자 프로필 캐싱
                    cacheService.cacheUserProfileByEmail(dto.getEmail(), user);
                }
            }
            
            if (user == null || !passwordEncoder.matches(dto.getPassword(), user.getPassword())) {
                // 로그인 실패 시 시도 횟수 증가
                cacheService.incrementLoginAttempts(dto.getEmail());
                return ApiResponseDTO.error("이메일 또는 비밀번호가 올바르지 않습니다");
            }
            
            // 이메일 인증 확인
            if (!user.isEmailVerified()) {
                return ApiResponseDTO.error("이메일 인증이 필요합니다");
            }
            
            // 로그인 성공 시 시도 횟수 초기화
            cacheService.resetLoginAttempts(dto.getEmail());
            
            // JWT 토큰 생성
            String accessToken = jwtService.generateToken(user.getEmail(), user.getId(), user.getRole());
            String refreshToken = jwtService.generateRefreshToken(user.getEmail(), user.getId());
            
            // 마지막 로그인 시간 업데이트
            user.updateLastLogin();
            userService.save(user);
            
            // 응답 데이터 생성
            AuthResponseDTO.UserInfo userInfo = AuthResponseDTO.UserInfo.builder()
                    .id(user.getId())
                    .email(user.getEmail())
                    .name(user.getName())
                    .phone(user.getPhone())
                    .role(user.getRole())
                    .isEmailVerified(user.isEmailVerified())
                    .lastLogin(user.getLastLogin())
                    .createdAt(user.getCreatedAt())
                    .build();
            
            AuthResponseDTO authResponse = AuthResponseDTO.builder()
                    .accessToken(accessToken)
                    .refreshToken(refreshToken)
                    .expiresIn(86400L) // 24시간
                    .user(userInfo)
                    .build();
            
            // 세션 ID 생성 및 캐싱
            String sessionId = UUID.randomUUID().toString();
            cacheService.cacheUserSession(sessionId, user);
            
            // 리프레시 토큰 캐싱
            cacheService.cacheRefreshToken(refreshToken, authResponse);
            
            // refresh token을 쿠키로 설정
            setRefreshTokenCookie(response, refreshToken);
            
            // 응답에서 refresh token 제거 (쿠키로만 전송)
            AuthResponseDTO authDataWithoutRefreshToken = AuthResponseDTO.builder()
                    .accessToken(accessToken)
                    .expiresIn(86400L)
                    .user(userInfo)
                    .build();
            
            log.info("User logged in successfully: {}", user.getEmail());
            
            return ApiResponseDTO.success("로그인 성공", authDataWithoutRefreshToken);
            
        } catch (Exception e) {
            log.error("Login failed: {}", e.getMessage(), e);
            return ApiResponseDTO.error("로그인 중 오류가 발생했습니다");
        }
    }
    
    /**
     * 이메일 인증 처리
     */
    @Transactional
    public ApiResponseDTO<Map<String, Object>> verifyEmail(EmailVerificationRequestDTO dto) {
        try {
            boolean success = userService.verifyEmail(dto.getToken());
            
            if (success) {
                return ApiResponseDTO.success(
                        "이메일 인증이 완료되었습니다",
                        Map.of("verified", true)
                );
            } else {
                return ApiResponseDTO.error("유효하지 않거나 만료된 토큰입니다");
            }
            
        } catch (Exception e) {
            log.error("Email verification failed: {}", e.getMessage(), e);
            return ApiResponseDTO.error("이메일 인증 중 오류가 발생했습니다");
        }
    }
    
    /**
     * 토큰 갱신 처리 (Redis 캐싱 적용)
     */
    @Transactional
    public ApiResponseDTO<AuthResponseDTO> refresh(HttpServletRequest request, HttpServletResponse response) {
        try {
            // 쿠키에서 refresh token 추출
            String refreshToken = getRefreshTokenFromCookie(request);
            
            if (refreshToken == null || refreshToken.isEmpty()) {
                return ApiResponseDTO.error("리프레시 토큰이 없습니다");
            }
            
            // JWT refresh token 유효성 검증
            if (!jwtService.validateToken(refreshToken)) {
                return ApiResponseDTO.error("유효하지 않은 리프레시 토큰입니다");
            }
            
            // refresh token이 만료되었는지 확인
            if (jwtService.isTokenExpired(refreshToken)) {
                return ApiResponseDTO.error("만료된 리프레시 토큰입니다");
            }
            
            // refresh token에서 사용자 이메일 추출
            String userEmail = jwtService.getUsernameFromToken(refreshToken);
            if (userEmail == null) {
                return ApiResponseDTO.error("리프레시 토큰에서 사용자 정보를 찾을 수 없습니다");
            }
            
            // 캐시에서 리프레시 토큰 조회
            AuthResponseDTO cachedResponse = cacheService.getRefreshToken(refreshToken);
            if (cachedResponse != null) {
                // 캐시에서 조회된 경우 새로운 액세스 토큰만 생성
                String newAccessToken = jwtService.generateToken(
                        cachedResponse.getUser().getEmail(),
                        cachedResponse.getUser().getId(),
                        cachedResponse.getUser().getRole()
                );
                
                AuthResponseDTO newResponse = AuthResponseDTO.builder()
                        .accessToken(newAccessToken)
                        .refreshToken(refreshToken) // 기존 refresh token 유지
                        .expiresIn(86400L)
                        .user(cachedResponse.getUser())
                        .build();
                
                // 새로운 응답으로 캐시 업데이트
                cacheService.cacheRefreshToken(refreshToken, newResponse);
                
                // 응답에서 refresh token 제거 (쿠키로만 전송)
                AuthResponseDTO authDataWithoutRefreshToken = AuthResponseDTO.builder()
                        .accessToken(newAccessToken)
                        .expiresIn(86400L)
                        .user(cachedResponse.getUser())
                        .build();
                
                return ApiResponseDTO.success("토큰 갱신 성공", authDataWithoutRefreshToken);
            }
            
            // 캐시에 없으면 DB에서 사용자 조회
            User user = userService.findUserByEmail(userEmail).orElse(null);
            
            if (user == null) {
                return ApiResponseDTO.error("사용자를 찾을 수 없습니다");
            }
            
            // 이메일 인증 확인
            if (!user.isEmailVerified()) {
                return ApiResponseDTO.error("이메일 인증이 필요합니다");
            }
            
            // 새로운 액세스 토큰 생성
            String newAccessToken = jwtService.generateToken(user.getEmail(), user.getId(), user.getRole());
            
            AuthResponseDTO.UserInfo userInfo = AuthResponseDTO.UserInfo.builder()
                    .id(user.getId())
                    .email(user.getEmail())
                    .name(user.getName())
                    .phone(user.getPhone())
                    .role(user.getRole())
                    .isEmailVerified(user.isEmailVerified())
                    .lastLogin(user.getLastLogin())
                    .createdAt(user.getCreatedAt())
                    .build();
            
            AuthResponseDTO authResponse = AuthResponseDTO.builder()
                    .accessToken(newAccessToken)
                    .refreshToken(refreshToken)
                    .expiresIn(86400L)
                    .user(userInfo)
                    .build();
            
            // 새로운 응답을 캐시에 저장
            cacheService.cacheRefreshToken(refreshToken, authResponse);
            
            // 응답에서 refresh token 제거 (쿠키로만 전송)
            AuthResponseDTO authDataWithoutRefreshToken = AuthResponseDTO.builder()
                    .accessToken(newAccessToken)
                    .expiresIn(86400L)
                    .user(userInfo)
                    .build();
            
            return ApiResponseDTO.success("토큰 갱신 성공", authDataWithoutRefreshToken);
            
        } catch (Exception e) {
            log.error("Token refresh failed: {}", e.getMessage(), e);
            // refresh token이 유효하지 않으면 쿠키 삭제
            clearRefreshTokenCookie(response);
            return ApiResponseDTO.error("토큰 갱신 중 오류가 발생했습니다");
        }
    }
    
    /**
     * 토큰 검증 처리 (Redis 블랙리스트 확인)
     */
    public ApiResponseDTO<Map<String, Object>> validate(String authHeader) {
        try {
            if (authHeader == null || !authHeader.startsWith("Bearer ")) {
                return ApiResponseDTO.error("유효하지 않은 인증 헤더입니다");
            }
            
            String token = authHeader.substring(7);
            
            // 블랙리스트 확인
            if (cacheService.isTokenBlacklisted(token)) {
                return ApiResponseDTO.error("로그아웃된 토큰입니다");
            }
            
            boolean isValid = jwtService.validateToken(token);
            
            if (isValid) {
                return ApiResponseDTO.success(
                        "토큰이 유효합니다",
                        Map.of("valid", true)
                );
            } else {
                return ApiResponseDTO.error("유효하지 않은 토큰입니다");
            }
            
        } catch (Exception e) {
            log.error("Token validation failed: {}", e.getMessage(), e);
            return ApiResponseDTO.error("토큰 검증 중 오류가 발생했습니다");
        }
    }
    
    /**
     * 로그아웃 처리 (Redis 캐시 정리)
     */
    public ApiResponseDTO<Map<String, Object>> logout(String authHeader, HttpServletResponse response) {
        try {
            if (authHeader != null && authHeader.startsWith("Bearer ")) {
                String token = authHeader.substring(7);
                
                // 토큰을 블랙리스트에 추가
                cacheService.addToBlacklist(token);
                
                // 사용자 정보 추출하여 관련 캐시 정리
                String username = jwtService.getUsernameFromToken(token);
                if (username != null) {
                    cacheService.clearUserCacheByEmail(username);
                }
            }
            
            // refresh token 쿠키 삭제
            clearRefreshTokenCookie(response);
            
            return ApiResponseDTO.success(
                    "로그아웃이 완료되었습니다",
                    Map.of("loggedOut", true)
            );
            
        } catch (Exception e) {
            log.error("Logout failed: {}", e.getMessage(), e);
            return ApiResponseDTO.error("로그아웃 중 오류가 발생했습니다");
        }
    }
    
    /**
     * 쿠키에서 refresh token 추출
     */
    private String getRefreshTokenFromCookie(HttpServletRequest request) {
        if (request.getCookies() == null) {
            return null;
        }
        
        Optional<Cookie> refreshTokenCookie = Arrays.stream(request.getCookies())
                .filter(cookie -> REFRESH_TOKEN_COOKIE_NAME.equals(cookie.getName()))
                .findFirst();
        
        return refreshTokenCookie.map(Cookie::getValue).orElse(null);
    }
    
    /**
     * refresh token 쿠키 설정
     */
    private void setRefreshTokenCookie(HttpServletResponse response, String refreshToken) {
        Cookie cookie = new Cookie(REFRESH_TOKEN_COOKIE_NAME, refreshToken);
        cookie.setHttpOnly(true); // XSS 공격 방지
        cookie.setSecure(true); // HTTPS에서만 전송
        cookie.setPath("/"); // 모든 경로에서 접근 가능
        cookie.setMaxAge(REFRESH_TOKEN_COOKIE_MAX_AGE); // 7일
        // SameSite 설정은 Spring Boot 2.6+ 에서 자동으로 처리됨
        
        response.addCookie(cookie);
        log.debug("Refresh token cookie set");
    }
    
    /**
     * refresh token 쿠키 삭제
     */
    private void clearRefreshTokenCookie(HttpServletResponse response) {
        Cookie cookie = new Cookie(REFRESH_TOKEN_COOKIE_NAME, "");
        cookie.setHttpOnly(true);
        cookie.setSecure(true);
        cookie.setPath("/");
        cookie.setMaxAge(0); // 즉시 만료
        
        response.addCookie(cookie);
        log.debug("Refresh token cookie cleared");
    }
}
