# Azure에서 OpenTelemetry 배포 확인 체크리스트

## 🎯 1. 기본 인프라 확인 (현재 상태 ✅)

### 1-1. AKS 클러스터 상태
```bash
# Azure Portal > Kubernetes services > aks-demo-hw
# 또는 CLI로 확인:
az aks show --resource-group <리소스그룹명> --name <AKS클러스터명> --query "powerState.code"
```
**예상 결과**: `"Running"`

### 1-2. 네임스페이스 확인
```bash
kubectl get ns
```
**필수 네임스페이스**: 
- ✅ `hyunwoo-hw` (애플리케이션)
- ⏳ `opentelemetry-operator-system` (설치 필요)
- ⏳ `cert-manager` (설치 필요)

### 1-3. 기본 애플리케이션 파드 상태
```bash
kubectl get pods -n hyunwoo-hw
```
**예상 결과**:
- ✅ `backend-xxxxx` - Running
- ✅ `frontend-xxxxx` - Running  
- ✅ `mariadb-0` - Running

## 🔧 2. OpenTelemetry 구성 요소 배포 및 확인

### 2-1. cert-manager 설치 확인
```bash
kubectl get pods -n cert-manager
```
**예상 결과**: 3개 파드 모두 Running 상태

### 2-2. OpenTelemetry Operator 설치 확인
```bash
kubectl get pods -n opentelemetry-operator-system
```
**예상 결과**: operator 파드 Running 상태

### 2-3. OpenTelemetry Collector 배포 확인
```bash
kubectl get pods -l app=otel-collector -n hyunwoo-hw
kubectl get svc otel-collector -n hyunwoo-hw
kubectl get svc otel-collector-lb -n hyunwoo-hw
```
**예상 결과**: 
- Collector 파드: Running
- ClusterIP 서비스: 4317, 4318 포트
- LoadBalancer 서비스: 외부 IP 할당됨

### 2-4. Instrumentation 리소스 확인
```bash
kubectl get instrumentation -n hyunwoo-hw
kubectl describe instrumentation hyunwoo-instrumentation -n hyunwoo-hw
```
**예상 결과**: hyunwoo-instrumentation 생성됨

### 2-5. 백엔드 파드 자동 계측 확인
```bash
kubectl describe pod -l app=backend -n hyunwoo-hw | grep -A 10 -B 10 "opentelemetry"
```
**예상 결과**: 
- `opentelemetry-auto-instrumentation` init-container 추가됨
- 어노테이션 `instrumentation.opentelemetry.io/inject-python: "hyunwoo-instrumentation"` 확인

## 🌐 3. 외부 접근 설정 확인

### 3-1. Ingress 리소스 확인
```bash
kubectl get ingress -n hyunwoo-hw
kubectl describe ingress otel-collector-ingress -n hyunwoo-hw
```
**예상 결과**: OpenTelemetry용 ingress 생성됨

### 3-2. LoadBalancer 외부 IP 확인
```bash
kubectl get svc otel-collector-lb -n hyunwoo-hw
```
**예상 결과**: EXTERNAL-IP 필드에 Azure 공인 IP 할당

### 3-3. Azure Portal에서 Load Balancer 확인
- **Azure Portal > Load balancers**
- AKS 관련 Load Balancer 찾기
- Frontend IP configurations에서 공인 IP 확인
- Load balancing rules에서 4317, 4318, 8889 포트 확인

## 🔍 4. 연결 테스트

### 4-1. 내부 연결 테스트
```bash
# Collector 파드에서 헬스체크
kubectl exec -it deploy/otel-collector -n hyunwoo-hw -- wget -qO- http://localhost:13133
```

### 4-2. 외부 접근 테스트
```bash
# 외부 IP 확인 후
EXTERNAL_IP=$(kubectl get svc otel-collector-lb -n hyunwoo-hw -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
curl -I http://$EXTERNAL_IP:8889/metrics
curl -I http://$EXTERNAL_IP:4318/v1/traces
```

### 4-3. Prometheus 메트릭 확인
```bash
curl http://$EXTERNAL_IP:8889/metrics | grep otelcol
```

## 📊 5. Azure Monitor와의 연동 확인 (선택사항)

### 5-1. Application Insights 연결
- Azure Portal > Application Insights
- OpenTelemetry 데이터 수신 확인

### 5-2. Azure Monitor Logs
```kusto
// Azure Portal > Log Analytics workspace
// 쿼리 예시
traces
| where timestamp > ago(1h)
| where cloud_RoleName contains "backend"
```

## 🚨 6. 문제 해결을 위한 로그 확인

### 6-1. Operator 로그
```bash
kubectl logs -l app.kubernetes.io/name=opentelemetry-operator -n opentelemetry-operator-system
```

### 6-2. Collector 로그
```bash
kubectl logs -l app=otel-collector -n hyunwoo-hw
```

### 6-3. 백엔드 애플리케이션 로그
```bash
kubectl logs -l app=backend -n hyunwoo-hw
```

### 6-4. Kubernetes 이벤트
```bash
kubectl get events -n hyunwoo-hw --sort-by='.lastTimestamp'
```

## ✅ 7. 최종 검증 체크리스트

- [ ] AKS 클러스터 정상 동작
- [ ] cert-manager 설치 완료
- [ ] OpenTelemetry Operator 설치 완료
- [ ] OpenTelemetry Collector 배포 완료
- [ ] Instrumentation 리소스 생성 완료
- [ ] 백엔드 파드에 자동 계측 적용 완료
- [ ] LoadBalancer 외부 IP 할당 완료
- [ ] Ingress 리소스 생성 완료
- [ ] 외부에서 Collector 접근 가능
- [ ] Prometheus 메트릭 수집 확인
- [ ] 144번 위 VM에서 연결 테스트 성공

## 🎯 다음 단계
모든 체크리스트가 완료되면:
1. 144번 위 VM의 Grafana에서 데이터 소스 추가
2. 대시보드 구성
3. 알람 설정
4. 실제 애플리케이션 사용 중 데이터 수집 확인
