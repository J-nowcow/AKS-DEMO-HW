# AKS 배포 트러블슈팅 보고서

## 📋 프로젝트 개요
- **프로젝트명**: aks-demo-hw
- **배포 환경**: Azure Kubernetes Service (AKS)
- **네임스페이스**: hyunwoo-hw
- **주요 구성**: Frontend, Backend, MariaDB, Redis, Kafka

---

## 🚨 발생한 문제점들

### 1. **ImagePullBackOff 오류**

#### 🔍 **문제 상황**
```bash
NAME                        READY   STATUS             RESTARTS   AGE
backend-5db54fbdd8-j2kqd    0/1     ImagePullBackOff   0          86m
frontend-55b6cb9f95-x4hp8   0/1     ImagePullBackOff   0          86m
```

#### 🎯 **원인 분석**
- Docker 이미지들이 Azure Container Registry (ACR)에 정상적으로 푸시되어 있음 확인
- AKS 클러스터가 ACR에 접근할 수 있는 권한이 없어서 이미지를 가져올 수 없음
- `ktech4.azurecr.io/aks-demo-hw-backend:latest` 및 `frontend` 이미지 접근 실패

#### 🔧 **해결 과정**

**1단계: ACR 이미지 존재 확인**
```bash
az acr repository list --name ktech4 --output table
az acr repository show-tags --name ktech4 --repository aks-demo-hw-backend --output table
```
✅ 이미지는 정상적으로 ACR에 존재함

**2단계: AKS-ACR 연결 권한 확인**
```bash
az aks update --resource-group rg-az01-co001501-sbox-poc-145 --name aks-az01-sbox-poc-145 --attach-acr ktech4
```
❌ 권한 부족으로 실패: "Could not create a role assignment for ACR. Are you an Owner on this subscription?"

**3단계: Docker Registry Secret 생성**
```bash
# ACR 자격 증명 확인
az acr credential show --name ktech4 --query "passwords[0].value" --output tsv

# Secret 생성
kubectl create secret docker-registry acr-secret \
    --docker-server=ktech4.azurecr.io \
    --docker-username=ktech4 \
    --docker-password=<PASSWORD> \
    --namespace=hyunwoo-hw
```

**4단계: Deployment YAML 수정**
```yaml
# k8s/backend-deployment.yaml, k8s/frontend-deployment.yaml에 추가
spec:
  template:
    spec:
      imagePullSecrets:
      - name: acr-secret
```

**5단계: 배포 적용**
```bash
kubectl apply -f k8s/backend-deployment.yaml -n hyunwoo-hw
kubectl apply -f k8s/frontend-deployment.yaml -n hyunwoo-hw
```

#### ✅ **결과**
```bash
NAME                       READY   STATUS    RESTARTS   AGE
backend-54d59bccdc-mt6zf   1/1     Running   0          2m16s
frontend-9c6c8f484-znwfq   1/1     Running   0          2m14s
```

---

### 2. **Ingress 설정 및 외부 IP 확인**

#### 🔍 **문제 상황**
- Ingress 설정 시 올바른 외부 IP 주소를 찾기 어려움
- 여러 개의 Public IP가 존재하여 어떤 것을 사용해야 할지 불분명

#### 🎯 **원인 분석**
- AKS 클러스터에 여러 사용자들의 LoadBalancer 서비스들이 존재
- 각 LoadBalancer마다 별도의 Public IP가 할당됨
- Ingress Controller용 IP와 개별 서비스용 IP가 혼재

#### 🔧 **해결 과정**

**1단계: Ingress Controller 확인**
```bash
kubectl get ingressclass
kubectl get pods -n app-routing-system
```
✅ Azure Application Routing 애드온이 정상 작동 중

**2단계: Public IP 목록 확인**
```bash
az network public-ip list --resource-group MC_rg-az01-co001501-sbox-poc-145_aks-az01-sbox-poc-145_koreacentral \
    --query "[].{Name:name, IP:ipAddress}" --output table
```

**3단계: LoadBalancer 서비스들과 IP 매핑 확인**
```bash
kubectl get services --all-namespaces -o wide | grep LoadBalancer
```

**결과 분석:**
- `app-routing-system nginx`: `20.249.180.207` (Ingress Controller용)
- `hyunwoo frontend-service`: `20.214.113.243` (개별 LoadBalancer)
- 기타 사용자들의 서비스들...

**4단계: Ingress 설정**
```yaml
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: hyunwoo-frontend-ingress
  namespace: hyunwoo-hw
spec:
  ingressClassName: webapprouting.kubernetes.azure.com
  rules:
  - host: hyunwoo.20.249.180.207.nip.io  # Ingress Controller IP 사용
    http:
      paths:
      - backend:
          service:
            name: frontend-service
            port:
              number: 80
        path: /
        pathType: Prefix
```

#### ✅ **결과**
- Ingress가 정상적으로 생성됨
- `http://hyunwoo.20.249.180.207.nip.io`로 외부 접근 가능

---

## 📚 **핵심 학습 내용**

### 1. **ACR 접근 권한 관리**
- **방법 1**: `az aks update --attach-acr` (Owner 권한 필요)
- **방법 2**: Docker Registry Secret 생성 (권한 제한 환경에서 유용)
- **권장**: Secret 방식이 더 세밀한 권한 제어 가능

### 2. **AKS의 IP 관리 이해**
- LoadBalancer 서비스마다 별도 Public IP 할당
- Ingress Controller는 공유 LoadBalancer 사용
- 여러 사용자 환경에서는 IP 충돌 방지를 위한 네임스페이스 분리 중요

### 3. **트러블슈팅 접근법**
1. **증상 확인**: `kubectl get pods`, `kubectl describe pod`
2. **원인 분석**: 로그 및 이벤트 확인
3. **권한 검증**: Azure RBAC 및 Kubernetes RBAC 확인
4. **대안 방법 적용**: 권한 제한 시 Secret 활용
5. **검증**: 배포 후 상태 재확인

---

## 🎯 **최종 아키텍처**

```
인터넷
    ↓
Ingress Controller (20.249.180.207)
    ↓
hyunwoo.20.249.180.207.nip.io
    ↓
frontend-service (ClusterIP)
    ↓
frontend Pod (with ACR Secret)
```

**주요 구성 요소:**
- ✅ Frontend/Backend Pod: Running
- ✅ MariaDB, Redis: Running  
- ✅ ACR Secret: 생성됨
- ✅ Ingress: 설정 완료
- ✅ 외부 접근: 가능

---

## 🚀 **향후 개선 방안**

1. **deploy-to-aks.sh 스크립트 개선**
   ```bash
   # ACR Secret 생성 로직 추가
   ACR_PASSWORD=$(az acr credential show --name ktech4 --query "passwords[0].value" --output tsv)
   kubectl create secret docker-registry acr-secret \
       --docker-server=ktech4.azurecr.io \
       --docker-username=ktech4 \
       --docker-password=$ACR_PASSWORD \
       --namespace=$NAMESPACE \
       --dry-run=client -o yaml | kubectl apply -f -
   ```

2. **CI/CD 파이프라인에 ACR Secret 자동 생성 추가**

3. **모니터링 및 로깅 시스템 구축**

4. **SSL/TLS 인증서 적용**

---

## 📝 **체크리스트 (향후 배포 시)**

- [ ] ACR에 이미지 푸시 확인
- [ ] ACR Secret 생성 (또는 AKS-ACR 연결)
- [ ] Deployment에 imagePullSecrets 설정
- [ ] Ingress Controller IP 확인
- [ ] Ingress 리소스 생성
- [ ] 외부 접근 테스트
- [ ] 로그 및 메트릭 확인

---

**작성일**: 2025-08-28  
**작성자**: hyunwoo  
**환경**: Azure AKS, Korea Central Region
