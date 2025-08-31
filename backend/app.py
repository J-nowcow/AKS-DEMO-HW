# 🚀 완전한 OpenTelemetry 자동 계측 초기화
import os

def init_opentelemetry():
    """완전한 OpenTelemetry 자동 계측 초기화"""
    try:
        # 필요한 모듈들 import
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.instrumentation.flask import FlaskInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor
        
        # Resource 설정
        resource = Resource.create({
            "service.name": os.getenv('OTEL_SERVICE_NAME', 'hyunwoo'),
            "service.version": "1.0.0",
            "deployment.environment": "development"
        })
        
        # TracerProvider 설정
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        
        # OTLP Exporter 설정
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://localhost:4318')
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint + '/v1/traces')
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
        
        # 자동 계측 활성화
        FlaskInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        
        print(f"✅ OpenTelemetry 완전 초기화 완료!")
        print(f"📡 서비스명: {os.getenv('OTEL_SERVICE_NAME', 'hyunwoo')}")
        print(f"📡 전송 엔드포인트: {otlp_endpoint}/v1/traces")
        print(f"📡 TracerProvider: {trace.get_tracer_provider()}")
        return True
        
    except ImportError as e:
        print(f"⚠️ OpenTelemetry 자동 계측 실패 (라이브러리 없음): {e}")
        return False
    except Exception as e:
        print(f"❌ OpenTelemetry 자동 계측 오류: {e}")
        return False

# 자동 계측 초기화 실행
otel_enabled = init_opentelemetry()

from flask import Flask, request, jsonify, session
from flask_cors import CORS
import redis
import mysql.connector
import json
from datetime import datetime
import pytz
from kafka import KafkaProducer, KafkaConsumer
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from threading import Thread

app = Flask(__name__)
CORS(app, supports_credentials=True)  # 세션을 위한 credentials 지원
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')  # 세션을 위한 시크릿 키

# # 스레드 풀 생성
# thread_pool = ThreadPoolExecutor(max_workers=5)

# MariaDB 연결 함수
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'my-mariadb'),
        user=os.getenv('MYSQL_USER', 'testuser'),
        password=os.getenv('MYSQL_PASSWORD'),
        database="testdb",
        connect_timeout=30
    )

# Redis 연결 함수
def get_redis_connection():
    return redis.Redis(
        host=os.getenv('REDIS_HOST', 'my-redis-master'),
        port=6379,
        password=os.getenv('REDIS_PASSWORD'),
        decode_responses=True,
        db=0
    )

# Kafka Producer 설정 (SASL_PLAINTEXT 인증)
def get_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=os.getenv('KAFKA_SERVERS', 'team-kafka.default.svc.cluster.local:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        security_protocol='SASL_PLAINTEXT',
        sasl_mechanism='PLAIN',
        sasl_plain_username=os.getenv('KAFKA_USERNAME', 'user1'),
        sasl_plain_password=os.getenv('KAFKA_PASSWORD', 'password')
    )

# 한국 시간대 가져오기
korea_tz = pytz.timezone('Asia/Seoul')

# 로깅 함수
def log_to_redis(action, details):
    try:
        redis_client = get_redis_connection()
        log_entry = {
            'timestamp': datetime.now(korea_tz).isoformat(),
            'action': action,
            'details': details
        }
        redis_client.lpush('api_logs', json.dumps(log_entry))
        redis_client.ltrim('api_logs', 0, 99)  # 최근 100개 로그만 유지
        redis_client.close()
    except Exception as e:
        print(f"Redis logging error: {str(e)}")

# API 통계 로깅을 비동기로 처리하는 함수 (Redis 백업 포함)
def async_log_api_stats(endpoint, method, status, user_id):
    def _log():
        try:
            # Kafka 로깅 시도
            producer = get_kafka_producer()
            log_data = {
                'developer_tag': os.getenv('DEVELOPER_TAG', 'hyunwoo'),  # 개발자 구분 태그
                'timestamp': datetime.now(korea_tz).isoformat(),
                'endpoint': endpoint,
                'method': method,
                'status': status,
                'user_id': user_id,
                'message': f"{user_id}가 {method} {endpoint} 호출 ({status})"
            }
            topic_name = f"api-logs-{os.getenv('DEVELOPER_TAG', 'hyunwoo')}"
            producer.send(topic_name, log_data)
            producer.flush()
        except Exception as e:
            print(f"Kafka logging error: {str(e)}")
            # Kafka 실패 시 Redis에 백업 저장
            try:
                redis_client = get_redis_connection()
                backup_log = {
                    'timestamp': datetime.now(korea_tz).isoformat(),
                    'action': 'api_stats',
                    'details': f"{user_id}가 {method} {endpoint} 호출 ({status})"
                }
                redis_client.lpush('api_logs', json.dumps(backup_log))
                redis_client.ltrim('api_logs', 0, 99)  # 최근 100개 로그만 유지
                redis_client.close()
                print("API 통계를 Redis에 백업 저장했습니다.")
            except Exception as redis_error:
                print(f"Redis backup logging error: {str(redis_error)}")
    
    # 새로운 스레드에서 로깅 실행
    Thread(target=_log).start()
    
    #  # 스레드 풀을 사용하여 작업 실행
    # thread_pool.submit(_log)

# 로그인 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "로그인이 필요합니다"}), 401
        return f(*args, **kwargs)
    return decorated_function

# 관리자 권한 데코레이터
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({"status": "error", "message": "로그인이 필요합니다"}), 401
        if session['user_id'] != 'admin':
            return jsonify({"status": "error", "message": "관리자 권한이 필요합니다"}), 403
        return f(*args, **kwargs)
    return decorated_function

# MariaDB 엔드포인트
@app.route('/db/message', methods=['POST'])
@login_required
def save_to_db():
    try:
        user_id = session['user_id']
        db = get_db_connection()
        data = request.json
        cursor = db.cursor()
        sql = "INSERT INTO messages (user_id, message, created_at) VALUES (%s, %s, %s)"
        cursor.execute(sql, (user_id, data['message'], datetime.now()))
        db.commit()
        cursor.close()
        db.close()
        
        # 로깅
        log_to_redis('db_insert', f"Message saved: {data['message'][:30]}...")
        
        async_log_api_stats('/db/message', 'POST', 'success', user_id)
        return jsonify({"status": "success"})
    except Exception as e:
        async_log_api_stats('/db/message', 'POST', 'error', user_id)
        log_to_redis('db_insert_error', str(e))
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/db/messages', methods=['GET'])
@login_required
def get_from_db():
    try:
        user_id = session['user_id']
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM messages WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        messages = cursor.fetchall()
        cursor.close()
        db.close()
        
        # 비동기 로깅으로 변경
        async_log_api_stats('/db/messages', 'GET', 'success', user_id)
        
        return jsonify(messages)
    except Exception as e:
        if 'user_id' in session:
            async_log_api_stats('/db/messages', 'GET', 'error', session['user_id'])
        return jsonify({"status": "error", "message": str(e)}), 500

# Redis 로그 조회
@app.route('/logs/redis', methods=['GET'])
def get_redis_logs():
    try:
        redis_client = get_redis_connection()
        logs = redis_client.lrange('api_logs', 0, -1)
        redis_client.close()
        return jsonify([json.loads(log) for log in logs])
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 회원가입 엔드포인트
@app.route('/register', methods=['POST'])
def register():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"status": "error", "message": "사용자명과 비밀번호는 필수입니다"}), 400
            
        # 비밀번호 해시화
        hashed_password = generate_password_hash(password)
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # 사용자명 중복 체크
        cursor.execute("SELECT username FROM users WHERE username = %s", (username,))
        if cursor.fetchone():
            return jsonify({"status": "error", "message": "이미 존재하는 사용자명입니다"}), 400
        
        # 사용자 정보 저장
        sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
        cursor.execute(sql, (username, hashed_password))
        db.commit()
        cursor.close()
        db.close()
        
        return jsonify({"status": "success", "message": "회원가입이 완료되었습니다"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 로그인 엔드포인트
@app.route('/login', methods=['POST'])
def login():
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({"status": "error", "message": "사용자명과 비밀번호는 필수입니다"}), 400
        
        # 관리자 계정 확인 (환경변수 사용)
        admin_username = os.getenv('ADMIN_USERNAME', 'admin')
        admin_password = os.getenv('ADMIN_PASSWORD', 'admin')
        if username == admin_username and password == admin_password:
            session['user_id'] = 'admin'
            session['is_admin'] = True
            
            # Redis 세션 저장 (선택적)
            try:
                redis_client = get_redis_connection()
                session_data = {
                    'user_id': 'admin',
                    'is_admin': True,
                    'login_time': datetime.now().isoformat()
                }
                redis_client.set(f"session:admin", json.dumps(session_data))
                redis_client.expire(f"session:admin", 3600)
            except Exception as redis_error:
                print(f"Redis session error: {str(redis_error)}")
                # Redis 오류는 무시하고 계속 진행
            
            return jsonify({
                "status": "success", 
                "message": "관리자 로그인 성공",
                "username": "admin",
                "is_admin": True
            })
        
        # 일반 사용자 로그인
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        db.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = username  # 세션에 사용자 정보 저장
            
            # Redis 세션 저장 (선택적)
            try:
                redis_client = get_redis_connection()
                session_data = {
                    'user_id': username,
                    'login_time': datetime.now().isoformat()
                }
                redis_client.set(f"session:{username}", json.dumps(session_data))
                redis_client.expire(f"session:{username}", 3600)
            except Exception as redis_error:
                print(f"Redis session error: {str(redis_error)}")
                # Redis 오류는 무시하고 계속 진행
            
            return jsonify({
                "status": "success", 
                "message": "로그인 성공",
                "username": username,
                "is_admin": False
            })
        
        return jsonify({"status": "error", "message": "잘못된 인증 정보"}), 401
        
    except Exception as e:
        print(f"Login error: {str(e)}")  # 서버 로그에 에러 출력
        return jsonify({"status": "error", "message": "로그인 처리 중 오류가 발생했습니다"}), 500

# 로그아웃 엔드포인트
@app.route('/logout', methods=['POST'])
def logout():
    try:
        if 'user_id' in session:
            username = session['user_id']
            # Redis 세션 삭제 시도 (실패해도 계속 진행)
            try:
                redis_client = get_redis_connection()
                redis_client.delete(f"session:{username}")
            except Exception as redis_error:
                print(f"Redis 세션 삭제 실패 (무시): {redis_error}")
            
            # Flask 세션 정리
            session.pop('user_id', None)
            session.pop('is_admin', None)
            
        return jsonify({"status": "success", "message": "로그아웃 성공"})
    except Exception as e:
        print(f"로그아웃 오류: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 메시지 검색 (DB에서 검색)
@app.route('/db/messages/search', methods=['GET'])
@login_required
def search_messages():
    try:
        query = request.args.get('q', '')
        user_id = session['user_id']
        
        # DB에서 검색
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        sql = "SELECT * FROM messages WHERE user_id = %s AND message LIKE %s ORDER BY created_at DESC"
        cursor.execute(sql, (user_id, f"%{query}%"))
        results = cursor.fetchall()
        cursor.close()
        db.close()
        
        # 검색 이력을 Kafka에 저장
        async_log_api_stats('/db/messages/search', 'GET', 'success', user_id)
        
        return jsonify(results)
    except Exception as e:
        if 'user_id' in session:
            async_log_api_stats('/db/messages/search', 'GET', 'error', session['user_id'])
        return jsonify({"status": "error", "message": str(e)}), 500

# Kafka 로그 조회 엔드포인트 (Redis 백업 포함)
@app.route('/logs/kafka', methods=['GET'])
@login_required
def get_kafka_logs():
    try:
        # Kafka에서 로그 조회 시도
        topic_name = f"api-logs-{os.getenv('DEVELOPER_TAG', 'hyunwoo')}"
        consumer = KafkaConsumer(
            topic_name,
            bootstrap_servers=os.getenv('KAFKA_SERVERS', 'team-kafka.default.svc.cluster.local:9092'),
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            group_id='api-logs-viewer',
            auto_offset_reset='earliest',
            consumer_timeout_ms=5000,
            security_protocol='SASL_PLAINTEXT',
            sasl_mechanism='PLAIN',
            sasl_plain_username=os.getenv('KAFKA_USERNAME', 'user1'),
            sasl_plain_password=os.getenv('KAFKA_PASSWORD', 'password')
        )
        
        logs = []
        my_developer_tag = os.getenv('DEVELOPER_TAG', 'hyunwoo')  # 내 개발자 태그
        
        try:
            for message in consumer:
                # 내 개발자 태그 로그만 필터링
                if message.value.get('developer_tag') == my_developer_tag:
                    logs.append({
                        'developer_tag': message.value['developer_tag'],
                        'timestamp': message.value['timestamp'],
                        'endpoint': message.value['endpoint'],
                        'method': message.value['method'],
                        'status': message.value['status'],
                        'user_id': message.value['user_id'],
                        'message': message.value['message']
                    })
                    if len(logs) >= 100:
                        break
        finally:
            consumer.close()
        
        # Kafka에서 로그를 가져왔다면 반환
        if logs:
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return jsonify(logs)
        
        # Kafka에서 로그가 없으면 Redis 백업에서 API 통계 로그 찾기
        print("Kafka에서 로그를 찾을 수 없어 Redis 백업을 확인합니다.")
        redis_client = get_redis_connection()
        redis_logs = redis_client.lrange('api_logs', 0, -1)
        redis_client.close()
        
        # Redis에서 API 통계 로그만 필터링
        api_stats_logs = []
        for log_str in redis_logs:
            try:
                log_data = json.loads(log_str)
                if log_data.get('action') == 'api_stats':
                    # Redis 백업 로그를 Kafka 형식으로 변환
                    details = log_data.get('details', '')
                    api_stats_logs.append({
                        'developer_tag': my_developer_tag,
                        'timestamp': log_data.get('timestamp'),
                        'endpoint': 'unknown',
                        'method': 'unknown',
                        'status': 'success',
                        'user_id': 'unknown',
                        'message': details
                    })
            except:
                continue
        
        # 시간 역순으로 정렬
        api_stats_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(api_stats_logs)
        
    except Exception as e:
        print(f"Kafka log retrieval error: {str(e)}")
        # Kafka 오류 시에도 Redis 백업 시도
        try:
            redis_client = get_redis_connection()
            redis_logs = redis_client.lrange('api_logs', 0, -1)
            redis_client.close()
            
            api_stats_logs = []
            for log_str in redis_logs:
                try:
                    log_data = json.loads(log_str)
                    if log_data.get('action') == 'api_stats':
                        details = log_data.get('details', '')
                        api_stats_logs.append({
                            'developer_tag': os.getenv('DEVELOPER_TAG', 'hyunwoo'),
                            'timestamp': log_data.get('timestamp'),
                            'endpoint': 'unknown',
                            'method': 'unknown',
                            'status': 'success',
                            'user_id': 'unknown',
                            'message': details
                        })
                except:
                    continue
            
            api_stats_logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return jsonify(api_stats_logs)
        except Exception as redis_error:
            print(f"Redis backup retrieval error: {str(redis_error)}")
            return jsonify({"status": "error", "message": "Kafka와 Redis 모두에서 로그를 가져올 수 없습니다."}), 500

# 관리자 전용 - 전체 사용자 목록 조회
@app.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        
        # 사용자 기본 정보와 통계 조회
        cursor.execute("""
            SELECT 
                u.id,
                u.username,
                u.created_at,
                COUNT(m.id) as message_count,
                MAX(m.created_at) as last_message_at
            FROM users u
            LEFT JOIN messages m ON u.username = m.user_id
            GROUP BY u.id, u.username, u.created_at
            ORDER BY u.created_at DESC
        """)
        users = cursor.fetchall()
        
        cursor.close()
        db.close()
        
        # 관리자 계정 정보 추가 (하드코딩)
        admin_info = {
            'id': 0,
            'username': 'admin',
            'created_at': '2025-01-01 00:00:00',  # 고정 날짜
            'message_count': 0,
            'last_message_at': None
        }
        
        # 관리자를 맨 위에 추가
        all_users = [admin_info] + users
        
        # API 통계 로깅
        async_log_api_stats('/admin/users', 'GET', 'success', 'admin')
        
        return jsonify({
            "status": "success",
            "users": all_users,
            "total_count": len(all_users)
        })
        
    except Exception as e:
        async_log_api_stats('/admin/users', 'GET', 'error', 'admin')
        print(f"Admin users list error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

# 관리자 전용 - 특정 사용자의 모든 메시지 조회
@app.route('/admin/users/<username>/messages', methods=['GET'])
@admin_required
def get_user_messages(username):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("""
            SELECT * FROM messages 
            WHERE user_id = %s 
            ORDER BY created_at DESC
        """, (username,))
        messages = cursor.fetchall()
        cursor.close()
        db.close()
        
        # API 통계 로깅
        async_log_api_stats(f'/admin/users/{username}/messages', 'GET', 'success', 'admin')
        
        return jsonify({
            "status": "success",
            "username": username,
            "messages": messages,
            "message_count": len(messages)
        })
        
    except Exception as e:
        async_log_api_stats(f'/admin/users/{username}/messages', 'GET', 'error', 'admin')
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 