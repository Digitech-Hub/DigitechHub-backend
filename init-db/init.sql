-- 사용자 생성
CREATE USER IF NOT EXISTS 'digitechhub_sso_user'@'%' IDENTIFIED BY 'digitechhub_sso!!';
CREATE USER IF NOT EXISTS 'digitechhub_equipment_user'@'%' IDENTIFIED BY 'digitechhub_equipment!!1234';
CREATE USER IF NOT EXISTS 'digitechhub_notification_user'@'%' IDENTIFIED BY 'digitechhub_notification!!1234';
CREATE USER IF NOT EXISTS 'digitechhub_meal_user'@'%' IDENTIFIED BY 'digitechhub_meal1234';

-- SSO 전용 DB  
CREATE DATABASE IF NOT EXISTS digitechhub_sso CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 기자재서비스용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_equipment CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 알림서비스용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_notification CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE TABLE IF NOT EXISTS digitechhub_notification.notice_info (
    id INT AUTO_INCREMENT PRIMARY KEY,
    notice_date DATE NOT NULL,
    notice_info JSON NOT NULL,
    grade INT NOT NULL,
    class INT NOT NULL
);

-- 식단표용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_meal CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 식단 정보 테이블
CREATE TABLE IF NOT EXISTS digitechhub_meal.MealInfo (
    id INT AUTO_INCREMENT PRIMARY KEY,
    meal_date DATETIME NOT NULL,
    meal_info JSON NOT NULL,
    dish_names JSON NULL
);


-- 사용자에게 두 DB에 대한 권한 부여
GRANT ALL PRIVILEGES ON digitechhub_sso.* TO 'digitechhub_sso_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_equipment.* TO 'digitechhub_equipment_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_notification.* TO 'digitechhub_notification_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_meal.* TO 'digitechhub_meal_user'@'%';
FLUSH PRIVILEGES;