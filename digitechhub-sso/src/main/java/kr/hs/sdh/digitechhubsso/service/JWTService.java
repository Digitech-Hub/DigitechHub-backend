package kr.hs.sdh.digitechhubsso.service;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import kr.hs.sdh.digitechhubsso.model.Role;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.FileSystemResource;
import org.springframework.stereotype.Service;

import java.io.IOException;
import java.nio.file.Files;
import java.security.KeyFactory;
import java.security.NoSuchAlgorithmException;
import java.security.PrivateKey;
import java.security.PublicKey;
import java.security.spec.InvalidKeySpecException;
import java.security.spec.PKCS8EncodedKeySpec;
import java.security.spec.X509EncodedKeySpec;
import java.util.Base64;
import java.util.Date;

@Service
public class JWTService {
    @Value("${jwt.expiration}")
    private long jwtExpiration;

    @Value("${jwt.refresh-expiration}")
    private long jwtRefreshExpiration;

    @Value("${jwt.private-key-path:/app/keys/private_key.pem}")
    private String privateKeyPath;

    @Value("${jwt.public-key-path:/app/keys/public_key.pem}")
    private String publicKeyPath;

    private PrivateKey getPrivateKey() {
        try {
            FileSystemResource resource = new FileSystemResource(privateKeyPath);
            byte[] keyBytes = Files.readAllBytes(resource.getFile().toPath());
            
            String privateKeyContent = new String(keyBytes)
                    .replace("-----BEGIN PRIVATE KEY-----", "")
                    .replace("-----END PRIVATE KEY-----", "")
                    .replaceAll("\\s", "");
            
            byte[] decodedKey = Base64.getDecoder().decode(privateKeyContent);
            PKCS8EncodedKeySpec keySpec = new PKCS8EncodedKeySpec(decodedKey);
            KeyFactory keyFactory = KeyFactory.getInstance("RSA");
            
            return keyFactory.generatePrivate(keySpec);
        } catch (IOException | NoSuchAlgorithmException | InvalidKeySpecException e) {
            throw new RuntimeException("Failed to load private key", e);
        }
    }

    private PublicKey getPublicKey() {
        try {
            FileSystemResource resource = new FileSystemResource(publicKeyPath);
            byte[] keyBytes = Files.readAllBytes(resource.getFile().toPath());
            
            String publicKeyContent = new String(keyBytes)
                    .replace("-----BEGIN PUBLIC KEY-----", "")
                    .replace("-----END PUBLIC KEY-----", "")
                    .replaceAll("\\s", "");
            
            byte[] decodedKey = Base64.getDecoder().decode(publicKeyContent);
            X509EncodedKeySpec keySpec = new X509EncodedKeySpec(decodedKey);
            KeyFactory keyFactory = KeyFactory.getInstance("RSA");
            
            return keyFactory.generatePublic(keySpec);
        } catch (IOException | NoSuchAlgorithmException | InvalidKeySpecException e) {
            throw new RuntimeException("Failed to load public key", e);
        }
    }

    public String generateToken(String username, Long userId, Role role) {
        return Jwts.builder()
                .subject(username)
                .claim("userId", userId)
                .claim("role", role.name())
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + jwtExpiration))
                .signWith(getPrivateKey(), Jwts.SIG.RS256)
                .compact();
    }

    public Claims parseToken(String token) {
        return Jwts.parser()
                .verifyWith(getPublicKey())
                .build()
                .parseSignedClaims(token)
                .getPayload();
    }

    /**
     * 리프레시 토큰 생성
     */
    public String generateRefreshToken(String username, Long userId) {
        return Jwts.builder()
                .subject(username)
                .claim("userId", userId)
                .claim("type", "refresh")
                .issuedAt(new Date())
                .expiration(new Date(System.currentTimeMillis() + jwtRefreshExpiration))
                .signWith(getPrivateKey(), Jwts.SIG.RS256)
                .compact();
    }

    /**
     * 토큰 유효성 검증
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                    .verifyWith(getPublicKey())
                    .build()
                    .parseSignedClaims(token);
            return true;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * 토큰에서 사용자명 추출
     */
    public String getUsernameFromToken(String token) {
        try {
            Claims claims = parseToken(token);
            return claims.getSubject();
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 토큰에서 사용자 ID 추출
     */
    public Long getUserIdFromToken(String token) {
        try {
            Claims claims = parseToken(token);
            return claims.get("userId", Long.class);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 토큰에서 사용자 역할 추출
     */
    public String getRoleFromToken(String token) {
        try {
            Claims claims = parseToken(token);
            return claims.get("role", String.class);
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 토큰 만료 여부 확인
     */
    public boolean isTokenExpired(String token) {
        try {
            Claims claims = parseToken(token);
            return claims.getExpiration().before(new Date());
        } catch (Exception e) {
            return true;
        }
    }
}
