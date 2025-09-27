package kr.hs.sdh.digitechhubsso.service;

import jakarta.mail.MessagingException;
import jakarta.mail.internet.MimeMessage;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.mail.javamail.JavaMailSender;
import org.springframework.mail.javamail.MimeMessageHelper;
import org.springframework.stereotype.Service;

@Service
@Slf4j
@RequiredArgsConstructor
public class EmailService {
    private final JavaMailSender mailSender;

    @Value("${app.domain:http://localhost:8080}")
    private String baseDomain;

    @Value("${spring.mail.username}")
    private String fromEmail;

    /**
     * 이메일 인증 링크를 전송합니다.
     * 
     * @param to 수신자 이메일
     * @param subject 이메일 제목
     * @param rawToken 인증 토큰
     */
    public void sendVerificationEmail(String to, String subject, String rawToken) {
        MimeMessage mimeMessage = mailSender.createMimeMessage();
        String text = generateVerificationContent(rawToken);

        try {
            MimeMessageHelper helper = new MimeMessageHelper(mimeMessage, true, "UTF-8");
            helper.setFrom(fromEmail);
            helper.setTo(to);
            helper.setSubject(subject);
            helper.setText(text, true); // HTML 형식으로 전송
            
            mailSender.send(mimeMessage);
            log.info("인증 이메일 전송 완료: {}", to);
        } catch (MessagingException e) {
            log.error("이메일 전송 실패: {}", e.getMessage());
            throw new RuntimeException("이메일 전송에 실패했습니다.", e);
        }
    }

    /**
     * 이메일 인증용 HTML 콘텐츠를 생성합니다.
     * 
     * @param rawToken 인증 토큰
     * @return HTML 형식의 이메일 내용
     */
    private String generateVerificationContent(String rawToken) {
        String verificationLink = baseDomain + "/api/auth/verify-email?token=" + rawToken;
        
        return String.format("""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background-color: #4CAF50; color: white; padding: 20px; text-align: center; }
                    .content { padding: 20px; background-color: #f9f9f9; }
                    .button { display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
                    .footer { text-align: center; padding: 20px; color: #666; font-size: 12px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🎓 DigitechHub</h1>
                        <p>서울디지텍을 한 손 안에!</p>
                    </div>
                    <div class="content">
                        <h2>이메일 인증이 필요합니다</h2>
                        <p>안녕하세요! DigitechHub 회원가입을 환영합니다.</p>
                        <p>아래 버튼을 클릭하여 이메일 인증을 완료해주세요.</p>
                        <p style="text-align: center;">
                            <a href="%s" class="button">이메일 인증하기</a>
                        </p>
                        <p><strong>링크가 작동하지 않나요?</strong><br>
                        아래 링크를 복사하여 브라우저에 붙여넣기 하세요:</p>
                        <p style="word-break: break-all; background-color: #eee; padding: 10px; border-radius: 3px;">
                            %s
                        </p>
                        <p><small>이 링크는 24시간 후에 만료됩니다.</small></p>
                    </div>
                    <div class="footer">
                        <p>이 이메일은 DigitechHub 시스템에서 자동으로 발송되었습니다.</p>
                        <p>문의사항이 있으시면 관리자에게 연락해주세요.</p>
                    </div>
                </div>
            </body>
            </html>
            """, verificationLink, verificationLink);
    }
}
