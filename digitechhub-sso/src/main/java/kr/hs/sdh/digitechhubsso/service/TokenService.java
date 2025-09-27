package kr.hs.sdh.digitechhubsso.service;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.security.SecureRandom;
import java.util.Base64;

@Service
public class TokenService {
    
    private final PasswordEncoder passwordEncoder = new BCryptPasswordEncoder();
    private final SecureRandom secureRandom = new SecureRandom();
    
    /**
     * 랜덤 토큰을 생성합니다.
     * 
     * @return 32바이트 랜덤 토큰 (Base64 인코딩)
     */
    public String generateRandomToken() {
        byte[] tokenBytes = new byte[32];
        secureRandom.nextBytes(tokenBytes);
        return Base64.getUrlEncoder().withoutPadding().encodeToString(tokenBytes);
    }
    
    /**
     * 토큰을 해시화합니다.
     * 
     * @param rawToken 원본 토큰
     * @return 해시화된 토큰
     */
    public String generateHashToken(String rawToken) {
        return passwordEncoder.encode(rawToken);
    }

}