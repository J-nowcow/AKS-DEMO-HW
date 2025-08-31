# 144번 위 VM에서 145번 위 AKS OpenTelemetry Collector 연동 가이드

## 🎯 개요
144번 위 VM의 Grafana Stack에서 145번 위 AKS의 OpenTelemetry Collector로 데이터를 가져와서 시각화하는 설정 방법입니다.

## 📋 전제 조건
- 144번 위 VM: Grafana + Loki + Tempo + Mimir 설치됨
- 145번 위 AKS: OpenTelemetry Collector + Ingress 배포됨

## 🔗 연결 구조
```
AKS (145번 위)                     VM (144번 위)
┌─────────────────┐                ┌──────────────────┐
│ Python App      │                │ Grafana Stack    │
│       ↓         │                │                  │
│ OTel Collector  │ ←── Pull ────  │ • Grafana        │
│       ↓         │                │ • Loki           │
│ Ingress/LB      │                │ • Tempo          │
│ (외부 노출)      │                │ • Mimir          │
└─────────────────┘                └──────────────────┘
```

## 🚀 설정 방법

### 1단계: AKS Collector 외부 접근 주소 확인
```bash
# 배포 스크립트 실행 후 출력되는 주소 사용
# 예: LoadBalancer IP가 20.249.180.100이라면:

OTLP_HTTP_ENDPOINT="http://20.249.180.100:4318"
OTLP_GRPC_ENDPOINT="20.249.180.100:4317"
PROMETHEUS_ENDPOINT="http://20.249.180.100:8889/metrics"
```

### 2단계: Grafana에서 데이터 소스 추가

#### 2-1. Prometheus 데이터 소스 (AKS Collector 메트릭)
```yaml
# Grafana > Configuration > Data Sources > Add data source > Prometheus
Name: AKS-OpenTelemetry-Metrics
URL: http://20.249.180.100:8889
Access: Server (default)
```

#### 2-2. Loki 데이터 소스 (로컬 Loki)
```yaml
# 기존 Loki 설정은 그대로 유지
Name: Local-Loki
URL: http://localhost:3100
```

#### 2-3. Tempo 데이터 소스 (로컬 Tempo)
```yaml
# 기존 Tempo 설정은 그대로 유지  
Name: Local-Tempo
URL: http://localhost:3100
```

### 3단계: 대시보드 설정

#### 3-1. OpenTelemetry Collector 상태 대시보드
```json
{
  "dashboard": {
    "title": "AKS OpenTelemetry Collector Status",
    "panels": [
      {
        "title": "Collector Health",
        "type": "stat",
        "targets": [
          {
            "expr": "up{job=\"otel-collector\"}",
            "datasource": "AKS-OpenTelemetry-Metrics"
          }
        ]
      },
      {
        "title": "Received Spans",
        "type": "graph", 
        "targets": [
          {
            "expr": "rate(otelcol_receiver_accepted_spans[5m])",
            "datasource": "AKS-OpenTelemetry-Metrics"
          }
        ]
      }
    ]
  }
}
```

### 4단계: 알람 설정 (선택사항)
```yaml
# Grafana > Alerting > Alert Rules
Rule Name: AKS Collector Down
Query: up{job="otel-collector"} == 0
Condition: IS BELOW 1
Evaluation: every 1m for 2m
```

## 🔧 트러블슈팅

### 연결 테스트
```bash
# 144번 위 VM에서 실행
curl -I http://20.249.180.100:8889/metrics
curl -I http://20.249.180.100:4318/v1/traces
```

### 일반적인 문제들
1. **방화벽**: AKS LoadBalancer 포트(4317, 4318, 8889) 열기
2. **네트워크 정책**: Ingress Controller 트래픽 허용
3. **DNS 해상도**: IP 주소 직접 사용 권장

## 📊 기대 결과
- Grafana에서 AKS 애플리케이션의 트레이싱, 로그, 메트릭 통합 확인
- OpenTelemetry Collector 상태 모니터링
- 실시간 애플리케이션 성능 관찰

## 🎨 추천 대시보드
1. **Application Performance Monitoring (APM)**
   - HTTP 요청 지연시간
   - 에러율
   - 스루풋

2. **Infrastructure Monitoring**
   - Pod CPU/Memory 사용률
   - Kubernetes 클러스터 상태

3. **Business Metrics**
   - 사용자 행동 분석
   - API 호출 패턴
