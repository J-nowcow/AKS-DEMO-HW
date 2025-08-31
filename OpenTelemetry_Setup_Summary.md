# OpenTelemetry 설정 및 Grafana 연동 완료 보고서

## 📊 **프로젝트 개요**

**목표**: 145번 AKS 클러스터의 애플리케이션에서 144번 클러스터의 Grafana/OpenTelemetry Stack으로 트레이스 데이터 전송

## 🏗️ **시스템 아키텍처**

### **144번 클러스터 (Observability Stack)**
- **역할**: 모니터링 및 관찰 가능성 스택
- **구성요소**: 
  - Grafana (http://grafana.20.249.154.255.nip.io)
  - OpenTelemetry Collector
  - Tempo (트레이스 저장소)
  - Loki (로그 저장소)
  - Mimir (메트릭 저장소)

### **145번 클러스터 (Application Stack)**
- **역할**: 실제 애플리케이션 실행
- **구성요소**:
  - Backend (Flask) - OpenTelemetry 자동 계측
  - Frontend (Vue.js)
  - MariaDB (데이터베이스)

## ✅ **완료된 작업 목록**

### **1. 환경 정리 및 설정**
- ✅ 145번 클러스터의 불필요한 OpenTelemetry 리소스 제거
  - `otel-collector` deployment 삭제
  - `otel-collector-lb` LoadBalancer 삭제
  - `otel-collector-basic-config` ConfigMap 삭제
- ✅ 불필요한 YAML 파일들 정리 (6개 파일 삭제)
  - `opentelemetry-collector-*.yaml`
  - `opentelemetry-ingress.yaml`
  - `jaeger-deployment.yaml`

### **2. OpenTelemetry 패키지 설정**
- ✅ `requirements.txt` 업데이트
  ```txt
  # OpenTelemetry 자동 계측 패키지
  opentelemetry-distro[otlp]
  opentelemetry-exporter-otlp
  opentelemetry-instrumentation-flask
  opentelemetry-instrumentation-requests
  opentelemetry-instrumentation-mysql
  opentelemetry-instrumentation-redis
  ```

### **3. 백엔드 애플리케이션 설정**
- ✅ `app.py`에 완전한 OpenTelemetry 초기화 코드 추가
- ✅ Flask, HTTP 요청, MySQL, Redis 자동 계측 활성화
- ✅ 144번 클러스터 Collector로 데이터 전송 설정

### **4. Kubernetes 배포 설정**
- ✅ `backend-deployment.yaml` 환경변수 설정
  ```yaml
  env:
  - name: OTEL_EXPORTER_OTLP_ENDPOINT
    value: "http://collector.lgtm.20.249.154.255.nip.io"
  - name: OTEL_SERVICE_NAME  
    value: "hyunwoo"
  - name: OTEL_RESOURCE_ATTRIBUTES
    value: "service.version=1.0.0,deployment.environment=development,k8s.namespace.name=hyunwoo-hw"
  ```

### **5. Docker 이미지 빌드 및 배포**
- ✅ AKS 노드 아키텍처 확인 (AMD64)
- ✅ 플랫폼별 이미지 빌드: `--platform=linux/amd64`
- ✅ ACR에 이미지 푸시: `ktech4.azurecr.io/aks-demo-hw-backend:otel-complete`
- ✅ Kubernetes 배포 업데이트

### **6. 연결성 및 데이터 플로우 확인**
- ✅ 144번 클러스터 OpenTelemetry Collector 외부 엔드포인트 확인
  - HTTP: `http://collector.lgtm.20.249.154.255.nip.io/v1/traces`
- ✅ 145번 → 144번 네트워크 연결 테스트
- ✅ 트레이스 데이터 전송 및 수신 확인

## 🧪 **테스트 결과**

### **API 테스트 (총 35개 요청)**
1. **Redis 로그 엔드포인트**: 10개 요청
2. **회원가입**: 5개 요청 (testuser1~5 생성)
3. **로그인**: 5개 요청
4. **DB 메시지 조회**: 3개 요청
5. **메시지 저장**: 4개 요청
6. **Kafka 로그**: 3개 요청
7. **최종 검증**: 5개 요청

### **트레이스 수신 확인**
- ✅ 144번 Collector 로그에서 트레이스 수신 확인
- ✅ Grafana Tempo에서 "hyunwoo" 서비스 트레이스 표시 확인

## 🎯 **최종 설정**

### **서비스 정보**
- **서비스명**: `hyunwoo`
- **환경**: `development`
- **네임스페이스**: `hyunwoo-hw`
- **클러스터**: `aks-az01-sbox-poc-145`

### **Grafana 접속 정보**
- **URL**: http://grafana.20.249.154.255.nip.io
- **계정**: admin / New1234!
- **데이터 소스**: Tempo
- **검색 조건**: Service Name = "hyunwoo"

## 📈 **모니터링 가능한 데이터**

### **자동 추적되는 컴포넌트**
- ✅ Flask HTTP 요청/응답
- ✅ MySQL 데이터베이스 쿼리
- ✅ Redis 캐시 작업
- ✅ HTTP 클라이언트 요청
- ✅ 세션 관리 및 인증

### **트레이스 정보**
- 요청 경로 및 메소드
- 응답 시간 및 상태 코드
- 데이터베이스 쿼리 성능
- 에러 및 예외 정보
- 서비스 간 의존성

## 🎊 **결과**

**✅ 145번 AKS 애플리케이션의 모든 활동이 144번 Grafana에서 실시간으로 모니터링 가능**

---

*작업 완료일: 2025-08-28*  
*최종 이미지: ktech4.azurecr.io/aks-demo-hw-backend:otel-complete*
