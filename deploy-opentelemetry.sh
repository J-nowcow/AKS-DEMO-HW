#!/bin/bash

# OpenTelemetry 자동 계측 배포 스크립트
# AKS 클러스터에 OpenTelemetry Operator와 관련 리소스를 배포합니다.

set -e

echo "🚀 OpenTelemetry 자동 계측 배포를 시작합니다..."

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

# OpenTelemetry Collector 배포
echo "📦 OpenTelemetry Collector 배포 중..."
kubectl apply -f k8s/opentelemetry-collector.yaml

echo "⏳ OpenTelemetry Collector 파드가 준비될 때까지 대기 중..."
kubectl wait --for=condition=ready pod -l app=otel-collector -n hyunwoo-hw --timeout=300s

echo "✅ OpenTelemetry Collector 배포 완료"

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
echo "🔍 OpenTelemetry Operator 상태:"
kubectl get pods -n opentelemetry-operator-system

echo ""
echo "🔍 OpenTelemetry Collector 상태:"
kubectl get pods -l app=otel-collector -n hyunwoo-hw

echo ""
echo "🔍 Instrumentation 리소스 상태:"
kubectl get instrumentation -n hyunwoo-hw

echo ""
echo "🔍 백엔드 파드 상태 및 어노테이션 확인:"
kubectl get pods -l app=backend -n hyunwoo-hw
kubectl describe pod -l app=backend -n hyunwoo-hw | grep -A 5 -B 5 "instrumentation\|opentelemetry"

echo ""
echo "🎉 OpenTelemetry 자동 계측 배포가 완료되었습니다!"
echo ""
echo "📊 확인 방법:"
echo "1. 백엔드 파드 로그 확인: kubectl logs -l app=backend -n hyunwoo-hw"
echo "2. Collector 로그 확인: kubectl logs -l app=otel-collector -n hyunwoo-hw"
echo "3. 백엔드 파드에 init-container 확인: kubectl describe pod -l app=backend -n hyunwoo-hw | grep opentelemetry"
echo ""
echo "🌐 Collector 메트릭 확인 (포트 포워딩):"
echo "kubectl port-forward svc/otel-collector 8888:8888 -n hyunwoo-hw"
echo "kubectl port-forward svc/otel-collector 55679:55679 -n hyunwoo-hw  # zpages"
