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
        
        return "<!DOCTYPE html>\n" +
            "<html lang=\"ko\">\n" +
            "<head>\n" +
            "  <meta charset=\"UTF-8\">\n" +
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n" +
            "  <title>이메일 인증</title>\n" +
            "  <style>\n" +
            "    body {\n" +
            "      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;\n" +
            "      margin: 0;\n" +
            "      padding: 0;\n" +
            "      background-color: #f5f5f5;\n" +
            "      line-height: 1.6;\n" +
            "    }\n" +
            "    .container {\n" +
            "      max-width: 600px;\n" +
            "      margin: 0 auto;\n" +
            "      background: white;\n" +
            "      border-radius: 12px;\n" +
            "      overflow: hidden;\n" +
            "      box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);\n" +
            "    }\n" +
            "    .header {\n" +
            "      background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);\n" +
            "      color: white;\n" +
            "      padding: 40px 20px;\n" +
            "      text-align: center;\n" +
            "      position: relative;\n" +
            "      overflow: hidden;\n" +
            "    }\n" +
            "    .header::before {\n" +
            "      content: '';\n" +
            "      position: absolute;\n" +
            "      width: 200px;\n" +
            "      height: 200px;\n" +
            "      background: rgba(255, 255, 255, 0.1);\n" +
            "      border-radius: 50%;\n" +
            "      top: -50%;\n" +
            "      right: -20%;\n" +
            "    }\n" +
            "    .header h1 {\n" +
            "      margin: 0;\n" +
            "      font-size: 28px;\n" +
            "      font-weight: 700;\n" +
            "      position: relative;\n" +
            "      z-index: 1;\n" +
            "    }\n" +
            "    .content {\n" +
            "      padding: 40px 30px;\n" +
            "    }\n" +
            "    .content h2 {\n" +
            "      color: #333;\n" +
            "      margin-bottom: 20px;\n" +
            "      font-size: 24px;\n" +
            "      font-weight: 600;\n" +
            "    }\n" +
            "    .content p {\n" +
            "      color: #666;\n" +
            "      margin-bottom: 16px;\n" +
            "      font-size: 16px;\n" +
            "    }\n" +
            "    .button-container {\n" +
            "      text-align: center;\n" +
            "      margin: 30px 0;\n" +
            "    }\n" +
            "    .button {\n" +
            "      display: inline-block;\n" +
            "      padding: 14px 40px;\n" +
            "      background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);\n" +
            "      color: white;\n" +
            "      text-decoration: none;\n" +
            "      border-radius: 6px;\n" +
            "      font-weight: 600;\n" +
            "      font-size: 15px;\n" +
            "      box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);\n" +
            "      transition: all 0.3s ease;\n" +
            "      border: none;\n" +
            "      cursor: pointer;\n" +
            "    }\n" +
            "    .button:hover {\n" +
            "      transform: translateY(-2px);\n" +
            "      box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);\n" +
            "    }\n" +
            "    .fallback-section {\n" +
            "      background: #f8f9fa;\n" +
            "      border: 1px solid #e9ecef;\n" +
            "      border-radius: 8px;\n" +
            "      padding: 20px;\n" +
            "      margin-top: 30px;\n" +
            "    }\n" +
            "    .link-box {\n" +
            "      background: white;\n" +
            "      border: 1px solid #dee2e6;\n" +
            "      border-radius: 4px;\n" +
            "      padding: 12px;\n" +
            "      font-family: 'Courier New', monospace;\n" +
            "      font-size: 14px;\n" +
            "      word-break: break-all;\n" +
            "      color: #495057;\n" +
            "    }\n" +
            "    .footer {\n" +
            "      background: #f8f9fa;\n" +
            "      padding: 20px 30px;\n" +
            "      text-align: center;\n" +
            "      color: #6c757d;\n" +
            "      font-size: 14px;\n" +
            "      border-top: 1px solid #e9ecef;\n" +
            "    }\n" +
            "    .highlight {\n" +
            "      background: linear-gradient(120deg, #a8edea 0%, #fed6e3 100%);\n" +
            "      padding: 2px 6px;\n" +
            "      border-radius: 4px;\n" +
            "      font-weight: 600;\n" +
            "    }\n" +
            "    @media (max-width: 600px) {\n" +
            "      .container {\n" +
            "        margin: 0;\n" +
            "        border-radius: 0;\n" +
            "      }\n" +
            "      .content {\n" +
            "        padding: 30px 20px;\n" +
            "      }\n" +
            "      .header {\n" +
            "        padding: 30px 20px;\n" +
            "      }\n" +
            "      .header h1 {\n" +
            "        font-size: 24px;\n" +
            "      }\n" +
            "    }\n" +
            "  </style>\n" +
            "</head>\n" +
            "<body>\n" +
            "  <div class=\"container\">\n" +
            "    <div class=\"header\">\n" +
            "      <h1>🎉 이메일 인증</h1>\n" +
            "    </div>\n" +
            "    \n" +
            "    <div class=\"content\">\n" +
            "      <h2>안녕하세요!</h2>\n" +
            "      <p>DigitechHub에 가입해주셔서 감사합니다. 계정을 활성화하기 위해 이메일 인증을 완료해주세요.</p>\n" +
            "      \n" +
            "      <p>아래 버튼을 클릭하여 이메일 인증을 완료하세요:</p>\n" +
            "      \n" +
            "      <div class=\"button-container\">\n" +
            "        <a href=\"" + verificationLink + "\" class=\"button\">이메일 인증하기</a>\n" +
            "      </div>\n" +
            "      \n" +
            "      <div class=\"fallback-section\">\n" +
            "        <p>⚠️ 버튼이 작동하지 않나요?</p>\n" +
            "        <p style=\"margin-bottom: 8px; font-weight: normal; color: #666;\">아래 링크를 복사하여 브라우저에 붙여넣기 하세요:</p>\n" +
            "        <div class=\"link-box\">" + verificationLink + "</div>\n" +
            "      </div>\n" +
            "      \n" +
            "      <p><strong>⏰ 인증 링크는 24시간 후에 만료됩니다.</strong></p>\n" +
            "      \n" +
            "      <p>만약 이 이메일을 요청하지 않으셨다면, 이 메시지를 무시하셔도 됩니다.</p>\n" +
            "    </div>\n" +
            "    \n" +
            "    <div class=\"footer\">\n" +
            "      <p>© 2024 DigitechHub. All rights reserved.</p>\n" +
            "    </div>\n" +
            "  </div>\n" +
            "</body>\n" +
            "</html>";
    }
}
