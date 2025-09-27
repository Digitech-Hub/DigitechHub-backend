package kr.hs.sdh.digitechhubsso.repository;

import kr.hs.sdh.digitechhubsso.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    
    /**
     * 이메일로 사용자 조회 (이메일 토큰 포함)
     * N+1 문제 해결을 위한 fetch join 사용
     */
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.emailTokens WHERE u.email = :email")
    Optional<User> findByEmailWithEmailTokens(@Param("email") String email);
    
    /**
     * ID로 사용자 조회 (이메일 토큰 포함)
     * N+1 문제 해결을 위한 fetch join 사용
     */
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.emailTokens WHERE u.id = :id")
    Optional<User> findByIdWithEmailTokens(@Param("id") Long id);
    
    /**
     * 이메일로 사용자 조회 (유효한 이메일 토큰만 포함)
     * 만료되지 않고 사용되지 않은 토큰만 fetch join
     */
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.emailTokens et " +
           "WHERE u.email = :email AND (et IS NULL OR (et.expirationTime > CURRENT_TIMESTAMP AND et.usedAt IS NULL))")
    Optional<User> findByEmailWithValidEmailTokens(@Param("email") String email);
    
    /**
     * 모든 사용자 조회 (이메일 토큰 포함)
     * 관리자용 - 모든 사용자와 토큰 정보를 한 번에 조회
     */
    @Query("SELECT DISTINCT u FROM User u LEFT JOIN FETCH u.emailTokens ORDER BY u.createdAt DESC")
    List<User> findAllWithEmailTokens();
    
    /**
     * 이메일 인증이 필요한 사용자들 조회
     * 학생/교사 중 이메일 인증이 완료되지 않은 사용자들
     */
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.emailTokens " +
           "WHERE (u.role = 'STUDENT' AND u.isVerifiedStudent = false) OR " +
           "(u.role = 'TEACHER' AND u.isVerifiedTeacher = false)")
    List<User> findUsersNeedingEmailVerification();
    
    /**
     * 특정 역할의 사용자들 조회 (이메일 토큰 포함)
     */
    @Query("SELECT u FROM User u LEFT JOIN FETCH u.emailTokens WHERE u.role = :role")
    List<User> findByRoleWithEmailTokens(@Param("role") String role);
    
    /**
     * 기본 이메일 조회 (토큰 없이)
     * 단순 조회용
     */
    Optional<User> findByEmail(String email);
    
    /**
     * 전화번호로 사용자 조회
     */
    Optional<User> findByPhone(String phone);
    
    /**
     * 이메일 존재 여부 확인
     */
    boolean existsByEmail(String email);
    
    /**
     * 전화번호 존재 여부 확인
     */
    boolean existsByPhone(String phone);
}
