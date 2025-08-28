-- AKS Demo Database Schema
-- 기존 테이블이 있다면 삭제
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS users;

-- 사용자 테이블 생성
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 메시지 테이블 생성 (사용자별 메시지 저장)
CREATE TABLE messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);

-- 샘플 데이터 삽입
INSERT INTO users (username, password) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewLO/5w1mP3lMfoe'), -- password: admin123
('demo', '$2b$12$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi');   -- password: password

INSERT INTO messages (user_id, message) VALUES 
('admin', '관리자 테스트 메시지입니다.'),
('admin', 'AKS 데모 애플리케이션이 정상 작동중입니다.'),
('demo', '데모 사용자의 첫 번째 메시지입니다.'),
('demo', 'Kubernetes에서 실행되는 마이크로서비스 테스트중입니다.'); 