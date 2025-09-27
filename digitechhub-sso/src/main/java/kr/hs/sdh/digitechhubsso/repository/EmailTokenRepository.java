package kr.hs.sdh.digitechhubsso.repository;

import kr.hs.sdh.digitechhubsso.model.EmailToken;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface EmailTokenRepository extends JpaRepository<EmailToken, Long> {
    
    /**
     * 토큰으로 조회 (사용자 정보 포함)
     * N+1 문제 해결을 위한 fetch join 사용
     */
    @Query("SELECT et FROM EmailToken et JOIN FETCH et.user WHERE et.token = :token")
    Optional<EmailToken> findByTokenWithUser(@Param("token") String token);
    
    /**
     * 사용자 ID로 유효한 토큰들 조회
     * 만료되지 않고 사용되지 않은 토큰들만 조회
     */
    @Query("SELECT et FROM EmailToken et WHERE et.user.id = :userId " +
           "AND et.expirationTime > :currentTime AND et.usedAt IS NULL")
    List<EmailToken> findValidTokensByUserId(@Param("userId") Long userId, @Param("currentTime") LocalDateTime currentTime);
    
    /**
     * 사용자 ID로 모든 토큰 조회 (사용자 정보 포함)
     */
    @Query("SELECT et FROM EmailToken et JOIN FETCH et.user WHERE et.user.id = :userId ORDER BY et.createdAt DESC")
    List<EmailToken> findByUserIdWithUser(@Param("userId") Long userId);
    
    /**
     * 만료된 토큰들 조회
     * 정리 작업용
     */
    @Query("SELECT et FROM EmailToken et WHERE et.expirationTime < :currentTime")
    List<EmailToken> findExpiredTokens(@Param("currentTime") LocalDateTime currentTime);
    
    /**
     * 사용된 토큰들 조회
     * 정리 작업용
     */
    @Query("SELECT et FROM EmailToken et WHERE et.usedAt IS NOT NULL")
    List<EmailToken> findUsedTokens();
    
    /**
     * 특정 사용자의 만료된 토큰들 조회
     */
    @Query("SELECT et FROM EmailToken et WHERE et.user.id = :userId AND et.expirationTime < :currentTime")
    List<EmailToken> findExpiredTokensByUserId(@Param("userId") Long userId, @Param("currentTime") LocalDateTime currentTime);
    
    /**
     * 특정 사용자의 사용된 토큰들 조회
     */
    @Query("SELECT et FROM EmailToken et WHERE et.user.id = :userId AND et.usedAt IS NOT NULL")
    List<EmailToken> findUsedTokensByUserId(@Param("userId") Long userId);
    
    /**
     * 토큰 존재 여부 확인
     */
    boolean existsByToken(String token);
    
    /**
     * 사용자별 토큰 개수 조회
     */
    @Query("SELECT COUNT(et) FROM EmailToken et WHERE et.user.id = :userId")
    long countByUserId(@Param("userId") Long userId);
    
    /**
     * 사용자별 유효한 토큰 개수 조회
     */
    @Query("SELECT COUNT(et) FROM EmailToken et WHERE et.user.id = :userId " +
           "AND et.expirationTime > :currentTime AND et.usedAt IS NULL")
    long countValidTokensByUserId(@Param("userId") Long userId, @Param("currentTime") LocalDateTime currentTime);
    
    /**
     * 만료된 토큰들 일괄 삭제
     * @return 삭제된 토큰 개수
     */
    @Modifying
    @Query("DELETE FROM EmailToken et WHERE et.expirationTime < :currentTime")
    int deleteExpiredTokens(@Param("currentTime") LocalDateTime currentTime);
    
    /**
     * 특정 사용자의 만료된 토큰들 일괄 삭제
     * @return 삭제된 토큰 개수
     */
    @Modifying
    @Query("DELETE FROM EmailToken et WHERE et.user.id = :userId AND et.expirationTime < :currentTime")
    int deleteExpiredTokensByUserId(@Param("userId") Long userId, @Param("currentTime") LocalDateTime currentTime);
    
    /**
     * 사용자 삭제 시 관련 토큰들도 함께 삭제
     * @return 삭제된 토큰 개수
     */
    @Modifying
    @Query("DELETE FROM EmailToken et WHERE et.user.id = :userId")
    int deleteByUserId(@Param("userId") Long userId);
}
