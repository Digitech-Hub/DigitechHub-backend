-- SSO 전용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_sso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 공용 서비스용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자에게 두 DB에 대한 권한 부여
GRANT ALL PRIVILEGES ON digitechhub_sso.* TO 'digitechhub_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_service.* TO 'digitechhub_user'@'%';
FLUSH PRIVILEGES;