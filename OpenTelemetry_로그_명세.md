# 🔍 OpenTelemetry 자동 계측 로그 명세

## 📋 개요
이 문서는 K8s 마이크로서비스 데모 애플리케이션에서 OpenTelemetry가 자동으로 생성하는 모든 로그, 메트릭, 추적 데이터의 명세를 정리한 문서입니다.

---

## 🚀 OpenTelemetry 설정

### 기본 설정
```python
# 서비스 정보
service.name: "hyunwoo"
service.version: "1.0.0"
deployment.environment: "development"

# 전송 설정
OTEL_EXPORTER_OTLP_ENDPOINT: "http://localhost:4318"
OTEL_SERVICE_NAME: "hyunwoo"
```

### 자동 계측 라이브러리
```bash
opentelemetry-distro[otlp]
opentelemetry-exporter-otlp
opentelemetry-instrumentation-flask
opentelemetry-instrumentation-requests
opentelemetry-instrumentation-mysql
opentelemetry-instrumentation-redis
```

---

## 📊 자동 생성되는 메트릭

### 1. Span Rate (초당 스팬 수)
- **메트릭명**: `span_rate`
- **단위**: `span/s`
- **설명**: 초당 생성되는 추적 스팬의 수
- **대시보드 표시**: 막대 그래프로 표시
- **정상 범위**: 0~0.6 span/s

### 2. Errors per Second (초당 에러 수)
- **메트릭명**: `error_rate`
- **단위**: `error/s`
- **설명**: 초당 발생하는 에러의 수
- **대시보드 표시**: 선 그래프로 표시
- **정상 범위**: 0 (에러 없음)

### 3. Duration (응답 시간)
- **메트릭명**: `duration`
- **단위**: `ms`, `µs`
- **설명**: API 호출의 응답 시간 분포
- **대시보드 표시**: 히트맵으로 표시
- **측정 범위**: 262µs ~ 268ms

---

## 🔍 자동 생성되는 추적 로그

### Flask 웹 프레임워크 추적

#### 1. HTTP 요청 추적
```json
{
  "trace_id": "abc123...",
  "span_id": "def456...",
  "parent_span_id": null,
  "operation_name": "GET /logs/kafka",
  "start_time": "2025-09-01T01:36:32.123Z",
  "end_time": "2025-09-01T01:36:32.456Z",
  "duration_ms": 333,
  "status": "OK",
  "attributes": {
    "http.method": "GET",
    "http.url": "http://localhost:5000/logs/kafka",
    "http.status_code": 200,
    "http.user_agent": "Mozilla/5.0...",
    "http.request_content_length": 0,
    "http.response_content_length": 1024,
    "flask.route": "/logs/kafka",
    "flask.endpoint": "get_kafka_logs",
    "flask.view_args": {},
    "flask.url_rule": "/logs/kafka"
  }
}
```

#### 2. 자동 추적되는 API 엔드포인트
| API 엔드포인트 | HTTP 메서드 | 추적 이름 | 설명 |
|----------------|-------------|-----------|------|
| `/register` | POST | `POST /register` | 회원가입 요청 |
| `/login` | POST | `POST /login` | 로그인 요청 |
| `/logout` | POST | `POST /logout` | 로그아웃 요청 |
| `/db/message` | POST | `POST /db/message` | 메시지 저장 |
| `/db/messages` | GET | `GET /db/messages` | 메시지 조회 |
| `/db/messages/search` | GET | `GET /db/messages/search` | 메시지 검색 |
| `/logs/redis` | GET | `GET /logs/redis` | Redis 로그 조회 |
| `/logs/kafka` | GET | `GET /logs/kafka` | Kafka 로그 조회 |
| `/admin/users` | GET | `GET /admin/users` | 관리자 사용자 목록 |
| `/admin/users/{username}/messages` | GET | `GET /admin/users/{username}/messages` | 관리자 사용자 메시지 |

### 데이터베이스 추적

#### 1. MySQL/MariaDB 추적
```json
{
  "trace_id": "abc123...",
  "span_id": "ghi789...",
  "parent_span_id": "def456...",
  "operation_name": "mysql.query",
  "start_time": "2025-09-01T01:36:32.200Z",
  "end_time": "2025-09-01T01:36:32.300Z",
  "duration_ms": 100,
  "status": "OK",
  "attributes": {
    "db.system": "mysql",
    "db.connection_string": "mysql://user@host:3306/testdb",
    "db.statement": "SELECT * FROM messages WHERE user_id = %s ORDER BY created_at DESC",
    "db.operation": "SELECT",
    "db.sql.table": "messages",
    "db.rows_affected": 5
  }
}
```

#### 2. Redis 추적
```json
{
  "trace_id": "abc123...",
  "span_id": "jkl012...",
  "parent_span_id": "def456...",
  "operation_name": "redis.command",
  "start_time": "2025-09-01T01:36:32.400Z",
  "end_time": "2025-09-01T01:36:32.450Z",
  "duration_ms": 50,
  "status": "OK",
  "attributes": {
    "db.system": "redis",
    "db.connection_string": "redis://redis-master:6379/0",
    "db.operation": "LRANGE",
    "db.redis.database_index": 0,
    "db.redis.command": "LRANGE api_logs 0 -1"
  }
}
```

### HTTP 클라이언트 추적

#### 1. 외부 API 호출 추적
```json
{
  "trace_id": "abc123...",
  "span_id": "mno345...",
  "parent_span_id": "def456...",
  "operation_name": "HTTP GET",
  "start_time": "2025-09-01T01:36:32.500Z",
  "end_time": "2025-09-01T01:36:32.600Z",
  "duration_ms": 100,
  "status": "OK",
  "attributes": {
    "http.method": "GET",
    "http.url": "http://external-api:443/api/data",
    "http.status_code": 200,
    "http.request_content_length": 0,
    "http.response_content_length": 512
  }
}
```

---

## 📈 대시보드에서 보이는 로그 패턴

### 1. Span Rate 패턴
```
시간대별 Span Rate:
- 01:12: ~0.6 span/s (높은 활동)
- 01:20: ~0.2 span/s (중간 활동)
- 01:36-01:40: 0.1-0.4 span/s (지속적 활동)
```

### 2. Duration 분포
```
응답 시간 분포:
- 262µs: 매우 빠른 응답 (캐시된 데이터)
- 1.05ms: 빠른 응답 (Redis 조회)
- 16.8ms: 일반적인 응답 (DB 조회)
- 67.1ms: 느린 응답 (복잡한 쿼리)
- 268ms: 매우 느린 응답 (외부 API 호출)
```

### 3. 에러 패턴
```
에러 발생 현황:
- 대부분의 시간대: 0 error/s (정상)
- 간헐적 에러: 네트워크 타임아웃, DB 연결 실패
```

---

## 🔧 자동 계측 설정

### Docker 실행 명령어
```dockerfile
CMD ["opentelemetry-instrument", "python", "app.py"]
```

### 환경변수 설정
```bash
# OpenTelemetry 설정
OTEL_SERVICE_NAME=hyunwoo
OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
OTEL_RESOURCE_ATTRIBUTES=service.name=hyunwoo,service.version=1.0.0

# 자동 계측 활성화
OTEL_PYTHON_DISABLED_INSTRUMENTATIONS=""
OTEL_PYTHON_LOG_CORRELATION=true
OTEL_PYTHON_LOG_FORMAT=%(asctime)s %(levelname)s [%(name)s] [%(filename)s:%(lineno)d] [trace_id=%(otelTraceID)s span_id=%(otelSpanID)s] - %(message)s
```

---

## 📊 추적 데이터 구조

### Span 기본 구조
```json
{
  "trace_id": "고유 추적 ID (16바이트)",
  "span_id": "고유 스팬 ID (8바이트)",
  "parent_span_id": "부모 스팬 ID (선택적)",
  "operation_name": "작업 이름",
  "start_time": "시작 시간 (Unix 타임스탬프)",
  "end_time": "종료 시간 (Unix 타임스탬프)",
  "duration_ms": "지속 시간 (밀리초)",
  "status": "OK | ERROR",
  "attributes": {
    "커스텀 속성": "값"
  },
  "events": [
    {
      "name": "이벤트 이름",
      "timestamp": "이벤트 시간",
      "attributes": {}
    }
  ]
}
```

### 자동 생성되는 속성들

#### HTTP 관련 속성
- `http.method`: HTTP 메서드 (GET, POST, PUT, DELETE)
- `http.url`: 요청 URL
- `http.status_code`: HTTP 상태 코드
- `http.user_agent`: 사용자 에이전트
- `http.request_content_length`: 요청 본문 길이
- `http.response_content_length`: 응답 본문 길이

#### 데이터베이스 관련 속성
- `db.system`: 데이터베이스 시스템 (mysql, redis)
- `db.connection_string`: 연결 문자열
- `db.statement`: SQL 쿼리 또는 Redis 명령어
- `db.operation`: 데이터베이스 작업 (SELECT, INSERT, UPDATE, DELETE)
- `db.sql.table`: SQL 테이블 이름
- `db.rows_affected`: 영향받은 행 수

#### Flask 관련 속성
- `flask.route`: Flask 라우트 패턴
- `flask.endpoint`: Flask 엔드포인트 이름
- `flask.view_args`: 뷰 함수 인수
- `flask.url_rule`: URL 규칙

---

## 🎯 모니터링 대시보드 해석

### 1. 성능 지표
- **Span Rate**: 시스템 부하 지표
- **Duration**: 응답 시간 성능
- **Error Rate**: 시스템 안정성 지표

### 2. 추적 로그 분석
- **Trace Service**: 모든 로그가 "hyunwoo" 서비스에서 생성
- **Trace Name**: 실제 API 엔드포인트 호출 추적
- **시간 분포**: 사용자 활동 패턴 분석

### 3. 문제 진단
- **높은 Duration**: 성능 병목 지점 식별
- **에러 발생**: 실패한 API 호출 추적
- **Span Rate 급증**: 트래픽 스파이크 감지

---

## 🔍 실제 로그 예시

### GET /logs/kafka 호출 추적
```json
{
  "trace_id": "a1b2c3d4e5f6g7h8",
  "span_id": "i9j0k1l2m3n4o5p6",
  "operation_name": "GET /logs/kafka",
  "start_time": "2025-09-01T01:36:32.123Z",
  "end_time": "2025-09-01T01:36:32.456Z",
  "duration_ms": 333,
  "status": "OK",
  "attributes": {
    "http.method": "GET",
    "http.url": "http://localhost:5000/logs/kafka",
    "http.status_code": 200,
    "flask.route": "/logs/kafka",
    "flask.endpoint": "get_kafka_logs"
  },
  "child_spans": [
    {
      "span_id": "q7r8s9t0u1v2w3x4",
      "operation_name": "kafka.consume",
      "duration_ms": 200,
      "attributes": {
        "messaging.system": "kafka",
        "messaging.destination": "api-logs-hyunwoo",
        "messaging.operation": "receive"
      }
    },
    {
      "span_id": "y5z6a7b8c9d0e1f2",
      "operation_name": "redis.command",
      "duration_ms": 50,
      "attributes": {
        "db.system": "redis",
        "db.operation": "LRANGE"
      }
    }
  ]
}
```

---

## 📝 요약

OpenTelemetry는 다음과 같은 데이터를 자동으로 생성합니다:

1. **메트릭**: Span Rate, Error Rate, Duration
2. **추적**: 모든 HTTP 요청, DB 쿼리, 외부 API 호출
3. **속성**: HTTP, 데이터베이스, 프레임워크 관련 메타데이터
4. **이벤트**: 예외, 로그, 커스텀 이벤트

이 모든 데이터는 **코드 수정 없이** 자동으로 수집되어 모니터링 대시보드에서 실시간으로 확인할 수 있습니다! 🚀
