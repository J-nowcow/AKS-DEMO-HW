# 🚀 K8s 마이크로서비스 데모 - API 호출 관계 정리

## 📋 개요
이 문서는 K8s 마이크로서비스 데모 애플리케이션의 모든 기능과 각 기능이 호출하는 API 엔드포인트를 정리한 문서입니다.

---

## 🏗️ 시스템 아키텍처

### 프론트엔드 (Vue.js)
- **경로**: `/frontend/`
- **포트**: 80 (nginx 프록시)
- **API 베이스 URL**: `/api` (nginx를 통해 백엔드로 프록시)

### 백엔드 (Flask)
- **경로**: `/backend/`
- **포트**: 5000
- **데이터베이스**: MariaDB, Redis, Kafka

### 인프라 구성요소
- **MariaDB**: 메시지 저장소
- **Redis**: 세션 관리 및 로그 백업
- **Kafka**: API 통계 로그 수집
- **OpenTelemetry**: 분산 추적 및 모니터링

---

## 🔐 인증 및 사용자 관리

### 1. 회원가입
- **기능**: 새로운 사용자 계정 생성
- **API 호출**: `POST /api/register`
- **요청 데이터**:
  ```json
  {
    "username": "사용자명",
    "password": "비밀번호"
  }
  ```
- **응답**: 성공/실패 메시지
- **백엔드 처리**: MariaDB에 해시된 비밀번호로 사용자 정보 저장

### 2. 로그인
- **기능**: 사용자 인증 및 세션 생성
- **API 호출**: `POST /api/login`
- **요청 데이터**:
  ```json
  {
    "username": "사용자명",
    "password": "비밀번호"
  }
  ```
- **응답**: 로그인 성공 시 사용자 정보 및 권한
- **백엔드 처리**: 
  - 관리자 계정 확인 (환경변수 기반)
  - 일반 사용자 MariaDB 인증
  - Flask 세션 및 Redis 세션 저장

### 3. 로그아웃
- **기능**: 세션 종료 및 정리
- **API 호출**: `POST /api/logout`
- **백엔드 처리**: Flask 세션 및 Redis 세션 삭제

---

## 💾 데이터베이스 관리

### 4. 메시지 저장
- **기능**: MariaDB에 새 메시지 저장
- **API 호출**: `POST /api/db/message`
- **권한**: 로그인 필요 (`@login_required`)
- **요청 데이터**:
  ```json
  {
    "message": "저장할 메시지"
  }
  ```
- **백엔드 처리**:
  - MariaDB에 메시지 저장
  - Redis에 로그 기록
  - Kafka에 API 통계 전송

### 5. 메시지 조회
- **기능**: 사용자별 메시지 목록 조회
- **API 호출**: `GET /api/db/messages`
- **권한**: 로그인 필요 (`@login_required`)
- **쿼리 파라미터**: `offset`, `limit` (페이지네이션)
- **백엔드 처리**:
  - MariaDB에서 사용자별 메시지 조회
  - Kafka에 API 통계 전송

### 6. 메시지 검색
- **기능**: 메시지 내용 기반 검색
- **API 호출**: `GET /api/db/messages/search`
- **권한**: 로그인 필요 (`@login_required`)
- **쿼리 파라미터**: `q` (검색어)
- **백엔드 처리**:
  - MariaDB에서 LIKE 검색 수행
  - Kafka에 검색 통계 전송

---

## 📊 로그 및 모니터링

### 7. Redis 로그 조회
- **기능**: Redis에 저장된 API 호출 로그 조회
- **API 호출**: `GET /api/logs/redis`
- **권한**: 없음 (공개)
- **백엔드 처리**: Redis에서 최근 100개 로그 조회

### 8. Kafka 통계 로그 조회
- **기능**: Kafka에 저장된 API 통계 및 감사 로그 조회
- **API 호출**: `GET /api/logs/kafka`
- **권한**: 로그인 필요 (`@login_required`)
- **백엔드 처리**:
  - Kafka에서 개발자별 로그 조회
  - 실패 시 Redis 백업 로그 조회
  - 최대 100개 로그 반환

---

## 👑 관리자 기능

### 9. 전체 사용자 목록 조회
- **기능**: 모든 사용자 정보 및 통계 조회
- **API 호출**: `GET /api/admin/users`
- **권한**: 관리자만 (`@admin_required`)
- **백엔드 처리**:
  - MariaDB에서 사용자 정보 및 메시지 통계 조회
  - 관리자 계정 정보 추가
  - Kafka에 관리자 활동 로그 전송

### 10. 특정 사용자 메시지 조회
- **기능**: 관리자가 특정 사용자의 모든 메시지 조회
- **API 호출**: `GET /api/admin/users/{username}/messages`
- **권한**: 관리자만 (`@admin_required`)
- **백엔드 처리**:
  - MariaDB에서 특정 사용자의 모든 메시지 조회
  - Kafka에 관리자 활동 로그 전송

---

## 🔄 API 호출 흐름도

```mermaid
graph TD
    A[프론트엔드 Vue.js] --> B[nginx 프록시]
    B --> C[백엔드 Flask]
    C --> D[MariaDB]
    C --> E[Redis]
    C --> F[Kafka]
    C --> G[OpenTelemetry]
    
    H[사용자] --> A
    
    subgraph "API 엔드포인트"
        I[POST /api/register]
        J[POST /api/login]
        K[POST /api/logout]
        L[POST /api/db/message]
        M[GET /api/db/messages]
        N[GET /api/db/messages/search]
        O[GET /api/logs/redis]
        P[GET /api/logs/kafka]
        Q[GET /api/admin/users]
        R[GET /api/admin/users/{username}/messages]
    end
    
    A --> I
    A --> J
    A --> K
    A --> L
    A --> M
    A --> N
    A --> O
    A --> P
    A --> Q
    A --> R
```

---

## 📈 API 통계 및 로깅

### 로깅 시스템
1. **Redis 로깅**: 모든 API 호출의 기본 로그
2. **Kafka 로깅**: API 통계 및 감사 로그 (비동기)
3. **OpenTelemetry**: 분산 추적 및 성능 모니터링

### 로그 데이터 구조
```json
{
  "developer_tag": "hyunwoo",
  "timestamp": "2025-01-01T12:00:00+09:00",
  "endpoint": "/db/messages",
  "method": "GET",
  "status": "success",
  "user_id": "username",
  "message": "username가 GET /db/messages 호출 (success)"
}
```

---

## 🛡️ 보안 및 권한

### 인증 방식
- **Flask 세션**: 서버 측 세션 관리
- **Redis 세션**: 세션 백업 및 확장성
- **쿠키**: `withCredentials: true`로 세션 쿠키 전송

### 권한 레벨
1. **공개**: Redis 로그 조회
2. **로그인 필요**: 대부분의 기능
3. **관리자 권한**: 사용자 관리 기능

### 보안 기능
- 비밀번호 해시화 (Werkzeug)
- SQL 인젝션 방지 (파라미터화된 쿼리)
- CORS 설정 (Flask-CORS)
- 세션 기반 인증

---

## 🔧 환경 설정

### 주요 환경변수
```bash
# 데이터베이스 설정
MYSQL_HOST=hyunwoo-mariadb.hyunwoo-hw.svc.cluster.local
REDIS_HOST=redis-master.default.svc.cluster.local
KAFKA_SERVERS=team-kafka.default.svc.cluster.local:9092

# 인증 설정
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
FLASK_SECRET_KEY=your-secret-key-here

# OpenTelemetry 설정
OTEL_SERVICE_NAME=hyunwoo
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
DEVELOPER_TAG=hyunwoo
```

---

## 📝 프론트엔드 기능별 API 호출 요약

| 기능 | API 엔드포인트 | HTTP 메서드 | 권한 | 설명 |
|------|----------------|-------------|------|------|
| 회원가입 | `/api/register` | POST | 없음 | 새 사용자 계정 생성 |
| 로그인 | `/api/login` | POST | 없음 | 사용자 인증 |
| 로그아웃 | `/api/logout` | POST | 없음 | 세션 종료 |
| 메시지 저장 | `/api/db/message` | POST | 로그인 필요 | DB에 메시지 저장 |
| 메시지 조회 | `/api/db/messages` | GET | 로그인 필요 | 사용자 메시지 목록 |
| 메시지 검색 | `/api/db/messages/search` | GET | 로그인 필요 | 메시지 내용 검색 |
| Redis 로그 | `/api/logs/redis` | GET | 없음 | Redis 로그 조회 |
| Kafka 로그 | `/api/logs/kafka` | GET | 로그인 필요 | API 통계 로그 조회 |
| 사용자 목록 | `/api/admin/users` | GET | 관리자 | 전체 사용자 조회 |
| 사용자 메시지 | `/api/admin/users/{username}/messages` | GET | 관리자 | 특정 사용자 메시지 |

---

## 🎯 주요 특징

1. **마이크로서비스 아키텍처**: 프론트엔드, 백엔드, 데이터베이스 분리
2. **다중 데이터 저장소**: MariaDB, Redis, Kafka 활용
3. **분산 추적**: OpenTelemetry를 통한 모니터링
4. **비동기 로깅**: Kafka를 통한 API 통계 수집
5. **권한 기반 접근 제어**: 일반 사용자/관리자 구분
6. **세션 관리**: Flask + Redis 이중 세션 관리
7. **프록시 설정**: nginx를 통한 API 라우팅

이 문서는 현재 시스템의 모든 API 호출 관계를 정리한 것으로, 시스템 이해 및 유지보수에 도움이 될 것입니다.
