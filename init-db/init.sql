-- 사용자 생성
CREATE USER IF NOT EXISTS 'digitechhub_sso_user'@'%' IDENTIFIED BY 'digitechhub_sso!!';
CREATE USER IF NOT EXISTS 'digitechhub_equipment_user'@'%' IDENTIFIED BY 'digitechhub_equipment!!1234';

-- SSO 전용 DB  
CREATE DATABASE IF NOT EXISTS digitechhub_sso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 기자재서비스용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_equipment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 사용자에게 두 DB에 대한 권한 부여
GRANT ALL PRIVILEGES ON digitechhub_sso.* TO 'digitechhub_sso_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_equipment.* TO 'digitechhub_equipment_user'@'%';
FLUSH PRIVILEGES;