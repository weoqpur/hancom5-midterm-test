# Flask Todo App

Flask + SQLite + jQuery를 사용한 할 일 관리 API 및 웹 UI입니다.
Todo 기능에서 발생하는 SQLite 쿼리는 별도 MySQL 서버의 `query_log` 테이블에 저장됩니다.

## 1. MySQL 서버 설정

MySQL 서버 VM에서 먼저 로그 DB와 계정을 생성합니다.

```bash
mysql -u root -p < mysql_log.sql
```

`mysql_log.sql`이 생성하는 항목:

- `todo_log` 데이터베이스
- `query_log(type, sql, dateime)` 테이블
- `todo_logger` 계정
- `todo_logger` 계정의 `todo_log` DB 접근 권한

Flask 서버와 MySQL 서버가 다른 VM이면 MySQL 외부 접속을 허용합니다.

```bash
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

아래 값을 찾습니다.

```text
bind-address = 127.0.0.1
```

다음처럼 변경합니다.

```text
bind-address = 0.0.0.0
```

MySQL을 재시작합니다.

```bash
sudo systemctl restart mysql
```

방화벽을 사용하는 경우 Flask 서버 IP에서 3306 포트 접속을 허용합니다.

```bash
sudo ufw allow from Flask서버IP to any port 3306
```

## 2. Flask 서버 설정

Flask 서버 VM에서 저장소를 클론한 뒤 프로젝트 폴더로 이동합니다.

```bash
git clone <저장소 주소>
cd <프로젝트명>
```

패키지를 설치합니다.

```bash
pip install -r requirements.txt
```

환경설정 파일을 생성합니다.

```bash
cp .env.example .env
nano .env
```

`.env`에서 MySQL 서버 IP를 실제 IP로 수정합니다.

```env
MYSQL_HOST=MySQL서버IP
```

`.env` 전체 예시:

```env
FLASK_SECRET_KEY=todo-app-secret-key
MYSQL_LOG_ENABLED=1
MYSQL_HOST=192.168.56.102
MYSQL_PORT=3306
MYSQL_USER=todo_logger
MYSQL_PASSWORD=todo_logger_pw
MYSQL_DATABASE=todo_log
```

MySQL 로그를 잠시 끄고 SQLite 기능만 확인하려면 아래처럼 변경합니다.

```env
MYSQL_LOG_ENABLED=0
```

## 3. MySQL 접속 확인

Flask 서버 VM에서 MySQL 서버 접속을 확인합니다.

```bash
mysql -h MySQL서버IP -P 3306 -u todo_logger -p todo_log
```

비밀번호:

```text
todo_logger_pw
```

접속이 안 되면 아래 항목을 확인합니다.

- Flask 서버 `.env`의 `MYSQL_HOST`
- MySQL 서버의 `bind-address`
- MySQL 계정 권한
- MySQL 서버 방화벽 3306 포트
- 두 VM 간 네트워크 통신

## 4. Flask 앱 실행

Flask 서버 VM에서 실행합니다.

```bash
python app.py
```

브라우저에서 접속합니다.

```text
http://localhost:5000
```

다른 PC에서 VM으로 접속할 경우:

```text
http://Flask서버IP:5000
```

최초 실행 시 `todo.db` 파일이 자동 생성되고, `member`, `todolist` 테이블과 기본 계정이 자동 생성됩니다.

## 5. 기본 로그인 정보

```text
ID: admin
PW: admin1234
```

로그인 화면에는 기본 계정 정보가 자동 입력되지 않습니다.

## 6. 주요 기능

- 회원가입
- 로그인
- 할 일 목록 조회
- 할 일 추가
- 할 일 완료 처리
- 할 일 삭제
- SQLite 쿼리 MySQL 로그 저장

## 7. API 테스트

### 회원가입

```http
POST /signup
Content-Type: application/json

{
  "uname": "홍길동",
  "uid": "hong",
  "upwd": "1234"
}
```

### 로그인

```http
POST /login
Content-Type: application/json

{
  "uid": "admin",
  "upwd": "admin1234"
}
```

### 할 일 조회

```http
GET /todos
```

### 할 일 추가

```http
POST /todos
Content-Type: application/json

{
  "title": "Flask 과제하기"
}
```

### 할 일 완료 처리

```http
PUT /todos/1
```

### 할 일 삭제

```http
DELETE /todos/1
```

## 8. 데이터베이스 구조

SQLite 파일명은 `todo.db`입니다.

SQLite 테이블:

- `member(idx, uname, uid, upwd, datetime)`
- `todolist(id, title, uid, completed, datetime)`

MySQL 로그 테이블:

- `query_log(type, sql, dateime)`

로그 예시:

```text
type: insert
sql: INSERT INTO todolist (title, uid, completed, datetime) VALUES ('Flask 과제하기', 'admin', 0, '2026-05-28 10:00:00')
dateime: 2026-05-28 10:00:00
```

로그 확인 쿼리:

```sql
SELECT type, sql, dateime FROM query_log ORDER BY dateime DESC;
```
