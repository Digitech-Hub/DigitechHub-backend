-- 사용자 생성
CREATE USER IF NOT EXISTS 'digitechhub_sso_user'@'%' IDENTIFIED BY 'digitechhub_sso!!';
CREATE USER IF NOT EXISTS 'digitechhub_equipment_user'@'%' IDENTIFIED BY 'digitechhub_equipment!!1234';
CREATE USER IF NOT EXISTS 'digitechhub_notification_user'@'%' IDENTIFIED BY 'digitechhub_notification!!1234';
CREATE USER IF NOT EXISTS 'digitechhub_meal_user'@'%' IDENTIFIED BY 'digitechhub_meal1234';
CREATE USER IF NOT EXISTS 'digitechhub_timetable_user'@'%' IDENTIFIED BY 'digitechhubtimetable1234';
CREATE USER IF NOT EXISTS 'digitechhub_club'@'%' IDENTIFIED BY 'digitechhubclub1234';

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

-- 시간표용 DB
CREATE DATABASE IF NOT EXISTS digitechhub_timetable CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 시간표 테이블
CREATE TABLE IF NOT EXISTS digitechhub_timetable.timetables (
    id INT AUTO_INCREMENT PRIMARY KEY,
    grade INT NOT NULL,
    class_number INT NOT NULL,
    subject VARCHAR(50) NOT NULL,
    day_of_week ENUM('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY') NOT NULL,
    semester ENUM('FIRST', 'SECOND') NOT NULL DEFAULT 'FIRST',
    academic_year YEAR NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_grade_class (grade, class_number),
    INDEX idx_day_semester (day_of_week, semester),
    INDEX idx_academic_year (academic_year)
);

-- 동아리 정보 DB
CREATE DATABASE IF NOT EXISTS digitechhub_club CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 동아리 정보 테이블
CREATE TABLE IF NOT EXISTS digitechhub_club.clubs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    advisor VARCHAR(100),
    members_count INT DEFAULT 0,
    club_room VARCHAR(50),
    bio_email VARCHAR(100),
    phone VARCHAR(20),
    instagram_url VARCHAR(100),    
    comment TEXT,
    tags JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE INDEX idx_name (name)
);

-- 동아리 모집 공고 테이블
CREATE TABLE IF NOT EXISTS digitechhub_club.club_recruitments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    club_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    recruitment_start DATE NOT NULL,
    recruitment_end DATE NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    recruitment_quota INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (club_id) REFERENCES digitechhub_club.clubs(id) ON DELETE CASCADE,
    INDEX idx_club_id (club_id)
);

-- 사용자에게 DB에 대한 권한 부여
GRANT ALL PRIVILEGES ON digitechhub_sso.* TO 'digitechhub_sso_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_equipment.* TO 'digitechhub_equipment_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_notification.* TO 'digitechhub_notification_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_meal.* TO 'digitechhub_meal_user'@'%';
GRANT ALL PRIVILEGES ON digitechhub_timetable.* TO 'digitechhub_timetable_user'@'%';
FLUSH PRIVILEGES;