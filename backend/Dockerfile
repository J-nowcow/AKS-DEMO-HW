FROM ktech4.azurecr.io/python:3.8-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host files.pythonhosted.org -r requirements.txt

# 먼저 전체 소스 코드 복사
COPY . .

# Secret Key 생성 및 환경변수 설정
RUN python generate_secret.py > /app/.env
RUN echo "FLASK_SECRET_KEY=$(cat /app/.env)" > /app/.env

EXPOSE 5000

# 🚀 OpenTelemetry 자동 계측으로 실행 (코드 수정 없이 모든 라이브러리 자동 추적!)
CMD ["opentelemetry-instrument", "python", "app.py"] 