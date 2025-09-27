package kr.hs.sdh.digitechhubsso.model;

import jakarta.persistence.*;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

@Entity
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Getter
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Email(message = "올바른 이메일 형식이 아닙니다")
    @NotBlank(message = "이메일은 필수입니다")
    @Column(unique = true, nullable = false)
    private String email;

    // Setter 메서드들
    @Setter
    @NotBlank(message = "이름은 필수입니다")
    @Size(min = 2, max = 50, message = "이름은 2-50자 사이여야 합니다")
    @Column(nullable = false)
    private String name;

    @NotBlank(message = "비밀번호는 필수입니다")
    @Column(nullable = false)
    private String password;

    @Setter
    @Pattern(regexp = "^\\d{3}[-]?\\d{4}[-]?\\d{4}$", message = "올바른 전화번호 형식이 아닙니다 (예: 010-1234-5678 또는 01012345678)")
    @NotBlank(message = "전화번호는 필수입니다")
    @Column(nullable = false, unique = true)
    private String phone;

    @Setter
    @Column(nullable = true)
    private LocalDateTime lastLogin;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    @Setter
    @Enumerated(EnumType.STRING)
    private Role role;

    @Column
    @Builder.Default
    private Boolean isVerifiedStudent = false;

    @Column
    @Builder.Default
    private Boolean isVerifiedTeacher = false;

    // 이메일 토큰과의 일대다 관계
    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL, orphanRemoval = true, fetch = FetchType.LAZY)
    @Builder.Default
    private List<EmailToken> emailTokens = new ArrayList<>();

    // JPA 생명주기 메서드
    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        this.updatedAt = LocalDateTime.now();
    }

    // 비즈니스 메서드
    public void updateLastLogin() {
        this.lastLogin = LocalDateTime.now();
    }

    public String getDisplayName() {
        return name + " (" + email + ")";
    }

    public boolean isAdmin() {
        return Role.ADMIN.equals(this.role);
    }

    public boolean isTeacher() {
        return Role.TEACHER.equals(this.role);
    }

    public boolean isStudent() {
        return Role.STUDENT.equals(this.role);
    }

    public void updateProfile(String name, String phone) {
        setName(name);
        setPhone(phone);
    }

    public void updatePassword(String hashedPassword) {
        this.password = hashedPassword;
    }

    // 이메일 토큰 관련 비즈니스 메서드
    public void addEmailToken(EmailToken emailToken) {
        if (this.emailTokens == null) {
            this.emailTokens = new ArrayList<>();
        }
        this.emailTokens.add(emailToken);
        emailToken.setUser(this);
    }

    public void removeEmailToken(EmailToken emailToken) {
        if (this.emailTokens != null) {
            this.emailTokens.remove(emailToken);
        }
        emailToken.setUser(null);
    }

    public List<EmailToken> getValidEmailTokens() {
        if (this.emailTokens == null) {
            return new ArrayList<>();
        }
        return this.emailTokens.stream()
                .filter(EmailToken::isValid)
                .toList();
    }
    
    public void clearExpiredTokens() {
        if (this.emailTokens != null) {
            this.emailTokens.removeIf(EmailToken::isExpired);
        }
    }

    public void markEmailAsVerified() {
        if (this.role == Role.STUDENT) {
            this.isVerifiedStudent = true;
        } else if (this.role == Role.TEACHER) {
            this.isVerifiedTeacher = true;
        }
    }

    public boolean isEmailVerified() {
        return (this.role == Role.STUDENT && this.isVerifiedStudent) ||
               (this.role == Role.TEACHER && this.isVerifiedTeacher) ||
               (this.role == Role.ADMIN);
    }
}
