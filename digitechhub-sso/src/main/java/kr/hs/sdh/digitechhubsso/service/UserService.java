package kr.hs.sdh.digitechhubsso.service;

import kr.hs.sdh.digitechhubsso.model.EmailToken;
import kr.hs.sdh.digitechhubsso.model.User;
import kr.hs.sdh.digitechhubsso.repository.EmailTokenRepository;
import kr.hs.sdh.digitechhubsso.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Service
@Slf4j
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {
    
    private final UserRepository userRepository;
    private final EmailTokenRepository emailTokenRepository;
    private final TokenService tokenService;
    
    /**
     * 사용자 저장
     */
    @Transactional
    public User save(User user) {
        return userRepository.save(user);
    }
    
    /**
     * 이메일로 사용자 조회 (이메일 토큰 포함)
     * N+1 문제 해결을 위한 fetch join 사용
     */
    public Optional<User> findByEmailWithTokens(String email) {
        return userRepository.findByEmailWithEmailTokens(email);
    }
    
    /**
     * ID로 사용자 조회 (이메일 토큰 포함)
     * N+1 문제 해결을 위한 fetch join 사용
     */
    public Optional<User> findByIdWithTokens(Long id) {
        return userRepository.findByIdWithEmailTokens(id);
    }
    
    /**
     * 이메일로 사용자 조회 (유효한 이메일 토큰만 포함)
     */
    public Optional<User> findByEmailWithValidTokens(String email) {
        return userRepository.findByEmailWithValidEmailTokens(email);
    }
    
    /**
     * 이메일 인증이 필요한 사용자들 조회
     */
    public List<User> findUsersNeedingEmailVerification() {
        return userRepository.findUsersNeedingEmailVerification();
    }
    
    /**
     * 이메일 인증 토큰 생성 및 저장
     */
    @Transactional
    public EmailToken createEmailVerificationToken(User user) {
        // 기존 유효한 토큰들 무효화
        invalidateExistingTokens(user);
        
        String rawToken = tokenService.generateRandomToken();
        String hashedToken = tokenService.generateHashToken(rawToken);
        
        EmailToken emailToken = EmailToken.builder()
                .token(hashedToken)
                .expirationTime(LocalDateTime.now().plusHours(24))
                .user(user)
                .build();
        
        // 양방향 관계 설정
        user.addEmailToken(emailToken);
        
        EmailToken savedToken = emailTokenRepository.save(emailToken);
        log.info("Completed: Email verification token created - userId={}, tokenId={}", user.getId(), savedToken.getId());
        
        return savedToken;
    }
    
    /**
     * 이메일 토큰으로 사용자 조회 (사용자 정보 포함)
     */
    public Optional<User> findUserByEmailToken(String token) {
        return emailTokenRepository.findByTokenWithUser(token)
                .map(EmailToken::getUser);
    }
    
    /**
     * 이메일로 사용자 조회 (refresh token용)
     */
    public Optional<User> findUserByEmail(String email) {
        return userRepository.findByEmail(email);
    }
    
    /**
     * 이메일 인증 처리
     */
    @Transactional
    public boolean verifyEmail(String token) {
        Optional<EmailToken> tokenOpt = emailTokenRepository.findByTokenWithUser(token);
        
        if (tokenOpt.isEmpty()) {
            log.warn("Token not found: {}", token);
            return false;
        }
        
        EmailToken emailToken = tokenOpt.get();
        
        if (!emailToken.isValid()) {
            log.warn("Invalid token: {}", token);
            return false;
        }
        
        User user = emailToken.getUser();
        user.markEmailAsVerified();
        emailToken.markAsUsed();
        
        userRepository.save(user);
        emailTokenRepository.save(emailToken);
        
        log.info("Completed: Email verification completed - userId={}, email={}", user.getId(), user.getEmail());
        return true;
    }
    
    /**
     * 사용자의 기존 유효한 토큰들 무효화
     */
    @Transactional
    public void invalidateExistingTokens(User user) {
        List<EmailToken> validTokens = user.getValidEmailTokens();
        validTokens.forEach(token -> {
            token.markAsUsed();
            emailTokenRepository.save(token);
        });
        
        if (!validTokens.isEmpty()) {
            log.info("Completed: Invalidated existing tokens - userId={}, count={}", user.getId(), validTokens.size());
        }
    }
    
    /**
     * 만료된 토큰들 정리
     */
    @Transactional
    public int cleanupExpiredTokens() {
        int deletedCount = emailTokenRepository.deleteExpiredTokens(LocalDateTime.now());
        log.info("Completed: Cleaned up expired tokens - {} deleted", deletedCount);
        return deletedCount;
    }
    
    /**
     * 특정 사용자의 만료된 토큰들 정리
     */
    @Transactional
    public int cleanupExpiredTokensByUser(Long userId) {
        int deletedCount = emailTokenRepository.deleteExpiredTokensByUserId(userId, LocalDateTime.now());
        log.info("Completed: Cleaned up expired tokens by user - userId={}, {} deleted", userId, deletedCount);
        return deletedCount;
    }
    
    /**
     * 사용자 삭제 시 관련 토큰들도 함께 삭제
     */
    @Transactional
    public void deleteUserWithTokens(Long userId) {
        int deletedTokens = emailTokenRepository.deleteByUserId(userId);
        userRepository.deleteById(userId);
        log.info("Completed: Deleted user and related tokens - userId={}, {} tokens deleted", userId, deletedTokens);
    }
    
    /**
     * 사용자의 토큰 통계 조회
     */
    public TokenStats getUserTokenStats(Long userId) {
        long totalTokens = emailTokenRepository.countByUserId(userId);
        long validTokens = emailTokenRepository.countValidTokensByUserId(userId, LocalDateTime.now());
        
        return new TokenStats(totalTokens, validTokens);
    }
    
    /**
     * 토큰 통계 DTO
     */
    public record TokenStats(long totalTokens, long validTokens) {
        public long getExpiredTokens() {
            return totalTokens - validTokens;
        }
    }
}
