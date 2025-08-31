#!/bin/bash

# OpenTelemetry + Ingress 배포 스크립트
# AKS 클러스터에 OpenTelemetry를 배포하고 외부 접근을 위한 Ingress 설정

set -e

echo "🚀 OpenTelemetry + Ingress 배포를 시작합니다..."

# 현재 클러스터 컨텍스트 확인
echo "📋 현재 kubectl 컨텍스트 확인..."
kubectl config current-context

# 네임스페이스 존재 확인
echo "📋 네임스페이스 확인 중..."
if ! kubectl get namespace hyunwoo-hw > /dev/null 2>&1; then
    echo "❌ 네임스페이스 'hyunwoo-hw'가 존재하지 않습니다. 먼저 네임스페이스를 생성해주세요."
    exit 1
fi

# cert-manager 설치 확인
echo "📋 cert-manager 설치 확인 중..."
if ! kubectl get pods -n cert-manager > /dev/null 2>&1; then
    echo "⚠️  cert-manager가 설치되지 않았습니다. 설치하시겠습니까? (y/n)"
    read -r response
    if [[ "$response" == "y" || "$response" == "Y" ]]; then
        echo "📦 cert-manager 설치 중..."
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
        echo "⏳ cert-manager 파드가 준비될 때까지 대기 중..."
        kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=300s
        echo "✅ cert-manager 설치 완료"
    else
        echo "❌ cert-manager가 필요합니다. 수동으로 설치한 후 다시 실행해주세요."
        exit 1
    fi
else
    echo "✅ cert-manager가 이미 설치되어 있습니다."
fi

# OpenTelemetry Operator 설치
echo "📦 OpenTelemetry Operator 설치 중..."
kubectl apply -f https://github.com/open-telemetry/opentelemetry-operator/releases/latest/download/opentelemetry-operator.yaml

echo "⏳ OpenTelemetry Operator 파드가 준비될 때까지 대기 중..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=opentelemetry-operator -n opentelemetry-operator-system --timeout=300s

echo "✅ OpenTelemetry Operator 설치 완료"

# OpenTelemetry Collector 배포 (Grafana 연동 버전)
echo "📦 OpenTelemetry Collector (Grafana 연동 버전) 배포 중..."
kubectl apply -f k8s/opentelemetry-collector-with-grafana.yaml

echo "⏳ OpenTelemetry Collector 파드가 준비될 때까지 대기 중..."
kubectl wait --for=condition=ready pod -l app=otel-collector -n hyunwoo-hw --timeout=300s

echo "✅ OpenTelemetry Collector 배포 완료"

# Ingress 생성 (외부 접근용)
echo "📦 OpenTelemetry Collector Ingress 생성 중..."
kubectl apply -f k8s/opentelemetry-ingress.yaml

echo "✅ OpenTelemetry Collector Ingress 생성 완료"

# Instrumentation 리소스 생성
echo "📦 Instrumentation 리소스 생성 중..."
kubectl apply -f k8s/opentelemetry-instrumentation.yaml

echo "✅ Instrumentation 리소스 생성 완료"

# 백엔드 재배포 (어노테이션 적용을 위해)
echo "🔄 백엔드 재배포 중 (자동 계측 어노테이션 적용)..."
kubectl apply -f k8s/backend-deployment.yaml

echo "⏳ 백엔드 파드가 준비될 때까지 대기 중..."
kubectl wait --for=condition=ready pod -l app=backend -n hyunwoo-hw --timeout=300s

echo "✅ 백엔드 재배포 완료"

# 배포 상태 확인
echo "📋 배포 상태 확인..."
echo ""
echo "🔍 OpenTelemetry Collector 상태:"
kubectl get pods -l app=otel-collector -n hyunwoo-hw

echo ""
echo "🔍 Ingress 상태:"
kubectl get ingress -n hyunwoo-hw

echo ""
echo "🔍 LoadBalancer 서비스 상태:"
kubectl get svc otel-collector-lb -n hyunwoo-hw

echo ""
echo "🔍 외부 접근 주소 확인:"
echo "OTLP HTTP: http://otel-http.hyunwoo.20.249.180.207.nip.io"
echo "OTLP gRPC: http://otel-grpc.hyunwoo.20.249.180.207.nip.io"
echo "Metrics: http://otel-metrics.hyunwoo.20.249.180.207.nip.io"

# LoadBalancer 외부 IP 확인
echo ""
echo "🔍 LoadBalancer 외부 IP 확인 중..."
EXTERNAL_IP=""
while [ -z $EXTERNAL_IP ]; do
    echo "외부 IP 할당을 기다리는 중..."
    EXTERNAL_IP=$(kubectl get svc otel-collector-lb -n hyunwoo-hw --template="{{range .status.loadBalancer.ingress}}{{.ip}}{{end}}")
    [ -z "$EXTERNAL_IP" ] && sleep 10
done

echo ""
echo "🎉 OpenTelemetry + Ingress 배포가 완료되었습니다!"
echo ""
echo "📊 외부 접근 정보:"
echo "LoadBalancer IP: $EXTERNAL_IP"
echo "OTLP gRPC: $EXTERNAL_IP:4317"
echo "OTLP HTTP: $EXTERNAL_IP:4318"
echo "Prometheus Metrics: $EXTERNAL_IP:8889"
echo ""
echo "🔧 144번 위 VM에서 사용할 수 있는 엔드포인트:"
echo "Collector HTTP: http://$EXTERNAL_IP:4318"
echo "Collector gRPC: $EXTERNAL_IP:4317"
echo ""
echo "📋 확인 방법:"
echo "1. Collector 상태: kubectl get pods -l app=otel-collector -n hyunwoo-hw"
echo "2. Ingress 상태: kubectl get ingress -n hyunwoo-hw"
echo "3. 외부 접근 테스트: curl http://$EXTERNAL_IP:8889/metrics"
