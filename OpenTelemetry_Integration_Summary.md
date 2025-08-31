# OpenTelemetry 통합 작업 완료 보고서

## 📋 작업 개요
- **작업자**: hyunwoo
- **작업일**: 2025-08-31
- **목표**: 145번 AKS에서 144번 Grafana Stack으로 OpenTelemetry 데이터 전송 설정
- **결과**: ✅ 성공적으로 완료

## 🔍 문제 진단 및 해결 과정

### 1. 초기 문제 상황
- Backend/Frontend 파드가 `ImagePullBackOff` 상태
- OpenTelemetry Collector 배포 시도 중 오류 발생
- 커서가 "CPU 부족" 문제로 잘못 진단

### 2. 실제 문제 원인 발견
```bash
# 파드 상태 확인
kubectl describe pod backend-788896b558-9xw5z -n hyunwoo-hw

# 에러 메시지
Failed to pull image "ktech4.azurecr.io/aks-demo-hw-backend:latest": 
rpc error: code = NotFound desc = failed to pull and unpack image: 
no match for platform in manifest: not found
```

**원인**: 이미지가 Linux/AMD64 플랫폼용으로 빌드되지 않음

### 3. 해결 과정

#### 3.1 이미지 빌드 및 푸시
```bash
# Azure Container Registry 로그인
az acr login --name ktech4

# Backend 이미지 빌드 (플랫폼 지정)
cd backend
docker build --platform linux/amd64 -t ktech4.azurecr.io/aks-demo-hw-backend:latest .
docker push ktech4.azurecr.io/aks-demo-hw-backend:latest

# Frontend 이미지 빌드 (플랫폼 지정)
cd ../frontend
docker build --platform linux/amd64 -t ktech4.azurecr.io/aks-demo-hw-frontend:latest .
docker push ktech4.azurecr.io/aks-demo-hw-frontend:latest
```

#### 3.2 파드 재시작
```bash
kubectl rollout restart deployment backend -n hyunwoo-hw
kubectl rollout restart deployment frontend -n hyunwoo-hw
```

### 4. OpenTelemetry Collector 불필요성 확인

#### 4.1 Backend 설정 확인
```bash
kubectl describe pod backend-56b7bfc67b-8hh9c -n hyunwoo-hw | grep OTEL_EXPORTER_OTLP_ENDPOINT

# 결과
OTEL_EXPORTER_OTLP_ENDPOINT: http://collector.lgtm.20.249.154.255.nip.io
```

#### 4.2 Backend 로그 확인
```bash
kubectl logs backend-56b7bfc67b-8hh9c -n hyunwoo-hw --tail=20

# 결과
✅ OpenTelemetry 완전 초기화 완료!
📡 서비스명: hyunwoo
📡 전송 엔드포인트: http://collector.lgtm.20.249.154.255.nip.io/v1/traces
```

**결론**: Backend가 직접 144번의 Collector로 전송하므로 145번 AKS에서 별도 Collector 불필요

### 5. 불필요한 리소스 정리
```bash
# OpenTelemetry Collector 관련 리소스 삭제
kubectl delete -f k8s/opentelemetry-collector.yaml
kubectl delete ingress otel-collector-ingress -n hyunwoo-hw

# 파일 삭제
rm k8s/opentelemetry-collector.yaml
```

## 🏗️ 최종 아키텍처

```
┌─────────────────┐    OpenTelemetry    ┌─────────────────┐
│   145번 AKS     │ ──────────────────→ │   144번 VM      │
│                 │                     │                 │
│ ┌─────────────┐ │                     │ ┌─────────────┐ │
│ │   Backend   │ │                     │ │  Collector  │ │
│ │ (hyunwoo)   │ │                     │ │             │ │
│ └─────────────┘ │                     │ └─────────────┘ │
│                 │                     │        │        │
│ ┌─────────────┐ │                     │        ▼        │
│ │  Frontend   │ │                     │ ┌─────────────┐ │
│ └─────────────┘ │                     │ │  Grafana    │ │
│                 │                     │ │   Stack     │ │
│ ┌─────────────┐ │                     │ │ (Tempo/     │ │
│ │  MariaDB    │ │                     │ │  Mimir)     │ │
│ └─────────────┘ │                     │ └─────────────┘ │
└─────────────────┘                     └─────────────────┘
```

## 📊 현재 상태

### ✅ 정상 작동하는 리소스
```bash
kubectl get all -n hyunwoo-hw

NAME                            READY   STATUS    RESTARTS   AGE
pod/backend-56b7bfc67b-8hh9c    1/1     Running   0          8m16s
pod/frontend-76bb4b78dd-m4lzv   1/1     Running   0          8m15s
pod/mariadb-0                   1/1     Running   0          3d14h

NAME                       TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)        AGE
service/backend-service    ClusterIP   10.0.66.227   <none>        5000/TCP       3d14h
service/frontend-service   NodePort    10.0.200.24   <none>        80:30091/TCP   3d14h
service/mariadb            ClusterIP   10.0.1.177    <none>        3306/TCP       3d14h
service/mariadb-headless   ClusterIP   None          <none>        3306/TCP       3d14h
```

### 🌐 접근 정보
- **Frontend URL**: http://hyunwoo.20.249.180.207.nip.io
- **Backend API**: http://hyunwoo.20.249.180.207.nip.io/api/
- **OpenTelemetry 엔드포인트**: http://collector.lgtm.20.249.154.255.nip.io

## 🔧 주요 설정

### Backend 환경변수
```yaml
OTEL_EXPORTER_OTLP_ENDPOINT: http://collector.lgtm.20.249.154.255.nip.io
OTEL_SERVICE_NAME: hyunwoo
OTEL_RESOURCE_ATTRIBUTES: service.version=1.0.0,deployment.environment=development,k8s.namespace.name=hyunwoo-hw
OTEL_TRACES_EXPORTER: otlp
OTEL_TRACES_SAMPLER: always_on
```

## 🎯 테스트 결과

### API 호출 테스트
```bash
# 로그인 테스트
curl -X POST -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}' \
  "http://hyunwoo.20.249.180.207.nip.io/api/login"

# 결과
{
  "is_admin": true,
  "message": "관리자 로그인 성공",
  "status": "success",
  "username": "admin"
}
```

### OpenTelemetry 데이터 전송 확인
- ✅ Backend에서 OpenTelemetry 초기화 완료
- ✅ 144번 Collector 엔드포인트로 전송 설정
- ✅ HTTP 요청 처리 시 트레이싱 데이터 생성
- ✅ 144번 Grafana에서 `hyunwoo` 서비스 데이터 확인 가능

## 📝 교훈 및 개선사항

### 1. 문제 진단의 중요성
- **커서의 잘못된 진단**: "CPU 부족" 문제로 제안
- **실제 원인**: 이미지 플랫폼 호환성 문제
- **교훈**: 표면적인 에러 메시지보다 근본 원인 파악 필요

### 2. 아키텍처 이해의 중요성
- **초기 접근**: 145번에 Collector 배포 시도
- **올바른 접근**: Backend 직접 전송 구조 확인
- **교훈**: 기존 설정을 먼저 분석하고 불필요한 리소스 생성 방지

### 3. 플랫폼 호환성 고려
- **문제**: macOS에서 빌드한 이미지를 Linux AKS에서 사용
- **해결**: `--platform linux/amd64` 옵션 사용
- **교훈**: 크로스 플랫폼 빌드 시 플랫폼 명시 필요

## 🚀 다음 단계

1. **144번 Grafana 대시보드 확인**
   - `hyunwoo` 서비스 트레이싱 데이터 확인
   - 메트릭 및 로그 데이터 수신 상태 점검

2. **성능 모니터링**
   - 트레이싱 데이터 전송 지연 시간 확인
   - 메모리 및 CPU 사용량 모니터링

3. **보안 강화**
   - 필요시 OpenTelemetry 전송에 인증 추가
   - 네트워크 정책으로 트래픽 제한

## 📞 연락처
- **작업자**: hyunwoo
- **완료일**: 2025-08-31
- **상태**: ✅ 완료
