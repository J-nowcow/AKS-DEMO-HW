#!/bin/bash

# AKS 배포 스크립트
# 사용법: ./deploy-to-aks.sh [리소스그룹명] [AKS클러스터명] [위치]

set -e

# 변수 설정
RESOURCE_GROUP=${1:-"rg-az01-co001501-sbox-poc-145"}
AKS_CLUSTER_NAME=${2:-"aks-az01-sbox-poc-145"}
LOCATION=${3:-"koreacentral"}
NAMESPACE="hyunwoo-hw"

echo "🚀 AKS 배포를 시작합니다..."
echo "리소스 그룹: $RESOURCE_GROUP"
echo "AKS 클러스터: $AKS_CLUSTER_NAME"
echo "위치: $LOCATION"
echo "네임스페이스: $NAMESPACE"
echo ""

# 1. Azure 로그인 확인
echo "📋 Azure 로그인 상태 확인..."
if ! az account show > /dev/null 2>&1; then
    echo "❌ Azure에 로그인되어 있지 않습니다. 로그인해주세요."
    az login
fi

# 2. 기존 AKS 클러스터 확인
echo "📋 기존 AKS 클러스터 확인..."
az aks show --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME

# 3. AKS 자격 증명 가져오기
echo "🔑 AKS 자격 증명 가져오기..."
az aks get-credentials --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --overwrite-existing

# 5. 네임스페이스 생성
echo "📁 네임스페이스 생성..."
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# 6. Helm 저장소 추가
echo "📚 Helm 저장소 추가..."
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add confluentinc https://packages.confluent.io/helm
helm repo update

# 7. MariaDB 배포
echo "🗄️ MariaDB 배포 중..."
helm install mariadb bitnami/mariadb \
    --namespace $NAMESPACE \
    --values k8s/mariadb-values.yaml \
    --wait

# 8. Kafka 배포
echo "📨 Kafka 배포 중..."
helm install kafka confluentinc/confluent-operator \
    --namespace $NAMESPACE \
    --values k8s/kafka-values.yaml \
    --wait

# 9. Storage Class 배포
echo "💾 Storage Class 배포..."
kubectl apply -f k8s/storage.yaml -n $NAMESPACE

# 10. ConfigMap 배포
echo "⚙️ ConfigMap 배포..."
kubectl apply -f k8s/configmap.yaml -n $NAMESPACE

# 11. Secret 배포
echo "🔐 Secret 배포..."
kubectl apply -f k8s/backend-secret.yaml -n $NAMESPACE

# 12. Backend 배포
echo "🔧 Backend 배포 중..."
kubectl apply -f k8s/backend-deployment.yaml -n $NAMESPACE

# 13. Frontend 배포
echo "🎨 Frontend 배포 중..."
kubectl apply -f k8s/frontend-deployment.yaml -n $NAMESPACE

# 14. Services 배포
echo "🌐 Services 배포..."
kubectl apply -f k8s/services.yaml -n $NAMESPACE

# 15. HPA 배포
echo "📈 HPA 배포..."
kubectl apply -f k8s/hpa.yaml -n $NAMESPACE

# 16. Network Policy 배포
echo "🛡️ Network Policy 배포..."
kubectl apply -f k8s/network-policy.yaml -n $NAMESPACE

# 17. 배포 상태 확인
echo "✅ 배포 완료! 상태 확인 중..."
echo ""
echo "📊 Pod 상태:"
kubectl get pods -n $NAMESPACE

echo ""
echo "🌐 Service 상태:"
kubectl get services -n $NAMESPACE

echo ""
echo "📈 HPA 상태:"
kubectl get hpa -n $NAMESPACE

echo ""
echo "🎉 배포가 완료되었습니다!"
echo ""
echo "📋 다음 명령어로 외부 IP 확인:"
echo "kubectl get service frontend-service -n $NAMESPACE"
echo ""
echo "🔍 로그 확인:"
echo "kubectl logs -f deployment/backend-deployment -n $NAMESPACE"
echo "kubectl logs -f deployment/frontend-deployment -n $NAMESPACE"
echo ""
echo "🗑️ 클러스터 삭제 시:"
echo "az aks delete --resource-group $RESOURCE_GROUP --name $AKS_CLUSTER_NAME --yes"
echo "az group delete --name $RESOURCE_GROUP --yes"
