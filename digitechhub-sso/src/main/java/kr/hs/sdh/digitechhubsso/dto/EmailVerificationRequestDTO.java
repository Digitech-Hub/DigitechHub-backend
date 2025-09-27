package kr.hs.sdh.digitechhubsso.dto;

import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class EmailVerificationRequestDTO {
    
    @NotBlank(message = "토큰은 필수입니다")
    private String token;
}
