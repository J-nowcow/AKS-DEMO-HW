<template>
  <div id="app">
    <h1>K8s 마이크로서비스 데모</h1>
    
    <!-- 로그인/회원가입 섹션 -->
    <div class="section" v-if="!isLoggedIn">
      <div v-if="!showRegister">
        <h2>로그인</h2>
        <input v-model="username" placeholder="사용자명">
        <input v-model="password" type="password" placeholder="비밀번호">
        <button @click="login">로그인</button>
        <button @click="showRegister = true" class="register-btn">회원가입</button>
      </div>
      <div v-else>
        <h2>회원가입</h2>
        <input v-model="registerUsername" placeholder="사용자명">
        <input v-model="registerPassword" type="password" placeholder="비밀번호">
        <input v-model="confirmPassword" type="password" placeholder="비밀번호 확인">
        <button @click="register">가입하기</button>
        <button @click="showRegister = false">로그인으로 돌아가기</button>
      </div>
    </div>

    <div v-else>
      <div class="user-info">
        <span>안녕하세요, {{ username }}님</span>
        <button @click="logout">로그아웃</button>
      </div>

      <div class="container">
        <div class="section">
          <h2>MariaDB 메시지 관리</h2>
          <input v-model="dbMessage" placeholder="저장할 메시지 입력">
          <button @click="saveToDb">DB에 저장</button>
          <button @click="getFromDb">DB에서 조회</button>
          <button @click="insertSampleData" class="sample-btn">샘플 데이터 저장</button>
          <div v-if="loading" class="loading-spinner">
            <p>데이터를 불러오는 중...</p>
          </div>
          <div v-if="dbData.length && !loading">
            <h3>저장된 메시지:</h3>
            <ul>
              <li v-for="item in dbData" :key="item.id">{{ item.message }} ({{ formatDate(item.created_at) }})</li>
            </ul>
          </div>
        </div>

        <div class="section">
          <h2>Redis 로그</h2>
          <button @click="getRedisLogs">로그 조회</button>
          <div v-if="redisLogs.length">
            <h3>API 호출 로그:</h3>
            <ul>
              <li v-for="(log, index) in redisLogs" :key="index">
                [{{ formatDate(log.timestamp) }}] {{ log.action }}: {{ log.details }}
              </li>
            </ul>
          </div>
        </div>

        <div class="section">
          <h2>Kafka 통계 로그</h2>
          <button @click="getKafkaLogs">통계 로그 조회</button>
          <div v-if="kafkaLogs.length">
            <h3>API 통계 및 감사 로그:</h3>
            <table class="log-table">
              <thead>
                <tr>
                  <th>시간</th>
                  <th>사용자</th>
                  <th>메서드</th>
                  <th>엔드포인트</th>
                  <th>상태</th>
                  <th>메시지</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(log, index) in kafkaLogs" :key="index" :class="{'error-log': log.status === 'error'}">
                  <td>{{ formatDate(log.timestamp) }}</td>
                  <td>{{ log.user_id }}</td>
                  <td><span class="method-badge" :class="log.method.toLowerCase()">{{ log.method }}</span></td>
                  <td>{{ log.endpoint }}</td>
                  <td><span class="status-badge" :class="log.status">{{ log.status }}</span></td>
                  <td>{{ log.message }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="section">
          <h2>메시지 검색</h2>
          <div class="search-section">
            <input v-model="searchQuery" placeholder="메시지 검색">
            <button @click="searchMessages">검색</button>
            <button @click="getAllMessages" class="view-all-btn">전체 메시지 보기</button>
          </div>
          <div v-if="searchResults.length > 0" class="search-results">
            <h3>검색 결과:</h3>
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>메시지</th>
                  <th>생성 시간</th>
                  <th>사용자</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="result in searchResults" :key="result.id">
                  <td>{{ result.id }}</td>
                  <td>{{ result.message }}</td>
                  <td>{{ formatDate(result.created_at) }}</td>
                  <td>{{ result.user_id || '없음' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 관리자 전용 사용자 목록 -->
        <div class="section admin-section" v-if="isAdmin">
          <h2>👑 관리자 전용 - 전체 사용자 목록</h2>
          <div class="admin-controls">
            <button @click="getAllUsers" class="admin-btn">사용자 목록 새로고침</button>
            <span class="user-count" v-if="allUsers.length">총 {{ allUsers.length }}명의 사용자</span>
          </div>
          <div v-if="allUsers.length" class="users-table">
            <table class="admin-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>사용자명</th>
                  <th>가입일</th>
                  <th>메시지 수</th>
                  <th>마지막 활동</th>
                  <th>권한</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="user in allUsers" :key="user.id" :class="{'admin-row': user.username === 'admin'}">
                  <td>{{ user.id }}</td>
                  <td>
                    <span v-if="user.username === 'admin'" class="admin-badge">👑</span>
                    {{ user.username }}
                  </td>
                  <td>{{ formatDate(user.created_at) }}</td>
                  <td>{{ user.message_count }}</td>
                  <td>{{ user.last_message_at ? formatDate(user.last_message_at) : '없음' }}</td>
                  <td>
                    <span v-if="user.username === 'admin'" class="role-badge admin">관리자</span>
                    <span v-else class="role-badge user">일반 사용자</span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

// nginx 프록시를 통해 요청하도록 수정
const API_BASE_URL = '/api';

export default {
  name: 'App',
  data() {
    return {
      username: '',
      password: '',
      isLoggedIn: false,
      isAdmin: false,
      searchQuery: '',
      dbMessage: '',
      dbData: [],
      redisLogs: [],
      kafkaLogs: [],
      allUsers: [],
      sampleMessages: [
        '안녕하세요! 테스트 메시지입니다.',
        'K8s 데모 샘플 데이터입니다.',
        '마이크로서비스 테스트 중입니다.',
        '샘플 메시지 입니다.'
      ],
      offset: 0,
      limit: 20,
      loading: false,
      hasMore: true,
      showRegister: false,
      registerUsername: '',
      registerPassword: '',
      confirmPassword: '',
      currentUser: null,
      searchResults: []
    }
  },
  methods: {
    // 날짜를 사용자 친화적인 형식으로 변환
    formatDate(dateString) {
      const date = new Date(dateString);
      return date.toLocaleString();
    },
    
    // MariaDB에 메시지 저장
    async saveToDb() {
      try {
        await axios.post(`${API_BASE_URL}/db/message`, {
          message: this.dbMessage
        }, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.dbMessage = '';
        this.getFromDb();
        this.getRedisLogs();
        this.getKafkaLogs();
      } catch (error) {
        console.error('DB 저장 실패:', error);
      }
    },

    // MariaDB에서 메시지 조회 (페이지네이션 적용)
    async getFromDb() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/db/messages?offset=${this.offset}&limit=${this.limit}`, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.dbData = response.data;
        this.hasMore = response.data.length === this.limit;
      } catch (error) {
        console.error('DB 조회 실패:', error);
      } finally {
        this.loading = false;
      }
    },

    // 샘플 데이터를 DB에 저장
    async insertSampleData() {
      const randomMessage = this.sampleMessages[Math.floor(Math.random() * this.sampleMessages.length)];
      try {
        await axios.post(`${API_BASE_URL}/db/message`, {
          message: randomMessage
        }, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.getFromDb();
        this.getRedisLogs();
        this.getKafkaLogs();
      } catch (error) {
        console.error('샘플 데이터 저장 실패:', error);
      }
    },

    // Redis에 저장된 API 호출 로그 조회
    async getRedisLogs() {
      try {
        const response = await axios.get(`${API_BASE_URL}/logs/redis`, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.redisLogs = response.data;
      } catch (error) {
        console.error('Redis 로그 조회 실패:', error);
      }
    },

    // Kafka에 저장된 API 통계 로그 조회
    async getKafkaLogs() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/logs/kafka`, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.kafkaLogs = response.data;
      } catch (error) {
        console.error('Kafka 로그 조회 실패:', error);
        if (error.response && error.response.status === 401) {
          alert('로그인이 필요합니다. 다시 로그인해주세요.');
        } else {
          alert('Kafka 로그 조회에 실패했습니다.');
        }
      } finally {
        this.loading = false;
      }
    },

    // 사용자 로그인 처리
    async login() {
      try {
        const response = await axios.post(`${API_BASE_URL}/login`, {
          username: this.username,
          password: this.password
        }, {
          withCredentials: true  // 세션 쿠키 포함
        });
        
        if (response.data.status === 'success') {
          this.isLoggedIn = true;
          this.isAdmin = response.data.is_admin || false;
          this.currentUser = this.username;
          this.username = '';
          this.password = '';
          // 로그인 성공 시 기본 데이터 로드 (Redis 로그는 자동으로 로드하지 않음)
          this.getFromDb();
          // 관리자인 경우 사용자 목록 로드
          if (this.isAdmin) {
            this.getAllUsers();
          }
        } else {
          alert(response.data.message || '로그인에 실패했습니다.');
        }
      } catch (error) {
        console.error('로그인 실패:', error);
        alert(error.response && error.response.data 
          ? error.response.data.message 
          : '로그인에 실패했습니다.');
      }
    },
    
    // 로그아웃 처리
    async logout() {
      try {
        await axios.post(`${API_BASE_URL}/logout`, {}, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.isLoggedIn = false;
        this.username = '';
        this.password = '';
        // 로그아웃 시 데이터 초기화
        this.redisLogs = [];
        this.kafkaLogs = [];
        this.dbData = [];
        this.allUsers = [];
        this.searchResults = [];
      } catch (error) {
        console.error('로그아웃 실패:', error);
      }
    },

    // 메시지 검색 기능
    async searchMessages() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/db/messages/search`, {
          params: { q: this.searchQuery },
          withCredentials: true  // 세션 쿠키 포함
        });
        this.searchResults = response.data;
        // 검색 후 로그 업데이트
        this.getKafkaLogs();
      } catch (error) {
        console.error('검색 실패:', error);
        alert('검색에 실패했습니다.');
      } finally {
        this.loading = false;
      }
    },

    // 전체 메시지 조회
    async getAllMessages() {
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/db/messages`, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.searchResults = response.data;
        // 전체 메시지 조회 후 로그 업데이트
        this.getKafkaLogs();
      } catch (error) {
        console.error('전체 메시지 로드 실패:', error);
      } finally {
        this.loading = false;
      }
    },

    // 페이지네이션을 위한 추가 데이터 로드
    async loadMore() {
      this.offset += this.limit;
      await this.getFromDb();
    },

    // 회원가입 처리
    async register() {
      if (this.registerPassword !== this.confirmPassword) {
        alert('비밀번호가 일치하지 않습니다');
        return;
      }
      
      try {
        const response = await axios.post(`${API_BASE_URL}/register`, {
          username: this.registerUsername,
          password: this.registerPassword
        }, {
          withCredentials: true  // 세션 쿠키 포함
        });
        
        if (response.data.status === 'success') {
          alert('회원가입이 완료되었습니다. 로그인해주세요.');
          this.showRegister = false;
          this.registerUsername = '';
          this.registerPassword = '';
          this.confirmPassword = '';
        }
      } catch (error) {
        console.error('회원가입 실패:', error);
        alert(error.response && error.response.data && error.response.data.message 
          ? error.response.data.message 
          : '회원가입에 실패했습니다.');
      }
    },

    // 관리자 전용 - 전체 사용자 목록 조회
    async getAllUsers() {
      if (!this.isAdmin) {
        alert('관리자 권한이 필요합니다.');
        return;
      }
      
      try {
        this.loading = true;
        const response = await axios.get(`${API_BASE_URL}/admin/users`, {
          withCredentials: true  // 세션 쿠키 포함
        });
        this.allUsers = response.data.users;
      } catch (error) {
        console.error('사용자 목록 조회 실패:', error);
        alert('사용자 목록 조회에 실패했습니다.');
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style>
.container {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.section {
  margin-bottom: 30px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 5px;
}

input {
  margin-right: 10px;
  padding: 5px;
  width: 300px;
}

button {
  margin-right: 10px;
  padding: 5px 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

button:hover {
  background-color: #0056b3;
}

.sample-btn {
  background-color: #28a745;
}

.sample-btn:hover {
  background-color: #218838;
}

ul {
  list-style-type: none;
  padding: 0;
}

li {
  margin: 5px 0;
  padding: 5px;
  border-bottom: 1px solid #eee;
}

.pagination {
  text-align: center;
  margin-top: 10px;
}

.pagination button {
  padding: 5px 10px;
  background-color: #007bff;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.pagination button:hover {
  background-color: #0056b3;
}

.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

.loading-spinner {
  text-align: center;
  margin-top: 20px;
  font-size: 16px;
  color: #555;
}

.user-info {
  text-align: right;
  padding: 10px;
  margin-bottom: 20px;
}

.search-section {
  margin: 10px 0;
}

.search-section input {
  width: 200px;
  margin-right: 10px;
}

.register-btn {
  background-color: #6c757d;
}

.register-btn:hover {
  background-color: #5a6268;
}

.search-results {
  margin-top: 20px;
}

.search-results table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
}

.search-results th,
.search-results td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #eee;
}

.search-results th {
  background-color: #f8f9fa;
  font-weight: bold;
}

.search-results tr:hover {
  background-color: #f5f5f5;
}

.view-all-btn {
  background-color: #6c757d;
}

.view-all-btn:hover {
  background-color: #5a6268;
}

/* Kafka 로그 테이블 스타일 */
.log-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 15px;
  font-size: 14px;
}

.log-table th,
.log-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #dee2e6;
  vertical-align: middle;
}

.log-table th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #495057;
  font-size: 13px;
}

.log-table tr:hover {
  background-color: #f8f9fa;
}

.log-table tr.error-log {
  background-color: #fff5f5;
}

.log-table tr.error-log:hover {
  background-color: #fed7d7;
}

/* 메서드 배지 스타일 */
.method-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
  color: white;
}

.method-badge.get {
  background-color: #28a745;
}

.method-badge.post {
  background-color: #007bff;
}

.method-badge.put {
  background-color: #ffc107;
  color: #212529;
}

.method-badge.delete {
  background-color: #dc3545;
}

/* 상태 배지 스타일 */
.status-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}

.status-badge.success {
  background-color: #d4edda;
  color: #155724;
  border: 1px solid #c3e6cb;
}

.status-badge.error {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

/* 반응형 테이블 */
@media (max-width: 768px) {
  .log-table {
    font-size: 12px;
  }
  
  .log-table th,
  .log-table td {
    padding: 6px 4px;
  }
  
  .method-badge,
  .status-badge {
    font-size: 10px;
    padding: 2px 6px;
  }
}

/* 관리자 전용 스타일 */
.admin-section {
  border: 2px solid #ffd700;
  background: linear-gradient(135deg, #fff9e6 0%, #ffffff 100%);
  box-shadow: 0 4px 12px rgba(255, 215, 0, 0.2);
}

.admin-section h2 {
  color: #b8860b;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
}

.admin-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: rgba(255, 215, 0, 0.1);
  border-radius: 5px;
}

.admin-btn {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4a 100%);
  color: #8b4513;
  border: none;
  padding: 8px 16px;
  border-radius: 5px;
  font-weight: bold;
  cursor: pointer;
  transition: all 0.3s ease;
}

.admin-btn:hover {
  background: linear-gradient(135deg, #ffed4a 0%, #ffd700 100%);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.4);
}

.user-count {
  color: #8b4513;
  font-weight: bold;
  background: rgba(255, 255, 255, 0.7);
  padding: 5px 10px;
  border-radius: 15px;
}

.admin-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 10px;
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.admin-table th {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4a 100%);
  color: #8b4513;
  font-weight: bold;
  padding: 12px;
  text-align: left;
  border-bottom: 2px solid #ddd;
}

.admin-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #eee;
  vertical-align: middle;
}

.admin-table tr:hover {
  background: rgba(255, 215, 0, 0.05);
}

.admin-table tr.admin-row {
  background: rgba(255, 215, 0, 0.1);
  font-weight: bold;
}

.admin-table tr.admin-row:hover {
  background: rgba(255, 215, 0, 0.15);
}

.admin-badge {
  margin-right: 5px;
  font-size: 16px;
}

.role-badge {
  display: inline-block;
  padding: 3px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: bold;
  text-transform: uppercase;
}

.role-badge.admin {
  background: linear-gradient(135deg, #ffd700 0%, #ffed4a 100%);
  color: #8b4513;
  border: 1px solid #daa520;
}

.role-badge.user {
  background: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}
</style> 