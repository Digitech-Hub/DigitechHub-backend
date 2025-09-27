package kr.hs.sdh.digitechhubsso.service;

import kr.hs.sdh.digitechhubsso.dto.AuthResponseDTO;
import kr.hs.sdh.digitechhubsso.model.User;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Service;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.concurrent.TimeUnit;

@Service
@Slf4j
@RequiredArgsConstructor
public class CacheService {
    
    private final RedisTemplate<String, Object> redisTemplate;
    
    // Redis 키 패턴
    private static final String USER_SESSION_PREFIX = "user:session:";
    private static final String USER_PROFILE_PREFIX = "user:profile:";
    private static final String USER_PROFILE_EMAIL_PREFIX = "user:profile:email:";
    private static final String LOGIN_ATTEMPT_PREFIX = "login:attempt:";
    private static final String REFRESH_TOKEN_PREFIX = "refresh:token:";
    private static final String BLACKLIST_TOKEN_PREFIX = "blacklist:token:";
    
    // 캐시 만료 시간
    private static final Duration SESSION_EXPIRE_TIME = Duration.ofHours(24);
    private static final Duration PROFILE_EXPIRE_TIME = Duration.ofHours(1);
    private static final Duration LOGIN_ATTEMPT_EXPIRE_TIME = Duration.ofMinutes(15);
    private static final Duration REFRESH_TOKEN_EXPIRE_TIME = Duration.ofDays(7);
    private static final Duration BLACKLIST_EXPIRE_TIME = Duration.ofHours(24);
    
    /**
     * 사용자 세션 캐싱
     */
    public void cacheUserSession(String sessionId, User user) {
        String key = USER_SESSION_PREFIX + sessionId;
        try {
            redisTemplate.opsForValue().set(key, user, SESSION_EXPIRE_TIME);
            log.debug("User session cached: sessionId={}, userId={}", sessionId, user.getId());
        } catch (Exception e) {
            log.error("Failed to cache user session: {}", e.getMessage());
        }
    }
    
    /**
     * 사용자 세션 조회
     */
    public User getUserSession(String sessionId) {
        String key = USER_SESSION_PREFIX + sessionId;
        try {
            return (User) redisTemplate.opsForValue().get(key);
        } catch (Exception e) {
            log.error("Failed to get user session: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * 사용자 세션 삭제
     */
    public void removeUserSession(String sessionId) {
        String key = USER_SESSION_PREFIX + sessionId;
        try {
            redisTemplate.delete(key);
            log.debug("User session removed: sessionId={}", sessionId);
        } catch (Exception e) {
            log.error("Failed to remove user session: {}", e.getMessage());
        }
    }
    
    /**
     * 사용자 프로필 캐싱
     */
    public void cacheUserProfile(Long userId, User user) {
        String key = USER_PROFILE_PREFIX + userId;
        try {
            redisTemplate.opsForValue().set(key, user, PROFILE_EXPIRE_TIME);
            log.debug("User profile cached: userId={}", userId);
        } catch (Exception e) {
            log.error("Failed to cache user profile: {}", e.getMessage());
        }
    }
    
    /**
     * 사용자 프로필 조회
     */
    public User getUserProfile(Long userId) {
        String key = USER_PROFILE_PREFIX + userId;
        try {
            return (User) redisTemplate.opsForValue().get(key);
        } catch (Exception e) {
            log.error("Failed to get user profile: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * 사용자 프로필 삭제
     */
    public void removeUserProfile(Long userId) {
        String key = USER_PROFILE_PREFIX + userId;
        try {
            redisTemplate.delete(key);
            log.debug("User profile removed: userId={}", userId);
        } catch (Exception e) {
            log.error("Failed to remove user profile: {}", e.getMessage());
        }
    }
    
    /**
     * 이메일로 사용자 프로필 캐싱
     */
    public void cacheUserProfileByEmail(String email, User user) {
        String key = USER_PROFILE_EMAIL_PREFIX + email;
        try {
            redisTemplate.opsForValue().set(key, user, PROFILE_EXPIRE_TIME);
            log.debug("User profile cached by email: email={}, userId={}", email, user.getId());
        } catch (Exception e) {
            log.error("Failed to cache user profile by email: {}", e.getMessage());
        }
    }
    
    /**
     * 이메일로 사용자 프로필 조회
     */
    public User getUserProfileByEmail(String email) {
        String key = USER_PROFILE_EMAIL_PREFIX + email;
        try {
            return (User) redisTemplate.opsForValue().get(key);
        } catch (Exception e) {
            log.error("Failed to get user profile by email: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * 이메일로 사용자 프로필 삭제
     */
    public void removeUserProfileByEmail(String email) {
        String key = USER_PROFILE_EMAIL_PREFIX + email;
        try {
            redisTemplate.delete(key);
            log.debug("User profile removed by email: email={}", email);
        } catch (Exception e) {
            log.error("Failed to remove user profile by email: {}", e.getMessage());
        }
    }
    
    /**
     * 로그인 시도 횟수 증가
     */
    public void incrementLoginAttempts(String email) {
        String key = LOGIN_ATTEMPT_PREFIX + email;
        try {
            Long attempts = redisTemplate.opsForValue().increment(key);
            if (attempts == 1) {
                redisTemplate.expire(key, LOGIN_ATTEMPT_EXPIRE_TIME);
            }
            log.debug("Login attempts incremented: email={}, attempts={}", email, attempts);
        } catch (Exception e) {
            log.error("Failed to increment login attempts: {}", e.getMessage());
        }
    }
    
    /**
     * 로그인 시도 횟수 조회
     */
    public Long getLoginAttempts(String email) {
        String key = LOGIN_ATTEMPT_PREFIX + email;
        try {
            Object attempts = redisTemplate.opsForValue().get(key);
            return attempts != null ? Long.valueOf(attempts.toString()) : 0L;
        } catch (Exception e) {
            log.error("Failed to get login attempts: {}", e.getMessage());
            return 0L;
        }
    }
    
    /**
     * 로그인 시도 횟수 초기화
     */
    public void resetLoginAttempts(String email) {
        String key = LOGIN_ATTEMPT_PREFIX + email;
        try {
            redisTemplate.delete(key);
            log.debug("Login attempts reset: email={}", email);
        } catch (Exception e) {
            log.error("Failed to reset login attempts: {}", e.getMessage());
        }
    }
    
    /**
     * 리프레시 토큰 캐싱
     */
    public void cacheRefreshToken(String refreshToken, AuthResponseDTO authResponse) {
        String key = REFRESH_TOKEN_PREFIX + refreshToken;
        try {
            redisTemplate.opsForValue().set(key, authResponse, REFRESH_TOKEN_EXPIRE_TIME);
            log.debug("Refresh token cached: token={}", refreshToken.substring(0, 10) + "...");
        } catch (Exception e) {
            log.error("Failed to cache refresh token: {}", e.getMessage());
        }
    }
    
    /**
     * 리프레시 토큰 조회
     */
    public AuthResponseDTO getRefreshToken(String refreshToken) {
        String key = REFRESH_TOKEN_PREFIX + refreshToken;
        try {
            return (AuthResponseDTO) redisTemplate.opsForValue().get(key);
        } catch (Exception e) {
            log.error("Failed to get refresh token: {}", e.getMessage());
            return null;
        }
    }
    
    /**
     * 리프레시 토큰 삭제
     */
    public void removeRefreshToken(String refreshToken) {
        String key = REFRESH_TOKEN_PREFIX + refreshToken;
        try {
            redisTemplate.delete(key);
            log.debug("Refresh token removed: token={}", refreshToken.substring(0, 10) + "...");
        } catch (Exception e) {
            log.error("Failed to remove refresh token: {}", e.getMessage());
        }
    }
    
    /**
     * 토큰 블랙리스트 추가
     */
    public void addToBlacklist(String token) {
        String key = BLACKLIST_TOKEN_PREFIX + token;
        try {
            redisTemplate.opsForValue().set(key, "blacklisted", BLACKLIST_EXPIRE_TIME);
            log.debug("Token added to blacklist: token={}", token.substring(0, 10) + "...");
        } catch (Exception e) {
            log.error("Failed to add token to blacklist: {}", e.getMessage());
        }
    }
    
    /**
     * 토큰 블랙리스트 확인
     */
    public boolean isTokenBlacklisted(String token) {
        String key = BLACKLIST_TOKEN_PREFIX + token;
        try {
            return redisTemplate.hasKey(key);
        } catch (Exception e) {
            log.error("Failed to check token blacklist: {}", e.getMessage());
            return false;
        }
    }
    
    /**
     * 사용자 관련 모든 캐시 삭제
     */
    public void clearUserCache(Long userId) {
        try {
            // 프로필 캐시 삭제
            removeUserProfile(userId);
            
            // 세션 캐시는 개별적으로 삭제해야 함 (패턴 매칭 필요)
            log.debug("User cache cleared: userId={}", userId);
        } catch (Exception e) {
            log.error("Failed to clear user cache: {}", e.getMessage());
        }
    }
    
    /**
     * 이메일로 사용자 관련 모든 캐시 삭제
     */
    public void clearUserCacheByEmail(String email) {
        try {
            // 이메일 기반 프로필 캐시 삭제
            removeUserProfileByEmail(email);
            
            // 로그인 시도 횟수 초기화
            resetLoginAttempts(email);
            
            log.debug("User cache cleared by email: email={}", email);
        } catch (Exception e) {
            log.error("Failed to clear user cache by email: {}", e.getMessage());
        }
    }
    
    /**
     * Redis 연결 상태 확인
     */
    public boolean isRedisAvailable() {
        try {
            redisTemplate.opsForValue().get("health_check");
            return true;
        } catch (Exception e) {
            log.error("Redis is not available: {}", e.getMessage());
            return false;
        }
    }
}
