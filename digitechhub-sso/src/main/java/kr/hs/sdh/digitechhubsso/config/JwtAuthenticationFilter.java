package kr.hs.sdh.digitechhubsso.config;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.ExpiredJwtException;
import io.jsonwebtoken.MalformedJwtException;
import io.jsonwebtoken.UnsupportedJwtException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import kr.hs.sdh.digitechhubsso.service.JWTService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Component
@RequiredArgsConstructor
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JWTService jwtService;
    private static final String AUTHORIZATION_HEADER = "Authorization";
    private static final String BEARER_PREFIX = "Bearer ";

    @Override
    protected boolean shouldNotFilter(HttpServletRequest request) {
        String path = request.getRequestURI();
        log.debug("JWT Filter 체크: path={}", path);
        // Swagger UI 및 API 문서 경로는 필터 건너뛰기
        boolean shouldSkip = path.startsWith("/api/auth/docs") ||
               path.startsWith("/api/auth/swagger-ui") ||
               path.startsWith("/api/auth/v3/api-docs") ||
               path.startsWith("/swagger-ui") ||
               path.startsWith("/v3/api-docs") ||
               path.startsWith("/swagger-resources") ||
               path.startsWith("/webjars") ||
               path.equals("/docs") ||
               path.startsWith("/docs/") ||
               path.equals("/error");
        if (shouldSkip) {
            log.debug("JWT Filter 건너뜀: path={}", path);
        }
        return shouldSkip;
    }

    @Override
    protected void doFilterInternal(HttpServletRequest request,
                                    HttpServletResponse response,
                                    FilterChain filterChain) throws ServletException, IOException {

        String jwt = resolveToken(request);

        if (StringUtils.hasText(jwt)) {
            try {
                Claims claims = jwtService.parseToken(jwt);
                String username = claims.getSubject();

                // 멀티 Role 지원: roles claim이 List<String>일 경우
                List<String> roles = extractRoles(claims);

                if (username != null && !roles.isEmpty()) {
                    List<SimpleGrantedAuthority> authorities = roles.stream()
                            .map(role -> new SimpleGrantedAuthority("ROLE_" + role))
                            .collect(Collectors.toList());

                    UsernamePasswordAuthenticationToken authentication =
                            new UsernamePasswordAuthenticationToken(username, null, authorities);
                    SecurityContextHolder.getContext().setAuthentication(authentication);

                    log.debug("JWT 인증 성공: username={}, roles={}", username, roles);
                }
            } catch (ExpiredJwtException e) {
                log.warn("JWT 토큰 만료: {}", e.getMessage());
                sendUnauthorized(response, "토큰이 만료되었습니다");
                return;
            } catch (UnsupportedJwtException e) {
                log.warn("지원하지 않는 JWT 토큰: {}", e.getMessage());
                sendUnauthorized(response, "지원하지 않는 토큰입니다");
                return;
            } catch (MalformedJwtException e) {
                log.warn("잘못된 JWT 토큰: {}", e.getMessage());
                sendUnauthorized(response, "잘못된 토큰입니다");
                return;
            } catch (Exception e) {
                log.error("JWT 처리 오류: {}", e.getMessage());
                sendUnauthorized(response, "토큰 처리 중 오류가 발생했습니다");
                return;
            }
        }

        filterChain.doFilter(request, response);
    }

    private String resolveToken(HttpServletRequest request) {
        String bearerToken = request.getHeader(AUTHORIZATION_HEADER);
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith(BEARER_PREFIX)) {
            return bearerToken.substring(BEARER_PREFIX.length());
        }
        return null;
    }

    /**
     * JWT Claims에서 역할(Roles) 정보를 안전하게 추출합니다.
     * 
     * @param claims JWT Claims 객체
     * @return 역할 목록 (List<String>)
     */
    private List<String> extractRoles(Claims claims) {
        try {
            // 멀티 Role 지원: roles claim이 List<String>일 경우
            Object rolesObj = claims.get("roles");
            if (rolesObj instanceof List<?> rolesList) {
                return rolesList.stream()
                        .filter(role -> role instanceof String)
                        .map(role -> (String) role)
                        .collect(Collectors.toList());
            }
            
            // 기존 단일 role 호환
            String singleRole = claims.get("role", String.class);
            if (singleRole != null && !singleRole.trim().isEmpty()) {
                return List.of(singleRole);
            }
            
            return Collections.emptyList();
        } catch (Exception e) {
            log.warn("역할 정보 추출 중 오류 발생: {}", e.getMessage());
            return Collections.emptyList();
        }
    }

    /**
     * 인증 실패 시 JSON 응답을 전송합니다.
     * 
     * @param response HTTP 응답 객체
     * @param message 에러 메시지
     * @throws IOException IO 예외
     */
    private void sendUnauthorized(HttpServletResponse response, String message) throws IOException {
        response.setContentType("application/json;charset=UTF-8");
        response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
        response.getWriter().write("{\"error\":\"" + message + "\"}");
        response.getWriter().flush();
        SecurityContextHolder.clearContext();
    }
}
