package kr.hs.sdh.digitechhubsso.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;
import jakarta.validation.constraints.Size;
import lombok.Data;

@Data
public class RegisterUserRequestDTO {
    
    @Email(message = "올바른 이메일 형식이 아닙니다")
    @NotBlank(message = "이메일은 필수입니다")
    private String email;
    
    @NotBlank(message = "이름은 필수입니다")
    @Size(min = 2, max = 50, message = "이름은 2-50자 사이여야 합니다")
    private String name;
    
    @NotBlank(message = "비밀번호는 필수입니다")
    @Size(min = 8, max = 100, message = "비밀번호는 8-100자 사이여야 합니다")
    private String password;
    
    @Pattern(regexp = "^\\d{3}[-]?\\d{4}[-]?\\d{4}$", message = "올바른 전화번호 형식이 아닙니다 (예: 010-1234-5678 또는 01012345678)")
    @NotBlank(message = "전화번호는 필수입니다")
    private String phone;
    
    @NotBlank(message = "역할은 필수입니다")
    @Pattern(regexp = "^(TEACHER|STUDENT)$", message = "역할은 TEACHER, STUDENT 중 하나여야 합니다")
    private String role;
}