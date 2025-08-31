# 🎯 Grafana + OpenTelemetry 완전 연동 가이드

## 📊 **Grafana 접속 정보**
- **URL**: http://grafana.20.249.154.255.nip.io
- **계정**: admin
- **비밀번호**: New1234!

## 🔗 **AKS OpenTelemetry 연결 정보**
- **LoadBalancer IP**: `20.249.138.86`
- **Prometheus 메트릭**: `http://20.249.138.86:8889/metrics`
- **OTLP HTTP**: `http://20.249.138.86:4318`
- **OTLP gRPC**: `20.249.138.86:4317`

## 🚀 **1단계: Grafana에 데이터 소스 추가**

### 1-1. Grafana 로그인
1. 웹 브라우저에서 `http://grafana.20.249.154.255.nip.io` 접속
2. **Username**: `admin`, **Password**: `New1234!` 입력
3. 로그인 후 대시보드 화면 확인

### 1-2. Prometheus 데이터 소스 추가
1. **왼쪽 메뉴** > **Configuration** (⚙️) > **Data sources** 클릭
2. **Add data source** 버튼 클릭
3. **Prometheus** 선택
4. 다음 정보 입력:
   ```
   Name: AKS-OpenTelemetry-Metrics
   URL: http://20.249.138.86:8889
   Access: Server (default)
   ```
5. **Save & test** 클릭 → "Data source is working" 확인

### 1-3. 기존 Tempo/Loki 확인
- **Configuration** > **Data sources**에서 기존 Tempo, Loki 데이터 소스 확인
- 없다면 추가 (144번 위 VM의 로컬 주소 사용)

## 📈 **2단계: OpenTelemetry 대시보드 생성**

### 2-1. 기본 모니터링 대시보드 생성
1. **왼쪽 메뉴** > **Create** (+) > **Dashboard** 클릭
2. **Add an empty panel** 클릭
3. 다음 쿼리들로 패널 생성:

#### **Collector 상태 확인**
```promql
# Data source: AKS-OpenTelemetry-Metrics
up
```

#### **수신된 메트릭 수**
```promql
rate(otelcol_receiver_accepted_metric_points_total[5m])
```

#### **수신된 트레이스 수**
```promql
rate(otelcol_receiver_accepted_spans_total[5m])
```

#### **메모리 사용량**
```promql
otelcol_process_memory_rss
```

### 2-2. 애플리케이션 메트릭 대시보드
1. 새 대시보드 생성
2. 다음 쿼리들 추가:

#### **HTTP 요청 수**
```promql
rate(http_requests_total[5m])
```

#### **응답 시간**
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## 🔍 **3단계: 트레이싱 확인**

### 3-1. Explore 메뉴 사용
1. **왼쪽 메뉴** > **Explore** (🔍) 클릭
2. **데이터 소스**에서 **Tempo** 선택
3. **Query type**: **Search** 
4. **Service**: `aks-demo-backend` 선택 (자동 계측 적용 후)

### 3-2. 트레이스 확인 방법
- 백엔드 애플리케이션에 HTTP 요청 발생
- Grafana Explore에서 최근 트레이스 확인
- 트레이스 세부 정보, 스팬 시간, 에러 등 분석

## 📝 **4단계: 로그 확인**

### 4-1. Loki에서 로그 조회
1. **Explore** > **데이터 소스**: **Loki** 선택
2. 다음 쿼리 사용:
```logql
{namespace="hyunwoo-hw"}
```

### 4-2. 애플리케이션 로그 필터링
```logql
{namespace="hyunwoo-hw", app="backend"} |= "ERROR"
```

## 🎨 **5단계: 통합 대시보드 구성**

### 5-1. 권장 대시보드 레이아웃
```
┌─────────────────┬─────────────────┐
│   시스템 상태    │   애플리케이션   │
│   (Collector)   │   메트릭        │
├─────────────────┼─────────────────┤
│   최근 트레이스  │   에러 로그     │
│   (Tempo)       │   (Loki)        │
└─────────────────┴─────────────────┘
```

### 5-2. 알림 설정
1. **Alerting** > **Alert Rules** > **New rule**
2. 예시 알림:
   ```
   Rule: OpenTelemetry Collector Down
   Query: up{job="opentelemetry-collector"} == 0
   Condition: IS BELOW 1
   Evaluation: every 1m for 2m
   ```

## 🧪 **6단계: 테스트 및 검증**

### 6-1. 애플리케이션 트래픽 생성
```bash
# 백엔드 API 호출 테스트
kubectl port-forward svc/frontend-service 8080:80 -n hyunwoo-hw

# 브라우저에서 http://localhost:8080 접속
# 여러 페이지 이동, API 호출 등 실행
```

### 6-2. 데이터 확인 체크리스트
- [ ] **Metrics**: Prometheus에서 otelcol_* 메트릭 확인
- [ ] **Traces**: Tempo에서 서비스 트레이스 확인  
- [ ] **Logs**: Loki에서 애플리케이션 로그 확인
- [ ] **Dashboard**: 통합 대시보드에서 실시간 데이터 확인

## 📊 **7단계: 고급 기능 활용**

### 7-1. 서비스 맵 생성
- Tempo의 Service Graph 기능 사용
- 마이크로서비스 간 의존성 시각화

### 7-2. 로그-트레이스 상관관계
- 로그에서 trace_id 확인
- 트레이스에서 관련 로그 검색

### 7-3. 커스텀 메트릭 추가
```python
# Python 애플리케이션에 커스텀 메트릭 추가 예시
from opentelemetry import metrics

meter = metrics.get_meter(__name__)
request_counter = meter.create_counter(
    "custom_requests_total",
    description="Total custom requests"
)
```

## 🚨 **문제 해결**

### 자주 발생하는 문제들
1. **데이터가 보이지 않는 경우**:
   - OpenTelemetry Collector 상태 확인: `kubectl get pods -n hyunwoo-hw`
   - LoadBalancer IP 접근 확인: `curl http://20.249.138.86:8889/metrics`

2. **트레이스가 수집되지 않는 경우**:
   - 백엔드 파드 어노테이션 확인: `kubectl describe pod -l app=backend -n hyunwoo-hw`
   - Instrumentation 리소스 확인: `kubectl get instrumentation -n hyunwoo-hw`

3. **Grafana 연결 오류**:
   - 네트워크 연결 확인
   - 데이터 소스 URL 정확성 확인

## 🎯 **완료 체크리스트**
- [ ] Grafana 로그인 성공
- [ ] Prometheus 데이터 소스 추가 완료
- [ ] OpenTelemetry 메트릭 확인
- [ ] 트레이스 데이터 확인
- [ ] 로그 데이터 확인  
- [ ] 통합 대시보드 생성
- [ ] 알림 설정 완료
- [ ] 실제 애플리케이션 데이터 수집 확인

**축하합니다! 🎉 AKS OpenTelemetry와 Grafana 통합 모니터링이 완료되었습니다!**
